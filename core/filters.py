# core/filters.py
from datetime import datetime
from urllib.parse import urlparse
from typing import List
import re

class URLFilter:
    def __init__(self):
        pass
    
    def filter_by_extensions(self, url_results: List, extensions: List[str], exclude: bool = False) -> List:
        """Filter URLs by file extensions"""
        filtered = []
        extensions = [ext.lower().strip('.') for ext in extensions]
        
        for result in url_results:
            url_path = urlparse(result.url).path.lower()
            has_extension = any(url_path.endswith(f'.{ext}') for ext in extensions)
            
            if exclude and not has_extension:
                filtered.append(result)
            elif not exclude and has_extension:
                filtered.append(result)
            elif not extensions:  # No filter specified
                filtered.append(result)
        
        return filtered
    
    def filter_by_date_range(self, url_results: List, start_date: str = None, end_date: str = None) -> List:
        """Filter URLs by date range (YYYY-MM-DD format)"""
        if not start_date and not end_date:
            return url_results
        
        filtered = []
        for result in url_results:
            if not result.timestamp or len(result.timestamp) < 8:
                continue
            
            try:
                url_date = datetime.strptime(result.timestamp[:8], '%Y%m%d')
                
                if start_date:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    if url_date < start:
                        continue
                
                if end_date:
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    if url_date > end:
                        continue
                
                filtered.append(result)
            except ValueError:
                continue
        
        return filtered
    
    def filter_by_patterns(self, url_results: List, include_patterns: List[str] = None, 
                          exclude_patterns: List[str] = None) -> List:
        """Filter URLs by regex patterns"""
        filtered = []
        
        for result in url_results:
            url = result.url
            
            # Check include patterns
            if include_patterns:
                if not any(re.search(pattern, url, re.IGNORECASE) for pattern in include_patterns):
                    continue
            
            # Check exclude patterns
            if exclude_patterns:
                if any(re.search(pattern, url, re.IGNORECASE) for pattern in exclude_patterns):
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def deduplicate_urls(self, url_results: List, by_url: bool = True, by_path: bool = False) -> List:
        """Remove duplicate URLs"""
        seen = set()
        filtered = []
        
        for result in url_results:
            if by_url:
                key = result.url
            elif by_path:
                key = urlparse(result.url).path
            else:
                key = result.url
            
            if key not in seen:
                seen.add(key)
                filtered.append(result)
        
        return filtered
    from urllib.parse import unquote, urlparse

    def clean_and_filter_urls(url_results, allowed_schemes=('http', 'https'),
                         min_length=10, filter_ext=None, filter_patterns=None, exclude_patterns=None):
        unique = set()
        filtered = []
        for result in url_results:
            url = unquote(result.url).strip()
            parsed = urlparse(url)
            if not url:
                continue
            if parsed.scheme not in allowed_schemes:
                continue
            if len(url) < min_length:
                continue
            if filter_ext:
                if not any(parsed.path.lower().endswith(f".{ext}") for ext in filter_ext):
                    continue
            if filter_patterns:
                if not any(pat in url for pat in filter_patterns):
                    continue
            if exclude_patterns:
                if any(pat in url for pat in exclude_patterns):
                    continue
            if url not in unique:
                unique.add(url)
                filtered.append(result)
        return filtered

