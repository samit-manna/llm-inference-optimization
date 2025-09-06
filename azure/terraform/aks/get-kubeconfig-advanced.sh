#!/bin/bash

# Advanced Kubernetes Config Manager
# Supports multiple output formats and automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR"

# Parse command line arguments
OUTPUT_FORMAT="file"  # file, stdout, base64, env
OUTPUT_PATH="$HOME/.kube/config"
MERGE_CONFIG="true"
CONTEXT_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --output)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --no-merge)
            MERGE_CONFIG="false"
            shift
            ;;
        --context-name)
            CONTEXT_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --format FORMAT     Output format: file, stdout, base64, env (default: file)"
            echo "  --output PATH       Output file path (default: ~/.kube/config)"
            echo "  --no-merge          Don't merge with existing kubeconfig"
            echo "  --context-name NAME Custom context name"
            echo "  --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$TERRAFORM_DIR"

# Get cluster information
CLUSTER_NAME=$(terraform output -raw cluster_name 2>/dev/null || echo "")
RG_NAME=$(terraform output -raw resource_group_name 2>/dev/null || echo "")

if [[ -z "$CLUSTER_NAME" || -z "$RG_NAME" ]]; then
    echo "❌ Could not get cluster information from Terraform state"
    echo "Make sure you've run 'terraform apply' and have the outputs configured"
    exit 1
fi

echo "📋 Cluster: $CLUSTER_NAME in Resource Group: $RG_NAME"

case $OUTPUT_FORMAT in
    "file")
        if [[ "$MERGE_CONFIG" == "true" ]]; then
            az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --overwrite-existing
            echo "✅ Kubeconfig merged into $HOME/.kube/config"
        else
            az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --file "$OUTPUT_PATH"
            echo "✅ Kubeconfig saved to $OUTPUT_PATH"
        fi
        ;;
        
    "stdout")
        # Get kubeconfig and output to stdout
        TEMP_CONFIG=$(mktemp)
        az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --file "$TEMP_CONFIG"
        cat "$TEMP_CONFIG"
        rm "$TEMP_CONFIG"
        ;;
        
    "base64")
        # Get kubeconfig as base64 (useful for secrets)
        TEMP_CONFIG=$(mktemp)
        az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --file "$TEMP_CONFIG"
        base64 < "$TEMP_CONFIG"
        rm "$TEMP_CONFIG"
        ;;
        
    "env")
        # Output as environment variable
        TEMP_CONFIG=$(mktemp)
        az aks get-credentials --resource-group "$RG_NAME" --name "$CLUSTER_NAME" --file "$TEMP_CONFIG"
        echo "export KUBECONFIG=\"$TEMP_CONFIG\""
        echo "# Run: eval \"\$(./get-kubeconfig-advanced.sh --format env)\""
        ;;
        
    *)
        echo "❌ Unknown format: $OUTPUT_FORMAT"
        exit 1
        ;;
esac

# Test connection if outputting to file
if [[ "$OUTPUT_FORMAT" == "file" ]]; then
    echo ""
    echo "🎉 Testing connection..."
    if kubectl get nodes 2>/dev/null; then
        echo "✅ Successfully connected to Kubernetes cluster!"
        
        # Show current context
        CURRENT_CONTEXT=$(kubectl config current-context)
        echo "📋 Current context: $CURRENT_CONTEXT"
        
        # Show available contexts
        echo ""
        echo "📋 Available contexts:"
        kubectl config get-contexts
    else
        echo "⚠️  Could not connect to cluster. Check your configuration."
    fi
fi
