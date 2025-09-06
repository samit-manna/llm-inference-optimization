#!/usr/bin/env python3
"""
AWS SageMaker Streaming Benchmark Script

Measures Time to First Token (TTFT) and total latency for streaming responses
from AWS API Gateway -> Lambda -> SageMaker endpoints.

Usage:
    python3 aws_streaming_bench.py \
        --url https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat/completions \
        --requests 50 \
        --max-tokens 64 \
        --output aws_streaming_results.json
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional

import httpx


def percentile(data: List[float], p: float) -> Optional[float]:
    """Calculate percentile using nearest-rank method."""
    if not data:
        return None
    sorted_data = sorted(data)
    k = max(0, min(len(sorted_data) - 1, int(round(p / 100 * (len(sorted_data) - 1)))))
    return sorted_data[k]


async def streaming_request(
    client: httpx.AsyncClient,
    url: str,
    prompt: str,
    max_tokens: int,
    timeout_s: float = 30.0
) -> Dict:
    """
    Send a single streaming request and measure TTFT and total latency.
    
    Returns:
        Dict with keys: ok, ttft_s, total_s, tokens_received, error, aws_headers
    """
    payload = {
        "model": "llama",
        "messages": [
            {"role": "system", "content": "You are a helpful and concise assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }
    
    start_time = time.time()
    ttft = None
    total_time = None
    tokens_received = 0
    aws_headers = {}
    error = None
    
    try:
        async with client.stream(
            "POST", url,
            json=payload,
            timeout=timeout_s,
            headers={"Accept": "text/event-stream"}
        ) as response:
            if response.status_code != 200:
                error = f"HTTP {response.status_code}: {response.text}"
                return {
                    "ok": False,
                    "ttft_s": None,
                    "total_s": None,
                    "tokens_received": 0,
                    "error": error,
                    "aws_headers": {}
                }
            
            # Extract AWS-specific headers
            for header_name, header_value in response.headers.items():
                if header_name.lower().startswith('x-'):
                    aws_headers[header_name] = header_value
            
            first_chunk = True
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                    
                if line.startswith("data: "):
                    data_part = line[6:]  # Remove "data: " prefix
                    
                    if data_part.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(data_part)
                        if "choices" in chunk_data and chunk_data["choices"]:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                if first_chunk:
                                    ttft = time.time() - start_time
                                    first_chunk = False
                                
                                tokens_received += 1  # Approximate token count
                                
                    except json.JSONDecodeError:
                        continue  # Skip malformed chunks
            
            total_time = time.time() - start_time
            
        return {
            "ok": True,
            "ttft_s": ttft,
            "total_s": total_time,
            "tokens_received": tokens_received,
            "error": None,
            "aws_headers": aws_headers
        }
        
    except Exception as e:
        return {
            "ok": False,
            "ttft_s": None,
            "total_s": None,
            "tokens_received": 0,
            "error": str(e),
            "aws_headers": {}
        }


async def run_benchmark(
    url: str,
    prompt: str,
    max_tokens: int,
    num_requests: int,
    concurrency: int = 1
) -> Dict:
    """Run streaming benchmark with specified parameters."""
    
    print(f"Running {num_requests} requests with concurrency {concurrency}")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Max tokens: {max_tokens}")
    print("-" * 60)
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    
    async with httpx.AsyncClient(timeout=timeout, limits=limits, http2=True) as client:
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request():
            async with semaphore:
                return await streaming_request(client, url, prompt, max_tokens)
        
        # Run all requests
        tasks = [bounded_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_results = []
    failed_results = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_results.append({"request_id": i, "error": str(result)})
        elif result["ok"]:
            result["request_id"] = i
            successful_results.append(result)
        else:
            result["request_id"] = i
            failed_results.append(result)
    
    # Calculate statistics
    ttft_values = [r["ttft_s"] for r in successful_results if r["ttft_s"] is not None]
    total_values = [r["total_s"] for r in successful_results if r["total_s"] is not None]
    tokens_values = [r["tokens_received"] for r in successful_results]
    
    # Extract AWS-specific metrics from headers
    aws_ttft_values = []
    aws_tps_values = []
    aws_cost_values = []
    
    for result in successful_results:
        headers = result.get("aws_headers", {})
        
        # Parse AWS Lambda headers
        if "X-TTFT-MS" in headers:
            try:
                aws_ttft_values.append(float(headers["X-TTFT-MS"]) / 1000.0)  # Convert to seconds
            except ValueError:
                pass
                
        if "X-Tokens-Per-Second" in headers:
            try:
                aws_tps_values.append(float(headers["X-Tokens-Per-Second"]))
            except ValueError:
                pass
                
        if "X-Cost-Per-1K-USD" in headers:
            try:
                aws_cost_values.append(float(headers["X-Cost-Per-1K-USD"]))
            except ValueError:
                pass
    
    stats = {
        "total_requests": num_requests,
        "successful_requests": len(successful_results),
        "failed_requests": len(failed_results),
        "success_rate": len(successful_results) / num_requests if num_requests > 0 else 0,
        
        "ttft_stats": {
            "count": len(ttft_values),
            "mean": sum(ttft_values) / len(ttft_values) if ttft_values else None,
            "median": median(ttft_values) if ttft_values else None,
            "p95": percentile(ttft_values, 95),
            "p99": percentile(ttft_values, 99),
            "min": min(ttft_values) if ttft_values else None,
            "max": max(ttft_values) if ttft_values else None,
        },
        
        "total_latency_stats": {
            "count": len(total_values),
            "mean": sum(total_values) / len(total_values) if total_values else None,
            "median": median(total_values) if total_values else None,
            "p95": percentile(total_values, 95),
            "p99": percentile(total_values, 99),
            "min": min(total_values) if total_values else None,
            "max": max(total_values) if total_values else None,
        },
        
        "tokens_stats": {
            "mean": sum(tokens_values) / len(tokens_values) if tokens_values else None,
            "median": median(tokens_values) if tokens_values else None,
            "total": sum(tokens_values),
        },
        
        # AWS-specific metrics from Lambda headers
        "aws_ttft_stats": {
            "count": len(aws_ttft_values),
            "mean": sum(aws_ttft_values) / len(aws_ttft_values) if aws_ttft_values else None,
            "median": median(aws_ttft_values) if aws_ttft_values else None,
            "p95": percentile(aws_ttft_values, 95),
            "p99": percentile(aws_ttft_values, 99),
        } if aws_ttft_values else None,
        
        "aws_tokens_per_second_stats": {
            "count": len(aws_tps_values),
            "mean": sum(aws_tps_values) / len(aws_tps_values) if aws_tps_values else None,
            "median": median(aws_tps_values) if aws_tps_values else None,
            "p95": percentile(aws_tps_values, 95),
            "p99": percentile(aws_tps_values, 99),
        } if aws_tps_values else None,
        
        "aws_cost_per_1k_stats": {
            "count": len(aws_cost_values),
            "mean": sum(aws_cost_values) / len(aws_cost_values) if aws_cost_values else None,
            "median": median(aws_cost_values) if aws_cost_values else None,
            "min": min(aws_cost_values) if aws_cost_values else None,
            "max": max(aws_cost_values) if aws_cost_values else None,
        } if aws_cost_values else None,
    }
    
    return {
        "benchmark_config": {
            "url": url,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "num_requests": num_requests,
            "concurrency": concurrency,
            "timestamp": time.time(),
        },
        "statistics": stats,
        "raw_results": successful_results,
        "failures": failed_results,
    }


def print_results(results: Dict):
    """Print formatted benchmark results."""
    config = results["benchmark_config"]
    stats = results["statistics"]
    
    print(f"\n{'='*60}")
    print("AWS STREAMING BENCHMARK RESULTS")
    print(f"{'='*60}")
    
    print(f"URL: {config['url']}")
    print(f"Requests: {config['num_requests']} (concurrency: {config['concurrency']})")
    print(f"Max tokens: {config['max_tokens']}")
    
    print(f"\nSuccess Rate: {stats['success_rate']:.1%} ({stats['successful_requests']}/{stats['total_requests']})")
    
    if stats['ttft_stats']['count'] > 0:
        ttft = stats['ttft_stats']
        print(f"\nTime to First Token (TTFT):")
        print(f"  Mean: {ttft['mean']:.3f}s")
        print(f"  Median: {ttft['median']:.3f}s")
        print(f"  P95: {ttft['p95']:.3f}s")
        print(f"  P99: {ttft['p99']:.3f}s")
        print(f"  Range: {ttft['min']:.3f}s - {ttft['max']:.3f}s")
    
    if stats['total_latency_stats']['count'] > 0:
        total = stats['total_latency_stats']
        print(f"\nTotal Latency:")
        print(f"  Mean: {total['mean']:.3f}s")
        print(f"  Median: {total['median']:.3f}s")
        print(f"  P95: {total['p95']:.3f}s")
        print(f"  P99: {total['p99']:.3f}s")
        print(f"  Range: {total['min']:.3f}s - {total['max']:.3f}s")
    
    if stats['tokens_stats']['mean']:
        tokens = stats['tokens_stats']
        print(f"\nTokens:")
        print(f"  Mean per request: {tokens['mean']:.1f}")
        print(f"  Total tokens: {tokens['total']}")
    
    # AWS-specific metrics
    if stats.get('aws_ttft_stats'):
        aws_ttft = stats['aws_ttft_stats']
        print(f"\nAWS TTFT (from Lambda headers):")
        print(f"  Mean: {aws_ttft['mean']:.3f}s")
        print(f"  Median: {aws_ttft['median']:.3f}s")
        print(f"  P95: {aws_ttft['p95']:.3f}s")
    
    if stats.get('aws_tokens_per_second_stats'):
        aws_tps = stats['aws_tokens_per_second_stats']
        print(f"\nAWS Tokens/Second (from Lambda headers):")
        print(f"  Mean: {aws_tps['mean']:.1f} tok/s")
        print(f"  Median: {aws_tps['median']:.1f} tok/s")
        print(f"  P95: {aws_tps['p95']:.1f} tok/s")
    
    if stats.get('aws_cost_per_1k_stats'):
        aws_cost = stats['aws_cost_per_1k_stats']
        print(f"\nAWS Cost per 1k tokens (from Lambda headers):")
        print(f"  Mean: ${aws_cost['mean']:.5f}")
        print(f"  Median: ${aws_cost['median']:.5f}")
        print(f"  Range: ${aws_cost['min']:.5f} - ${aws_cost['max']:.5f}")
    
    print(f"\n{'='*60}")


async def main():
    parser = argparse.ArgumentParser(
        description="AWS SageMaker Streaming Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic benchmark
  python3 aws_streaming_bench.py --url https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat/completions

  # Custom parameters
  python3 aws_streaming_bench.py \\
    --url https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat/completions \\
    --requests 100 \\
    --concurrency 4 \\
    --max-tokens 128 \\
    --output aws_streaming_results.json
        """
    )
    
    parser.add_argument("--url", required=True, help="API Gateway URL")
    parser.add_argument("--requests", type=int, default=30, help="Number of requests (default: 30)")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent requests (default: 1)")
    parser.add_argument("--max-tokens", type=int, default=64, help="Max tokens per request (default: 64)")
    parser.add_argument("--prompt", default="Explain the benefits of microservices architecture in modern software development, including scalability, maintainability, and team organization aspects.", help="Custom prompt")
    parser.add_argument("--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    try:
        results = await run_benchmark(
            url=args.url,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            num_requests=args.requests,
            concurrency=args.concurrency
        )
        
        # Print results to console
        print_results(results)
        
        # Save to file if specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\nResults saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running benchmark: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
