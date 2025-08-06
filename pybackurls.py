# pywayback.py

import argparse
import asyncio
from datetime import datetime
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from core.harvester import URLHarvester
from core.analyzer import URLAnalyzer
from core.exporters import URLExporter
from core.filters import URLFilter
from core.utils import DisplayManager
import os

def clean_and_filter_urls(
    url_results,
    allowed_schemes=('http', 'https'),
    min_length=10,
    filter_ext=None,
    filter_patterns=None,
    exclude_patterns=None
):
    unique = set()
    filtered = []
    for result in url_results:
        url = unquote(result.url).strip()
        parsed = urlparse(url)
        if not url or parsed.scheme not in allowed_schemes or len(url) < min_length:
            continue
        if filter_ext and not any(parsed.path.lower().endswith(f".{ext}") for ext in filter_ext):
            continue
        if filter_patterns and not any(pat in url for pat in filter_patterns):
            continue
        if exclude_patterns and any(pat in url for pat in exclude_patterns):
            continue
        if url not in unique:
            unique.add(url)
            # Update the result's URL field to make sure it's decoded/cleaned everywhere else
            result.url = url
            filtered.append(result)
    return filtered

async def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Pybackurls - Python Wayback and Recon URL Extractor")
    parser.add_argument('domains', nargs='*', help='Target domains')
    parser.add_argument('--include-subs', action='store_true', help='Include subdomains')
    parser.add_argument('--format', choices=['txt', 'json', 'csv', 'html'], default='txt')
    parser.add_argument('--output', '-o', help='Output filename')
    parser.add_argument('--threads', type=int, default=50, help='Concurrent threads')
    parser.add_argument('--extensions', help='Only include URLs with these extensions (comma-separated)')
    parser.add_argument('--exclude-extensions', help='Exclude URLs with these extensions (comma-separated)')
    parser.add_argument('--minlen', type=int, default=10, help='Minimum URL length (default 10)')
    parser.add_argument('--include', help='Only include URLs containing these strings (comma-separated)')
    parser.add_argument('--exclude', help='Exclude URLs containing these strings (comma-separated)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--analyze', action='store_true', help='Perform URL analysis')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--show-stats', action='store_true', help='Show statistics')
    args = parser.parse_args()

    # Initialize components
    # Clear the screen before running the app
    os.system('cls' if os.name == 'nt' else 'clear')
    display = DisplayManager()
    display.show_banner()

    # Handle input
    domains = args.domains if args.domains else [line.strip() for line in sys.stdin if line.strip()]
    if not domains:
        display.console.print("No domains provided.", style="red")
        return

    # Main harvesting logic
    all_results = []
    async with URLHarvester(max_concurrent=args.threads) as harvester:
        with display.create_progress_bar() as progress:
            for domain in domains:
                task = progress.add_task(f"Harvesting {domain}...", total=100)
                wayback_task = harvester.fetch_wayback_urls(domain, args.include_subs)
                cc_task = harvester.fetch_commoncrawl_urls(domain, args.include_subs)
                vt_task = harvester.fetch_virustotal_urls(domain)
                progress.update(task, advance=33)
                wayback_results = await wayback_task
                progress.update(task, advance=33)
                cc_results = await cc_task
                progress.update(task, advance=34)
                vt_results = await vt_task
                domain_results = wayback_results + cc_results + vt_results
                all_results.extend(domain_results)
                progress.update(task, completed=True)

    # --- SMART FILTERING & CLEANING ---
    filter_ext = args.extensions.split(',') if args.extensions else None
    exclude_ext = args.exclude_extensions.split(',') if args.exclude_extensions else None
    filter_patterns = args.include.split(',') if args.include else None
    exclude_patterns = args.exclude.split(',') if args.exclude else None

    all_results = clean_and_filter_urls(
        all_results,
        min_length=args.minlen,
        filter_ext=filter_ext,
        filter_patterns=filter_patterns,
        exclude_patterns=exclude_patterns
    )

    if exclude_ext:
        # Remove URLs with specified extensions
        all_results = [res for res in all_results if not any(res.url.lower().endswith(f".{ext}") for ext in exclude_ext)]

    # Deduplicate (by URL only)
    url_filter = URLFilter()
    all_results = url_filter.deduplicate_urls(all_results)

    # --- RECON HIGHLIGHTS ---
    analyzer = URLAnalyzer()
    recon_highlights = analyzer.find_recon_highlights(all_results)
    if recon_highlights:
        print("\nRecon Highlights")
        print("-" * 60)
        for item in recon_highlights:
            print(f"{item['type']}: {item['url']}")
        print("-" * 60)
    else:
        print("\nNo recon highlights detected in this run.")

    # --- ANALYSIS/STATS ---
    if args.analyze or args.show_stats:
        stats = analyzer.analyze_urls(all_results)
        if args.show_stats:
            display.show_stats_table(stats)
        if args.analyze and stats.get('parameters_found'):
            print("\nCommon GET parameters (Top 10):")
            for k, v in stats['parameters_found'].items():
                print(f"  {k}: {v}")

    # --- EXPORT ---
    exporter = URLExporter(display)
    output_dir = "results"
    Path(output_dir).mkdir(exist_ok=True)
    if args.output:
        # If user provided a filename, save inside the output directory if it's just a filename (no path)
        if os.path.dirname(args.output):
            # User provided full or relative path, respect it as-is
            filename = args.output
        else:
            filename = os.path.join(output_dir, args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f"pybackurls_results_{timestamp}.{args.format}")

    if args.format == 'json':
        exporter.export_json(all_results, filename, include_stats=args.analyze)
    elif args.format == 'csv':
        exporter.export_csv(all_results, filename)
    elif args.format == 'html':
        stats = analyzer.analyze_urls(all_results) if args.analyze else None
        exporter.export_html(all_results, filename, stats)
    else:
        exporter.export_txt(all_results, filename)

    display.console.print(f"\nHarvesting complete! Found {len(all_results)} unique URLs", style="bold green")
    print("\n")
    display.console.print(f"Results saved to: [bold]{filename}[/bold]", style="green")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
