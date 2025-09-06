#!/usr/bin/env bash
set -euo pipefail

# Docker Build & Push Script for VLLM Proxy
# 
# This script builds the proxy image for the correct architecture (AMD64)
# to work with AKS nodes. Your AKS nodes are linux/amd64 architecture.
#
# Usage:
#   ./build_push_proxy.sh                    # Build for AMD64 only
#   MULTI_ARCH=true ./build_push_proxy.sh    # Build for both AMD64 and ARM64
#
# Environment Variables:
#   ACR_NAME     - Azure Container Registry name (default: samllmacr123456)
#   ACR_RG       - Resource Group name (default: rg-llm-aks)  
#   IMAGE_NAME   - Image name (default: vllm-proxy)
#   IMAGE_TAG    - Image tag (default: latest)
#   MULTI_ARCH   - Build multi-arch image (default: false)
#

# ====== CONFIG ======
ACR_NAME="${ACR_NAME:-samllmacr123456}"          # e.g., llmacr123456
ACR_RG="${ACR_RG:-sam-rg-llm-aks}"
IMAGE_NAME="${IMAGE_NAME:-vllm-proxy}"
IMAGE_TAG="${IMAGE_TAG:-latest}"               # or $(git rev-parse --short HEAD)
MULTI_ARCH="${MULTI_ARCH:-false}"             # Set to "true" for multi-arch build

CONTEXT_DIR="${CONTEXT_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo ">> Logging in to Azure (if not already)..."
az account show >/dev/null 2>&1 || az login

ACR_LOGIN_SERVER=$(az acr show -n "$ACR_NAME" -g "$ACR_RG" --query "loginServer" -o tsv)

echo ">> Docker login to ACR..."
az acr login -n "$ACR_NAME" >/dev/null

if [ "$MULTI_ARCH" = "true" ]; then
    echo ">> Building for multiple architectures (amd64, arm64) using buildx..."
    # Ensure buildx is available and create/use a builder instance
    docker buildx create --use --name multiarch-builder 2>/dev/null || docker buildx use multiarch-builder 2>/dev/null || true
    docker buildx build --platform linux/amd64,linux/arm64 -t "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" "$CONTEXT_DIR" --push
    echo ">> Multi-arch build and push completed!"
else
    echo ">> Building for AMD64 platform (AKS nodes are amd64)..."
    docker build --platform linux/amd64 -t "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" "$CONTEXT_DIR"

    echo ">> Pushing to ACR..."
    docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo ""
if [ "$MULTI_ARCH" = "true" ]; then
    echo "✔ Multi-arch image pushed: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  Architectures: linux/amd64, linux/arm64"
else
    echo "✔ AMD64 image pushed: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  Architecture: linux/amd64 (compatible with your AKS nodes)"
fi
echo "👉 Set this in terraform.tfvars:"
echo "proxy_image = \"${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}\""
