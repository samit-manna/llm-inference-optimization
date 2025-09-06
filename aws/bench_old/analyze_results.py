#!/usr/bin/env python3
"""
AWS Benchmark Results Analyzer

Processes raw OHA JSON output files and generates summary reports.

Usage:
    python3 analyze_results.py /path/to/results/directory
    python3 analyze_results.py --input /path/to/results --output summary.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re


def load_oha_result(file_path: Path) -> Optional[Dict]:
    """Load and parse OHA JSON result file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None


def extract_concurrency(filename: str) -> Optional[int]:
    """Extract concurrency level from filename (e.g., 'c24.json' -> 24)."""
    match = re.search(r'c(\d+)', filename)
    return int(match.group(1)) if match else None


def analyze_results_directory(results_dir: Path) -> Dict:
    """Analyze all OHA result files in a directory."""
    results = []
    
    # Find all JSON files that look like OHA results
    json_files = list(results_dir.glob("*.json"))
    oha_files = [f for f in json_files if f.name.startswith('c') and f.name.endswith('.json')]
    
    for file_path in sorted(oha_files):
        concurrency = extract_concurrency(file_path.name)
        if concurrency is None:
            continue
            
        data = load_oha_result(file_path)
        if data is None:
            continue
            
        try:
            summary = data.get('summary', {})
            results.append({
                'concurrency': concurrency,
                'file': file_path.name,
                'rps': summary.get('requestsPerSec', 0),
                'total_requests': summary.get('totalRequests', 0),
                'successful_requests': summary.get('successfulRequests', 0),
                'mean_latency_ms': summary.get('meanResponseTime', 0) * 1000,
                'p50_latency_ms': summary.get('responseTimePercentiles', {}).get('p50', 0) * 1000,
                'p95_latency_ms': summary.get('responseTimePercentiles', {}).get('p95', 0) * 1000,
                'p99_latency_ms': summary.get('responseTimePercentiles', {}).get('p99', 0) * 1000,
                'min_latency_ms': summary.get('minResponseTime', 0) * 1000,
                'max_latency_ms': summary.get('maxResponseTime', 0) * 1000,
                'test_duration_s': summary.get('totalTime', 0),
                'raw_data': data
            })
        except Exception as e:
            print(f"Warning: Error processing {file_path}: {e}")
    
    # Sort by concurrency
    results.sort(key=lambda x: x['concurrency'])
    
    return {
        'results': results,
        'summary_stats': calculate_summary_stats(results)
    }


def calculate_summary_stats(results: List[Dict]) -> Dict:
    """Calculate summary statistics across all test runs."""
    if not results:
        return {}
    
    max_tokens = 64  # Default assumption
    
    return {
        'total_test_runs': len(results),
        'concurrency_range': {
            'min': min(r['concurrency'] for r in results),
            'max': max(r['concurrency'] for r in results)
        },
        'peak_performance': {
            'max_rps': max(r['rps'] for r in results),
            'max_tokens_per_sec': max(r['rps'] * max_tokens for r in results),
            'best_concurrency': max(results, key=lambda x: x['rps'])['concurrency']
        },
        'latency_analysis': {
            'lowest_p95_ms': min(r['p95_latency_ms'] for r in results),
            'highest_p95_ms': max(r['p95_latency_ms'] for r in results),
            'slo_compliant_runs': len([r for r in results if r['p95_latency_ms'] < 2000])
        }
    }


def generate_markdown_report(analysis: Dict, output_file: Optional[Path] = None) -> str:
    """Generate a markdown report from analysis results."""
    results = analysis['results']
    summary = analysis['summary_stats']
    
    if not results:
        return "# No results found\n"
    
    # Estimate tokens per second (assuming 64 tokens per request by default)
    max_tokens = 64
    
    report = [
        "# AWS Benchmark Results Analysis",
        "",
        f"**Analysis Date**: {Path.cwd()}",  # Could be improved with actual timestamp
        f"**Test Runs**: {summary['total_test_runs']}",
        f"**Concurrency Range**: C={summary['concurrency_range']['min']} to C={summary['concurrency_range']['max']}",
        "",
        "## Performance Summary",
        "",
        f"- **Peak RPS**: {summary['peak_performance']['max_rps']:.2f} at C={summary['peak_performance']['best_concurrency']}",
        f"- **Peak Tokens/Second**: ~{summary['peak_performance']['max_tokens_per_sec']:.0f}",
        f"- **P95 Latency Range**: {summary['latency_analysis']['lowest_p95_ms']:.0f}ms - {summary['latency_analysis']['highest_p95_ms']:.0f}ms", 
        f"- **SLO Compliance**: {summary['latency_analysis']['slo_compliant_runs']}/{summary['total_test_runs']} runs under 2s P95",
        "",
        "## Detailed Results",
        "",
        "| Concurrency | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Success Rate | Est. Tokens/s |",
        "|-------------|-----|----------|----------|----------|--------------|---------------|"
    ]
    
    for result in results:
        success_rate = result['successful_requests'] / max(result['total_requests'], 1)
        est_tokens_per_sec = result['rps'] * max_tokens
        
        report.append(
            f"| C={result['concurrency']:<2} | "
            f"{result['rps']:>6.2f} | "
            f"{result['p50_latency_ms']:>7.0f} | "
            f"{result['p95_latency_ms']:>7.0f} | "
            f"{result['p99_latency_ms']:>7.0f} | "
            f"{success_rate:>9.1%} | "
            f"{est_tokens_per_sec:>12.0f} |"
        )
    
    # Add recommendations
    report.extend([
        "",
        "## Recommendations",
        "",
        _generate_recommendations(results, summary),
        "",
        "## Raw Data Files",
        ""
    ])
    
    for result in results:
        report.append(f"- `{result['file']}`: C={result['concurrency']} concurrency test")
    
    report.append("")  # Final newline
    
    markdown_content = "\n".join(report)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        print(f"Report saved to: {output_file}")
    
    return markdown_content


def _generate_recommendations(results: List[Dict], summary: Dict) -> str:
    """Generate performance recommendations based on results."""
    recommendations = []
    
    # Find sweet spot
    best_result = max(results, key=lambda x: x['rps'])
    
    recommendations.append(f"### Optimal Configuration")
    recommendations.append(f"- **Best throughput**: C={best_result['concurrency']} achieving {best_result['rps']:.2f} RPS")
    
    # SLO analysis
    compliant_results = [r for r in results if r['p95_latency_ms'] < 2000]
    if compliant_results:
        best_compliant = max(compliant_results, key=lambda x: x['rps'])
        recommendations.append(f"- **Best SLO-compliant**: C={best_compliant['concurrency']} with {best_compliant['rps']:.2f} RPS and {best_compliant['p95_latency_ms']:.0f}ms P95")
    
    # Scaling analysis
    if len(results) >= 2:
        low_conc = results[0]
        high_conc = results[-1]
        scaling_factor = high_conc['rps'] / low_conc['rps']
        recommendations.append(f"- **Scaling efficiency**: {scaling_factor:.1f}x RPS improvement from C={low_conc['concurrency']} to C={high_conc['concurrency']}")
    
    recommendations.append("")
    recommendations.append("### Autoscaling Recommendations")
    
    if compliant_results:
        best_compliant_tokens = max(compliant_results, key=lambda x: x['rps'])['rps'] * 64
        recommendations.append(f"- **Token target**: Set autoscaling target to ~{best_compliant_tokens * 60:.0f} tokens/min")
        recommendations.append(f"- **Conservative target**: Use ~{best_compliant_tokens * 60 * 0.8:.0f} tokens/min for safety margin")
    
    return "\n".join(recommendations)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze AWS benchmark results from OHA JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze results in current directory
  python3 analyze_results.py .
  
  # Analyze specific directory and save report
  python3 analyze_results.py --input ./results --output analysis_report.md
  
  # Just print to stdout
  python3 analyze_results.py /path/to/results
        """
    )
    
    parser.add_argument("directory", nargs="?", default=".", 
                       help="Directory containing OHA JSON result files")
    parser.add_argument("--input", "-i", help="Input directory (alternative to positional arg)")
    parser.add_argument("--output", "-o", help="Output markdown file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown")
    
    args = parser.parse_args()
    
    # Determine input directory
    input_dir = Path(args.input) if args.input else Path(args.directory)
    
    if not input_dir.exists():
        print(f"Error: Directory {input_dir} does not exist")
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)
    
    # Analyze results
    print(f"Analyzing results in: {input_dir}")
    analysis = analyze_results_directory(input_dir)
    
    if not analysis['results']:
        print("No OHA result files found (looking for c*.json files)")
        sys.exit(1)
    
    # Output results
    if args.json:
        output_content = json.dumps(analysis, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_content)
            print(f"JSON analysis saved to: {args.output}")
        else:
            print(output_content)
    else:
        output_file = Path(args.output) if args.output else None
        markdown_content = generate_markdown_report(analysis, output_file)
        
        if not output_file:
            print(markdown_content)


if __name__ == "__main__":
    main()
