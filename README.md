# Multi-Cloud LLM Inference Performance Study

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-AWS%20%7C%20Azure%20%7C%20GCP-green.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Terraform](https://img.shields.io/badge/terraform-1.0%2B-purple.svg)

This repository contains a comprehensive analysis of Large Language Model (LLM) inference performance across multiple cloud providers, with a focus on cost optimization, latency characteristics, and scalability patterns.

## Why this repo
- **Multi-Cloud Analysis**: Compare AWS, Azure, GCP inference costs and performance
- **Production-Ready**: SRE-style metrics (p50/p95, tokens/sec, TTFT, cost/1k tokens)
- **Reproducible**: Infrastructure as Code + standardized benchmarking
- **Baseline**: Local M4 MacBook Pro performance using llama.cpp

---

## Project Structure

```
llm-inference-optimization/
├── README.md                          # This file - project overview
├── aws/                              # AWS-specific experiments and tools
│   ├── README.md                     # AWS setup and usage guide
│   ├── experiments/                  # Experiment results and reports
│   │   └── llama-3.1-8b-awq-int4/   # Specific model experiment
│   ├── terraform/                    # Infrastructure as Code
│   ├── scripts/                      # Benchmarking automation
│   └── bench/                        # Benchmark execution environment
├── azure/                            # Azure experiments and infrastructure
├── gcp/                              # Google Cloud experiments and infrastructure
├── bench/                            # Cross-platform benchmarking tools
└── llama.cpp/                        # Local inference baseline
```

## Experiments Overview

### Completed
- ✅ **AWS SageMaker**: Llama-3.1-8B-Instruct-AWQ-INT4 on ml.g5.2xlarge
  - Sub-1¢ per 1k tokens at scale
  - Token-aware autoscaling
  - P95 < 2s latency SLO compliance
- ✅ **Azure Container Instances**: Standard_NV36adms_A10_v5 with A10 GPU
- ✅ **GCP GKE**: g2-standard-8 with L4 GPU deployment
- ✅ **Local M4 MacBook Pro**: llama.cpp performance baseline

### Benchmarking Tools
- ✅ **Comprehensive Reporting**: Cross-platform performance analysis
- ✅ **Cost Analysis**: Cost per 1M tokens comparison
- ✅ **Automated Benchmarking**: Makefile-driven testing suite

## Key Findings (AWS)

| Metric | Value | Notes |
|--------|-------|-------|
| **Peak Throughput** | 1,188 tokens/sec | With autoscaling (C=32, 5min test) |
| **Single Instance** | 910-1,150 tokens/sec | ml.g5.2xlarge sweet spot |
| **Cost Efficiency** | $0.00866/1k tokens | At good utilization |
| **P95 Latency** | 1,952ms | Under autoscaled load |
| **SLO Compliance** | < 2 seconds | Maintained with token-aware scaling |

---

## Local Baseline Hardware & Software

- **Machine**: MacBook Pro **M4 Pro**, 24 GB
- **Runtime**: `llama.cpp` server (OpenAI-compatible)
- **Model**: `Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf` (~4.9 GB)
- **Server flags**: `-np 4 -c 8192`
- **Tools**: `oha`, `python3` (`httpx`)

Server command:
```bash
./build/bin/llama-server -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf --port 8080 -c 8192 -np 4
```

---

## 📊 Latest Results

For detailed performance analysis and cross-platform comparisons, see:
- [Comprehensive Report](bench/results/comprehensive_report.md)
- [Performance Charts](bench/results/charts/)

---

## 🛡️ Security

This project includes comprehensive security measures:
- Automated credential scanning
- Pre-commit hooks for sensitive data prevention
- Secure credential management practices

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Why MIT License?
- **Open Source Friendly**: Encourages collaboration and learning
- **Portfolio Showcase**: Demonstrates understanding of open source licensing
- **Permissive**: Allows others to use, modify, and distribute the code
- **Industry Standard**: Widely recognized and trusted by employers

---

## 🤝 Contributing

This is primarily a portfolio project, but contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-improvement`)
3. Follow the security guidelines in [SECURITY.md](SECURITY.md)
4. Commit your changes (`git commit -am 'Add amazing improvement'`)
5. Push to the branch (`git push origin feature/amazing-improvement`)
6. Open a Pull Request

---

## 📞 Contact

**Samit Manna**
- Portfolio: [GitHub Profile](https://github.com/samit-manna)
- LinkedIn: [Connect with me](https://linkedin.com/in/samit-manna)

---

*This project demonstrates production-ready infrastructure automation, cost optimization strategies, and performance engineering across multiple cloud platforms.*
