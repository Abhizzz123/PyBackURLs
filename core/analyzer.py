# core/analyzer.py

import re
from collections import Counter
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Set
from datetime import datetime

class URLAnalyzer:

    def __init__(self):
        self.suspicious_patterns = {
            'Admin Panel': [r'/admin\b', r'/administrator\b', r'/wp-admin\b', r'/phpmyadmin\b'],
            'Backup/Config File': [r'\.env$', r'\.config$', r'/config\.', r'\.ini$', r'\.bak$', r'\.backup$', r'\.old$', r'\.orig$', r'\.sql$', r'\.db$', r'\.sqlite'],
            'Development/Test Endpoint': [r'/dev\b', r'/test\b', r'/staging\b', r'/debug\b'],
            'Sensitive Directory': [r'/private\b', r'/internal\b', r'/secure\b', r'/restricted\b'],
            'API Endpoint': [r'/api/', r'/v1/', r'/v2/', r'/rest/'],
            'Upload Directory': [r'/uploads/', r'/files/', r'/documents/'],
        }

    def analyze_urls(self, url_results: List) -> Dict:
        """Comprehensive URL analysis"""
        urls = [result.url for result in url_results]
        stats = {
            'total_urls': len(urls),
            'unique_domains': len(self._extract_domains(urls)),
            'file_extensions': self._analyze_extensions(urls),
            'parameters_found': self._analyze_parameters(urls),
            'date_range': self._analyze_date_range(url_results),
            'source_distribution': self._analyze_sources(url_results),
        }
        return stats

    def _extract_domains(self, urls: List[str]) -> Set[str]:
        domains = set()
        for url in urls:
            try:
                parsed = urlparse(url)
                domains.add(parsed.netloc.lower())
            except:
                continue
        return domains

    def _analyze_extensions(self, urls: List[str]) -> Dict[str, int]:
        extensions = []
        for url in urls:
            try:
                path = urlparse(url).path
                if '.' in path:
                    ext = path.split('.')[-1].lower()
                    if len(ext) <= 5:
                        extensions.append(ext)
            except:
                continue
        return dict(Counter(extensions).most_common(10))

    def _analyze_parameters(self, urls: List[str]) -> Dict[str, int]:
        params = []
        for url in urls:
            try:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                params.extend(query_params.keys())
            except:
                continue
        return dict(Counter(params).most_common(10))

    def _analyze_date_range(self, url_results: List) -> Dict[str, str]:
        timestamps = [result.timestamp for result in url_results if result.timestamp]
        if not timestamps:
            return {'earliest': 'N/A', 'latest': 'N/A'}
        try:
            dates = [datetime.strptime(ts[:8], '%Y%m%d') for ts in timestamps if len(ts) >= 8]
            if dates:
                return {
                    'earliest': min(dates).strftime('%Y-%m-%d'),
                    'latest': max(dates).strftime('%Y-%m-%d')
                }
        except:
            pass
        return {'earliest': 'N/A', 'latest': 'N/A'}

    def _analyze_sources(self, url_results: List) -> Dict[str, int]:
        sources = [result.source for result in url_results]
        return dict(Counter(sources))

    def find_recon_highlights(self, url_results: List) -> List[Dict[str, str]]:
        """Finds and tags 'hot' recon discovery URLs."""
        highlights = []
        for result in url_results:
            url = result.url
            for label, patterns in self.suspicious_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        highlights.append({'url': url, 'type': label})
                        break
        return highlights
