# 🛡️ Security Guide

This document outlines security best practices for the LLM Inference Optimization project.

## 🚨 Critical Security Issues to Avoid

### 1. Never Commit Credentials
- **HuggingFace tokens** (format: `hf_...`)
- **AWS access keys** (format: `AKIA...`)
- **OpenAI API keys** (format: `sk-...`)
- **Google API keys** (format: `AIza...`)
- **Azure subscription IDs**
- **Terraform state files** (may contain sensitive data)

### 2. Files to Never Commit
```
*.tfvars (except *.tfvars.example)
*.env (except *.env.example)
terraform.tfstate*
.aws/
.azure/
.gcp/
service-account-key.json
```

## 🔧 Security Tools Included

### 1. Automated Security Scanner
Run comprehensive security scans:
```bash
./scripts/security_scan.sh
```

### 2. Pre-commit Hook
Automatically prevents commits with credentials:
- Located at `.git/hooks/pre-commit`
- Runs before every commit
- Blocks commits containing sensitive patterns

### 3. Comprehensive .gitignore
Prevents accidental commits of:
- Credential files
- Terraform state
- Large model files
- Cloud configuration

## 🛠️ Secure Development Workflow

### 1. Using Credentials Safely

**✅ Good Practice:**
```bash
# Use environment variables
export HF_TOKEN="your_token_here"
export AWS_ACCESS_KEY_ID="your_key_here"

# Or use dedicated credential files (gitignored)
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values
```

### 2. Terraform Security

**For terraform.tfvars files:**
1. Copy from `.example` file
2. Edit with real values
3. Keep gitignored
4. Use environment variables when possible

```bash
# Good practice
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform plan -var-file=terraform.tfvars
```

### 3. Environment Files

**For .env files:**
1. Copy from `.env.example`
2. Never commit the actual `.env` file
3. Document required variables in README

## 🔍 Regular Security Audits

### Daily Checks
```bash
# Quick security scan
./scripts/security_scan.sh

# Check git status for sensitive files
git status
```

### Before Each Commit
```bash
# The pre-commit hook will run automatically, but you can test it:
git add .
git commit -m "test"  # Will be blocked if credentials found
```

### Weekly Reviews
1. Rotate API keys and tokens
2. Review access logs on cloud platforms
3. Check for any new sensitive files
4. Update security scanner patterns

## 🆘 What to Do If Credentials Are Exposed

### 1. Immediate Actions (within 5 minutes)
1. **Revoke the token immediately:**
   - HuggingFace: https://huggingface.co/settings/tokens
   - AWS: IAM Console > Users > Security credentials
   - OpenAI: https://platform.openai.com/api-keys
   - Google: Cloud Console > APIs & Services > Credentials

2. **Remove from git history:**
```bash
# If already committed, use git filter-branch or BFG Repo-Cleaner
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/sensitive/file' \
--prune-empty --tag-name-filter cat -- --all
```

### 2. Follow-up Actions (within 24 hours)
1. Generate new credentials
2. Update all deployment configurations
3. Review access logs for unauthorized usage
4. Strengthen security practices

## 📚 Resources

- [Git Secrets Tool](https://github.com/awslabs/git-secrets)
- [TruffleHog - Find secrets in git repos](https://github.com/trufflesecurity/trufflehog)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [HuggingFace Security](https://huggingface.co/docs/hub/security)

## 📞 Emergency Contact

If you discover a security vulnerability:
1. Do not create a public issue
2. Follow responsible disclosure practices
3. Immediately revoke any exposed credentials

## 📄 License and Legal

This security guide is part of the Multi-Cloud LLM Inference Performance Study project, licensed under the MIT License. See [LICENSE](LICENSE) for details.

By following these security practices, you help maintain the integrity and trustworthiness of this open source project.

---

**Remember: Security is everyone's responsibility!** 🛡️
