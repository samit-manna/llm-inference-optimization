#!/usr/bin/env make -f

# LLM Inference Benchmarking Makefile
# Provides convenient commands for benchmarking and reporting

.PHONY: help report report-view report-enhanced show clean bench-local bench-aws bench-azure bench-gcp bench-custom bench-all test-setup

# Environment Variables for benchmarking
PAYLOAD_FILE ?= data/streaming_payload.json
LOCAL_URL ?= http://localhost:8080/v1/chat/completions
AWS_URL ?= https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/llama/invocations
AZURE_URL ?= http://azure-endpoint.eastus.azurecontainer.io/v1/chat/completions
GCP_URL ?= http://34.138.201.70/v1/chat/completions
CUSTOM_URL ?= https://api.example.com/v1/chat/completions

# Benchmark parameters
LOCAL_DURATION ?= 60
CLOUD_DURATION ?= 300
LOCAL_CONCURRENCY ?= 4
CLOUD_CONCURRENCY ?= 32

# Default target
help:
	@echo "LLM Inference Benchmarking Tools"
	@echo ""
	@echo "📊 Reporting Commands:"
	@echo "  help             Show this help message"
	@echo "  report           Generate comprehensive performance report"
	@echo "  report-view      Generate report and open in default viewer"
	@echo "  report-enhanced  Generate enhanced report with charts"
	@echo "  show             Show current report summary"
	@echo "  clean            Clean up temporary files"
	@echo ""
	@echo "🧪 Benchmarking Commands:"
	@echo "  bench-local      Run benchmark against local endpoint"
	@echo "  bench-aws        Run benchmark against AWS endpoint"
	@echo "  bench-azure      Run benchmark against Azure endpoint"
	@echo "  bench-gcp        Run benchmark against GCP endpoint"
	@echo "  bench-custom     Run benchmark against custom endpoint"
	@echo "  bench-all        Run benchmarks against all configured platforms"
	@echo "  test-setup       Test benchmark setup and dependencies"
	@echo ""
	@echo "🔧 Environment Variables:"
	@echo "  PAYLOAD_FILE     JSON payload file (default: $(PAYLOAD_FILE))"
	@echo "  LOCAL_URL        Local endpoint URL (default: $(LOCAL_URL))"
	@echo "  AWS_URL          AWS endpoint URL (default: $(AWS_URL))"
	@echo "  AZURE_URL        Azure endpoint URL (default: $(AZURE_URL))"
	@echo "  GCP_URL          GCP endpoint URL (default: $(GCP_URL))"
	@echo "  CUSTOM_URL       Custom endpoint URL (default: $(CUSTOM_URL))"
	@echo ""
	@echo "Examples:"
	@echo "  make bench-local"
	@echo "  make bench-gcp"
	@echo "  make bench-all"
	@echo "  GCP_URL=http://my-endpoint.com make bench-gcp"
	@echo "  make report"

# Generate comprehensive report
report:
	@echo "📊 Generating comprehensive performance report..."
	python3 scripts/comprehensive_report.py
	@echo ""
	@echo "✅ Report generated successfully!"
	@echo "📄 Markdown report: results/comprehensive_report.md"
	@echo "📊 CSV export: results/comprehensive_report.csv"

# Generate report and open it
report-view: report
	@echo "👁️  Opening report in default viewer..."
	@if command -v open >/dev/null 2>&1; then \
		open results/comprehensive_report.md; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open results/comprehensive_report.md; \
	else \
		echo "Please manually open: results/comprehensive_report.md"; \
	fi

# Generate enhanced report with charts
report-enhanced: report
	@echo "📈 Generating enhanced report with visualizations..."
	@python3 scripts/enhanced_report.py results || echo "⚠️  Enhanced reporting requires: pip install matplotlib seaborn pandas"

# Show current report summary
show:
	@echo "📋 Current Performance Summary"
	@echo "============================="
	@if [ -f "results/comprehensive_report.md" ]; then \
		head -25 results/comprehensive_report.md | tail -20; \
		echo ""; \
		echo "📄 Full report: results/comprehensive_report.md"; \
	else \
		echo "❌ No report found. Run 'make report' first."; \
	fi

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

# Benchmarking targets
bench-local:
	@echo "🧪 Running LOCAL benchmark..."
	@echo "   URL: $(LOCAL_URL)"
	@echo "   Duration: $(LOCAL_DURATION)s, Concurrency: $(LOCAL_CONCURRENCY)"
	@echo "   Payload: $(PAYLOAD_FILE)"
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then \
		echo "❌ Payload file not found: $(PAYLOAD_FILE)"; \
		exit 1; \
	fi
	python3 scripts/llm_metrics.py \
		"$(LOCAL_URL)" \
		"$(PAYLOAD_FILE)" \
		--platform local \
		--duration $(LOCAL_DURATION) \
		--concurrency $(LOCAL_CONCURRENCY) \
		--mode both
	@echo "✅ Local benchmark complete! Results in results/local/"

bench-aws:
	@echo "🧪 Running AWS benchmark..."
	@echo "   URL: $(AWS_URL)"
	@echo "   Duration: $(CLOUD_DURATION)s, Concurrency: $(CLOUD_CONCURRENCY)"
	@echo "   Payload: $(PAYLOAD_FILE)"
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then \
		echo "❌ Payload file not found: $(PAYLOAD_FILE)"; \
		exit 1; \
	fi
	python3 scripts/llm_metrics.py \
		"$(AWS_URL)" \
		"$(PAYLOAD_FILE)" \
		--platform aws \
		--duration $(CLOUD_DURATION) \
		--concurrency $(CLOUD_CONCURRENCY) \
		--mode both
	@echo "✅ AWS benchmark complete! Results in results/aws/"

bench-azure:
	@echo "🧪 Running AZURE benchmark..."
	@echo "   URL: $(AZURE_URL)"
	@echo "   Duration: $(CLOUD_DURATION)s, Concurrency: $(CLOUD_CONCURRENCY)"
	@echo "   Payload: $(PAYLOAD_FILE)"
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then \
		echo "❌ Payload file not found: $(PAYLOAD_FILE)"; \
		exit 1; \
	fi
	python3 scripts/llm_metrics.py \
		"$(AZURE_URL)" \
		"$(PAYLOAD_FILE)" \
		--platform azure \
		--duration $(CLOUD_DURATION) \
		--concurrency $(CLOUD_CONCURRENCY) \
		--mode both
	@echo "✅ Azure benchmark complete! Results in results/azure/"

bench-gcp:
	@echo "🧪 Running GCP benchmark..."
	@echo "   URL: $(GCP_URL)"
	@echo "   Duration: $(CLOUD_DURATION)s, Concurrency: $(CLOUD_CONCURRENCY)"
	@echo "   Payload: $(PAYLOAD_FILE)"
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then \
		echo "❌ Payload file not found: $(PAYLOAD_FILE)"; \
		exit 1; \
	fi
	python3 scripts/llm_metrics.py \
		"$(GCP_URL)" \
		"$(PAYLOAD_FILE)" \
		--platform gcp \
		--duration $(CLOUD_DURATION) \
		--concurrency $(CLOUD_CONCURRENCY) \
		--mode both
	@echo "✅ GCP benchmark complete! Results in results/gcp/"

bench-custom:
	@echo "🧪 Running CUSTOM benchmark..."
	@echo "   URL: $(CUSTOM_URL)"
	@echo "   Duration: $(CLOUD_DURATION)s, Concurrency: $(CLOUD_CONCURRENCY)"
	@echo "   Payload: $(PAYLOAD_FILE)"
	@if [ ! -f "$(PAYLOAD_FILE)" ]; then \
		echo "❌ Payload file not found: $(PAYLOAD_FILE)"; \
		exit 1; \
	fi
	@if [ "$(CUSTOM_URL)" = "https://api.example.com/v1/chat/completions" ]; then \
		echo "⚠️  Please set CUSTOM_URL environment variable"; \
		echo "   Example: CUSTOM_URL=https://my-api.com/v1/chat make bench-custom"; \
		exit 1; \
	fi
	python3 scripts/llm_metrics.py \
		"$(CUSTOM_URL)" \
		"$(PAYLOAD_FILE)" \
		--platform custom \
		--duration $(CLOUD_DURATION) \
		--concurrency $(CLOUD_CONCURRENCY) \
		--mode both
	@echo "✅ Custom benchmark complete! Results in results/custom/"

# Run all platform benchmarks
bench-all:
	@echo "🚀 Running benchmarks for all platforms..."
	@echo "This will take several minutes to complete."
	@echo ""
	@$(MAKE) bench-local || echo "⚠️  Local benchmark failed (server may not be running)"
	@echo ""
	@$(MAKE) bench-aws || echo "⚠️  AWS benchmark failed (check endpoint configuration)"
	@echo ""
	@$(MAKE) bench-azure || echo "⚠️  Azure benchmark failed (check endpoint configuration)"
	@echo ""
	@$(MAKE) bench-gcp || echo "⚠️  GCP benchmark failed (check endpoint configuration)"
	@echo ""
	@echo "🎉 All platform benchmarks completed!"
	@echo "📊 Generating comprehensive report..."
	@$(MAKE) report
	@echo ""
	@echo "✅ Complete! Check results/comprehensive_report.md for the full analysis."

# Test setup and dependencies
test-setup:
	@echo "🔍 Testing benchmark setup..."
	@echo ""
	@echo "📋 Checking required files:"
	@if [ -f "$(PAYLOAD_FILE)" ]; then \
		echo "✅ Payload file found: $(PAYLOAD_FILE)"; \
	else \
		echo "❌ Payload file missing: $(PAYLOAD_FILE)"; \
	fi
	@if [ -f "scripts/llm_metrics.py" ]; then \
		echo "✅ Benchmark script found: scripts/llm_metrics.py"; \
	else \
		echo "❌ Benchmark script missing: scripts/llm_metrics.py"; \
	fi
	@echo ""
	@echo "📋 Testing Python dependencies:"
	@python3 -c "import httpx" 2>/dev/null && echo "✅ httpx available" || echo "❌ httpx missing (pip install httpx)"
	@python3 -c "import asyncio" 2>/dev/null && echo "✅ asyncio available" || echo "❌ asyncio missing"
	@python3 -c "import json" 2>/dev/null && echo "✅ json available" || echo "❌ json missing"
	@echo ""
	@echo "📋 Testing argument parsing:"
	@python3 -c "import sys; sys.path.append('scripts'); exec(open('scripts/llm_metrics.py').read().split('async def main')[0] + 'print(\"✅ Script syntax OK\")')" 2>/dev/null || echo "❌ Script syntax error"
	@echo ""
	@echo "📋 Current configuration:"
	@echo "   Payload file: $(PAYLOAD_FILE)"
	@echo "   Local URL: $(LOCAL_URL)"
	@echo "   AWS URL: $(AWS_URL)"
	@echo "   Azure URL: $(AZURE_URL)"
	@echo "   GCP URL: $(GCP_URL)"
	@echo ""
	@echo "🏁 Setup test complete!"
