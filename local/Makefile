# lla# Variables
MODEL_PATH = models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
MODEL_URL = https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
PORT = 8080
CONTEXT_SIZE = 8192
PARALLEL_SEQUENCES = 4
# M4 Pro optimizations (conservative settings)
# GPU_LAYERS = 32
# BATCH_SIZE = 512
# UBATCH_SIZE = 128
# THREADS = 8r (OpenAI-compatible)
# Hardware: MacBook Pro M4 Pro, 24 GB
# Model: Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf (~4.9 GB)
# KV cache: f16/f16 (default)

# Variables
MODEL_PATH = models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
MODEL_URL = https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
PORT = 8080
CONTEXT_SIZE = 8192
PARALLEL_SEQUENCES = 4
# M4 Pro optimizations
GPU_LAYERS = 99
BATCH_SIZE = 2048
UBATCH_SIZE = 512
THREADS = 12
FLASH_ATTENTION = on

.PHONY: clone configure build server download-model clean help

# Default target
all: clone configure build

help:
	@echo "Available targets:"
	@echo "  clone        - Clone llama.cpp repository"
	@echo "  configure    - Configure build with Metal support"
	@echo "  build        - Build llama.cpp with server"
	@echo "  download-model - Download the model if it doesn't exist"
	@echo "  server       - Start llama.cpp server with parallel decoding"
	@echo "  clean        - Clean build directory"
	@echo "  all          - Clone, configure, and build (default)"

# Clone llama.cpp repository
clone:
	@if [ ! -d "llama.cpp" ]; then \
		git clone https://github.com/ggml-org/llama.cpp; \
	else \
		echo "llama.cpp directory already exists"; \
	fi

# Configure build
configure:
	cd llama.cpp && cmake -S . -B build \
		-DCMAKE_BUILD_TYPE=Release \
		-DGGML_METAL=ON \
		-DLLAMA_BUILD_SERVER=ON

# Build llama.cpp
build:
	cd llama.cpp && cmake --build build -j

# Download model if it doesn't exist
download-model:
	@if [ ! -f "llama.cpp/$(MODEL_PATH)" ]; then \
		echo "Downloading model..."; \
		mkdir -p llama.cpp/models; \
		curl -L -o "llama.cpp/$(MODEL_PATH)" "$(MODEL_URL)"; \
		echo "Model downloaded successfully"; \
	else \
		echo "Model already exists at llama.cpp/$(MODEL_PATH)"; \
	fi

# Start server with parallel decoding
server: download-model
	cd llama.cpp && ./build/bin/llama-server \
		-m $(MODEL_PATH) \
		--port $(PORT) \
		-c $(CONTEXT_SIZE) \
		-np $(PARALLEL_SEQUENCES) \
		--host 127.0.0.1 \
		--metrics

# Clean build directory
clean:
	@if [ -d "llama.cpp/build" ]; then \
		rm -rf llama.cpp/build; \
		echo "Build directory cleaned"; \
	else \
		echo "No build directory to clean"; \
	fi