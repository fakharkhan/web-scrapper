"""Browser Fetcher: Handles JavaScript-rendered pages using Playwright."""

import logging
from typing import Optional, Tuple, List
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None
    Page = None


class BrowserFetcher:
    """Fetches and extracts links from JavaScript-rendered pages using Playwright."""
    
    def __init__(
        self,
        timeout: int = 30,
        wait_for: str = "networkidle",
        user_agent: str = 'WebScraper/1.0',
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize browser fetcher.
        
        Args:
            timeout: Page load timeout in seconds
            wait_for: What to wait for: "load", "domcontentloaded", "networkidle", or "commit"
            user_agent: User agent string
            logger: Logger instance
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install it with: pip install playwright && playwright install"
            )
        
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.wait_for = wait_for
        self.user_agent = user_agent
        self.logger = logger or logging.getLogger(__name__)
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._browser_launched = False
    
    def start(self):
        """Start the browser instance."""
        if not self._browser_launched:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']  # For Linux compatibility
            )
            self._browser_launched = True
            self.logger.debug("Browser started")
    
    def stop(self):
        """Stop the browser instance."""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        self._browser_launched = False
        self.logger.debug("Browser stopped")
    
    def fetch_page(self, url: str) -> Tuple[int, Optional[str], str]:
        """
        Fetch a page using browser and wait for JavaScript to execute.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (status_code, html_content, final_url)
        """
        if not self._browser_launched:
            self.start()
        
        page: Optional[Page] = None
        try:
            # Create new page
            page = self.browser.new_page(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Navigate to URL
            response = page.goto(
                url,
                wait_until=self.wait_for,
                timeout=self.timeout
            )
            
            if response is None:
                self.logger.warning(f"No response for {url}")
                return 0, None, url
            
            status_code = response.status
            final_url = page.url
            
            # Get rendered HTML after JavaScript execution
            html_content = page.content()
            
            return status_code, html_content, final_url
            
        except PlaywrightTimeoutError:
            self.logger.warning(f"Timeout loading {url} (timeout: {self.timeout}ms)")
            return 0, None, url
        except Exception as e:
            self.logger.warning(f"Error fetching {url} with browser: {e}")
            return 0, None, url
        finally:
            if page:
                page.close()
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract links from rendered HTML.
        
        This method can also extract links from JavaScript-rendered content,
        including client-side routing links.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of absolute URLs
        """
        from bs4 import BeautifulSoup
        
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
            
            # Extract router links (common in SPAs)
            # React Router: data attributes, onClick handlers with paths
            for tag in soup.find_all(['a', 'button', 'div'], attrs={'data-path': True}):
                path = tag.get('data-path')
                if path:
                    links.append(path)
            
            # Vue Router: router-link components
            for tag in soup.find_all(['a', 'router-link'], attrs={'to': True}):
                to = tag.get('to')
                if to:
                    links.append(to)
            
            # Angular Router: routerLink
            for tag in soup.find_all(attrs={'routerlink': True}):
                routerlink = tag.get('routerlink')
                if routerlink:
                    links.append(routerlink)
            
            # Extract from onclick handlers (basic pattern matching)
            for tag in soup.find_all(attrs={'onclick': True}):
                onclick = tag.get('onclick', '')
                # Simple pattern: look for URLs in onclick
                import re
                url_pattern = r'["\'](https?://[^"\']+|/[^"\']*)["\']'
                matches = re.findall(url_pattern, onclick)
                links.extend(matches)
        
        except Exception as e:
            self.logger.warning(f"Error parsing HTML from {base_url}: {e}")
            return []
        
        return links
    
    def extract_links_from_page(self, url: str) -> List[str]:
        """
        Fetch page and extract links in one call.
        
        Args:
            url: URL to fetch and extract links from
            
        Returns:
            List of absolute URLs
        """
        status, html, final_url = self.fetch_page(url)
        if html:
            return self.extract_links(html, final_url)
        return []
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
