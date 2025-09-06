#!/bin/bash

# Dynamic Kubernetes Config Retrieval Script
# Usage: ./get-kubeconfig.sh [method]
# Methods: terraform, azure-cli, direct

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR"

METHOD=${1:-"azure-cli"}

case $METHOD in
    "terraform")
        echo "🔧 Getting kubeconfig from Terraform state..."
        cd "$TERRAFORM_DIR"
        if terraform output kube_config >/dev/null 2>&1; then
            terraform output -raw kube_config > ~/.kube/config-aks-terraform
            echo "✅ Kubeconfig saved to ~/.kube/config-aks-terraform"
            echo "To use: export KUBECONFIG=~/.kube/config-aks-terraform"
        else
            echo "❌ No kube_config output found in Terraform state"
            exit 1
        fi
        ;;
        
    "azure-cli")
        echo "🔧 Getting kubeconfig using Azure CLI..."
        cd "$TERRAFORM_DIR"
        
        # Get cluster info from Terraform
        CLUSTER_NAME=$(terraform output -raw cluster_name)
        RG_NAME=$(terraform output -raw resource_group_name)
        
        echo "📋 Cluster: $CLUSTER_NAME in Resource Group: $RG_NAME"
        
        # Get credentials
        az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --overwrite-existing
        echo "✅ Kubeconfig updated in ~/.kube/config"
        ;;
        
    "direct")
        echo "🔧 Getting kubeconfig using direct Azure CLI (no Terraform)..."
        
        # You can customize these values or make them parameters
        SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}
        RG_NAME=${RESOURCE_GROUP:-"sam-rg-llm-aks"}
        CLUSTER_NAME=${CLUSTER_NAME:-"sam-aks-llm"}
        
        echo "📋 Using Subscription: $SUBSCRIPTION_ID"
        echo "📋 Resource Group: $RG_NAME"
        echo "📋 Cluster: $CLUSTER_NAME"
        
        az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --overwrite-existing
        echo "✅ Kubeconfig updated in ~/.kube/config"
        ;;
        
    "auto")
        echo "🔧 Auto-detecting best method..."
        cd "$TERRAFORM_DIR"
        
        if terraform output cluster_name >/dev/null 2>&1; then
            echo "Found Terraform state, using azure-cli method..."
            $0 azure-cli
        else
            echo "No Terraform state found, using direct method..."
            $0 direct
        fi
        ;;
        
    *)
        echo "Usage: $0 [method]"
        echo "Methods:"
        echo "  terraform  - Extract from Terraform state (requires outputs)"
        echo "  azure-cli  - Use Azure CLI with Terraform outputs (recommended)"
        echo "  direct     - Use Azure CLI directly (no Terraform dependency)"
        echo "  auto       - Auto-detect best method"
        exit 1
        ;;
esac

echo ""
echo "🎉 Testing connection..."
if kubectl get nodes 2>/dev/null; then
    echo "✅ Successfully connected to Kubernetes cluster!"
else
    echo "⚠️  Could not connect to cluster. Check your configuration."
fi
