#!/usr/bin/env bash
set -xeuo pipefail

: "${MODEL_ID:=hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4}"
: "${OPTION_MAX_MODEL_LEN:=4096}"
: "${OPTION_GPU_MEMORY_UTILIZATION:=0.95}"
: "${OPTION_ENFORCE_EAGER:=true}"
: "${MAX_BATCH_TOTAL_TOKENS:=16384}"
: "${VLLM_PORT:=8000}"
: "${PORT:=8080}"

# Start vLLM and mirror logs to container stdout/stderr so Vertex Logging captures them
vllm serve "$MODEL_ID" \
  --host 0.0.0.0 \
  --port "$VLLM_PORT" \
  --max-model-len "$OPTION_MAX_MODEL_LEN" \
  --gpu-memory-utilization "$OPTION_GPU_MEMORY_UTILIZATION" \
  --enforce-eager \
  --max-num-seqs 8 \
  --trust-remote-code \
  --dtype auto \
  --tensor-parallel-size 1 \
  --max-log-len 4096 \
  --served-model-name llm \
  > >(tee -a /tmp/vllm.log) 2> >(tee -a /tmp/vllm.err >&2) &

# Wait up to 180s for vLLM to listen
for i in {1..180}; do
  if bash -c "</dev/tcp/127.0.0.1/$VLLM_PORT" 2>/dev/null; then break; fi
  sleep 1
done

# Run adapter with python3 explicitly
exec python3 -m uvicorn server:app --host 0.0.0.0 --port "$PORT"
