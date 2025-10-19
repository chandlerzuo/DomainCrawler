#!/usr/bin/env python3
"""
Web Crawler - Crawls a seed domain and saves discovered links to files.
"""

import argparse
import time
import os
import sys
from urllib.parse import urlparse, urljoin, urldefrag
from collections import deque
from typing import Set, Dict, Optional
import requests
from bs4 import BeautifulSoup


class WebCrawler:
    def __init__(self, seed_url: str, output_dir: str = "crawled_links", delay: float = 1.0):
        """
        Initialize the web crawler.
        
        Args:
            seed_url: The starting URL to crawl
            output_dir: Directory to save crawled links
            delay: Delay between requests in seconds (polite crawling)
        """
        self.seed_url = seed_url
        self.output_dir = output_dir
        self.delay = delay
        
        parsed = urlparse(seed_url)
        self.domain = parsed.netloc
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        self.visited: Set[str] = set()
        self.to_visit = deque([seed_url])
        self.all_links: Set[str] = set()
        self.link_sources: Dict[str, Set[str]] = {}
        
        self.pages_crawled = 0
        self.links_found = 0
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WebCrawler/1.0 (Educational Purpose; +https://example.com/bot)'
        })
    
    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the seed domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc == ''
        except:
            return False
    
    def normalize_url(self, url: str, base: Optional[str] = None) -> Optional[str]:
        """Normalize and clean URL."""
        if base:
            url = urljoin(base, url)
        
        url, _ = urldefrag(url)
        
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return None
        
        return url
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content with error handling."""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error {e.response.status_code}: {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {url} - {str(e)}")
            return None
    
    def extract_links(self, html: str, page_url: str) -> Set[str]:
        """Extract all links from HTML content."""
        links = set()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup.find_all(['a', 'link']):
                href = tag.get('href')
                if not href or not isinstance(href, str):
                    continue
                
                normalized = self.normalize_url(href, page_url)
                if normalized:
                    links.add(normalized)
        except Exception as e:
            print(f"⚠️  Error parsing HTML from {page_url}: {str(e)}")
        
        return links
    
    def crawl(self, max_pages: int = 100):
        """Main crawling loop."""
        print(f"🚀 Starting crawl of {self.seed_url}")
        print(f"📁 Saving links to: {self.output_dir}")
        print(f"⏱️  Delay between requests: {self.delay}s")
        print(f"🎯 Max pages: {max_pages}")
        print("-" * 60)
        
        while self.to_visit and self.pages_crawled < max_pages:
            url = self.to_visit.popleft()
            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            self.pages_crawled += 1
            
            print(f"\n[{self.pages_crawled}/{max_pages}] Crawling: {url}")
            
            html = self.fetch_page(url)
            
            time.sleep(self.delay)
            
            if not html:
                continue
            
            links = self.extract_links(html, url)
            
            internal_links = 0
            external_links = 0
            
            for link in links:
                self.all_links.add(link)
                
                if link not in self.link_sources:
                    self.link_sources[link] = set()
                self.link_sources[link].add(url)
                
                if self.is_same_domain(link):
                    internal_links += 1
                    if link not in self.visited and link not in self.to_visit:
                        self.to_visit.append(link)
                else:
                    external_links += 1
            
            self.links_found += len(links)
            print(f"   Found {len(links)} links ({internal_links} internal, {external_links} external)")
        
        print("\n" + "=" * 60)
        print("✅ Crawling complete!")
        print(f"📊 Statistics:")
        print(f"   Pages crawled: {self.pages_crawled}")
        print(f"   Unique links found: {len(self.all_links)}")
        print(f"   Total links discovered: {self.links_found}")
    
    def save_results(self):
        """Save crawled links to files."""
        print(f"\n💾 Saving results to {self.output_dir}...")
        
        all_links_file = os.path.join(self.output_dir, "all_links.txt")
        with open(all_links_file, 'w', encoding='utf-8') as f:
            f.write(f"# All links discovered from {self.seed_url}\n")
            f.write(f"# Total: {len(self.all_links)} unique links\n\n")
            for link in sorted(self.all_links):
                f.write(f"{link}\n")
        print(f"   ✓ All links: {all_links_file}")
        
        internal_links = [l for l in self.all_links if self.is_same_domain(l)]
        internal_file = os.path.join(self.output_dir, "internal_links.txt")
        with open(internal_file, 'w', encoding='utf-8') as f:
            f.write(f"# Internal links (same domain) from {self.seed_url}\n")
            f.write(f"# Total: {len(internal_links)} links\n\n")
            for link in sorted(internal_links):
                f.write(f"{link}\n")
        print(f"   ✓ Internal links: {internal_file}")
        
        external_links = [l for l in self.all_links if not self.is_same_domain(l)]
        external_file = os.path.join(self.output_dir, "external_links.txt")
        with open(external_file, 'w', encoding='utf-8') as f:
            f.write(f"# External links (outbound) from {self.seed_url}\n")
            f.write(f"# Total: {len(external_links)} links\n\n")
            for link in sorted(external_links):
                f.write(f"{link}\n")
        print(f"   ✓ External links: {external_file}")
        
        visited_file = os.path.join(self.output_dir, "visited_pages.txt")
        with open(visited_file, 'w', encoding='utf-8') as f:
            f.write(f"# Pages visited during crawl of {self.seed_url}\n")
            f.write(f"# Total: {len(self.visited)} pages\n\n")
            for page in sorted(self.visited):
                f.write(f"{page}\n")
        print(f"   ✓ Visited pages: {visited_file}")
        
        sources_file = os.path.join(self.output_dir, "link_sources.txt")
        with open(sources_file, 'w', encoding='utf-8') as f:
            f.write(f"# Link sources (where each link was found)\n")
            f.write(f"# Format: LINK -> found on: SOURCE1, SOURCE2, ...\n\n")
            for link in sorted(self.all_links):
                sources = sorted(self.link_sources.get(link, set()))
                f.write(f"{link}\n")
                for source in sources:
                    f.write(f"  -> {source}\n")
                f.write("\n")
        print(f"   ✓ Link sources: {sources_file}")
        
        print(f"\n✨ All results saved to directory: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Web Crawler - Crawl a domain and save discovered links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawler.py https://example.com
  python crawler.py https://example.com --max-pages 50 --delay 0.5
  python crawler.py https://blog.example.com --output my_crawl_results
        """
    )
    
    parser.add_argument(
        'seed_url',
        help='The seed URL to start crawling from'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--output',
        default='crawled_links',
        help='Output directory for crawled links (default: crawled_links)'
    )
    
    args = parser.parse_args()
    
    if not args.seed_url.startswith(('http://', 'https://')):
        print("❌ Error: Seed URL must start with http:// or https://")
        sys.exit(1)
    
    crawler = WebCrawler(
        seed_url=args.seed_url,
        output_dir=args.output,
        delay=args.delay
    )
    
    try:
        crawler.crawl(max_pages=args.max_pages)
        crawler.save_results()
    except KeyboardInterrupt:
        print("\n\n⚠️  Crawl interrupted by user")
        print("💾 Saving partial results...")
        crawler.save_results()
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
