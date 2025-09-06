import argparse, asyncio, json, os, subprocess, time
from datetime import datetime
import httpx

# Calls Vertex Endpoint :predict. Requires `gcloud` auth set up (user or SA).
# We intentionally do a raw REST call to keep dependencies light.

API_FMT = "https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/endpoints/{endpoint_id}:predict"

async def one_call(client, url, headers, instance):
    t0 = time.perf_counter()
    try:
        r = await client.post(url, headers=headers, json={"instances": [instance]})
        ok = r.status_code == 200
        data = r.json() if ok else {"error": r.text}
    except Exception as e:
        ok, data = False, {"error": str(e)}
    t1 = time.perf_counter()
    return {
        "ts": datetime.utcnow().isoformat()+"Z",
        "status": "ok" if ok else "error",
        "latency_s": t1 - t0,
        "resp": data
    }

async def run_steady(url, headers, instance, duration_sec, target_rps, concurrency, out_path):
    interval = 1.0 / target_rps
    sem = asyncio.Semaphore(concurrency)
    results = []

    async with httpx.AsyncClient(timeout=120) as client:
        start = time.perf_counter()
        async def worker():
            async with sem:
                res = await one_call(client, url, headers, instance)
                results.append(res)
        i = 0
        while time.perf_counter() - start < duration_sec:
            asyncio.create_task(worker())
            i += 1
            await asyncio.sleep(interval)
        # drain
        await asyncio.sleep(concurrency * 0.05)

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r)+"\n")

async def run_n(url, headers, instance, n, concurrency, out_path):
    sem = asyncio.Semaphore(concurrency)
    results = []
    async with httpx.AsyncClient(timeout=120) as client:
        async def worker():
            async with sem:
                res = await one_call(client, url, headers, instance)
                results.append(res)
        tasks = [asyncio.create_task(worker()) for _ in range(n)]
        await asyncio.gather(*tasks)
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r)+"\n")

def access_token():
    return subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--endpoint-id", required=True)
    ap.add_argument("--scenario", required=True)
    args = ap.parse_args()

    with open(args.scenario) as f:
        cfg = json.load(f)

    url = API_FMT.format(project=args.project, region=args.region, endpoint_id=args.endpoint_id)
    headers = {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"}

    instance = {
        "prompt": cfg.get("prompt", "Hello"),
        "max_tokens": int(cfg.get("max_tokens", 128)),
        "temperature": float(cfg.get("temperature", 0.0))
    }

    os.makedirs("bench/results", exist_ok=True)
    out = f"bench/results/{cfg['name']}-{int(time.time())}.ndjson"

    if "duration_sec" in cfg:
        asyncio.run(run_steady(url, headers, instance, int(cfg["duration_sec"]), int(cfg["target_rps"]), int(cfg["concurrency"]), out))
    elif "runs" in cfg:
        # multi-run sweep → emit one file per run
        for i, r in enumerate(cfg["runs"], 1):
            run_cfg = instance | {
                "max_tokens": int(r.get("max_tokens", instance["max_tokens"])),
                "temperature": float(r.get("temperature", instance["temperature"]))
            }
            out_i = f"bench/results/{cfg['name']}-run{i}-{int(time.time())}.ndjson"
            asyncio.run(run_steady(url, headers, run_cfg, int(r["target_rps"]) * 10, int(r["target_rps"]), int(r["concurrency"]), out_i))
    else:
        asyncio.run(run_n(url, headers, instance, int(cfg.get("requests", 30)), int(cfg.get("concurrency", 8)), out))

    print("Wrote:", out)

if __name__ == "__main__":
    main()
