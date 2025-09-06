# Lightweight path: use upstream vLLM OpenAI-compatible image.
# It already bundles CUDA, PyTorch, and vLLM server.
FROM vllm/vllm-openai:v0.4.2


# Minimal adapter to make Vertex :predict work with vLLM’s OpenAI API server
WORKDIR /app
COPY server.py /app/server.py
COPY entrypoint.sh /app/entrypoint.sh
COPY requirements.txt /app/requirements.txt


RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt \
    && chmod +x /app/entrypoint.sh


# Vertex defaults to port 8080 for container contracts
ENV PORT=8080
EXPOSE 8080


# vLLM default HTTP port (internal)
ENV VLLM_PORT=8000
EXPOSE 8000


# The model is pulled at container start by vLLM unless pre-baked.
# You may pre-download at build-time if you want faster cold-starts.


ENTRYPOINT ["/app/entrypoint.sh"]
