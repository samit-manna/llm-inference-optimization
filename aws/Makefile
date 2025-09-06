#!/usr/bin/env make -f

# AWS LLM Inference Benchmarking Makefile
# Provides convenient commands for common operations

.PHONY: help deploy benchmark analyze clean destroy

# Default target
help:
	@echo "AWS LLM Inference Benchmarking"
	@echo ""
	@echo "Available commands:"
	@echo "  help        Show this help message"
	@echo "  deploy      Deploy infrastructure via Terraform" 
	@echo "  plan        Show Terraform execution plan"
	@echo "  benchmark   Run performance benchmarks (requires URL)"
	@echo "  stream      Run streaming TTFT benchmarks (requires URL)" 
	@echo "  analyze     Analyze benchmark results"
	@echo "  clean       Clean up temporary files"
	@echo "  destroy     Destroy infrastructure"
	@echo ""
	@echo "Environment Variables:"
	@echo "  API_URL     API Gateway URL for benchmarking"
	@echo "  MAX_TOKENS  Max tokens per request (default: 64)"
	@echo "  DURATION    Test duration (default: 60s)"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy"
	@echo "  API_URL=https://xyz.execute-api.us-east-1.amazonaws.com/prod/chat/completions make benchmark"
	@echo "  make analyze RESULTS_DIR=./results/aws_benchmark_20240825_143022"

# Terraform operations
plan:
	@echo "Planning Terraform deployment..."
	cd terraform && terraform plan

deploy:
	@echo "Deploying AWS infrastructure..."
	cd terraform && terraform init && terraform apply --auto-approve
	@echo ""
	@echo "Deployment complete! Get your API Gateway URL with:"
	@echo "  cd terraform && terraform output api_gateway_url"

destroy:
	@echo "Destroying AWS infrastructure..."
	cd terraform && terraform destroy

# Benchmarking
benchmark:
ifndef API_URL
	$(error API_URL is required. Set it to your API Gateway URL)
endif
	@echo "Running HTTP/2 benchmarks against: $(API_URL)"
	./scripts/aws_benchmark.sh "$(API_URL)" "$(DURATION)" "$(RESULTS_DIR)"

stream:
ifndef API_URL  
	$(error API_URL is required. Set it to your API Gateway URL)
endif
	@echo "Running streaming TTFT benchmarks against: $(API_URL)"
	python3 scripts/aws_streaming_bench.py --url "$(API_URL)" --requests 50 --max-tokens $(or $(MAX_TOKENS),64) --output streaming_results.json

# Analysis
analyze:
ifdef RESULTS_DIR
	@echo "Analyzing results in: $(RESULTS_DIR)"
	python3 scripts/analyze_results.py "$(RESULTS_DIR)"
else
	@echo "Analyzing most recent results..."
	python3 scripts/analyze_results.py $$(find bench/results -name "aws_benchmark_*" -type d | sort | tail -1)
endif

# Quick analysis of streaming results
analyze-stream:
	@echo "Streaming results analysis:"
	@if [ -f streaming_results.json ]; then \
		echo "TTFT Stats:"; \
		cat streaming_results.json | jq -r '.statistics.ttft_stats | "Mean: \(.mean)s, P95: \(.p95)s, P99: \(.p99)s"'; \
		echo "AWS TTFT Stats:"; \
		cat streaming_results.json | jq -r '.statistics.aws_ttft_stats | "Mean: \(.mean)s, P95: \(.p95)s"' 2>/dev/null || echo "No AWS headers found"; \
		echo "Cost Stats:"; \
		cat streaming_results.json | jq -r '.statistics.aws_cost_per_1k_stats | "Mean: $\(.mean), Min: $\(.min), Max: $\(.max)"' 2>/dev/null || echo "No cost data found"; \
	else \
		echo "streaming_results.json not found. Run 'make stream' first."; \
	fi

# Utility targets
install-deps:
	@echo "Installing dependencies..."
	@command -v oha >/dev/null 2>&1 || (echo "Installing oha..." && cargo install oha)
	@command -v jq >/dev/null 2>&1 || (echo "Please install jq: brew install jq" && exit 1)
	@python3 -c "import httpx" 2>/dev/null || (echo "Installing httpx..." && pip3 install httpx)
	@echo "Dependencies OK"

clean:
	@echo "Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -f streaming_results.json
	@echo "Clean complete"

# Full workflow
full-test: deploy
	@echo "Waiting for deployment to be ready..."
	sleep 30
	$(eval API_URL := $(shell cd terraform && terraform output -raw api_gateway_url))
	@echo "Running full benchmark suite..."
	$(MAKE) benchmark API_URL="$(API_URL)"
	$(MAKE) stream API_URL="$(API_URL)" 
	$(MAKE) analyze
	$(MAKE) analyze-stream
	@echo ""
	@echo "Full test complete!"
	@echo "Don't forget to run 'make destroy' to clean up resources."

# Development helpers
terraform-fmt:
	cd terraform && terraform fmt

validate:
	@echo "Validating Terraform configuration..."
	cd terraform && terraform validate
	@echo "Validating Python scripts..."
	python3 -m py_compile scripts/*.py
	@echo "Validation complete"
