#!/usr/bin/env python3
"""
Enhanced Report Generator with Visual Insights
Creates charts and visualizations for the performance data
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
import os
from pathlib import Path

def load_comprehensive_data(results_dir):
    """Load the comprehensive CSV data"""
    csv_file = os.path.join(results_dir, 'comprehensive_report.csv')
    if not os.path.exists(csv_file):
        print("❌ Please run the comprehensive report first: python3 scripts/comprehensive_report.py")
        return None
    
    df = pd.read_csv(csv_file)
    return df

def create_performance_charts(df, output_dir):
    """Create performance comparison charts"""
    plt.style.use('seaborn-v0_8')
    
    # Set up the plotting style
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('LLM Inference Performance Comparison', fontsize=16, fontweight='bold')
    
    # 1. Throughput Comparison
    ax1 = axes[0, 0]
    throughput_data = df[df['Aggregate TPS'].notna()]
    sns.barplot(data=throughput_data, x='Platform', y='Aggregate TPS', hue='Mode', ax=ax1)
    ax1.set_title('Aggregate Throughput (Tokens/sec)')
    ax1.set_ylabel('Tokens per Second')
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Latency Comparison
    ax2 = axes[0, 1]
    latency_data = df[df['Avg Latency (ms)'].notna()]
    sns.barplot(data=latency_data, x='Platform', y='Avg Latency (ms)', hue='Mode', ax=ax2)
    ax2.set_title('Average Latency')
    ax2.set_ylabel('Milliseconds')
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. TTFT Comparison (Streaming only)
    ax3 = axes[1, 0]
    ttft_data = df[(df['Mode'] == 'streaming') & (df['Avg TTFT (ms)'].notna())]
    if not ttft_data.empty:
        sns.barplot(data=ttft_data, x='Platform', y='Avg TTFT (ms)', ax=ax3, color='skyblue')
        ax3.set_title('Time to First Token (Streaming Mode)')
        ax3.set_ylabel('Milliseconds')
        ax3.tick_params(axis='x', rotation=45)
    else:
        ax3.text(0.5, 0.5, 'No TTFT data available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Time to First Token (Streaming Mode)')
    
    # 4. Cost vs Performance
    ax4 = axes[1, 1]
    cost_mapping = {'LOCAL': 0.0045, 'AWS': 1.515, 'AZURE': 3.40, 'GCP': 0.88}
    
    # Calculate performance per dollar (tokens per dollar per hour)
    perf_cost_data = []
    for platform in df['Platform'].unique():
        platform_data = df[df['Platform'] == platform]
        max_throughput_tps = platform_data['Aggregate TPS'].max()
        cost_per_hour = cost_mapping.get(platform.upper(), 0)
        if max_throughput_tps and cost_per_hour > 0:
            # Convert TPS to tokens per hour, then divide by cost per hour
            tokens_per_hour = max_throughput_tps * 3600
            perf_per_dollar = tokens_per_hour / cost_per_hour
            perf_cost_data.append({'Platform': platform, 'Performance per Dollar': perf_per_dollar})
    
    if perf_cost_data:
        perf_df = pd.DataFrame(perf_cost_data)
        sns.barplot(data=perf_df, x='Platform', y='Performance per Dollar', ax=ax4, color='lightgreen')
        ax4.set_title('Cost Efficiency (Tokens/sec per $)')
        ax4.set_ylabel('Tokens/sec per Dollar/hour')
        ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save the chart
    chart_file = os.path.join(output_dir, 'performance_charts.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"📊 Performance charts saved: {chart_file}")
    
    plt.close()

def calculate_cost_per_million_tokens(df, output_dir):
    """Calculate and display cost per 1M tokens"""
    cost_mapping = {'LOCAL': 0.0045, 'AWS': 1.515, 'AZURE': 3.40, 'GCP': 0.88}
    
    cost_data = []
    for platform in df['Platform'].unique():
        platform_data = df[df['Platform'] == platform]
        max_throughput_tps = platform_data['Aggregate TPS'].max()
        cost_per_hour = cost_mapping.get(platform.upper(), 0)
        
        if max_throughput_tps and cost_per_hour > 0:
            # Calculate cost per 1M tokens
            tokens_per_hour = max_throughput_tps * 3600
            cost_per_million_tokens = (cost_per_hour / tokens_per_hour) * 1_000_000
            
            cost_data.append({
                'Platform': platform,
                'Cost per 1M Tokens': cost_per_million_tokens,
                'Hourly Cost': cost_per_hour,
                'TPS': max_throughput_tps
            })
    
    if cost_data:
        # Print cost per 1M tokens summary
        print(f"\n💰 Cost per 1M Tokens Analysis:")
        print(f"{'Platform':<8} {'TPS':<8} {'$/Hour':<10} {'$/1M Tokens':<12} {'vs OpenAI GPT-4':<15}")
        print("=" * 70)
        
        openai_cost = 30.0  # GPT-4 reference cost
        for data in sorted(cost_data, key=lambda x: x['Cost per 1M Tokens']):
            cost_ratio = data['Cost per 1M Tokens'] / openai_cost
            comparison = f"{cost_ratio:.1f}x" if cost_ratio >= 1 else f"{1/cost_ratio:.1f}x cheaper"
            
            print(f"{data['Platform']:<8} {data['TPS']:<8.1f} ${data['Hourly Cost']:<9.4f} "
                  f"${data['Cost per 1M Tokens']:<11.4f} {comparison:<15}")
        
        # Save detailed cost analysis to file
        cost_file = os.path.join(output_dir, 'cost_per_million_tokens.txt')
        with open(cost_file, 'w') as f:
            f.write("Cost per 1M Tokens Analysis\n")
            f.write("=" * 40 + "\n\n")
            for data in sorted(cost_data, key=lambda x: x['Cost per 1M Tokens']):
                f.write(f"Platform: {data['Platform']}\n")
                f.write(f"  Throughput: {data['TPS']:.1f} TPS\n")
                f.write(f"  Hourly Cost: ${data['Hourly Cost']:.4f}\n")
                f.write(f"  Cost per 1M Tokens: ${data['Cost per 1M Tokens']:.4f}\n")
                f.write(f"  Tokens per Hour: {data['TPS'] * 3600:,.0f}\n\n")
        
        print(f"💾 Cost analysis saved: {cost_file}")

def create_summary_chart(df, output_dir):
    """Create a summary radar/spider chart"""
    try:
        from math import pi
        
        # Prepare data for radar chart
        platforms = df['Platform'].unique()
        metrics = ['Throughput', 'Latency', 'Cost Efficiency']
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Normalize metrics for radar chart (0-1 scale)
        normalized_data = {}
        cost_mapping = {'LOCAL': 0.0045, 'AWS': 1.515, 'AZURE': 3.40, 'GCP': 0.88}
        
        for platform in platforms:
            platform_data = df[df['Platform'] == platform]
            max_throughput_tps = platform_data['Aggregate TPS'].max() or 0
            min_latency = platform_data['Avg Latency (ms)'].min() or float('inf')
            cost_per_hour = cost_mapping.get(platform.upper(), 1)
            
            # Normalize (higher is better for all)
            norm_throughput = max_throughput_tps / 1000  # Scale down
            norm_latency = 1 / (min_latency / 1000) if min_latency != float('inf') else 0  # Inverse latency
            # Fix cost efficiency calculation: convert TPS to tokens/hour then divide by cost/hour
            tokens_per_hour = max_throughput_tps * 3600
            cost_efficiency = tokens_per_hour / cost_per_hour if cost_per_hour > 0 else 0
            norm_cost_eff = cost_efficiency / 10000  # Scale down for visualization
            
            normalized_data[platform] = [norm_throughput, norm_latency, norm_cost_eff]
        
        # Set up the radar chart
        angles = [n / len(metrics) * 2 * pi for n in range(len(metrics))]
        angles += angles[:1]  # Complete the circle
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i, (platform, values) in enumerate(normalized_data.items()):
            values += values[:1]  # Complete the circle
            ax.plot(angles, values, 'o-', linewidth=2, label=platform.upper(), color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
        
        # Customize the chart
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 1)
        ax.set_title('Platform Performance Overview\n(Normalized Metrics)', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)
        
        # Save the radar chart
        radar_file = os.path.join(output_dir, 'performance_radar.png')
        plt.savefig(radar_file, dpi=300, bbox_inches='tight')
        print(f"📊 Radar chart saved: {radar_file}")
        
        plt.close()
        
    except ImportError:
        print("⚠️  Skipping radar chart (requires matplotlib with polar projection)")

def generate_enhanced_report(results_dir):
    """Generate enhanced report with visualizations"""
    print("📊 Generating enhanced performance report...")
    
    # Load data
    df = load_comprehensive_data(results_dir)
    if df is None:
        return
    
    print(f"📈 Loaded data for {len(df)} test configurations")
    
    # Create output directory for charts
    charts_dir = os.path.join(results_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    try:
        # Create charts
        create_performance_charts(df, charts_dir)
        create_summary_chart(df, charts_dir)
        
        # Calculate cost per 1M tokens
        calculate_cost_per_million_tokens(df, charts_dir)
        
        # Update the markdown report to include charts
        update_markdown_with_charts(results_dir, charts_dir)
        
        print("✅ Enhanced report generated successfully!")
        print(f"📊 Charts available in: {charts_dir}")
        
    except ImportError as e:
        print(f"⚠️  Could not generate charts: {e}")
        print("To enable charts, install required packages: pip install matplotlib seaborn pandas")

def update_markdown_with_charts(results_dir, charts_dir):
    """Update the markdown report to include chart references"""
    report_file = os.path.join(results_dir, 'comprehensive_report.md')
    
    if not os.path.exists(report_file):
        return
    
    # Read the current report
    with open(report_file, 'r') as f:
        content = f.read()
    
    # Add charts section after the executive summary
    charts_section = """
## 📈 Performance Visualizations

### Performance Comparison Charts
![Performance Charts](charts/performance_charts.png)

### Platform Overview (Normalized Metrics)
![Performance Radar](charts/performance_radar.png)

*Charts show comparative performance across all platforms. Higher values are better for all metrics.*

"""
    
    # Insert after executive summary
    updated_content = content.replace(
        "## 📊 Detailed Performance Metrics",
        f"{charts_section}## 📊 Detailed Performance Metrics"
    )
    
    # Write updated report
    with open(report_file, 'w') as f:
        f.write(updated_content)
    
    print(f"📝 Updated markdown report with chart references")

if __name__ == "__main__":
    import sys
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    generate_enhanced_report(results_dir)
