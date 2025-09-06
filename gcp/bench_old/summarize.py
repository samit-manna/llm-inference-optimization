import json, glob, statistics as stats

# Summarize ndjson from bench/ into CSV-like stdout

def summarize(path_pattern="bench/results/*.ndjson"):
    files = sorted(glob.glob(path_pattern))
    for fp in files:
        latencies = []
        ok = 0
        tok = []
        with open(fp) as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("status") == "ok":
                    ok += 1
                latencies.append(rec.get("latency_s", 0))
                # try to read tokens from resp.predictions[0].usage.completion_tokens
                try:
                    pred = rec["resp"]["predictions"][0]
                    usage = pred.get("usage", {})
                    if "completion_tokens" in usage:
                        tok.append(usage["completion_tokens"])  # per request
                except Exception:
                    pass
        n = len(latencies)
        p50 = stats.quantiles(latencies, n=100)[49] if n else 0
        p95 = stats.quantiles(latencies, n=100)[94] if n else 0
        rps = n / (max(latencies) if n else 1)
        avg_tok = (sum(tok)/len(tok)) if tok else 0
        print(f"file={fp}, n={n}, ok={ok}, rps~={rps:.2f}, p50={p50:.3f}s, p95={p95:.3f}s, avg_tok={avg_tok:.1f}")

if __name__ == "__main__":
    summarize()
