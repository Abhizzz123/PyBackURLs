# core/utils.py
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich import box

class DisplayManager:
    def __init__(self):
        self.console = Console()
    
    def show_banner(self):
        banner_text = """
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]
[bold white]                        PYBACKURLS[/bold white]
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]

[yellow]Historical URL Discovery & Analysis Framework[/yellow]

[bold white]Features:[/bold white]
  • [green]Multi-source URL harvesting[/green] - Wayback, CommonCrawl, VirusTotal(requires API key)
  • [green]Asynchronous processing[/green] - High-performance concurrent requests
  • [green]Smart filtering[/green] - Duplicate removal & pattern matching
  • [green]Flexible output[/green] - JSON, CSV, TXT formats

[bold white]Data Sources:[/bold white]
  • [blue]Wayback Machine[/blue] - Internet Archive snapshots
  • [blue]CommonCrawl[/blue] - Web crawl data repository
  • [blue]VirusTotal[/blue] - Security intelligence platform

[dim white]Author: github.com/Abhizzz123[/dim white]
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]
        """
        
        panel = Panel(
            banner_text,
            box=box.HEAVY,
            padding=(1, 3),
            style="bright_white"
        )
        self.console.print(panel)
    
    def create_progress_bar(self):
        return Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            console=self.console,
            transient=True
        )
    
    def show_stats_table(self, stats: Dict):
        table = Table(title="📊 Harvesting Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        for key, value in stats.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        self.console.print(table)
    
    def show_interesting_urls(self, urls: List[str]):
        if not urls:
            return
        
        table = Table(title="🔍 Interesting URLs Found", box=box.SIMPLE)
        table.add_column("URL", style="yellow")
        table.add_column("Reason", style="red")
        
        for url_data in urls:
            table.add_row(url_data['url'], url_data['reason'])
        
        self.console.print(table)

