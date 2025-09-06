#!/usr/bin/env make -f

# GCP LLM Inference Benchmarking Makefile
# Provides convenient commands for common operations

.PHONY: help auth init build deploy deploy-gke deploy-proxy deploy-k8s plan plan-gke plan-k8s info check-deps validate terraform-fmt status get-gke-credentials clean destroy destroy-k8s destroy-proxy destroy-gke

# Environment Variables
PROJECT_ID ?= samit-learning
REGION     ?= us-east1
GAR_REPO   ?= llm-images
IMAGE_NAME ?= vllm-proxy
IMAGE_TAG  ?= v0.1
INSTANCE_HOURLY_USD ?= 0.8536

IMAGE_URI := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(GAR_REPO)/$(IMAGE_NAME):$(IMAGE_TAG)
TF_GKE_DIR := terraform/gke
TF_K8S_DIR := terraform/k8s

# Default target
help:
	@echo "GCP LLM Inference Benchmarking"
	@echo ""
	@echo "Available commands:"
	@echo "  help          Show this help message"
	@echo "  deploy        Deploy full infrastructure (GKE -> Proxy -> K8s)"
	@echo "  deploy-gke    Deploy GKE cluster via Terraform"
	@echo "  deploy-proxy  Build and push proxy app to GAR"
	@echo "  deploy-k8s    Deploy K8s resources via Terraform"
	@echo "  plan          Show Terraform execution plan for all components"
	@echo "  plan-gke      Show Terraform execution plan for GKE"
	@echo "  plan-k8s      Show Terraform execution plan for K8s"
	@echo "  info          Show infrastructure information"
	@echo "  check-deps    Check required dependencies"
	@echo "  get-gke-credentials Get GKE cluster credentials"
	@echo "  validate      Validate Terraform configurations"
	@echo "  terraform-fmt Format Terraform files"
	@echo "  status        Show GCP infrastructure status"
	@echo "  clean         Clean up temporary files"
	@echo "  destroy       Destroy infrastructure in reverse order (K8s -> Proxy -> GKE)"
	@echo "  destroy-k8s   Destroy K8s resources"
	@echo "  destroy-proxy Clean up proxy images (optional)"
	@echo "  destroy-gke   Destroy GKE cluster"
	@echo ""
	@echo "Environment Variables:"
	@echo "  PROJECT_ID           GCP Project ID (default: $(PROJECT_ID))"
	@echo "  REGION               GCP Region (default: $(REGION))"
	@echo "  GAR_REPO             Google Artifact Registry repo (default: $(GAR_REPO))"
	@echo "  IMAGE_NAME           Docker image name (default: $(IMAGE_NAME))"
	@echo "  IMAGE_TAG            Docker image tag (default: $(IMAGE_TAG))"
	@echo "  INSTANCE_HOURLY_USD  Instance hourly cost (default: $(INSTANCE_HOURLY_USD))"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy"
	@echo "  PROJECT_ID=my-project make deploy"
	@echo "  make destroy"

# Terraform Variables
TFVARS_GKE := -var=project_id=$(PROJECT_ID) -var=region=$(REGION) -var=image_uri=$(IMAGE_URI)
TFVARS_K8S := -var=proxy_image=$(IMAGE_URI) -var=instance_hourly_usd=$(INSTANCE_HOURLY_USD)

# Authentication
auth:
	@echo "🔐 Configuring GCP authentication..."
	gcloud config set project $(PROJECT_ID)
	gcloud auth configure-docker $(REGION)-docker.pkg.dev -q || true
	@echo "✅ Authentication configured!"

# Initialization
init:
	@echo "ℹ️  Nothing to init. Use deploy-gke or deploy-k8s for Terraform init."

# Full deployment workflow
deploy: deploy-gke deploy-proxy get-gke-credentials deploy-k8s
	@echo ""
	@echo "🎉 Full GCP deployment complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Get the service external IP:"
	@echo "   kubectl get services -n default"
	@echo "2. When done, clean up:"
	@echo "   make destroy"

# Terraform planning
plan: plan-gke plan-k8s

plan-gke:
	@echo "📋 Planning GKE Terraform deployment..."
	cd $(TF_GKE_DIR) && terraform plan $(TFVARS_GKE)

plan-k8s:
	@echo "📋 Planning K8s Terraform deployment..."
	cd $(TF_K8S_DIR) && terraform plan $(TFVARS_K8S)

# Step 1: Deploy GKE cluster
deploy-gke:
	@echo "🚀 Deploying GKE cluster..."
	cd $(TF_GKE_DIR) && terraform init && terraform apply -auto-approve $(TFVARS_GKE)
	@echo "✅ GKE cluster deployment complete!"

# Step 2: Build and push proxy to GAR
deploy-proxy: auth
	@echo "🐋 Building and pushing proxy to GAR..."
	docker build --platform linux/amd64 -t $(IMAGE_URI) proxy
	docker push $(IMAGE_URI)
	@echo "✅ Proxy build and push complete!"

# Get GKE credentials
get-gke-credentials:
	@echo "🔑 Getting GKE credentials..."
	@gcloud container clusters get-credentials $$(cd $(TF_GKE_DIR) && terraform output -raw cluster_name) --zone us-east1-c --project $(PROJECT_ID)
	@echo "✅ GKE credentials configured!"

# Step 3: Deploy K8s resources
deploy-k8s:
	@echo "☸️  Deploying K8s resources..."
	cd $(TF_K8S_DIR) && terraform init && terraform apply -auto-approve $(TFVARS_K8S)
	@echo "✅ K8s resources deployment complete!"
	@echo ""
	@echo "Waiting for services to be ready..."
	@echo "Checking service status..."
	kubectl get services -n default

# Utility targets
check-deps:
	@echo "🔍 Checking dependencies..."
	@command -v gcloud >/dev/null 2>&1 || (echo "❌ Google Cloud CLI not found. Install: brew install google-cloud-sdk" && exit 1)
	@command -v terraform >/dev/null 2>&1 || (echo "❌ Terraform not found. Install: brew install terraform" && exit 1)
	@command -v kubectl >/dev/null 2>&1 || (echo "❌ kubectl not found. Install: brew install kubectl" && exit 1)
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker not found. Install Docker Desktop" && exit 1)
	@echo "✅ All dependencies are available"

# Get infrastructure info
info:
	@echo "📋 GCP Infrastructure Information"
	@echo ""
	@echo "GKE Cluster:"
	@if [ -d "$(TF_GKE_DIR)" ] && [ -f "$(TF_GKE_DIR)/terraform.tfstate" ]; then \
		cd $(TF_GKE_DIR) && terraform output; \
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
	@echo "  Project ID: $(PROJECT_ID)"
	@echo "  Region: $(REGION)"
	@echo "  GAR Repo: $(GAR_REPO)"
	@echo "  Image: $(IMAGE_NAME):$(IMAGE_TAG)"
	@echo "  Full URI: $(IMAGE_URI)"

# Cleanup
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".terraform.lock.hcl" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

# Full destruction workflow (reverse order)
destroy: destroy-k8s destroy-gke
	@echo ""
	@echo "🗑️  Full GCP infrastructure destruction complete!"

# Step 1: Destroy K8s resources
destroy-k8s:
	@echo "🗑️  Destroying K8s resources..."
	@if [ -d "$(TF_K8S_DIR)" ] && [ -f "$(TF_K8S_DIR)/terraform.tfstate" ]; then \
		cd $(TF_K8S_DIR) && terraform destroy -auto-approve $(TFVARS_K8S); \
		echo "✅ K8s resources destroyed!"; \
	else \
		echo "ℹ️  No K8s terraform state found, skipping..."; \
	fi

# Step 2: Clean up proxy images (optional)
destroy-proxy:
	@echo "🐋 Cleaning up proxy images from GAR..."
	@echo "ℹ️  Note: This will remove the proxy image from GAR"
	@gcloud artifacts docker images delete $(IMAGE_URI) --quiet 2>/dev/null || echo "ℹ️  No proxy image found in GAR or already deleted"
	@echo "✅ Proxy cleanup complete!"

# Step 3: Destroy GKE cluster
destroy-gke:
	@echo "🗑️  Destroying GKE cluster..."
	@if [ -d "$(TF_GKE_DIR)" ] && [ -f "$(TF_GKE_DIR)/terraform.tfstate" ]; then \
		cd $(TF_GKE_DIR) && terraform destroy -auto-approve $(TFVARS_GKE); \
		echo "✅ GKE cluster destroyed!"; \
	else \
		echo "ℹ️  No GKE terraform state found, skipping..."; \
	fi

# Development helpers
terraform-fmt:
	@echo "🎨 Formatting Terraform files..."
	cd $(TF_GKE_DIR) && terraform fmt
	cd $(TF_K8S_DIR) && terraform fmt
	@echo "✅ Terraform formatting complete"

validate:
	@echo "✅ Validating Terraform configurations..."
	@echo "Validating GKE configuration..."
	cd $(TF_GKE_DIR) && terraform validate
	@echo "Validating K8s configuration..."
	cd $(TF_K8S_DIR) && terraform validate
	@echo "✅ Validation complete"

# Quick status check
status:
	@echo "📊 GCP Infrastructure Status"
	@echo ""
	@echo "GKE Clusters:"
	@gcloud container clusters list --project=$(PROJECT_ID) --format="table(name,status,currentMasterVersion,location)" 2>/dev/null || echo "  No GKE clusters found or not logged in"
	@echo ""
	@echo "GAR Images:"
	@gcloud artifacts docker images list $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(GAR_REPO) --format="table(package,version,createTime)" 2>/dev/null || echo "  No GAR images found or not logged in"
	@echo ""
	@if command -v kubectl >/dev/null 2>&1; then \
		echo "K8s Services:"; \
		kubectl get services -n default 2>/dev/null || echo "  kubectl not configured or no services"; \
	fi
