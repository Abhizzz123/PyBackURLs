
# core/harvester.py
import os
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class URLResult:
    url: str
    source: str
    timestamp: str = ""
    status_code: Optional[int] = None

class URLHarvester:
    def __init__(self, max_concurrent=50, timeout=30):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        self.session = aiohttp.ClientSession(
            connector=connector, 
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_wayback_urls(self, domain: str, include_subs: bool = True) -> List[URLResult]:
        subs = "*." if include_subs else ""
        url = f"http://web.archive.org/cdx/search/cdx?url={subs}{domain}/*&output=json&collapse=urlkey"

        try:
            async with self.session.get(url) as response:
                # Check HTTP status
                if response.status != 200:
                    print(f"[Wayback] HTTP error {response.status} for domain {domain} at URL: {url}")
                    
                    # Print response text for more info
                    content = await response.text()
                    print(f"[Wayback] Response content:\n{content}")
                    return []
                
                # Try to decode JSON
                try:
                    data = await response.json()
                except Exception as json_err:
                    content = await response.text()
                    print(f"[Wayback] JSON decode error: {json_err}")
                    print(f"[Wayback] Response content:\n{content}")
                    return []

                # Check if we got data or just header row
                if not data or len(data) <= 1:
                    print(f"[Wayback] No archived URLs found for {domain}")
                    print(f"[Wayback] Raw data: {data}")
                    return []

                results = []
                # data[0] is header, iterate from 1
                for row in data[1:]:
                    if len(row) >= 3:
                        results.append(URLResult(url=row[2], source="wayback", timestamp=row[1]))

                print(f"[Wayback] Retrieved {len(results)} URLs for domain {domain}")
                return results

        except Exception as e:
            print(f"[Wayback] Unexpected exception for domain {domain}: {e}")
            return []

    
    async def fetch_commoncrawl_urls(self, domain: str, include_subs: bool = True) -> List[URLResult]:
        """Fetch URLs from Common Crawl"""
        subdomain_prefix = "*." if include_subs else ""
        url = f"http://index.commoncrawl.org/CC-MAIN-2018-22-index?url={subdomain_prefix}{domain}/*&output=json"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                results = []
                async for line in response.content:
                    try:
                        data = json.loads(line.decode())
                        results.append(URLResult(
                            url=data.get('url', ''),
                            source="commoncrawl",
                            timestamp=data.get('timestamp', '')
                        ))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                
                return results
        except Exception as e:
            print(f"Error fetching CommonCrawl URLs for {domain}: {e}")
            return []
    
    async def fetch_virustotal_urls(self, domain: str) -> List[URLResult]:
        """Fetch URLs from VirusTotal (requires API key)"""
        api_key = os.getenv('VT_API_KEY')
        if not api_key:
            return []
        
        url = f"https://www.virustotal.com/vtapi/v2/domain/report?apikey={api_key}&domain={domain}"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = []
                
                for url_data in data.get('detected_urls', []):
                    results.append(URLResult(
                        url=url_data.get('url', ''),
                        source="virustotal"
                    ))
                
                return results
        except Exception as e:
            print(f"Error fetching VirusTotal URLs for {domain}: {e}")
            return []

