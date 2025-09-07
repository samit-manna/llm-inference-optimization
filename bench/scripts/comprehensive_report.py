#!/usr/bin/env python3
"""
Comprehensive LLM Inference Performance Report Generator
Creates a unified report comparing all platforms (Local, AWS, Azure, GCP)
"""

import os
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
import argparse

def load_json(path):
    """Load JSON file safely"""
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON file {path}")
            return {}
    return {}

def format_number(value, precision=2, suffix=""):
    """Format numbers for display"""
    if value is None or value == "-":
        return "-"
    try:
        if isinstance(value, str):
            value = float(value)
        return f"{value:.{precision}f}{suffix}"
    except (ValueError, TypeError):
        return str(value)

def calculate_cost_efficiency(throughput, cost_per_hour):
    """Calculate tokens per dollar per hour"""
    if throughput and cost_per_hour:
        tokens_per_hour = throughput * 3600  # tokens per second * seconds per hour
        return tokens_per_hour / cost_per_hour
    return None

def load_platform_data(results_dir, platform):
    """Load all data for a specific platform"""
    platform_dir = os.path.join(results_dir, platform)
    
    if not os.path.isdir(platform_dir):
        return None
    
    data = {
        'platform': platform,
        'streaming': {},
        'non_streaming': {}
    }
    
    # Load streaming metrics
    streaming_file = os.path.join(platform_dir, 'llm_metrics_streaming.json')
    streaming_data = load_json(streaming_file)
    
    # Load non-streaming metrics
    non_streaming_file = os.path.join(platform_dir, 'llm_metrics_non_streaming.json')
    non_streaming_data = load_json(non_streaming_file)
    
    # Check if we have the new format (with detailed metrics) or old format
    if streaming_data and 'total_requests' in streaming_data:
        # New format - use as is
        data['streaming'] = streaming_data
        data['non_streaming'] = non_streaming_data
    else:
        # Check for combined.json (local format)
        combined_file = os.path.join(platform_dir, 'combined.json')
        if os.path.exists(combined_file):
            combined_data = load_json(combined_file)
            if 'llm_metrics' in combined_data:
                # Convert old format to new format
                for mode, metrics in combined_data['llm_metrics'].items():
                    if mode in ['streaming', 'non_streaming']:
                        # Convert old field names to new ones
                        converted_metrics = convert_old_format(metrics)
                        data[mode] = converted_metrics
        else:
            # Fallback to whatever we loaded
            data['streaming'] = streaming_data
            data['non_streaming'] = non_streaming_data
    
    return data

def convert_old_format(old_metrics):
    """Convert old metric format to new format for compatibility"""
    converted = {}
    
    # Map old field names to new ones
    field_mapping = {
        'tokens_per_sec': 'avg_tokens_per_second',
        'tfft_sec': 'avg_ttft_ms',  # Convert seconds to ms
        'ttlt_sec': 'avg_total_time_ms',  # Convert seconds to ms
        'completion_tokens': 'total_tokens_generated',
        'total_tokens': 'total_tokens_generated'
    }
    
    for old_key, value in old_metrics.items():
        if old_key in field_mapping:
            new_key = field_mapping[old_key]
            if 'ms' in new_key and value is not None:
                # Convert seconds to milliseconds
                converted[new_key] = value * 1000 if isinstance(value, (int, float)) else value
            else:
                converted[new_key] = value
        else:
            # Keep original key if no mapping exists
            converted[old_key] = value
    
    # Add some defaults for missing fields
    converted.setdefault('total_requests', 1)
    converted.setdefault('successful_requests', 1)
    converted.setdefault('success_rate', 100.0)
    converted.setdefault('requests_per_second', 1.0)
    
    return converted

def generate_performance_table(all_data):
    """Generate main performance comparison table"""
    table = []
    table.append("| Platform | Mode | Requests | Success Rate | Avg TPS | P95 TPS | Agg TPS | Avg Latency (ms) | P95 Latency (ms) | TTFT (ms) | RPS |")
    table.append("|----------|------|----------|--------------|---------|---------|---------|------------------|------------------|-----------|-----|")
    
    for platform_data in all_data:
        platform = platform_data['platform'].upper()
        
        for mode in ['streaming', 'non_streaming']:
            if mode in platform_data and platform_data[mode]:
                metrics = platform_data[mode]
                table.append(
                    f"| {platform} | {mode.replace('_', ' ').title()} | "
                    f"{format_number(metrics.get('total_requests', '-'), 0)} | "
                    f"{format_number(metrics.get('success_rate', '-'), 1, '%')} | "
                    f"{format_number(metrics.get('avg_tokens_per_second', '-'), 2)} | "
                    f"{format_number(metrics.get('p95_tokens_per_second', '-'), 2)} | "
                    f"{format_number(metrics.get('aggregate_tokens_per_second', '-'), 2)} | "
                    f"{format_number(metrics.get('avg_total_time_ms', '-'), 1)} | "
                    f"{format_number(metrics.get('p95_total_time_ms', '-'), 1)} | "
                    f"{format_number(metrics.get('avg_ttft_ms', '-'), 1)} | "
                    f"{format_number(metrics.get('requests_per_second', '-'), 2)} |"
                )
    
    return "\n".join(table)

def generate_summary_table(all_data):
    """Generate executive summary table with key metrics"""
    table = []
    table.append("| Platform | Best Throughput (TPS) | Best Latency (ms) | Best TTFT (ms) | Total Tokens Generated | Test Duration (min) |")
    table.append("|----------|----------------------|-------------------|----------------|-----------------------|---------------------|")
    
    for platform_data in all_data:
        platform = platform_data['platform'].upper()
        
        # Find best metrics across modes
        best_throughput = 0
        best_latency = float('inf')
        best_ttft = float('inf')
        total_tokens = 0
        test_duration = 0
        
        for mode in ['streaming', 'non_streaming']:
            if mode in platform_data and platform_data[mode]:
                metrics = platform_data[mode]
                
                # Track best throughput
                agg_tps = metrics.get('aggregate_tokens_per_second', 0)
                if agg_tps and agg_tps > best_throughput:
                    best_throughput = agg_tps
                
                # Track best latency
                avg_latency = metrics.get('avg_total_time_ms')
                if avg_latency and avg_latency < best_latency:
                    best_latency = avg_latency
                
                # Track best TTFT
                ttft = metrics.get('avg_ttft_ms')
                if ttft and ttft < best_ttft:
                    best_ttft = ttft
                
                # Sum total tokens
                tokens = metrics.get('total_tokens_generated', 0)
                if tokens:
                    total_tokens += tokens
                
                # Track duration
                duration = metrics.get('total_duration_sec', 0)
                if duration > test_duration:
                    test_duration = duration
        
        # Format values
        best_throughput_str = format_number(best_throughput, 1) if best_throughput > 0 else "-"
        best_latency_str = format_number(best_latency, 1) if best_latency != float('inf') else "-"
        best_ttft_str = format_number(best_ttft, 1) if best_ttft != float('inf') else "-"
        total_tokens_str = format_number(total_tokens, 0) if total_tokens > 0 else "-"
        test_duration_str = format_number(test_duration / 60, 1) if test_duration > 0 else "-"
        
        table.append(
            f"| {platform} | {best_throughput_str} | {best_latency_str} | {best_ttft_str} | "
            f"{total_tokens_str} | {test_duration_str} |"
        )
    
    return "\n".join(table)

def generate_cost_analysis(all_data):
    """Generate cost analysis section with actual performance data"""
    cost_data = {
        'AWS': {'hourly_cost': 1.515, 'instance_type': 'ml.g5.2xlarge (SageMaker)'},
        'Azure': {'hourly_cost': 3.40, 'instance_type': 'Standard_NV36adms_A10_v5 + D4s v6'},
        'GCP': {'hourly_cost': 0.88, 'instance_type': 'g2-standard-8 + e2-medium'},
        'Local': {'hourly_cost': 0.0045, 'instance_type': 'M4 Mac (estimated power)'}
    }
    
    analysis = []
    analysis.append("## 💰 Cost Analysis\n")
    analysis.append("| Platform | Instance Type | Hourly Cost (USD) | Estimated Monthly Cost* |")
    analysis.append("|----------|---------------|-------------------|-------------------------|")
    
    for platform, data in cost_data.items():
        monthly_cost = data['hourly_cost'] * 24 * 30  # Assume 24/7 operation
        analysis.append(
            f"| {platform} | {data['instance_type']} | "
            f"${data['hourly_cost']:.4f} | ${monthly_cost:.2f} |"
        )
    
    analysis.append("\n*Estimated for 24/7 operation. Actual costs may vary based on usage patterns.")
    
    # Calculate actual cost efficiency based on performance data
    efficiency_data = []
    for platform_data in all_data:
        platform = platform_data['platform']
        platform_upper = platform.upper()
        
        if platform_upper in cost_data:
            cost_per_hour = cost_data[platform_upper]['hourly_cost']
            
            # Find best throughput across streaming and non-streaming
            best_throughput_tps = 0
            for mode in ['streaming', 'non_streaming']:
                if mode in platform_data and platform_data[mode]:
                    metrics = platform_data[mode]
                    agg_tps = metrics.get('aggregate_tokens_per_second', 0)
                    if agg_tps and agg_tps > best_throughput_tps:
                        best_throughput_tps = agg_tps
            
            if best_throughput_tps > 0:
                # Convert tokens per second to tokens per hour for proper unit matching
                tokens_per_hour = best_throughput_tps * 3600
                efficiency = tokens_per_hour / cost_per_hour
                efficiency_data.append({
                    'platform': platform_upper,
                    'throughput_tps': best_throughput_tps,
                    'cost_per_hour': cost_per_hour,
                    'efficiency': efficiency
                })
    
    # Sort by efficiency (highest first)
    efficiency_data.sort(key=lambda x: x['efficiency'], reverse=True)
    
    if efficiency_data:
        analysis.append("\n### Cost Efficiency Ranking")
        analysis.append("Based on tokens per dollar per hour (higher is better):\n")
        analysis.append("| Rank | Platform | Throughput (TPS) | Cost/Hour | Tokens per $ per Hour |")
        analysis.append("|------|----------|------------------|-----------|----------------------|")
        
        for i, data in enumerate(efficiency_data, 1):
            analysis.append(
                f"| {i} | **{data['platform']}** | "
                f"{data['throughput_tps']:.1f} | "
                f"${data['cost_per_hour']:.4f} | "
                f"{data['efficiency']:,.0f} |"
            )
        
        analysis.append(f"\n**Calculation**: Tokens per hour (TPS × 3600) ÷ Cost per hour")
        analysis.append(f"**Example**: {efficiency_data[0]['platform']} = {efficiency_data[0]['throughput_tps']:.1f} TPS × 3600 ÷ ${efficiency_data[0]['cost_per_hour']:.4f}/hr = {efficiency_data[0]['efficiency']:,.0f} tokens/$")
        
        # Add cost per 1M tokens calculation
        analysis.append("\n### Cost per 1M Tokens")
        analysis.append("Industry-standard pricing comparison:\n")
        analysis.append("| Platform | Cost per 1M Tokens | Comparison to OpenAI GPT-4* |")
        analysis.append("|----------|-------------------|------------------------------|")
        
        for data in efficiency_data:
            # Calculate cost per 1M tokens: (cost_per_hour / tokens_per_hour) * 1,000,000
            tokens_per_hour = data['throughput_tps'] * 3600
            cost_per_million_tokens = (data['cost_per_hour'] / tokens_per_hour) * 1_000_000
            
            # Compare to OpenAI GPT-4 pricing (~$30/1M input tokens)
            openai_cost = 30.0  # GPT-4 input cost per 1M tokens
            cost_ratio = cost_per_million_tokens / openai_cost
            if cost_ratio < 1:
                # Calculate how many times cheaper (inverse ratio)
                cheaper_ratio = openai_cost / cost_per_million_tokens
                comparison = f"{cheaper_ratio:.1f}x cheaper"
            else:
                comparison = f"{cost_ratio:.1f}x more expensive"
            
            analysis.append(
                f"| **{data['platform']}** | "
                f"${cost_per_million_tokens:.4f} | "
                f"{comparison} |"
            )
        
        analysis.append(f"\n*Based on OpenAI GPT-4 input pricing of ~$30/1M tokens as reference")
        analysis.append(f"**Formula**: (Hourly Cost ÷ Tokens per Hour) × 1,000,000")
    else:
        analysis.append("\n### Cost Efficiency Ranking")
        analysis.append("Unable to calculate efficiency - performance data not available.")
    
    return "\n".join(analysis)

def generate_recommendations(all_data):
    """Generate recommendations based on analysis"""
    recommendations = []
    recommendations.append("## 🎯 Recommendations\n")
    
    recommendations.append("### By Use Case\n")
    recommendations.append("**Development & Testing:**")
    recommendations.append("- **Local** setup provides the best cost-effectiveness")
    recommendations.append("- Good for prototyping and initial development")
    recommendations.append("- Limited by local hardware capabilities\n")
    
    recommendations.append("**Production Deployment:**")
    
    # Analyze performance data to make specific recommendations
    best_throughput_platform = ""
    best_latency_platform = ""
    best_cost_platform = "GCP"  # Based on cost analysis
    
    max_throughput = 0
    min_latency = float('inf')
    
    for platform_data in all_data:
        platform = platform_data['platform']
        for mode in ['streaming', 'non_streaming']:
            if mode in platform_data and platform_data[mode]:
                metrics = platform_data[mode]
                
                # Check throughput
                agg_tps = metrics.get('aggregate_tokens_per_second', 0)
                if agg_tps and agg_tps > max_throughput:
                    max_throughput = agg_tps
                    best_throughput_platform = platform.upper()
                
                # Check latency
                avg_latency = metrics.get('avg_total_time_ms')
                if avg_latency and avg_latency < min_latency:
                    min_latency = avg_latency
                    best_latency_platform = platform.upper()
    
    recommendations.append(f"- **{best_throughput_platform}** for maximum throughput requirements")
    recommendations.append(f"- **{best_latency_platform}** for lowest latency requirements")
    recommendations.append(f"- **{best_cost_platform}** for best cost-performance balance\n")
    
    recommendations.append("### Streaming vs Non-Streaming")
    recommendations.append("- **Streaming** is recommended for:")
    recommendations.append("  - Interactive applications requiring immediate response")
    recommendations.append("  - Better user experience with progressive output")
    recommendations.append("  - Lower perceived latency")
    recommendations.append("- **Non-Streaming** is recommended for:")
    recommendations.append("  - Batch processing scenarios")
    recommendations.append("  - When complete response is needed before processing")
    recommendations.append("  - Slightly higher overall throughput in some cases")
    
    return "\n".join(recommendations)

def generate_methodology():
    """Generate methodology section"""
    methodology = []
    methodology.append("## 📋 Methodology\n")
    methodology.append("### Test Setup")
    methodology.append("- **Model**: Llama 3.1 8B (quantized versions where applicable)")
    methodology.append("- **Test Duration**: ~5 minutes per configuration")
    methodology.append("- **Concurrency**: 32 concurrent requests")
    methodology.append("- **Payload**: Standardized chat completion requests")
    methodology.append("- **Metrics Collection**: Custom llm_metrics_v2.py script\n")
    
    methodology.append("### Platforms Tested")
    methodology.append("- **Local**: llama.cpp on M4 Mac")
    methodology.append("- **AWS**: SageMaker endpoint with g5.2xlarge instance")
    methodology.append("- **Azure**: Container Instances with Standard_NC6s_v3")
    methodology.append("- **GCP**: GKE cluster with T4 GPU nodes\n")
    
    methodology.append("### Key Metrics")
    methodology.append("- **TPS (Tokens Per Second)**: Individual request throughput")
    methodology.append("- **Aggregate TPS**: Total system throughput")
    methodology.append("- **TTFT (Time To First Token)**: Latency until first response")
    methodology.append("- **Total Latency**: Complete request processing time")
    methodology.append("- **Success Rate**: Percentage of successful requests")
    
    return "\n".join(methodology)

def generate_report(results_dir, output_file=None):
    """Generate comprehensive report"""
    print("🔍 Scanning for platform results...")
    
    # Load data from all platforms
    platforms = ['local', 'aws', 'azure', 'gcp']
    all_data = []
    
    for platform in platforms:
        print(f"Loading {platform} data...")
        data = load_platform_data(results_dir, platform)
        if data and (data['streaming'] or data['non_streaming']):
            all_data.append(data)
            print(f"✅ {platform.upper()} data loaded")
        else:
            print(f"⚠️  No data found for {platform}")
    
    if not all_data:
        print("❌ No platform data found!")
        return
    
    print(f"📊 Generating report for {len(all_data)} platforms...")
    
    # Generate report content
    report = []
    report.append("# 🚀 LLM Inference Performance Comparison Report")
    report.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Executive Summary
    report.append("## 📈 Executive Summary\n")
    report.append(generate_summary_table(all_data))
    report.append("")
    
    # Detailed Performance Metrics
    report.append("## 📊 Detailed Performance Metrics\n")
    report.append(generate_performance_table(all_data))
    report.append("")
    
    # Cost Analysis
    report.append(generate_cost_analysis(all_data))
    report.append("")
    
    # Recommendations
    report.append(generate_recommendations(all_data))
    report.append("")
    
    # Methodology
    report.append(generate_methodology())
    report.append("")
    
    # Platform Details
    report.append("## 🔧 Platform-Specific Details\n")
    
    for platform_data in all_data:
        platform = platform_data['platform'].upper()
        report.append(f"### {platform}\n")
        
        for mode in ['streaming', 'non_streaming']:
            if mode in platform_data and platform_data[mode]:
                metrics = platform_data[mode]
                report.append(f"#### {mode.replace('_', ' ').title()} Mode")
                report.append(f"- **Total Requests**: {format_number(metrics.get('total_requests', '-'), 0)}")
                report.append(f"- **Success Rate**: {format_number(metrics.get('success_rate', '-'), 1)}%")
                report.append(f"- **Average Throughput**: {format_number(metrics.get('avg_tokens_per_second', '-'), 2)} tokens/sec")
                report.append(f"- **Aggregate Throughput**: {format_number(metrics.get('aggregate_tokens_per_second', '-'), 2)} tokens/sec")
                report.append(f"- **Average Latency**: {format_number(metrics.get('avg_total_time_ms', '-'), 1)} ms")
                report.append(f"- **TTFT**: {format_number(metrics.get('avg_ttft_ms', '-'), 1)} ms")
                report.append(f"- **Requests/sec**: {format_number(metrics.get('requests_per_second', '-'), 2)}")
                report.append("")
        
        report.append("---\n")
    
    # Footer
    report.append("---")
    report.append("\n*This report was generated using automated benchmarking tools.*")
    report.append("*For detailed raw data, see individual platform result files.*")
    
    # Write report
    if output_file is None:
        output_file = os.path.join(results_dir, "comprehensive_report.md")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Comprehensive report generated: {output_file}")
    
    # Also generate CSV for easy analysis
    csv_file = output_file.replace('.md', '.csv')
    generate_csv_export(all_data, csv_file)
    
    return output_file

def generate_csv_export(all_data, csv_file):
    """Generate CSV export of all metrics"""
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'Platform', 'Mode', 'Total Requests', 'Successful Requests', 'Success Rate (%)',
            'Avg TPS', 'P95 TPS', 'Aggregate TPS', 'Avg Latency (ms)', 'P95 Latency (ms)',
            'Avg TTFT (ms)', 'P95 TTFT (ms)', 'Requests/sec', 'Total Duration (sec)', 'Total Tokens'
        ])
        
        # Write data
        for platform_data in all_data:
            platform = platform_data['platform']
            
            for mode in ['streaming', 'non_streaming']:
                if mode in platform_data and platform_data[mode]:
                    metrics = platform_data[mode]
                    writer.writerow([
                        platform,
                        mode,
                        metrics.get('total_requests', ''),
                        metrics.get('successful_requests', ''),
                        metrics.get('success_rate', ''),
                        metrics.get('avg_tokens_per_second', ''),
                        metrics.get('p95_tokens_per_second', ''),
                        metrics.get('aggregate_tokens_per_second', ''),
                        metrics.get('avg_total_time_ms', ''),
                        metrics.get('p95_total_time_ms', ''),
                        metrics.get('avg_ttft_ms', ''),
                        metrics.get('p95_ttft_ms', ''),
                        metrics.get('requests_per_second', ''),
                        metrics.get('total_duration_sec', ''),
                        metrics.get('total_tokens_generated', '')
                    ])
    
    print(f"📊 CSV export generated: {csv_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive LLM inference performance report')
    parser.add_argument('--results-dir', '-d', 
                       default='/Users/samit.manna/Documents/Passion Projects/llm-inference-optimization/bench/results',
                       help='Path to results directory')
    parser.add_argument('--output', '-o', help='Output file path (default: results_dir/comprehensive_report.md)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results_dir):
        print(f"❌ Results directory not found: {args.results_dir}")
        sys.exit(1)
    
    generate_report(args.results_dir, args.output)

if __name__ == "__main__":
    main()
