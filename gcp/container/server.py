from fastapi import FastAPI, Response
from pydantic import BaseModel
import httpx
import os
import json

VLLM_PORT = os.getenv('VLLM_PORT', '8000')
VLLM_URL = f"http://127.0.0.1:{VLLM_PORT}/v1/chat/completions"
VLLM_API_KEY = os.getenv('VLLM_API_KEY')  # optional

app = FastAPI()

# Accept a more flexible schema so either our bench or Vertex-style callers work
class Instance(BaseModel):
    prompt: str | None = None
    messages: list[dict] | None = None
    max_tokens: int | None = 256
    temperature: float | None = 0.0

class PredictRequest(BaseModel):
    instances: list[Instance] | None = None
    parameters: dict | None = None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/probe")
async def probe():
    payload = {
        "model": "llm",
        "messages": [{"role": "user", "content": "say hello"}],
        "max_tokens": 16,
        "temperature": 0.0,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}
    if VLLM_API_KEY:
        headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(VLLM_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

@app.post("/predict")
async def predict(req: PredictRequest):
    inst = (req.instances or [Instance()])[0]

    # Pull parameters (supports either top-level parameters or in instance)
    max_tokens = (inst.max_tokens if inst.max_tokens is not None else 256)
    temperature = (inst.temperature if inst.temperature is not None else 0.0)
    if req.parameters:
        max_tokens = int(req.parameters.get("max_tokens", max_tokens))
        temperature = float(req.parameters.get("temperature", temperature))

    # Build messages: prefer messages if provided, otherwise wrap prompt
    if inst.messages:
        messages = inst.messages
    elif inst.prompt:
        messages = [{"role": "user", "content": inst.prompt}]
    else:
        return Response(status_code=400, content="missing prompt/messages")

    payload = {
        "model": "llm",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    headers = {"Content-Type": "application/json"}
    if VLLM_API_KEY:
        headers["Authorization"] = f"Bearer {VLLM_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(VLLM_URL, headers=headers, json=payload)
            # Bubble up vLLM error bodies to the caller
            if r.status_code >= 400:
                return Response(status_code=502, content=f"vLLM {r.status_code}: {r.text}")
            data = r.json()
    except Exception as e:
        # include payload summary to help debug
        dbg = json.dumps({"err": str(e), "payload": {k: v for k, v in payload.items() if k != 'messages'}}, ensure_ascii=False)
        return Response(status_code=500, content=f"adapter error: {dbg}")

    choice = (data.get("choices") or [{}])[0]
    text = choice.get("message", {}).get("content", "")
    usage = data.get("usage", {})

    return {"predictions": [{"text": text, "usage": usage}]}
