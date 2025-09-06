#!/bin/bash
# AWS SageMaker Endpoint Benchmark Script
# Usage: ./aws_benchmark.sh <api_gateway_url> <test_duration> <output_dir>

set -euo pipefail

# Default values
DURATION=${2:-"60s"}
OUTPUT_DIR=${3:-"./results"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
AWS SageMaker Endpoint Benchmark Script

Usage: $0 <api_gateway_url> [duration] [output_dir]

Arguments:
  api_gateway_url    API Gateway URL for the SageMaker endpoint
  duration          Test duration (default: 60s)
  output_dir        Output directory for results (default: ./results)

Environment Variables:
  AWS_REGION        AWS region (default: us-east-1)
  MAX_TOKENS        Maximum tokens per request (default: 64)
  
Examples:
  $0 https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat/completions
  $0 https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat/completions 120s ./aws-results
EOF
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v oha &> /dev/null; then
        error "oha not found. Install with: cargo install oha"
    fi
    
    if ! command -v jq &> /dev/null; then
        error "jq not found. Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    fi
    
    log "Dependencies OK"
}

validate_endpoint() {
    local url=$1
    log "Validating endpoint: $url"
    
    # Test with a simple request
    local test_payload=$(cat << 'EOF'
{
    "model": "llama",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 10,
    "temperature": 0
}
EOF
)
    
    if curl -s --fail -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null; then
        log "Endpoint validation successful"
    else
        warn "Endpoint validation failed. Continuing anyway..."
    fi
}

create_payload() {
    local max_tokens=${MAX_TOKENS:-64}
    local output_file="$1"
    
    cat > "$output_file" << EOF
{
    "model": "llama",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant that provides concise, accurate responses."
        },
        {
            "role": "user", 
            "content": "Explain the key differences between microservices and monolithic architecture in terms of scalability, maintainability, and deployment complexity."
        }
    ],
    "max_tokens": ${max_tokens},
    "temperature": 0.7,
    "stream": false
}
EOF
}

run_benchmark() {
    local url=$1
    local concurrency=$2
    local duration=$3
    local output_file=$4
    local payload_file=$5
    
    log "Running benchmark: C=${concurrency}, Duration=${duration}"
    
    oha --http2 \
        -z "$duration" \
        -c "$concurrency" \
        --output-format json \
        -m POST \
        -H "Content-Type: application/json" \
        -d "@$payload_file" \
        "$url" > "$output_file" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "Benchmark C=${concurrency} completed successfully"
    else
        error "Benchmark C=${concurrency} failed"
    fi
}

generate_summary() {
    local results_dir=$1
    local summary_file="$results_dir/benchmark_summary.json"
    
    log "Generating benchmark summary..."
    
    echo "{" > "$summary_file"
    echo "  \"experiment_timestamp\": \"$(date -Iseconds)\"," >> "$summary_file"
    echo "  \"aws_region\": \"${AWS_REGION:-us-east-1}\"," >> "$summary_file"
    echo "  \"max_tokens\": ${MAX_TOKENS:-64}," >> "$summary_file"
    echo "  \"test_duration\": \"$DURATION\"," >> "$summary_file"
    echo "  \"results\": [" >> "$summary_file"
    
    local first=true
    for result_file in "$results_dir"/c*.json; do
        if [ -f "$result_file" ]; then
            local concurrency=$(basename "$result_file" .json | sed 's/c//')
            
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$summary_file"
            fi
            
            echo -n "    {" >> "$summary_file"
            echo -n "\"concurrency\": $concurrency, " >> "$summary_file"
            
            # Extract key metrics using jq
            local rps=$(jq -r '.summary.requestsPerSec // 0' "$result_file")
            local p50=$(jq -r '.summary.responseTimePercentiles.p50 * 1000 // 0' "$result_file")
            local p95=$(jq -r '.summary.responseTimePercentiles.p95 * 1000 // 0' "$result_file")
            local p99=$(jq -r '.summary.responseTimePercentiles.p99 * 1000 // 0' "$result_file")
            local total_requests=$(jq -r '.summary.totalRequests // 0' "$result_file")
            local successful_requests=$(jq -r '.summary.successfulRequests // 0' "$result_file")
            
            echo -n "\"rps\": $rps, " >> "$summary_file"
            echo -n "\"p50_ms\": $p50, " >> "$summary_file"
            echo -n "\"p95_ms\": $p95, " >> "$summary_file"
            echo -n "\"p99_ms\": $p99, " >> "$summary_file"
            echo -n "\"total_requests\": $total_requests, " >> "$summary_file"
            echo -n "\"successful_requests\": $successful_requests, " >> "$summary_file"
            echo -n "\"estimated_tokens_per_sec\": $(echo "$rps * ${MAX_TOKENS:-64}" | bc -l)" >> "$summary_file"
            echo -n "}" >> "$summary_file"
        fi
    done
    
    echo "" >> "$summary_file"
    echo "  ]" >> "$summary_file"
    echo "}" >> "$summary_file"
    
    log "Summary generated at: $summary_file"
}

print_results() {
    local results_dir=$1
    local summary_file="$results_dir/benchmark_summary.json"
    
    echo -e "\n${BLUE}=== BENCHMARK RESULTS ===${NC}"
    printf "%-12s %-8s %-10s %-10s %-10s %-15s\n" "Concurrency" "RPS" "P50(ms)" "P95(ms)" "P99(ms)" "Est.Tokens/s"
    printf "%-12s %-8s %-10s %-10s %-10s %-15s\n" "----------" "---" "------" "------" "------" "------------"
    
    jq -r '.results[] | [.concurrency, (.rps|tostring), (.p50_ms|tostring), (.p95_ms|tostring), (.p99_ms|tostring), (.estimated_tokens_per_sec|tostring)] | @tsv' "$summary_file" | \
    while IFS=$'\t' read -r conc rps p50 p95 p99 tps; do
        printf "%-12s %-8.2f %-10.0f %-10.0f %-10.0f %-15.0f\n" "C=$conc" "$rps" "$p50" "$p95" "$p99" "$tps"
    done
    
    echo -e "\n${GREEN}Results saved to: $results_dir${NC}"
    echo -e "${GREEN}Summary file: $summary_file${NC}"
}

main() {
    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi
    
    local API_URL=$1
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local results_dir="${OUTPUT_DIR}/aws_benchmark_${timestamp}"
    
    # Setup
    log "Starting AWS SageMaker Endpoint Benchmark"
    log "API URL: $API_URL"
    log "Duration: $DURATION"
    log "Results directory: $results_dir"
    
    check_dependencies
    validate_endpoint "$API_URL"
    
    # Create directories
    mkdir -p "$results_dir"
    
    # Create payload
    local payload_file="$results_dir/payload.json"
    create_payload "$payload_file"
    log "Test payload created at: $payload_file"
    
    # Run benchmarks with different concurrency levels
    local concurrencies=(6 12 24 32)
    
    for c in "${concurrencies[@]}"; do
        local output_file="$results_dir/c${c}.json"
        run_benchmark "$API_URL" "$c" "$DURATION" "$output_file" "$payload_file"
        
        # Brief pause between tests
        sleep 5
    done
    
    # Generate summary and display results
    generate_summary "$results_dir"
    print_results "$results_dir"
    
    log "Benchmark completed successfully!"
}

# Run main function with all arguments
main "$@"
