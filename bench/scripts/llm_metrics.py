#!/usr/bin/env python3
"""
LLM Performance Metrics Tool

Measures key LLM inference metrics:
- TTFT (Time to First Token) for streaming
- Throughput (tokens/second) 
- Latency (total response time)
- Concurrent performance

Usage:
    python3 llm_metrics.py <url> <payload_file> [options]
    
Options:
    --mode streaming|non_streaming|both (default: both)
    --duration <seconds> (default: 60 for local, 300 for cloud)
    --concurrency <num> (default: 1 for single request test, 10 for load test)
    --requests <num> (run exact number of requests instead of time-based)
    --platform <name> (platform name for output directory: local, aws, azure, gcp, etc.)

Examples:
    python3 llm_metrics.py http://localhost:8000/v1/chat/completions data/payload.json --platform local
    python3 llm_metrics.py https://api.aws.com/v1/chat/completions data/payload.json --platform aws --duration 300
"""

import httpx
import asyncio
import time
import json
import sys
import argparse
import os
from dataclasses import dataclass
from typing import List, Optional
from statistics import mean, median, stdev


@dataclass
class RequestResult:
    """Single request metrics"""
    mode: str
    success: bool
    ttft_ms: Optional[float]  # Time to first token (streaming only)
    total_time_ms: float      # Total request time
    tokens_generated: int     # Number of tokens generated
    tokens_per_second: float  # Throughput for this request
    error: Optional[str] = None


@dataclass
class AggregateMetrics:
    """Aggregated metrics across multiple requests"""
    mode: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    
    # Latency metrics (ms)
    avg_total_time_ms: float
    p50_total_time_ms: float
    p95_total_time_ms: float
    p99_total_time_ms: float
    
    # TTFT metrics (ms) - streaming only
    avg_ttft_ms: Optional[float]
    p50_ttft_ms: Optional[float] 
    p95_ttft_ms: Optional[float]
    
    # Throughput metrics
    avg_tokens_per_second: float
    p50_tokens_per_second: float
    p95_tokens_per_second: float
    total_tokens_generated: int
    
    # Load test metrics
    requests_per_second: float
    total_duration_sec: float
    
    # Summary
    aggregate_tokens_per_second: float  # Total tokens across all requests / total time


class LLMBenchmark:
    def __init__(self, base_url: str, headers: dict = None):
        self.base_url = base_url
        self.headers = headers or {"Content-Type": "application/json"}
        
        # HTTP/2 connection limits and timeouts for better performance
        self.http_limits = httpx.Limits(
            max_keepalive_connections=50,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        # Optimized timeouts for streaming
        self.streaming_timeout = httpx.Timeout(
            connect=10.0,   # Connection timeout
            read=300.0,     # Long read timeout for streaming
            write=30.0,     # Write timeout
            pool=10.0       # Pool timeout
        )
        
        self.non_streaming_timeout = httpx.Timeout(
            connect=10.0,
            read=120.0,     # Shorter for non-streaming
            write=30.0,
            pool=10.0
        )
        
    async def single_request_streaming(self, client: httpx.AsyncClient, payload: dict) -> RequestResult:
        """Execute a single streaming request and measure TTFT + throughput"""
        request_start = time.perf_counter()
        first_token_time = None
        tokens = 0
        
        try:
            # Use streaming with optimized headers for better performance
            stream_headers = self.headers.copy()
            stream_headers.update({
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            })
            
            async with client.stream(
                "POST", 
                self.base_url, 
                json=payload, 
                headers=stream_headers,
                timeout=self.streaming_timeout
            ) as response:
                if response.status_code != 200:
                    return RequestResult(
                        mode="streaming",
                        success=False,
                        ttft_ms=None,
                        total_time_ms=(time.perf_counter() - request_start) * 1000,
                        tokens_generated=0,
                        tokens_per_second=0.0,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
                
                buffer = ""
                async for chunk in response.aiter_bytes(chunk_size=1024):  # Optimized chunk size
                    buffer += chunk.decode('utf-8', errors='ignore')
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                            
                        try:
                            # Parse streaming response
                            if line.startswith("data: "):
                                if line.strip() == "data: [DONE]":
                                    break
                                json_str = line[6:]  # Remove "data: " prefix
                            else:
                                json_str = line
                                
                            data = json.loads(json_str)
                            choices = data.get("choices", [])
                            
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content and first_token_time is None:
                                    first_token_time = time.perf_counter()
                                
                                if content:
                                    # More accurate token counting
                                    new_tokens = len(content.split()) if content.split() else (1 if content.strip() else 0)
                                    tokens += new_tokens
                                
                                # Check for completion
                                if choices[0].get("finish_reason"):
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                        
        except Exception as e:
            return RequestResult(
                mode="streaming",
                success=False,
                ttft_ms=None,
                total_time_ms=(time.perf_counter() - request_start) * 1000,
                tokens_generated=0,
                tokens_per_second=0.0,
                error=str(e)
            )
        
        request_end = time.perf_counter()
        total_time = request_end - request_start
        ttft = (first_token_time - request_start) if first_token_time else None
        tokens_per_sec = tokens / total_time if total_time > 0 else 0.0
        
        return RequestResult(
            mode="streaming",
            success=tokens > 0,
            ttft_ms=ttft * 1000 if ttft else None,
            total_time_ms=total_time * 1000,
            tokens_generated=tokens,
            tokens_per_second=tokens_per_sec
        )
    
    async def single_request_non_streaming(self, client: httpx.AsyncClient, payload: dict) -> RequestResult:
        """Execute a single non-streaming request and measure throughput"""
        request_start = time.perf_counter()
        
        try:
            response = await client.post(
                self.base_url, 
                json=payload, 
                headers=self.headers, 
                timeout=self.non_streaming_timeout
            )
            request_end = time.perf_counter()
            
            if response.status_code != 200:
                return RequestResult(
                    mode="non_streaming",
                    success=False,
                    ttft_ms=None,
                    total_time_ms=(request_end - request_start) * 1000,
                    tokens_generated=0,
                    tokens_per_second=0.0,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            usage = data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)
            
            total_time = request_end - request_start
            tokens_per_sec = completion_tokens / total_time if total_time > 0 else 0.0
            
            return RequestResult(
                mode="non_streaming", 
                success=completion_tokens > 0,
                ttft_ms=None,  # N/A for non-streaming
                total_time_ms=total_time * 1000,
                tokens_generated=completion_tokens,
                tokens_per_second=tokens_per_sec
            )
            
        except Exception as e:
            return RequestResult(
                mode="non_streaming",
                success=False,
                ttft_ms=None,
                total_time_ms=(time.perf_counter() - request_start) * 1000,
                tokens_generated=0,
                tokens_per_second=0.0,
                error=str(e)
            )
    
    async def run_benchmark(self, payload: dict, mode: str, duration_sec: int = None, 
                          max_requests: int = None, concurrency: int = 1) -> AggregateMetrics:
        """Run benchmark with specified parameters"""
        results: List[RequestResult] = []
        start_time = time.perf_counter()
        
        async with httpx.AsyncClient(
            limits=self.http_limits,
            timeout=self.streaming_timeout if mode == "streaming" else self.non_streaming_timeout,
            http2=True  # Enable HTTP/2
        ) as client:
            if max_requests:
                # Request-count based test
                semaphore = asyncio.Semaphore(concurrency)
                
                async def make_request():
                    async with semaphore:
                        if mode == "streaming":
                            return await self.single_request_streaming(client, payload)
                        else:
                            return await self.single_request_non_streaming(client, payload)
                
                tasks = [make_request() for _ in range(max_requests)]
                results = await asyncio.gather(*tasks)
                
            else:
                # Duration-based test
                end_time = start_time + duration_sec
                semaphore = asyncio.Semaphore(concurrency)
                tasks = []
                
                async def worker():
                    worker_results = []
                    while time.perf_counter() < end_time:
                        async with semaphore:
                            if mode == "streaming":
                                result = await self.single_request_streaming(client, payload)
                            else:
                                result = await self.single_request_non_streaming(client, payload)
                            worker_results.append(result)
                    return worker_results
                
                # Start workers
                worker_tasks = [worker() for _ in range(min(concurrency, 50))]  # Limit workers
                worker_results = await asyncio.gather(*worker_tasks)
                
                # Flatten results
                for worker_result_list in worker_results:
                    results.extend(worker_result_list)
        
        actual_duration = time.perf_counter() - start_time
        return self._calculate_metrics(results, actual_duration, mode)
    
    def _calculate_metrics(self, results: List[RequestResult], duration_sec: float, mode: str) -> AggregateMetrics:
        """Calculate aggregate metrics from individual results"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if not results:
            raise ValueError("No results to analyze")
        
        # Latency metrics
        total_times = [r.total_time_ms for r in successful]
        ttft_times = [r.ttft_ms for r in successful if r.ttft_ms is not None]
        tokens_per_sec = [r.tokens_per_second for r in successful if r.tokens_per_second > 0]
        
        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return None
            sorted_data = sorted(data)
            index = (len(sorted_data) - 1) * p / 100
            lower = int(index)
            upper = min(lower + 1, len(sorted_data) - 1)
            weight = index - lower
            return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
        
        total_tokens = sum(r.tokens_generated for r in successful)
        aggregate_tps = total_tokens / duration_sec if duration_sec > 0 else 0
        
        return AggregateMetrics(
            mode=mode,
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            success_rate=len(successful) / len(results) * 100 if results else 0,
            
            # Latency
            avg_total_time_ms=mean(total_times) if total_times else 0,
            p50_total_time_ms=percentile(total_times, 50) or 0,
            p95_total_time_ms=percentile(total_times, 95) or 0,
            p99_total_time_ms=percentile(total_times, 99) or 0,
            
            # TTFT (streaming only)
            avg_ttft_ms=mean(ttft_times) if ttft_times else None,
            p50_ttft_ms=percentile(ttft_times, 50) if ttft_times else None,
            p95_ttft_ms=percentile(ttft_times, 95) if ttft_times else None,
            
            # Throughput
            avg_tokens_per_second=mean(tokens_per_sec) if tokens_per_sec else 0,
            p50_tokens_per_second=percentile(tokens_per_sec, 50) or 0,
            p95_tokens_per_second=percentile(tokens_per_sec, 95) or 0,
            total_tokens_generated=total_tokens,
            
            # Load metrics
            requests_per_second=len(results) / duration_sec if duration_sec > 0 else 0,
            total_duration_sec=duration_sec,
            aggregate_tokens_per_second=aggregate_tps
        )


def print_metrics(metrics: AggregateMetrics):
    """Print formatted metrics"""
    print(f"\n{'='*60}")
    print(f"LLM PERFORMANCE METRICS - {metrics.mode.upper()}")
    print(f"{'='*60}")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Requests:     {metrics.total_requests}")
    print(f"  Successful:         {metrics.successful_requests}")
    print(f"  Failed:             {metrics.failed_requests}")
    print(f"  Success Rate:       {metrics.success_rate:.1f}%")
    print(f"  Test Duration:      {metrics.total_duration_sec:.1f}s")
    print(f"  Requests/sec:       {metrics.requests_per_second:.2f}")
    
    print(f"\n⚡ THROUGHPUT:")
    print(f"  Avg tokens/sec:     {metrics.avg_tokens_per_second:.2f}")
    print(f"  P50 tokens/sec:     {metrics.p50_tokens_per_second:.2f}")
    print(f"  P95 tokens/sec:     {metrics.p95_tokens_per_second:.2f}")
    print(f"  Total tokens:       {metrics.total_tokens_generated}")
    print(f"  Aggregate tps:      {metrics.aggregate_tokens_per_second:.2f}")
    
    print(f"\n⏱️  LATENCY:")
    print(f"  Avg response:       {metrics.avg_total_time_ms:.0f}ms")
    print(f"  P50 response:       {metrics.p50_total_time_ms:.0f}ms")
    print(f"  P95 response:       {metrics.p95_total_time_ms:.0f}ms")
    print(f"  P99 response:       {metrics.p99_total_time_ms:.0f}ms")
    
    if metrics.avg_ttft_ms is not None:
        print(f"\n🚀 TIME TO FIRST TOKEN (TTFT):")
        print(f"  Avg TTFT:           {metrics.avg_ttft_ms:.0f}ms")
        print(f"  P50 TTFT:           {metrics.p50_ttft_ms:.0f}ms")
        print(f"  P95 TTFT:           {metrics.p95_ttft_ms:.0f}ms")


async def main():
    parser = argparse.ArgumentParser(description="LLM Performance Metrics Tool")
    parser.add_argument("url", help="API endpoint URL")
    parser.add_argument("payload_file", help="JSON payload file")
    parser.add_argument("--mode", choices=["streaming", "non_streaming", "both"], 
                       default="both", help="Test mode")
    parser.add_argument("--duration", type=int, help="Test duration in seconds")
    parser.add_argument("--requests", type=int, help="Number of requests (overrides duration)")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent requests")
    parser.add_argument("--platform", help="Platform name (local, aws, azure, gcp, etc.)")
    
    args = parser.parse_args()
    
    # Load payload
    with open(args.payload_file) as f:
        base_payload = json.load(f)
    
    # Determine default duration based on URL
    if args.duration is None:
        if "localhost" in args.url or "127.0.0.1" in args.url:
            default_duration = 30
        else:
            default_duration = 60
        args.duration = default_duration
    
    # Determine platform for output directory
    if args.platform:
        platform = args.platform.lower()
    elif "localhost" in args.url or "127.0.0.1" in args.url:
        platform = "local"
    else:
        platform = "cloud"
    
    benchmark = LLMBenchmark(args.url)
    
    # Run tests
    modes_to_test = ["non_streaming", "streaming"] if args.mode == "both" else [args.mode]
    
    for mode in modes_to_test:
        payload = base_payload.copy()
        payload["stream"] = (mode == "streaming")
        
        print(f"\n🧪 Running {mode} test...")
        print(f"   Duration: {args.duration}s, Concurrency: {args.concurrency}")
        
        metrics = await benchmark.run_benchmark(
            payload=payload,
            mode=mode,
            duration_sec=args.duration if not args.requests else None,
            max_requests=args.requests,
            concurrency=args.concurrency
        )
        
        print_metrics(metrics)
        
        # Save results
        output_dir = f"results/{platform}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = f"{output_dir}/llm_metrics_{mode}.json"
        with open(output_file, "w") as f:
            json.dump({
                "mode": metrics.mode,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "success_rate": metrics.success_rate,
                "avg_tokens_per_second": metrics.avg_tokens_per_second,
                "p95_tokens_per_second": metrics.p95_tokens_per_second,
                "aggregate_tokens_per_second": metrics.aggregate_tokens_per_second,
                "avg_total_time_ms": metrics.avg_total_time_ms,
                "p95_total_time_ms": metrics.p95_total_time_ms,
                "avg_ttft_ms": metrics.avg_ttft_ms,
                "p95_ttft_ms": metrics.p95_ttft_ms,
                "requests_per_second": metrics.requests_per_second,
                "total_duration_sec": metrics.total_duration_sec,
                "total_tokens_generated": metrics.total_tokens_generated
            }, f, indent=2)
        
        print(f"\n💾 Results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
