# GCP LLM Inference Setup

This directory contains the Google Cloud Platform implementation for LLM inference benchmarking using Google Kubernetes Engine (GKE) and Vertex AI.

## 🏗️ Architecture

- **Google Kubernetes Engine (GKE)**: Container orchestration platform
- **g2-standard-8**: GPU-enabled compute instance with L4 GPU
- **e2-medium**: Proxy/management instance
- **Terraform**: Infrastructure as Code for reproducible deployments
- **Vertex AI**: Optional managed inference endpoint

## 📁 Directory Structure

```
gcp/
├── Makefile                    # Build and deployment automation
├── bench/                      # Benchmarking scripts and payloads
├── container/                  # Docker container definitions
├── proxy/                      # Load balancer service
├── terraform/                  # Infrastructure definitions
│   ├── gke/                   # GKE cluster setup
│   ├── k8s/                   # Kubernetes manifests
│   └── vertexai/              # Vertex AI endpoints
├── config/                     # Configuration files
└── reports/                    # Benchmarking reports
```

## 🚀 Quick Start

### Prerequisites
- Google Cloud CLI installed and configured
- Terraform installed
- Docker (for container builds)
- kubectl (for Kubernetes management)

### Deploy Infrastructure
```bash
make deploy
```

### Build and Push Container
```bash
make build-push
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

- **Estimated Cost**: ~$0.88/hour during active benchmarking
- **Instance Types**: g2-standard-8 (L4 GPU) + e2-medium (proxy)
- **Recommendation**: Excellent cost-performance balance for development and production

## 📊 Performance Characteristics

- **High Efficiency**: Great performance per dollar
- **Google Hardware**: Optimized for ML workloads
- **Auto-scaling**: Kubernetes-native scaling capabilities
- **Regional Deployment**: Multi-zone availability

## ⚙️ Configuration

Key configuration files:
- `terraform/gke/main.tf`: GKE cluster definitions
- `terraform/k8s/deployment.yaml`: Application deployment
- `config/model.env`: Model configuration
- `container/server.py`: Inference server implementation

## 🔧 Available Deployment Options

### 1. GKE with Custom Container
- Full control over inference stack
- Custom optimization possible
- Best for development and testing

### 2. Vertex AI Endpoints
- Managed inference service
- Automatic scaling and monitoring
- Production-ready with SLA

## 📈 Benchmarking

The GCP setup supports both deployment options:

```bash
# Benchmark GKE deployment
make bench-gke

# Benchmark Vertex AI endpoint
make bench-vertex

# Generate performance reports
make report
```

## 🛠 Troubleshooting

Common issues:
- **GPU Quotas**: Ensure sufficient GPU quota in your project
- **Network Issues**: Check VPC and firewall configurations
- **Authentication**: Verify GCloud CLI authentication
- **Container Registry**: Ensure proper registry permissions

For detailed setup instructions, see the project root README.md.
