# Contributing to Multi-Cloud LLM Inference Performance Study

Thank you for your interest in contributing to this project! This is primarily a portfolio project showcasing multi-cloud infrastructure and performance optimization, but contributions are welcome.

## 🤝 How to Contribute

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/llm-inference-optimization.git
cd llm-inference-optimization
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # If available
```

### 3. Follow Security Guidelines
**Important**: This project handles cloud credentials and API keys.

- Read [SECURITY.md](SECURITY.md) before making changes
- Never commit real credentials or API keys
- Use `.env.example` and `.tfvars.example` files as templates
- The pre-commit hook will automatically scan for credentials

### 4. Areas for Contribution

#### 🚀 New Cloud Platforms
- **Oracle Cloud Infrastructure (OCI)**
- **IBM Cloud**
- **DigitalOcean**
- **Vultr GPU instances**

#### 📊 Enhanced Benchmarking
- **New Models**: Support for other LLMs (Mixtral, CodeLlama, etc.)
- **Metrics**: Additional performance metrics (memory usage, GPU utilization)
- **Load Patterns**: Different traffic patterns (burst, sustained, spike)

#### 🔧 Infrastructure Improvements
- **Cost Optimization**: Better autoscaling policies
- **Monitoring**: Enhanced observability and alerting
- **CI/CD**: Automated testing and deployment pipelines

#### 📈 Analysis & Reporting
- **Visualizations**: Interactive charts and dashboards
- **Cost Models**: More sophisticated cost analysis
- **Recommendations**: ML-based optimization suggestions

### 5. Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow existing code patterns
   - Add appropriate documentation
   - Update README if needed

3. **Test your changes**:
   ```bash
   # Run security scan
   ./scripts/security_scan.sh
   
   # Test relevant platform
   cd aws/  # or azure/, gcp/, local/
   make test  # if available
   ```

4. **Commit with clear messages**:
   ```bash
   git add .
   git commit -m "feat: add Oracle Cloud Infrastructure support"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### 6. Code Style and Standards

#### Python
- Follow PEP 8 style guidelines
- Use type hints where possible
- Add docstrings for functions and classes

#### Terraform
- Use consistent naming conventions
- Include comments for complex resources
- Follow HashiCorp's style guide

#### Documentation
- Update relevant README files
- Include examples and usage instructions
- Keep security documentation current

### 7. Commit Message Convention

Use conventional commits for clear history:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Adding tests
- `ci:` - CI/CD changes

Examples:
```
feat: add Azure GPU instance support
fix: correct cost calculation for GCP
docs: update AWS setup instructions
perf: optimize token counting algorithm
```

### 8. Pull Request Guidelines

When submitting a PR:

1. **Clear title and description**
2. **Reference any related issues**
3. **Include testing evidence** (screenshots, logs, metrics)
4. **Update documentation** as needed
5. **Ensure security scan passes**

### 9. Questions and Support

- **Create an issue** for bugs or feature requests
- **Start a discussion** for questions or ideas
- **Check existing issues** before creating new ones

## 🛡️ Security First

This project demonstrates security best practices:

- Automated credential scanning
- Pre-commit hooks
- Secure infrastructure patterns
- Proper secret management

Any contributions must maintain these security standards.

## 📄 License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for helping make this project better! 🚀
