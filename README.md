# Cross-Cloud LLM Inference Optimization Framework

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-AWS%20%7C%20Azure%20%7C%20GCP%20%7C%20Local-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Terraform](https://img.shields.io/badge/terraform-1.0%2B-purple.svg)

## 🎯 Project Overview

This project demonstrates a systematic approach to optimizing LLM inference costs and performance across multiple deployment scenarios. Using custom benchmarking tools, I've quantified the trade-offs between different cloud providers and deployment strategies for production LLM workloads.

### Key Achievements
- **4 Deployment Platforms**: Local (MacBook Pro M4), AWS SageMaker, Azure AKS, GCP GKE
- **Production-Grade Benchmarking**: Custom Python script with streaming/non-streaming analysis
- **Comprehensive Metrics**: TTFT, P95 latencies, cost per 1M tokens, success rates
- **Cost Optimization**: AWS leads with 2.26M tokens/$1/hour efficiency

## 📊 Performance Executive Summary

| Platform | Best Throughput (TPS) | Best Latency (ms) | TTFT (ms) | Cost per 1M Tokens | Tokens/$/Hour |
|----------|----------------------|-------------------|-----------|-------------------|---------------|
| **AWS** | **950.0** | **2,151** | 2,123 | $0.44 | **2,257,386** |
| **Azure** | 822.4 | 2,488 | **668** | $1.15 | 870,776 |
| **GCP** | 530.7 | 3,857 | 1,279 | $0.46 | 2,170,860 |
| **Local** | 41.6 | 6,160 | **410** | $0.00 | ∞ |

*All tests: Llama 3.1 8B quantized, 32 concurrent requests, 5-minute duration, 100% success rate*

## 🏗️ Architecture & Technical Implementation

### Multi-Cloud Deployment Strategy
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│     LOCAL       │       AWS       │      AZURE      │       GCP       │
├─────────────────├─────────────────├─────────────────├─────────────────┤
│ llama.cpp       │ SageMaker       │ AKS             │ GKE + vLLM      │
│ llama-server    │ + vLLM          │ Instances       │ + L4 GPUs       │
│ M4 Pro (24GB)   │ g5.2xlarge      │ NV36adms_A10_v5 │ Custom Metrics  │
│ TTFT: 410ms     │ Target Tracking │ A10 GPUs        │ Auto-scaling    │
│ 42 TPS          │ Custom Metrics  │ KEDA Scaling    │ Cost-optimized  │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Key Technical Decisions

**Advanced Benchmarking Methodology**:
- Custom Python script with streaming/non-streaming modes
- Statistical analysis with P95 latencies and variance tracking
- Industry-standard cost comparisons vs OpenAI GPT-4 baseline
- TTFT measurements for real-world UX assessment

**Quantization Strategy**: AWQ-INT4/Q4_K_M for optimal memory efficiency
- 4x memory reduction with minimal quality loss
- Enables higher concurrency on GPU-constrained instances
- Consistent performance across all cloud platforms

**Production Auto-Scaling**:
- **AWS**: SageMaker target tracking on `TokensPerSecond`
- **Azure**: KEDA with `rate(llm_completion_tokens_total[1m])`
- **GCP**: Custom HPA with token throughput metrics

---

## 📁 Project Structure

```
llm-inference-optimization/
├── README.md                          # This file - comprehensive project overview
├── aws/                              # AWS SageMaker experiments
│   ├── README.md                     # AWS-specific setup and usage guide
│   ├── terraform/                    # SageMaker + auto-scaling IaC
│   ├── bench/                        # AWS-specific benchmarks
│   └── scripts/                      # Deployment automation
├── azure/                            # Azure Container Instances experiments
│   ├── README.md                     # Azure setup guide
│   ├── terraform/                    # AKS + KEDA scaling IaC
│   │   ├── aks/                     # AKS cluster configuration
│   │   └── k8s/                     # Kubernetes resources
│   ├── proxy/                        # Custom proxy for API compatibility
│   └── bench/                        # Azure benchmarks
├── gcp/                              # Google Cloud experiments
│   ├── README.md                     # GCP setup guide
│   ├── terraform/                    # GKE + HPA IaC
│   │   ├── gke/                     # GKE cluster configuration
│   │   ├── k8s/                     # Kubernetes resources
│   │   └── vertexai/                # Vertex AI experiments
│   ├── container/                    # Custom vLLM container
│   └── bench/                        # GCP benchmarks
├── local/                            # Local inference baseline
│   └── llama.cpp/                    # llama.cpp setup and benchmarks
├── bench/                            # Cross-platform benchmarking tools
│   ├── scripts/                      # Custom benchmarking framework
│   │   ├── comprehensive_report.py  # Automated reporting
│   │   ├── enhanced_report.py       # Enhanced analysis
│   │   └── llm_metrics.py          # Core metrics collection
│   ├── data/                         # Test payloads
│   └── results/                      # Performance data and reports
├── scripts/                          # Project-wide utilities
└── SECURITY.md                       # Security guidelines
```

## 🔧 Quick Start & Reproduction

### Prerequisites
- Terraform >= 1.0
- Python 3.9+ with custom benchmarking dependencies
- Cloud CLI tools (aws-cli, az-cli, gcloud)
- Docker (for local builds)

### Deploy to AWS
```bash
cd aws
make deploy

# Run comprehensive benchmarks
cd ../bench
make bench-aws
```

### Deploy to Azure
```bash
cd azure
make deploy

# Run benchmarks with TTFT analysis
cd ../bench
make bench-azure
```

### Deploy to GCP
```bash
cd gcp
make deploy

# Run benchmarks
cd ../bench
make bench-gcp
```

### Local Setup (macOS)
```bash
cd local
# Build llama.cpp server
make configure
make build

# Download model
make download-model

# Start server
make server
```

---

## Detailed Performance Analysis

### Throughput & Latency Deep Dive

**AWS SageMaker (Winner: Raw Performance)**
- **Aggregate Throughput**: 950 TPS (non-streaming), 900 TPS (streaming)
- **P95 Latency**: 2,974ms (manageable for most use cases)
- **TTFT**: 2,123ms (slower initial response)
- **Best For**: High-throughput batch processing, enterprise workloads

**Azure AKS (Winner: TTFT)**
- **Aggregate Throughput**: 822 TPS
- **TTFT**: 668ms (best cloud performance for interactive use)
- **Challenge**: Oversized instances (36 vCPU for single A10 GPU)
- **Best For**: Interactive applications, real-time chat

**GCP GKE (Winner: Cost Efficiency)**
- **Aggregate Throughput**: 531 TPS
- **Cost per 1M Tokens**: $0.46 (competitive with AWS)
- **Reliable Performance**: Consistent across streaming/non-streaming
- **Best For**: Cost-conscious production deployments

**Local M4 Mac (Winner: Development)**
- **TTFT**: 410ms (fastest first token)
- **Zero Infrastructure Cost**: Perfect for development
- **Throughput**: 42 TPS (sufficient for prototyping)
- **Best For**: Development, experimentation, cost-free testing

### Cost Efficiency Analysis

**Tokens per Dollar per Hour (Higher = Better)**:
1. **AWS**: 2,257,386 tokens/$/hour
2. **GCP**: 2,170,860 tokens/$/hour  
3. **Azure**: 870,776 tokens/$/hour
4. **Local**: ∞ (infrastructure cost only)

**Key Insight**: AWS and GCP are nearly equivalent in cost efficiency, with AWS having a slight edge due to higher throughput. Azure is significantly more expensive due to oversized instances but offers the fastest TTFT for interactive applications.

## 💡 Production Recommendations

### By Use Case

**🚀 High-Throughput Production (AWS)**
- Maximum tokens/second requirement
- Batch processing workloads
- Enterprise SLAs with 2-3s latency tolerance

**⚡ Interactive Applications (Azure)**
- Real-time chat, streaming responses
- User-facing applications requiring fast TTFT
- Accept slightly lower throughput for better UX

**💰 Cost-Optimized Production (GCP)**
- Balanced performance and cost
- Startup/scale-up budgets
- Good baseline for most workloads

**🛠️ Development & Experimentation (Local)**
- Rapid prototyping
- Algorithm development
- Cost-free experimentation

### Streaming vs Non-Streaming

**Streaming Recommended For**:
- Interactive applications (chat, code generation)
- Better perceived performance (users see progress)
- Real-time user feedback requirements

**Non-Streaming Recommended For**:
- Batch processing pipelines
- When complete response needed before processing
- Slightly higher peak throughput requirements

## 🔍 Technical Deep Dive

### Custom Benchmarking Framework

**Why Custom vs oha/wrk?**
- **Streaming Support**: Real LLM apps use streaming for UX
- **TTFT Measurement**: Critical for interactive applications
- **Statistical Rigor**: P95 analysis, variance tracking
- **LLM-Specific Metrics**: Token-based analysis vs simple HTTP

**Methodology Highlights**:
```python
# Example from llm_metrics.py
def measure_streaming_performance():
    ttft_times = []
    token_rates = []
    
    for request in concurrent_requests:
        ttft = measure_time_to_first_token(request)
        tps = measure_tokens_per_second(request)
        
        ttft_times.append(ttft)
        token_rates.append(tps)
    
    return {
        'ttft_p50': np.percentile(ttft_times, 50),
        'ttft_p95': np.percentile(ttft_times, 95),
        'tps_aggregate': sum(token_rates)
    }
```

---

## Next Steps Target

### **Immediate Improvements**
- [ ] Add error rate analysis and retry logic
- [ ] Implement queue depth monitoring
- [ ] Add model quality validation pipeline
- [ ] Optimize Azure instance sizing to reduce cost overhead

### **Advanced Experiments**
- [ ] **Model Size Comparison**: 7B vs 13B vs 70B performance curves
- [ ] **Quantization Deep Dive**: AWQ vs GPTQ vs FP16 accuracy/performance
- [ ] **Auto-scaling Stress Tests**: Cold start times, scale-out behavior
- [ ] **Security Hardening**: Authentication, rate limiting, PII detection

### **Platform Optimization**
- [ ] **AWS**: Test ml.g5.xlarge vs 2xlarge cost efficiency
- [ ] **Azure**: Right-size GPU instances (avoid 36 vCPU overhead)
- [ ] **GCP**: Explore preemptible instances for cost reduction

## 📊 Latest Results

For detailed performance analysis and cross-platform comparisons, see:
- [Comprehensive Report](bench/results/comprehensive_report.md)
- [Performance Charts](bench/results/charts/)

---

## 🏆 About This Experiment

This comprehensive benchmarking represents Week 1 of my transition into LLMOps from 14 years of DevOps architecture experience. The project demonstrates:

**Infrastructure Engineering**:
- Multi-cloud deployment patterns with Terraform IaC
- Production-grade auto-scaling with custom metrics
- Cost optimization through quantitative analysis

**Performance Engineering**:
- Custom benchmarking tools for LLM-specific workloads
- Statistical analysis with P95/P99 latency tracking
- TTFT optimization for real-world user experience

**Operational Excellence**:
- Comprehensive monitoring and observability
- Reproducible deployment automation
- Industry-standard cost comparison methodologies

**Next**: Building on this foundation to explore advanced LLMOps patterns including model versioning, A/B testing, and ML pipeline integration.

---

## Security

This project includes comprehensive security measures:
- Automated credential scanning via pre-commit hooks
- Secure credential management practices (see [SECURITY.md](SECURITY.md))
- Environment variable-based configuration
- Terraform state encryption and access controls

---

## 🪪 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Why MIT License?
- **Open Source Friendly**: Encourages collaboration and learning
- **Portfolio Showcase**: Demonstrates understanding of open source licensing
- **Permissive**: Allows others to use, modify, and distribute the code
- **Industry Standard**: Widely recognized and trusted by employers

---

## 🤝 Contributing

This is primarily a portfolio project demonstrating LLMOps capabilities, but contributions are welcome! Please:

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

*This project demonstrates production-ready infrastructure automation, cost optimization strategies, and performance engineering across multiple cloud platforms as part of a structured transition into LLMOps engineering.*

*Full performance report and raw data available in `/bench/results` directory*
