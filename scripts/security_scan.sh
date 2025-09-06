#!/bin/bash
# Security scanning script for LLM inference project
# This script scans for various types of sensitive data

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Security Scan Report - $(date)"
echo "=========================================="

# Function to print colored output
print_header() {
    echo -e "\n\033[1;34m$1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_danger() {
    echo -e "\033[1;31m🚨 $1\033[0m"
}

print_success() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

# 1. Check for common credential patterns
print_header "1. Scanning for API Keys and Tokens"
if grep -r -i -E "(api[_-]?key|secret[_-]?key|access[_-]?token)" \
    --include="*.tf" --include="*.py" --include="*.json" --include="*.yaml" \
    --include="*.yml" --include="*.sh" --include="*.env" \
    --exclude-dir=".git" --exclude-dir=".terraform" --exclude-dir="local/llama.cpp" \
    . 2>/dev/null | grep -v "tokenizer" | grep -v "token_" | head -5; then
    print_warning "Found potential API key references (review above)"
else
    print_success "No obvious API key patterns found"
fi

# 2. Check for actual token values
print_header "2. Scanning for Token Values"
if grep -r -E "(sk-[a-zA-Z0-9]{48}|hf_[a-zA-Z0-9]{34}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})" \
    --include="*.tf" --include="*.py" --include="*.json" --include="*.yaml" \
    --include="*.yml" --include="*.sh" --include="*.env" \
    --exclude-dir=".git" --exclude-dir=".terraform" --exclude-dir="local/llama.cpp" \
    . 2>/dev/null; then
    print_danger "FOUND ACTUAL TOKENS! REVOKE IMMEDIATELY!"
else
    print_success "No actual token values found"
fi

# 3. Check for credential files
print_header "3. Scanning for Credential Files"
credential_files=$(find . -name "*.tfvars" -not -name "*.example" \
    -o -name "*.env" -not -name "*.env.example" \
    -o -name "credentials.json" \
    -o -name "service-account.json" \
    -o -name ".aws" -type d \
    -o -name ".gcp" -type d \
    -o -name ".azure" -type d \
    2>/dev/null || true)

if [[ -n "$credential_files" ]]; then
    print_warning "Found credential files:"
    echo "$credential_files" | while read -r file; do
        echo "  - $file"
    done
else
    print_success "No credential files found"
fi

# 4. Check for terraform state files
print_header "4. Scanning for Terraform State Files"
state_files=$(find . -name "terraform.tfstate*" 2>/dev/null || true)
if [[ -n "$state_files" ]]; then
    print_warning "Found terraform state files (may contain sensitive data):"
    echo "$state_files" | while read -r file; do
        echo "  - $file"
    done
else
    print_success "No terraform state files found"
fi

# 5. Check for large files that shouldn't be committed
print_header "5. Scanning for Large Files"
large_files=$(find . -type f -size +50M \
    -not -path "./.git/*" \
    -not -path "./local/llama.cpp/*" \
    2>/dev/null || true)

if [[ -n "$large_files" ]]; then
    print_warning "Found large files (>50MB):"
    echo "$large_files" | while read -r file; do
        size=$(du -h "$file" | cut -f1)
        echo "  - $file ($size)"
    done
else
    print_success "No large files found"
fi

# 6. Check git status for staged sensitive files
print_header "6. Checking Git Status"
if git rev-parse --git-dir > /dev/null 2>&1; then
    staged_files=$(git diff --cached --name-only 2>/dev/null || true)
    if [[ -n "$staged_files" ]]; then
        print_warning "Files staged for commit:"
        echo "$staged_files" | while read -r file; do
            if [[ "$file" == *.tfvars ]] || [[ "$file" == *.env ]] || [[ "$file" == *tfstate* ]]; then
                print_danger "  - $file (SENSITIVE FILE TYPE!)"
            else
                echo "  - $file"
            fi
        done
    else
        print_success "No files staged for commit"
    fi
else
    print_warning "Not in a git repository"
fi

echo ""
print_header "🛡️ Security Recommendations"
echo "1. Never commit .tfvars files with real credentials"
echo "2. Use environment variables for sensitive data"
echo "3. Always use .gitignore for credential files"
echo "4. Regularly rotate API keys and tokens"
echo "5. Use git-secrets or pre-commit hooks for automatic scanning"
echo "6. Review .terraform/terraform.tfstate files before committing"

echo ""
print_header "📋 Next Steps"
echo "1. If tokens found: Revoke immediately on respective platforms"
echo "2. Remove sensitive files from git history if already committed"
echo "3. Update .gitignore to prevent future accidents"
echo "4. Set up environment-based credential management"

echo ""
echo "🔍 Scan completed at $(date)"
