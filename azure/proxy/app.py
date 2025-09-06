import os
import time
import json
from io import BytesIO
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
import httpx
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8000/v1/chat/completions")
INSTANCE_HOURLY_USD = float(os.getenv("INSTANCE_HOURLY_USD", "0.0"))

# Prometheus metrics
c_completion_tokens = Counter("llm_completion_tokens_total", "Completion tokens total")
c_prompt_tokens     = Counter("llm_prompt_tokens_total",     "Prompt tokens total")
g_tokens_per_sec    = Gauge  ("llm_tokens_per_second",       "Tokens/sec (last request)")
g_cost_per_1k_usd   = Gauge  ("llm_cost_per_1k_usd",         "Cost per 1k tokens (estimate)")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def parse_usage_from_json_bytes(b: bytes):
    """Return (prompt_tokens, completion_tokens) from a non-streaming OpenAI response body."""
    try:
        obj = json.loads(b.decode("utf-8"))
        usage = obj.get("usage") or {}
        return int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
    except Exception:
        return 0, 0

def consume_usage_from_sse_chunk(chunk: bytes, prompt_tokens: int, completion_tokens: int):
    """Best-effort: parse any usage objects present in SSE stream lines."""
    try:
        for line in chunk.split(b"\n"):
            if not line.startswith(b"data: "):  # ignore comments/keepalives
                continue
            if line.strip() == b"data: [DONE]":
                continue
            obj = json.loads(line[6:])
            usage = obj.get("usage")
            if usage:
                prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                completion_tokens = usage.get("completion_tokens", completion_tokens)
    except Exception:
        pass
    return int(prompt_tokens or 0), int(completion_tokens or 0)

@app.post("/v1/chat/completions")
async def chat(request: Request):
    payload = await request.json()
    t0 = time.perf_counter()

    client = httpx.AsyncClient(timeout=None)
    stream_cm = client.stream(
        "POST",
        TARGET_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    rstream = await stream_cm.__aenter__()

    # Peek first chunk to measure TTFT and detect content-type/shape
    aiter = rstream.aiter_bytes()
    first_chunk: Optional[bytes] = None
    try:
        async for chunk in aiter:
            if chunk:
                first_chunk = chunk
                break
    except StopAsyncIteration:
        first_chunk = b""

    ttft_ms = max((time.perf_counter() - t0) * 1000.0, 0.0)
    upstream_ct = (rstream.headers.get("content-type") or "").lower()

    # If upstream isn't SSE, treat it as JSON: stream + buffer for usage
    if "text/event-stream" not in upstream_ct:
        buffer = BytesIO()
        if first_chunk:
            buffer.write(first_chunk)

        async def json_stream() -> AsyncGenerator[bytes, None]:
            try:
                if first_chunk:
                    yield first_chunk
                async for chunk in aiter:
                    if chunk:
                        buffer.write(chunk)
                        yield chunk
            finally:
                # When stream ends, parse usage and update metrics
                body = buffer.getvalue()
                p_tok, c_tok = parse_usage_from_json_bytes(body)
                gen_dur = max(time.perf_counter() - (t0 + ttft_ms / 1000.0), 1e-6)
                tps = (c_tok / gen_dur) if c_tok > 0 else 0.0
                cost_per_1k = 0.0
                if INSTANCE_HOURLY_USD > 0 and c_tok > 0:
                    cost_per_token = (INSTANCE_HOURLY_USD * (gen_dur / 3600.0)) / c_tok
                    cost_per_1k = cost_per_token * 1000.0
                if c_tok > 0:
                    c_completion_tokens.inc(c_tok)
                if p_tok > 0:
                    c_prompt_tokens.inc(p_tok)
                g_tokens_per_sec.set(tps)
                g_cost_per_1k_usd.set(cost_per_1k)
                try:
                    await stream_cm.__aexit__(None, None, None)
                finally:
                    await client.aclose()

        resp = StreamingResponse(json_stream(), media_type="application/json")
        resp.headers["X-TTFT-MS"] = f"{ttft_ms:.0f}"
        return resp

    # Else: SSE streaming path
    prompt_tokens = 0
    completion_tokens = 0
    if first_chunk:
        prompt_tokens, completion_tokens = consume_usage_from_sse_chunk(first_chunk, prompt_tokens, completion_tokens)

    async def sse_stream() -> AsyncGenerator[bytes, None]:
        nonlocal prompt_tokens, completion_tokens
        try:
            if first_chunk:
                yield first_chunk
            async for chunk in aiter:
                if chunk:
                    prompt_tokens, completion_tokens = consume_usage_from_sse_chunk(
                        chunk, prompt_tokens, completion_tokens
                    )
                    yield chunk
        finally:
            gen_dur = max(time.perf_counter() - (t0 + ttft_ms / 1000.0), 1e-6)
            tps = (completion_tokens / gen_dur) if completion_tokens > 0 else 0.0
            cost_per_1k = 0.0
            if INSTANCE_HOURLY_USD > 0 and completion_tokens > 0:
                cost_per_token = (INSTANCE_HOURLY_USD * (gen_dur / 3600.0)) / completion_tokens
                cost_per_1k = cost_per_token * 1000.0
            if completion_tokens > 0:
                c_completion_tokens.inc(completion_tokens)
            if prompt_tokens > 0:
                c_prompt_tokens.inc(prompt_tokens)
            g_tokens_per_sec.set(tps)
            g_cost_per_1k_usd.set(cost_per_1k)
            # send optional meta event
            try:
                yield f"event: meta\ndata: {json.dumps({'tps': round(tps,2), 'cost_per_1k': round(cost_per_1k,5)})}\n\n".encode()
            except Exception:
                pass
            try:
                await stream_cm.__aexit__(None, None, None)
            finally:
                await client.aclose()

    resp = StreamingResponse(sse_stream(), media_type="text/event-stream")
    resp.headers["X-TTFT-MS"] = f"{ttft_ms:.0f}"
    return resp
