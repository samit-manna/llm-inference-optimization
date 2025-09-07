#!/usr/bin/env make -f

# Azure LLM Inference Benchmarking Makefile
# Provides convenient commands for common operations

.PHONY: help deploy deploy-aks deploy-proxy deploy-k8s clean destroy destroy-k8s destroy-proxy destroy-aks integrate-acr check-acr-auth fix-acr-auth

# Environment Variables
ACR_NAME ?= samllmacr123456
ACR_RG ?= sam-rg-llm-aks
IMAGE_NAME ?= vllm-proxy
IMAGE_TAG ?= latest
DURATION ?= 60
CONCURRENCY ?= 6
SERVICE_IP ?=

# Default target
help:
	@echo "Azure LLM Inference Benchmarking"
	@echo ""
	@echo "Available commands:"
	@echo "  help        Show this help message"
	@echo "  deploy      Deploy full infrastructure (AKS -> Proxy -> K8s)"
	@echo "  deploy-aks  Deploy AKS cluster via Terraform"
	@echo "  deploy-proxy Build and push proxy app to ACR"
	@echo "  deploy-k8s  Deploy K8s resources via Terraform"
	@echo "  plan        Show Terraform execution plan for all components"
	@echo "  plan-aks    Show Terraform execution plan for AKS"
	@echo "  plan-k8s    Show Terraform execution plan for K8s"
	@echo "  benchmark   Run performance benchmarks (requires SERVICE_IP)"
	@echo "  analyze     Analyze benchmark results"
	@echo "  integrate-acr Integrate AKS with ACR for image pulling"
	@echo "  check-acr-auth Check ACR authentication status"
	@echo "  fix-acr-auth Fix ACR authentication issues (integrate + restart pods)"
	@echo "  clean       Clean up temporary files"
	@echo "  destroy     Destroy infrastructure in reverse order (K8s -> Proxy -> AKS)"
	@echo "  destroy-k8s Destroy K8s resources"
	@echo "  destroy-proxy Clean up proxy images (optional)"
	@echo "  destroy-aks Destroy AKS cluster"
	@echo ""
	@echo "Environment Variables:"
	@echo "  ACR_NAME     Azure Container Registry name (default: $(ACR_NAME))"
	@echo "  ACR_RG       Resource Group name (default: $(ACR_RG))"
	@echo "  IMAGE_NAME   Docker image name (default: $(IMAGE_NAME))"
	@echo "  IMAGE_TAG    Docker image tag (default: $(IMAGE_TAG))"
	@echo "  SERVICE_IP   K8s service external IP for benchmarking"
	@echo "  DURATION     Test duration in seconds (default: $(DURATION))"
	@echo "  CONCURRENCY  Number of concurrent connections (default: $(CONCURRENCY))"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy"
	@echo "  SERVICE_IP=20.185.210.17 make benchmark"
	@echo "  make destroy"

# Full deployment workflow
deploy: deploy-aks deploy-proxy deploy-k8s
	@echo ""
	@echo "🎉 Full Azure deployment complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Get the service external IP:"
	@echo "   kubectl get services -n default"
	@echo "2. Run benchmarks:"
	@echo "3. When done, clean up:"
	@echo "   make destroy"

# Terraform planning
plan: plan-aks plan-k8s

plan-aks:
	@echo "📋 Planning AKS Terraform deployment..."
	cd terraform/aks && terraform plan

plan-k8s:
	@echo "📋 Planning K8s Terraform deployment..."
	cd terraform/k8s && terraform plan

# Step 1: Deploy AKS cluster
deploy-aks:
	@echo "🚀 Deploying AKS cluster..."
	cd terraform/aks && terraform init && terraform apply -auto-approve
	@echo "✅ AKS cluster deployment complete!"
	@echo ""
	@echo "Getting AKS credentials..."
	az aks get-credentials --resource-group $(ACR_RG) --name $$(cd terraform/aks && terraform output -raw cluster_name) --overwrite-existing
	@echo "✅ AKS credentials configured!"

# Step 2: Build and push proxy to ACR
deploy-proxy:
	@echo "🐋 Building and pushing proxy to ACR..."
	cd proxy && ACR_NAME=$(ACR_NAME) ACR_RG=$(ACR_RG) IMAGE_NAME=$(IMAGE_NAME) IMAGE_TAG=$(IMAGE_TAG) ./build_push_proxy.sh
	@echo "✅ Proxy build and push complete!"

# Step 3: Deploy K8s resources
deploy-k8s:
	@echo "☸️  Deploying K8s resources..."
	$(eval PROXY_IMAGE := $(ACR_NAME).azurecr.io/$(IMAGE_NAME):$(IMAGE_TAG))
	@echo "Using proxy image: $(PROXY_IMAGE)"
	@echo "Deploying K8s resources without custom resources"
	cd terraform/k8s && terraform init && terraform apply --var "create_custom_resources=false" --var "proxy_image=$(PROXY_IMAGE)" -auto-approve
	@echo "Deploying K8s resources with custom resources"
	cd terraform/k8s && terraform init && terraform apply --var "create_custom_resources=true" --var "proxy_image=$(PROXY_IMAGE)" -auto-approve
	@echo "✅ K8s resources deployment complete!"
	@echo ""
	@echo "Waiting for services to be ready..."
	@echo "Checking service status..."
	kubectl get services -n vllm

# Utility targets
check-deps:
	@echo "🔍 Checking dependencies..."
	@command -v az >/dev/null 2>&1 || (echo "❌ Azure CLI not found. Install: brew install azure-cli" && exit 1)
	@command -v terraform >/dev/null 2>&1 || (echo "❌ Terraform not found. Install: brew install terraform" && exit 1)
	@command -v kubectl >/dev/null 2>&1 || (echo "❌ kubectl not found. Install: brew install kubectl" && exit 1)
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker not found. Install Docker Desktop" && exit 1)
	@command -v oha >/dev/null 2>&1 || (echo "❌ oha not found. Install: cargo install oha" && exit 1)
	@echo "✅ All dependencies are available"

# Get cluster info
info:
	@echo "📋 Azure Infrastructure Information"
	@echo ""
	@echo "AKS Cluster:"
	@if [ -d "terraform/aks" ] && [ -f "terraform/aks/terraform.tfstate" ]; then \
		cd terraform/aks && terraform output; \
	else \
		echo "  Not deployed yet"; \
	fi
	@echo ""
	@echo "K8s Resources:"
	@if command -v kubectl >/dev/null 2>&1; then \
		echo "  Services:"; \
		kubectl get services -n default 2>/dev/null || echo "    No services or kubectl not configured"; \
		echo "  Pods:"; \
		kubectl get pods -n default 2>/dev/null || echo "    No pods or kubectl not configured"; \
	else \
		echo "  kubectl not available"; \
	fi
	@echo ""
	@echo "Container Registry:"
	@echo "  ACR Name: $(ACR_NAME)"
	@echo "  Resource Group: $(ACR_RG)"
	@echo "  Image: $(IMAGE_NAME):$(IMAGE_TAG)"

# ACR Integration
integrate-acr:
	@echo "🔗 Integrating AKS with ACR..."
	@echo "Getting AKS cluster name..."
	$(eval AKS_CLUSTER_NAME := $(shell cd terraform/aks && terraform output -raw cluster_name 2>/dev/null || echo ""))
	@if [ -z "$(AKS_CLUSTER_NAME)" ]; then \
		echo "❌ AKS cluster name not found. Make sure AKS is deployed first."; \
		exit 1; \
	fi
	@echo "AKS cluster: $(AKS_CLUSTER_NAME)"
	@echo "Attaching ACR to AKS cluster..."
	az aks update --name $(AKS_CLUSTER_NAME) --resource-group $(ACR_RG) --attach-acr $(ACR_NAME)
	@echo "✅ ACR integration complete!"

# Cleanup
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".terraform.lock.hcl" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

# Full destruction workflow (reverse order)
destroy: destroy-k8s destroy-aks
	@echo ""
	@echo "🗑️  Full Azure infrastructure destruction complete!"

# Step 1: Destroy K8s resources
destroy-k8s:
	@echo "🗑️  Destroying K8s resources..."
	@if [ -d "terraform/k8s" ] && [ -f "terraform/k8s/terraform.tfstate" ]; then \
		cd terraform/k8s && terraform destroy -auto-approve; \
		echo "✅ K8s resources destroyed!"; \
	else \
		echo "ℹ️  No K8s terraform state found, skipping..."; \
	fi

# Step 2: Clean up proxy images (optional)
destroy-proxy:
	@echo "🐋 Cleaning up proxy images from ACR..."
	@echo "ℹ️  Note: This will remove the proxy image from ACR"
	@az acr repository delete --name $(ACR_NAME) --repository $(IMAGE_NAME) --yes 2>/dev/null || echo "ℹ️  No proxy image found in ACR or already deleted"
	@echo "✅ Proxy cleanup complete!"

# Step 3: Destroy AKS cluster
destroy-aks:
	@echo "🗑️  Destroying AKS cluster..."
	@if [ -d "terraform/aks" ] && [ -f "terraform/aks/terraform.tfstate" ]; then \
		cd terraform/aks && terraform destroy -auto-approve; \
		echo "✅ AKS cluster destroyed!"; \
	else \
		echo "ℹ️  No AKS terraform state found, skipping..."; \
	fi

# Development helpers
terraform-fmt:
	@echo "🎨 Formatting Terraform files..."
	cd terraform/aks && terraform fmt
	cd terraform/k8s && terraform fmt
	@echo "✅ Terraform formatting complete"

validate:
	@echo "✅ Validating Terraform configurations..."
	@echo "Validating AKS configuration..."
	cd terraform/aks && terraform validate
	@echo "Validating K8s configuration..."
	cd terraform/k8s && terraform validate
	@echo "✅ Validation complete"

# Quick status check
status:
	@echo "📊 Azure Infrastructure Status"
	@echo ""
	@echo "AKS Cluster:"
	@az aks list --resource-group $(ACR_RG) --query "[].{name:name,status:provisioningState,version:kubernetesVersion}" -o table 2>/dev/null || echo "  No AKS clusters found or not logged in"
	@echo ""
	@echo "ACR Images:"
	@az acr repository list --name $(ACR_NAME) -o table 2>/dev/null || echo "  No ACR repositories found or not logged in"
	@echo ""
	@if command -v kubectl >/dev/null 2>&1; then \
		echo "K8s Services:"; \
		kubectl get services -n default 2>/dev/null || echo "  kubectl not configured or no services"; \
	fi
