# core/exporters.py
import json
import csv
from datetime import datetime
from typing import List, Dict
import xml.etree.ElementTree as ET

class URLExporter:
    def __init__(self, display_manager=None):
        self.display = display_manager
    
    def export_json(self, url_results: List, filename: str, include_stats: bool = True):
        """Export results as JSON with optional statistics"""
        data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'total_urls': len(url_results),
                'tool': 'PyWayback v2.0'
            },
            'urls': [
                {
                    'url': result.url,
                    'source': result.source,
                    'timestamp': result.timestamp,
                    'status_code': result.status_code
                }
                for result in url_results
            ]
        }
        
        if include_stats:
            from .analyzer import URLAnalyzer
            analyzer = URLAnalyzer()
            data['statistics'] = analyzer.analyze_urls(url_results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if self.display:
            self.display.console.print(f"[*] Exported {len(url_results)} URLs to {filename}", style="green")
    
    def export_csv(self, url_results: List, filename: str):
        """Export results as CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Source', 'Timestamp', 'Status Code'])
            
            for result in url_results:
                writer.writerow([result.url, result.source, result.timestamp, result.status_code])
        
        if self.display:
            self.display.console.print(f"[*] Exported {len(url_results)} URLs to {filename}", style="green")
    
    def export_txt(self, url_results: List, filename: str, include_metadata: bool = False):
        """Export results as plain text"""
        with open(filename, 'w', encoding='utf-8') as f:
            if include_metadata:
                f.write(f"# PyWayback Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total URLs: {len(url_results)}\n\n")
            
            for result in url_results:
                if include_metadata:
                    f.write(f"{result.url} # {result.source} {result.timestamp}\n")
                else:
                    f.write(f"{result.url}\n")
        
        if self.display:
            self.display.console.print(f"[*] Exported {len(url_results)} URLs to {filename}", style="green")
    
    def export_html(self, url_results: List, filename: str, stats: Dict = None):
        """Export results as HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pybackurl Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .stats {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .url-list {{ background: white; border: 1px solid #ddd; }}
                .url-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .suspicious {{ background: #fff5f5; border-left: 4px solid #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🕸️ Pybackrls URL Harvest Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        if stats:
            html_content += "<div class='stats'><h2>📊 Statistics</h2>"
            for key, value in stats.items():
                html_content += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            html_content += "</div>"
        
        html_content += "<div class='url-list'><h2>🔗 Discovered URLs</h2>"
        for result in url_results:
            css_class = "url-item suspicious" if self._is_suspicious_url(result.url) else "url-item"
            html_content += f"""
            <div class="{css_class}">
                <a href="{result.url}" target="_blank">{result.url}</a>
                <small> - Source: {result.source} | Time: {result.timestamp}</small>
            </div>
            """
        
        html_content += "</div></body></html>"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if self.display:
            self.display.console.print(f"[*] Exported HTML report to {filename}", style="green")
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Quick check if URL looks suspicious"""
        suspicious_indicators = ['/admin', '/config', '.env', '.bak', '/private']
        return any(indicator in url.lower() for indicator in suspicious_indicators)

