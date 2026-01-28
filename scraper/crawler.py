"""Crawler Engine: Main orchestration logic."""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple
import logging

from .url_manager import URLManager
from .filters import URLFilter
from .rate_limiter import RateLimiter
from .robots_checker import RobotsChecker
from .output_writer import OutputWriter
from .logger import setup_logger

# Try to import browser fetcher (optional dependency)
try:
    from .browser_fetcher import BrowserFetcher, PLAYWRIGHT_AVAILABLE
except ImportError:
    BrowserFetcher = None
    PLAYWRIGHT_AVAILABLE = False


class Crawler:
    """Main crawler engine that orchestrates the crawling process."""
    
    def __init__(
        self,
        max_urls: int,
        max_depth: int = 3,
        allowed_domains: Optional[List[str]] = None,
        deny_patterns: Optional[List[str]] = None,
        max_concurrent: int = 5,
        timeout: int = 10,
        rate_limit: float = 1.0,
        user_agent: str = 'WebScraper/1.0',
        respect_robots: bool = True,
        follow_redirects: bool = True,
        use_browser: bool = False,
        browser_wait_for: str = "networkidle",
        output_writer: Optional[OutputWriter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize crawler.
        
        Args:
            max_urls: Maximum number of URLs to collect (required)
            max_depth: Maximum crawl depth from seed URLs (default: 3)
            allowed_domains: List of allowed domains (whitelist)
            deny_patterns: List of regex patterns or substrings to deny
            max_concurrent: Maximum concurrent requests
            timeout: Request timeout in seconds
            rate_limit: Requests per second
            user_agent: User agent string
            respect_robots: Whether to respect robots.txt
            follow_redirects: Whether to follow HTTP redirects
            use_browser: Whether to use browser for JavaScript rendering (default: False)
            browser_wait_for: What to wait for in browser: "load", "domcontentloaded", "networkidle" (default: "networkidle")
            output_writer: Output writer instance
            logger: Logger instance
        """
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.use_browser = use_browser
        self.browser_wait_for = browser_wait_for
        
        # Initialize components
        self.url_manager = URLManager()
        self.url_filter = URLFilter(
            allowed_domains=allowed_domains,
            deny_patterns=deny_patterns,
        )
        self.rate_limiter = RateLimiter(global_rate_limit=rate_limit)
        self.robots_checker = RobotsChecker(
            user_agent=user_agent,
            respect_robots=respect_robots,
        )
        self.output_writer = output_writer
        self.logger = logger or setup_logger()
        
        # Initialize browser fetcher if needed
        self.browser_fetcher = None
        if self.use_browser:
            if not PLAYWRIGHT_AVAILABLE or BrowserFetcher is None:
                self.logger.warning(
                    "Browser mode requested but Playwright not available. "
                    "Install with: pip install playwright && playwright install"
                )
                self.use_browser = False
            else:
                try:
                    self.browser_fetcher = BrowserFetcher(
                        timeout=self.timeout,
                        wait_for=self.browser_wait_for,
                        user_agent=user_agent,
                        logger=self.logger,
                    )
                    self.browser_fetcher.start()
                    self.logger.info("Browser mode enabled for JavaScript-rendered pages")
                except Exception as e:
                    self.logger.error(f"Failed to initialize browser: {e}")
                    self.use_browser = False
        
        # Statistics
        self.stats = {
            'fetched': 0,
            'errors': 0,
            'skipped_robots': 0,
            'skipped_filter': 0,
            'skipped_non_html': 0,
        }
    
    def crawl(self, seed_urls: List[str]) -> dict:
        """
        Start crawling from seed URLs.
        
        Args:
            seed_urls: List of seed URLs to start crawling from
            
        Returns:
            Dictionary with crawl statistics and summary
        """
        self.logger.info(f"Starting crawl with {len(seed_urls)} seed URL(s)")
        self.logger.info(f"Max URLs: {self.max_urls}, Max Depth: {self.max_depth}")
        
        # Add seed URLs to queue (depth=0)
        for seed_url in seed_urls:
            self.url_manager.add_to_queue(seed_url, '', 0)
        
        # Adjust concurrency for browser mode (browsers are heavier)
        effective_concurrent = self.max_concurrent
        if self.use_browser:
            # Limit browser concurrency to avoid resource exhaustion
            effective_concurrent = min(self.max_concurrent, 3)
            if self.max_concurrent > 3:
                self.logger.info(f"Browser mode: limiting concurrency to {effective_concurrent} (browsers are resource-intensive)")
        
        try:
            # Main crawl loop
            with ThreadPoolExecutor(max_workers=effective_concurrent) as executor:
                futures = {}
                
                while self.url_manager.has_urls() and not self._should_stop():
                    # Submit batch of URLs for processing
                    batch_size = min(
                        self.max_concurrent - len(futures),
                        self.url_manager.queue_size()
                    )
                    
                    for _ in range(batch_size):
                        if not self.url_manager.has_urls() or self._should_stop():
                            break
                        
                        url_data = self.url_manager.get_next_url()
                        if url_data is None:
                            break
                        
                        url, source_url, depth = url_data
                        
                        # Check if already visited (double-check)
                        if self.url_manager.is_visited(url):
                            continue
                        
                        # Submit for processing
                        future = executor.submit(self._process_url, url, source_url, depth)
                        futures[future] = (url, source_url, depth)
                    
                    # Process completed futures
                    if futures:
                        for future in as_completed(futures):
                            url, source_url, depth = futures.pop(future)
                            try:
                                future.result()  # Get result (or raise exception)
                            except Exception as e:
                                self.logger.error(f"Error processing {url}: {e}")
                                self.stats['errors'] += 1
        finally:
            # Always stop browser if used, even on errors
            if self.browser_fetcher:
                self.browser_fetcher.stop()
        
        # Generate summary
        summary = self._generate_summary()
        self.logger.info("Crawl completed")
        self.logger.info(f"Summary: {summary}")
        
        return summary
    
    def _process_url(self, url: str, source_url: str, depth: int) -> None:
        """
        Process a single URL: fetch, parse, extract links.
        
        Args:
            url: URL to process
            source_url: URL where this link was discovered
            depth: Depth from seed URL
        """
        # Check if already visited
        if self.url_manager.is_visited(url):
            return
        
        # Check robots.txt
        if not self.robots_checker.can_fetch(url):
            self.logger.debug(f"Skipping {url} (disallowed by robots.txt)")
            self.stats['skipped_robots'] += 1
            self.url_manager.mark_visited(url)
            return
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed(url)
        
        # Fetch page (using browser if enabled)
        if self.use_browser and self.browser_fetcher:
            status_code, content, final_url = self.browser_fetcher.fetch_page(url)
        else:
            status_code, content, final_url = self._fetch_page(url)
        
        # Mark as visited
        self.url_manager.mark_visited(url)
        
        # Write to output
        if self.output_writer:
            redirect_target = final_url if final_url != url else None
            self.output_writer.write_url(
                url=url,
                source_url=source_url,
                depth=depth,
                status_code=status_code,
                redirect_target=redirect_target,
            )
        
        # Check if we should stop (max URLs reached)
        if self._should_stop():
            return
        
        # Process only successful HTML responses
        if status_code == 200 and content:
            if not self._is_html(content):
                self.logger.debug(f"Skipping {url} (not HTML)")
                self.stats['skipped_non_html'] += 1
                return
            
            # Check depth limit before extracting links
            if depth >= self.max_depth:
                self.logger.debug(f"Skipping link extraction for {url} (max depth reached)")
                return
            
            # Extract and process links (using browser extractor if browser mode)
            if self.use_browser and self.browser_fetcher:
                links = self.browser_fetcher.extract_links(content, url)
            else:
                links = self._extract_links(content, url)
            
            for link in links:
                # Normalize link
                normalized_link = self.url_manager.normalize_url(link, url)
                
                # Check if already discovered
                if normalized_link in self.url_manager.discovered:
                    continue
                
                # Apply filters
                if not self.url_filter.is_valid_url(normalized_link):
                    self.logger.debug(f"Filtered out: {normalized_link}")
                    self.stats['skipped_filter'] += 1
                    continue
                
                # Add to queue if within depth limit
                if depth + 1 <= self.max_depth:
                    self.url_manager.add_to_queue(normalized_link, url, depth + 1)
        
        self.stats['fetched'] += 1
    
    def _fetch_page(self, url: str) -> Tuple[int, Optional[str], str]:
        """
        Fetch a page using HTTP GET.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (status_code, content, final_url)
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=self.follow_redirects,
                headers={'User-Agent': self.robots_checker.user_agent},
            )
            
            # Get final URL after redirects
            final_url = response.url
            
            # Only return content for successful responses
            if response.status_code == 200:
                # Check Content-Type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    try:
                        # Try to decode with UTF-8, fallback to latin-1
                        content = response.text
                        return response.status_code, content, final_url
                    except UnicodeDecodeError:
                        self.logger.warning(f"Encoding error for {url}, attempting fallback")
                        try:
                            content = response.content.decode('latin-1', errors='replace')
                            return response.status_code, content, final_url
                        except Exception as e:
                            self.logger.warning(f"Failed to decode content for {url}: {e}")
                            return response.status_code, None, final_url
                else:
                    return response.status_code, None, final_url
            
            # Log non-200 status codes
            if response.status_code >= 400:
                self.logger.debug(f"HTTP {response.status_code} for {url}")
            
            return response.status_code, None, final_url
            
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout fetching {url} (timeout: {self.timeout}s)")
            self.stats['errors'] += 1
            return 0, None, url
        except requests.exceptions.TooManyRedirects:
            self.logger.warning(f"Too many redirects for {url}")
            self.stats['errors'] += 1
            return 0, None, url
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request error fetching {url}: {e}")
            self.stats['errors'] += 1
            return 0, None, url
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
            self.stats['errors'] += 1
            return 0, None, url
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract links from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract <a href> links (mandatory)
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                if href:
                    links.append(href)
            
            # Extract <link href> links (optional)
            for tag in soup.find_all('link', href=True):
                href = tag['href']
                if href:
                    links.append(href)
        
        except Exception as e:
            self.logger.warning(f"Error parsing HTML from {base_url}: {e}")
            # Return empty list on parse error - don't crash
            return []
        
        return links
    
    def _is_html(self, content: str) -> bool:
        """
        Check if content appears to be HTML.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be HTML
        """
        # Simple check: look for HTML tags
        content_lower = content.lower().strip()
        return content_lower.startswith('<html') or '<html' in content_lower[:1000]
    
    def _should_stop(self) -> bool:
        """
        Check if crawling should stop.
        
        Returns:
            True if crawl limits reached
        """
        # Stop if max URLs reached
        if len(self.url_manager.visited) >= self.max_urls:
            return True
        
        return False
    
    def _generate_summary(self) -> dict:
        """
        Generate crawl summary.
        
        Returns:
            Dictionary with crawl statistics
        """
        url_stats = self.url_manager.get_stats()
        
        summary = {
            'total_discovered': url_stats['discovered_count'],
            'total_visited': url_stats['visited_count'],
            'total_fetched': self.stats['fetched'],
            'total_errors': self.stats['errors'],
            'skipped_robots': self.stats['skipped_robots'],
            'skipped_filter': self.stats['skipped_filter'],
            'skipped_non_html': self.stats['skipped_non_html'],
            'max_urls_limit': self.max_urls,
            'max_depth_limit': self.max_depth,
        }
        
        return summary
