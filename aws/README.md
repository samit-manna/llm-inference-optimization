# AWS LLM Inference Benchmarking

This directory contains tools and results for benchmarking LLM inference performance on AWS SageMaker endpoints via API Gateway and Lambda.

## Directory Structure

```
aws/
├── experiments/                    # Experiment results and reports
│   └── llama-3.1-8b-awq-int4/     # Specific model experiment
│       ├── EXPERIMENT_REPORT.md   # Detailed experiment report
│       └── raw-results/           # Raw OHA benchmark outputs
├── terraform/                     # Infrastructure as Code
│   ├── *.tf                      # Terraform configuration files
│   └── scripts/                  # Lambda deployment scripts
├── scripts/                       # Benchmarking tools
│   ├── aws_benchmark.sh          # Main HTTP/2 benchmark script
│   └── aws_streaming_bench.py    # Streaming TTFT benchmark script  
├── bench/                         # Benchmark execution environment
│   ├── payloads/                 # Test payloads
│   └── results/                  # Benchmark results
└── README.md                     # This file
```

## Quick Start

### 1. Deploy Infrastructure

```bash
cd aws/terraform
terraform init
terraform plan
terraform apply
```

**Note the API Gateway URL from the output - you'll need it for benchmarking.**

### 2. Run Performance Benchmarks

#### HTTP/2 Load Testing with OHA
```bash
# Basic benchmark (60s test with multiple concurrency levels)
./aws/scripts/aws_benchmark.sh https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat/completions

# Custom duration and output directory
./aws/scripts/aws_benchmark.sh \
  https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat/completions \
  120s \
  ./my-results
```

#### Streaming TTFT Analysis
```bash
# Install Python dependencies
pip install httpx

# Basic streaming benchmark
python3 aws/scripts/aws_streaming_bench.py \
  --url https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat/completions \
  --requests 50 \
  --output streaming_results.json

# High concurrency streaming test
python3 aws/scripts/aws_streaming_bench.py \
  --url https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat/completions \
  --requests 100 \
  --concurrency 4 \
  --max-tokens 128 \
  --output streaming_high_concurrency.json
```

### 3. Monitor and Analyze

- **CloudWatch Dashboard**: Available in AWS Console after deployment
- **Custom Metrics**: `TokensPerSecond`, `CompletionTokens`, `CostPer1kTokensUSD`
- **Lambda Headers**: `X-TTFT-MS`, `X-Tokens-Per-Second`, `X-Cost-Per-1K-USD`

## Benchmarking Tools

### aws_benchmark.sh

Main benchmarking script using `oha` HTTP load tester.

**Features:**
- HTTP/2 support for optimal performance
- Multiple concurrency levels (6, 12, 24, 32)
- JSON output format for analysis
- Automatic summary generation
- Endpoint validation

**Environment Variables:**
- `AWS_REGION`: AWS region (default: us-east-1)
- `MAX_TOKENS`: Maximum tokens per request (default: 64)

**Output:**
- Individual JSON files per concurrency level
- `benchmark_summary.json` with aggregated results
- Console summary table

### aws_streaming_bench.py

Streaming benchmark script for measuring TTFT and analyzing AWS-specific metrics.

**Features:**
- Server-Sent Events (SSE) streaming support
- Time to First Token (TTFT) measurement
- AWS Lambda custom headers parsing
- Configurable concurrency and request count
- Statistical analysis (P50, P95, P99)

**Key Metrics:**
- **Client-side TTFT**: Measured from request start to first content chunk
- **AWS TTFT**: From `X-TTFT-MS` header (Lambda → SageMaker measurement)
- **Tokens per Second**: From `X-Tokens-Per-Second` header
- **Cost per 1k Tokens**: From `X-Cost-Per-1K-USD` header

## Infrastructure Components

### SageMaker Endpoint
- **Instance**: `ml.g5.2xlarge` (A10G 24GB GPU)
- **Model**: `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`
- **Backend**: LMI v15 → vLLM
- **Context**: 8,192 tokens

### API Gateway + Lambda
- **Streaming**: Server-Sent Events via `InvokeEndpointWithResponseStream`
- **Monitoring**: Custom CloudWatch metrics
- **Headers**: Performance and cost metadata

### Autoscaling
- **Metric**: `CompletionTokens` (token volume)
- **Target**: 54,000 tokens/min (≈900 tok/s)
- **Policy**: Target tracking with 1-minute evaluation periods

## Test Profiles

### Load Testing Patterns
1. **C=6** (Baseline): Light load validation
2. **C=12** (Linear): Scaling verification  
3. **C=24** (Sweet Spot): Single-instance optimal load
4. **C=32** (Autoscale Trigger): Multi-instance scaling test

### Expected Performance
- **Single g5.2xlarge**: 900-1,150 tokens/second
- **P95 Latency**: < 2 seconds (SLO compliance)
- **Cost**: < $0.01 per 1k tokens at good utilization

## Usage Examples

### Basic Performance Testing
```bash
# Deploy infrastructure
cd aws/terraform && terraform apply

# Get API Gateway URL from output
export API_URL=$(terraform output -raw api_gateway_url)

# Run standard benchmark
./aws/scripts/aws_benchmark.sh "$API_URL"
```

### Custom Benchmark Configuration
```bash
# Long-duration test with custom tokens
export MAX_TOKENS=128
./aws/scripts/aws_benchmark.sh "$API_URL" 300s ./long-test-results

# Streaming analysis with high concurrency  
python3 aws/scripts/aws_streaming_bench.py \
  --url "$API_URL" \
  --requests 200 \
  --concurrency 8 \
  --max-tokens 128 \
  --output detailed_streaming.json
```

### Result Analysis
```bash
# View benchmark summary
cat aws/bench/results/aws_benchmark_*/benchmark_summary.json | jq '.results[]'

# Extract key metrics
jq -r '.results[] | [.concurrency, .rps, .p95_ms, .estimated_tokens_per_sec] | @csv' \
  aws/bench/results/aws_benchmark_*/benchmark_summary.json
```

## Dependencies

### Required Tools
- **Terraform**: Infrastructure deployment
- **oha**: HTTP load testing (`cargo install oha`)
- **jq**: JSON processing (`brew install jq`)
- **Python 3.8+**: Streaming benchmarks
- **httpx**: Python HTTP client (`pip install httpx`)

### AWS Prerequisites
- AWS CLI configured with appropriate permissions
- Hugging Face Hub token (for model access)
- SageMaker service limits sufficient for g5.2xlarge instances

## Troubleshooting

### Common Issues

1. **OHA Installation**: `cargo install oha` or download from [releases](https://github.com/hatoo/oha/releases)
2. **Permission Errors**: Ensure AWS credentials have SageMaker, API Gateway, Lambda, and CloudWatch permissions
3. **Model Download Timeouts**: Increase SageMaker endpoint deployment timeout in Terraform
4. **Rate Limiting**: AWS API Gateway has default limits; adjust if needed

### Performance Debugging
- Monitor CloudWatch metrics during tests
- Check Lambda logs for errors or timeouts
- Verify SageMaker endpoint health and scaling events
- Use streaming benchmark to isolate TTFT vs total latency issues

## Next Steps

1. **Comparative Analysis**: Run similar tests on Azure and GCP
2. **Model Variants**: Test different quantization levels and model sizes  
3. **Cost Optimization**: Experiment with spot instances and scheduled scaling
4. **Multi-Region**: Deploy across regions for latency comparison

## Contributing

When adding new experiments:
1. Create a new directory under `experiments/` 
2. Include `EXPERIMENT_REPORT.md` with detailed results
3. Save raw benchmark outputs in `raw-results/`
4. Update this README with any new tools or procedures
