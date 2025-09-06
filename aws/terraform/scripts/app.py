# app.py  (Lambda proxy for SageMaker, with streaming TTFT + cost/1k)
import os, json, time, base64, boto3, math

REGION   = os.environ.get("REGION")
ENDPOINT = os.environ["ENDPOINT_NAME"]
NS       = "LLM/Serving"

# Set this via Terraform (recommended) or let the code try to fetch it at cold start.
INSTANCE_HOURLY_USD = os.environ.get("INSTANCE_HOURLY_USD")  # e.g. "1.34"
INSTANCE_HOURLY_USD = float(INSTANCE_HOURLY_USD) if INSTANCE_HOURLY_USD else None

smr = boto3.client("sagemaker-runtime", region_name=REGION)
cw  = boto3.client("cloudwatch")

def put_metric(name, value, unit="Count", dims=None):
    dims = dims or [{"Name": "EndpointName", "Value": ENDPOINT}]
    try:
        cw.put_metric_data(
            Namespace=NS,
            MetricData=[{
                "MetricName": name,
                "Dimensions": dims,
                "Unit": unit,
                "Value": float(value)
            }]
        )
    except Exception:
        pass

# Optional: one-time price lookup (fallback if env var not set).
# NOTE: Pricing API lives in us-east-1 and needs iam: pricing:GetProducts
_pricing = None
def get_hourly_price():
    global INSTANCE_HOURLY_USD, _pricing
    if INSTANCE_HOURLY_USD is not None:
        return INSTANCE_HOURLY_USD
    try:
        if _pricing is None:
            _pricing = boto3.client("pricing", region_name="us-east-1")
        # Very simple filter; in practice you may refine by Tenancy/OS/term, etc.
        # For SageMaker, we select the OnDemand rate for your instance type in your region.
        resp = _pricing.get_products(
            ServiceCode="AmazonSageMaker",
            Filters=[
                {"Type":"TERM_MATCH","Field":"instanceType","Value":os.environ.get("SM_INSTANCE_TYPE","ml.g5.2xlarge")},
                {"Type":"TERM_MATCH","Field":"location","Value": region_to_location(REGION)},
                {"Type":"TERM_MATCH","Field":"operation","Value":"CreateEndpoint"}
            ],
            MaxResults=1
        )
        item = json.loads(resp["PriceList"][0])
        # Walk to OnDemand USD price per hour
        terms = next(iter(item["terms"]["OnDemand"].values()))
        dim   = next(iter(terms["priceDimensions"].values()))
        price = float(dim["pricePerUnit"]["USD"])
        INSTANCE_HOURLY_USD = price
        return price
    except Exception:
        return None

# map region to pricing "location" string (minimal set; add as needed)
_REGION_TO_LOCATION = {
    "us-east-1": "US East (N. Virginia)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "EU (Ireland)",
    "ap-south-1": "Asia Pacific (Mumbai)",
}
def region_to_location(r): return _REGION_TO_LOCATION.get(r, "US East (N. Virginia)")

def handler(event, context):
    # Read body
    if "body" not in event:
        return {"statusCode": 400, "body": "missing body"}
    body = event["body"]
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        payload = json.loads(body)
    except Exception:
        return {"statusCode": 400, "body": "invalid JSON"}

    # Check if streaming is requested
    is_streaming = payload.get("stream", False)
    
    if is_streaming:
        return handle_streaming_request(payload)
    else:
        return handle_non_streaming_request(payload)

def handle_streaming_request(payload):
    """Optimized streaming handler with proper SSE format"""
    t0 = time.time()
    first_token_at = None
    total_tokens = 0
    sse_chunks = []  # Store SSE formatted chunks

    try:
        resp = smr.invoke_endpoint_with_response_stream(
            EndpointName=ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(payload).encode("utf-8"),
        )

        # Stream processing with SSE formatting
        last_chunk_json = None
        
        for event in resp["Body"]:
            if "PayloadPart" in event:
                if first_token_at is None:
                    first_token_at = time.time()
                
                chunk_data = event["PayloadPart"]["Bytes"]
                
                # Parse chunk for real-time token counting and SSE formatting
                try:
                    chunk_str = chunk_data.decode("utf-8")
                    chunk_json = json.loads(chunk_str)
                    choices = chunk_json.get("choices", [])
                    
                    if choices and "delta" in choices[0]:
                        content = choices[0]["delta"].get("content", "")
                        if content:
                            # Count tokens in this chunk
                            new_tokens = len(content.split()) if content.split() else (1 if content.strip() else 0)
                            total_tokens += new_tokens
                        
                        # Format as SSE and add to chunks
                        sse_line = f"data: {json.dumps(chunk_json)}\n\n"
                        sse_chunks.append(sse_line)
                        last_chunk_json = chunk_json
                        
                except:
                    # If parsing fails, still try to format as SSE
                    try:
                        sse_line = f"data: {chunk_data.decode('utf-8')}\n\n"
                        sse_chunks.append(sse_line)
                    except:
                        pass
                    
            elif "ModelStreamError" in event:
                err = event["ModelStreamError"]["Message"]
                return {"statusCode": 502, "body": json.dumps({"error": err})}

        # Add final DONE marker
        sse_chunks.append("data: [DONE]\n\n")
        
        # Create final SSE response
        final_sse_response = "".join(sse_chunks)
        
        # Get final usage info from last chunk or estimate
        if last_chunk_json and "usage" in last_chunk_json:
            usage = last_chunk_json["usage"]
            comp_toks = int(usage.get("completion_tokens", total_tokens))
            prompt_toks = int(usage.get("prompt_tokens", 0))
        else:
            comp_toks = total_tokens
            prompt_toks = payload.get("messages", [{}])[0].get("content", "").count(" ") + 1 if payload.get("messages") else 0

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # Calculate metrics
    ttft_ms = int((first_token_at or time.time())*1000 - t0*1000)

    dur_s = max(1e-6, time.time() - t0)
    tps = (comp_toks / dur_s) if comp_toks else 0.0

    # Push metrics
    put_metric("TTFT", ttft_ms, unit="Milliseconds")
    if prompt_toks: put_metric("PromptTokens", prompt_toks, unit="Count")
    if comp_toks:
        put_metric("CompletionTokens", comp_toks, unit="Count")
        put_metric("TokensPerSecond", tps, unit="Count/Second")
        put_metric("TokensGenerated", comp_toks, unit="Count")
        put_metric("RequestCount", 1, unit="Count")
        put_metric("CompletionTimeSeconds", dur_s, unit="Seconds")

    # Cost calculation
    hourly = get_hourly_price()
    cost_per_1k = None
    if hourly and tps > 0:
        cost_per_1k = (hourly / (tps * 3600.0)) * 1000.0
        put_metric("CostPer1kTokensUSD", cost_per_1k, unit="None")

    headers = {
        "Content-Type": "text/event-stream",  # Changed to SSE content type
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Endpoint": ENDPOINT,
        "X-TTFT-MS": str(ttft_ms),
        "X-Completion-Tokens": str(comp_toks),
        "X-Prompt-Tokens": str(prompt_toks),
        "X-Tokens-Per-Second": f"{tps:.2f}",
    }
    if cost_per_1k is not None:
        headers["X-Cost-Per-1K-USD"] = f"{cost_per_1k:.6f}"

    return {"statusCode": 200, "headers": headers, "body": final_sse_response}

def handle_non_streaming_request(payload):
    """Optimized non-streaming handler"""
    t0 = time.time()
    
    try:
        resp = smr.invoke_endpoint(
            EndpointName=ENDPOINT,
            ContentType="application/json", 
            Body=json.dumps(payload).encode("utf-8")
        )
        
        result = json.loads(resp["Body"].read().decode("utf-8"))
        
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # Calculate metrics  
    usage = result.get("usage", {})
    prompt_toks = int(usage.get("prompt_tokens") or 0)
    comp_toks = int(usage.get("completion_tokens") or 0)
    
    dur_s = max(1e-6, time.time() - t0)
    tps = (comp_toks / dur_s) if comp_toks else 0.0

    # Push metrics
    if prompt_toks: put_metric("PromptTokens", prompt_toks, unit="Count")
    if comp_toks:
        put_metric("CompletionTokens", comp_toks, unit="Count")
        put_metric("TokensPerSecond", tps, unit="Count/Second")
        put_metric("TokensGenerated", comp_toks, unit="Count")
        put_metric("RequestCount", 1, unit="Count")
        put_metric("CompletionTimeSeconds", dur_s, unit="Seconds")

    # Cost calculation
    hourly = get_hourly_price()
    cost_per_1k = None
    if hourly and tps > 0:
        cost_per_1k = (hourly / (tps * 3600.0)) * 1000.0
        put_metric("CostPer1kTokensUSD", cost_per_1k, unit="None")

    headers = {
        "Content-Type": "application/json",
        "X-Endpoint": ENDPOINT,
        "X-Completion-Tokens": str(comp_toks),
        "X-Prompt-Tokens": str(prompt_toks),
        "X-Tokens-Per-Second": f"{tps:.2f}",
    }
    if cost_per_1k is not None:
        headers["X-Cost-Per-1K-USD"] = f"{cost_per_1k:.6f}"

    return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
