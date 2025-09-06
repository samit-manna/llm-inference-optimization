# LLM Inference Benchmarking Suite

This directory contains tools for benchmarking LLM inference performance across different platforms (Local, AWS, Azure, GCP) and generating comprehensive reports.

## 📁 Directory Structure

```
bench/
├── Makefile                    # Main automation commands
├── configs/                    # Configuration files for different platforms
├── data/                      # Test payloads and input data
├── results/                   # Benchmark results and reports
│   ├── aws/                   # AWS-specific results
│   ├── azure/                 # Azure-specific results  
│   ├── gcp/                   # GCP-specific results
│   ├── local/                 # Local benchmarking results
│   ├── comprehensive_report.md # Main performance report
│   └── comprehensive_report.csv # Data export
└── scripts/                   # Benchmarking and reporting scripts
    ├── llm_metrics_v2.py      # Core benchmarking script
    ├── comprehensive_report.py # Report generator
    └── enhanced_report.py     # Enhanced reporting with charts
```

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Test setup and dependencies
make test-setup

# Run benchmarks for specific platforms
make bench-local    # Local endpoint
make bench-gcp      # GCP endpoint
make bench-aws      # AWS endpoint
make bench-azure    # Azure endpoint

# Run all platforms and generate report
make bench-all

# Generate reports
make report         # Comprehensive report
make show          # Quick summary
```

### Generate Comprehensive Report

```bash
# Generate performance report for all platforms
make report

# Generate report and open in viewer
make report-view
```

### Manual Report Generation

```bash
# Basic comprehensive report
python3 scripts/comprehensive_report.py

# Enhanced report with visualizations (requires matplotlib, seaborn, pandas)
python3 scripts/enhanced_report.py
```

## 📊 Report Contents

The comprehensive report includes:

### Executive Summary
- Best performance metrics per platform
- Token generation totals
- Test duration summary

### Detailed Performance Metrics
- Throughput (Tokens per Second)
- Latency metrics
- Time to First Token (TTFT)
- Success rates
- Request rates

### Cost Analysis
- Hourly costs per platform
- Monthly cost estimates
- Cost efficiency rankings

### Recommendations
- Use case specific guidance
- Streaming vs non-streaming advice
- Platform selection criteria

### Platform-Specific Details
- Detailed metrics breakdown
- Configuration information
- Performance characteristics

## 📈 Key Metrics Explained

| Metric | Description | Unit |
|--------|-------------|------|
| **TPS** | Tokens Per Second (individual request) | tokens/sec |
| **Aggregate TPS** | Total system throughput | tokens/sec |
| **TTFT** | Time To First Token | milliseconds |
| **Latency** | Total request processing time | milliseconds |
| **RPS** | Requests Per Second | requests/sec |
| **Success Rate** | Percentage of successful requests | % |

## 🔧 Platform Configurations

### Local
- **Setup**: llama.cpp on M4 Mac
- **Model**: Llama 3.1 8B quantized
- **Cost**: ~$0.0045/hour (estimated power)

### AWS
- **Setup**: SageMaker endpoint
- **Instance**: ml.g5.2xlarge
- **Cost**: $1.515/hour

### Azure
- **Setup**: Container Instances
- **Instance**: Standard_NV36adms_A10_v5
- **Cost**: $3.40/hour

### GCP
- **Setup**: GKE cluster
- **Instance**: g2-standard-8 + e2-medium
- **Cost**: $0.88/hour

## 📋 Running Benchmarks

To collect new benchmark data:

```bash
# Example: Run benchmark against GCP endpoint
python3 scripts/llm_metrics.py \
  http://34.138.201.70/v1/chat/completions \
  data/streaming_payload.json \
  --platform gcp \
  --duration 300 \
  --concurrency 32

# Example: Local testing
python3 scripts/llm_metrics.py \
  http://localhost:8080/v1/chat/completions \
  data/streaming_payload.json \
  --platform local \
  --duration 60 \
  --concurrency 4

# Example: AWS testing
python3 scripts/llm_metrics.py \
  https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/llama/invocations \
  data/streaming_payload.json \
  --platform aws \
  --duration 300 \
  --concurrency 32
```

**Note**: The `--platform` parameter organizes results into platform-specific directories (e.g., `results/gcp/`, `results/aws/`). If not specified, the script auto-detects based on the URL.

## 📝 Output Files

After running benchmarks and reports:

- `comprehensive_report.md` - Main markdown report
- `comprehensive_report.csv` - Raw data export
- `charts/` - Performance visualizations (if enhanced reporting enabled)

## 🛠 Requirements

### Basic Reporting
- Python 3.7+
- Standard library only

### Enhanced Reporting (Charts)
```bash
pip install matplotlib seaborn pandas
```

## 🎯 Best Practices

1. **Consistent Testing**: Use same payload and duration across platforms
2. **Multiple Runs**: Average results across multiple benchmark runs
3. **Resource Monitoring**: Monitor CPU/GPU utilization during tests
4. **Network Factors**: Account for network latency in cloud deployments
5. **Cost Tracking**: Monitor actual cloud costs vs estimates

## 🔍 Troubleshooting

### Missing Platform Data
- Ensure benchmark files exist in `results/<platform>/`
- Check file naming: `llm_metrics_streaming.json`, `llm_metrics_non_streaming.json`
- Verify JSON format is valid

### Report Generation Issues
- Confirm Python 3.7+ is installed
- Check file permissions on results directory
- Ensure all required input files are present

### Chart Generation Problems
- Install visualization libraries: `pip install matplotlib seaborn pandas`
- Check available system memory for large datasets
- Verify display capabilities for chart rendering

## 📚 Additional Resources

- [llm_metrics.py documentation](scripts/llm_metrics.py) - Benchmarking script details
- [Platform setup guides](../) - Individual platform deployment instructions
- [Terraform configurations](../*/terraform/) - Infrastructure as code

---

*This benchmarking suite is designed for comparing LLM inference performance across cloud platforms and local deployments.*
