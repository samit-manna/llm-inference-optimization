# Azure LLM Inference Setup

This directory contains the Azure-specific implementation for LLM inference benchmarking using Azure Container Instances (ACI).

## 🏗️ Architecture

- **Azure Container Instances**: Hosts the LLM inference service
- **Standard_NV36adms_A10_v5**: GPU-enabled instance for optimal performance (36 vCPUs, 440 GB RAM, 1x A10 GPU)
- **Terraform**: Infrastructure as Code for reproducible deployments
- **Proxy Service**: Load balancer and request routing

## 📁 Directory Structure

```
azure/
├── Makefile              # Build and deployment automation
├── bench/                # Benchmarking scripts and payloads
├── proxy/                # Load balancer service
└── terraform/            # Infrastructure definitions
```

## 🚀 Quick Start

### Prerequisites
- Azure CLI installed and configured
- Terraform installed
- Docker (for local proxy testing)

### Deploy Infrastructure
```bash
make deploy
```

### Run Benchmarks
```bash
make bench
```

### Cleanup
```bash
make destroy
```

## 💰 Cost Considerations

- **Estimated Cost**: ~$3.40/hour during active benchmarking
- **Instance Type**: Standard_NV36adms_A10_v5 (A10 GPU) + D4s v6 (proxy)
- **Recommendation**: Use for production-grade performance testing

## 📊 Performance Characteristics

- **High GPU Performance**: Excellent for compute-intensive workloads
- **Enterprise Grade**: Built for production reliability
- **Scalable**: Can handle high concurrency loads

## ⚙️ Configuration

Key configuration files:
- `terraform/main.tf`: Infrastructure definitions
- `bench/body_*.json`: Request payloads
- `proxy/app.py`: Load balancer configuration

For detailed setup instructions, see the project root README.md.
