# Kubernetes Configuration Aliases and Functions
# Source this file in your shell: source kube-aliases.sh

alias k='kubectl'
alias kgn='kubectl get nodes'
alias kgs='kubectl get services'
alias kgp='kubectl get pods'
alias kga='kubectl get all'

# Function to get kubeconfig dynamically
get-aks-config() {
    local method=${1:-"azure-cli"}
    local terraform_dir="/Users/samit.manna/Documents/Passion Projects/llm-inference-optimization/azure/terraform/aks"
    
    cd "$terraform_dir"
    ./get-kubeconfig.sh "$method"
}

# Function to switch between kubeconfig files
switch-kube-context() {
    local context_name=$1
    if [[ -z "$context_name" ]]; then
        echo "Available contexts:"
        kubectl config get-contexts
        return
    fi
    kubectl config use-context "$context_name"
}

# Function to get cluster credentials with auto-detection
aks-login() {
    local terraform_dir="/Users/samit.manna/Documents/Passion Projects/llm-inference-optimization/azure/terraform/aks"
    cd "$terraform_dir"
    
    if terraform output cluster_name >/dev/null 2>&1; then
        local cluster_name=$(terraform output -raw cluster_name)
        local rg_name=$(terraform output -raw resource_group_name)
        
        echo "🔧 Getting credentials for $cluster_name in $rg_name..."
        az aks get-credentials --resource-group "$rg_name" --name "$cluster_name" --overwrite-existing
        
        echo "✅ Connected to AKS cluster!"
        kubectl get nodes
    else
        echo "❌ No Terraform state found. Make sure you're in the right directory and have applied Terraform."
    fi
}

# Quick cluster info
aks-info() {
    local terraform_dir="/Users/samit.manna/Documents/Passion Projects/llm-inference-optimization/azure/terraform/aks"
    cd "$terraform_dir"
    make -f Makefile.kubeconfig cluster-info
}

# Export kubeconfig as environment variable (useful for CI/CD)
export-kube-env() {
    local terraform_dir="/Users/samit.manna/Documents/Passion Projects/llm-inference-optimization/azure/terraform/aks"
    cd "$terraform_dir"
    eval "$($terraform_dir/get-kubeconfig-advanced.sh --format env)"
}

echo "🚀 Kubernetes aliases and functions loaded!"
echo "Available functions:"
echo "  get-aks-config [method]  - Get kubeconfig (terraform, azure-cli, direct, auto)"
echo "  aks-login                - Quick login to AKS cluster"
echo "  aks-info                 - Show cluster information"
echo "  switch-kube-context      - Switch kubectl context"
echo "  export-kube-env          - Export kubeconfig as env var"
echo "Available aliases: k, kgn, kgs, kgp, kga"
