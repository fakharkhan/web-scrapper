"""Markdown Converter: Converts web page content to Markdown format."""

import logging
from typing import Optional
from urllib.parse import urlparse

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

try:
    from .browser_fetcher import BrowserFetcher, PLAYWRIGHT_AVAILABLE
except ImportError:
    BrowserFetcher = None
    PLAYWRIGHT_AVAILABLE = False


class MarkdownConverter:
    """Converts web page HTML content to Markdown format."""
    
    def __init__(
        self,
        use_browser: bool = False,
        timeout: int = 30,
        user_agent: str = 'WebScraper/1.0',
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize markdown converter.
        
        Args:
            use_browser: Whether to use browser for JavaScript-rendered pages
            timeout: Request timeout in seconds
            user_agent: User agent string
            logger: Logger instance
        """
        if not HTML2TEXT_AVAILABLE:
            raise ImportError(
                "html2text is not installed. Install it with: pip install html2text"
            )
        
        self.use_browser = use_browser
        self.timeout = timeout
        self.user_agent = user_agent
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize html2text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # Don't wrap lines
        self.html_converter.unicode_snob = True  # Use unicode characters
        self.html_converter.escape_snob = False  # Don't escape special characters
        self.html_converter.skip_internal_links = False  # Include internal links
        self.html_converter.inline_links = True  # Use inline link format
        self.html_converter.protect_links = True  # Protect links from line wrapping
        self.html_converter.ignore_tables = False  # Include tables
        self.html_converter.bypass_tables = False  # Process tables
        self.html_converter.ignore_anchors = False  # Include anchors
        
        # Initialize browser fetcher if needed
        self.browser_fetcher = None
        if self.use_browser:
            if not PLAYWRIGHT_AVAILABLE:
                self.logger.warning(
                    "Browser mode requested but Playwright not available. "
                    "Falling back to static HTML parsing."
                )
                self.use_browser = False
            else:
                try:
                    from .browser_fetcher import BrowserFetcher
                    self.browser_fetcher = BrowserFetcher(
                        timeout=self.timeout,
                        wait_for="networkidle",
                        user_agent=self.user_agent,
                        logger=self.logger,
                    )
                    self.browser_fetcher.start()
                except Exception as e:
                    self.logger.error(f"Failed to initialize browser: {e}")
                    self.use_browser = False
    
    def fetch_content(self, url: str) -> tuple[int, Optional[str], str]:
        """
        Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (status_code, html_content, final_url)
        """
        if self.use_browser and self.browser_fetcher:
            return self.browser_fetcher.fetch_page(url)
        else:
            # Use requests for static HTML
            import requests
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    headers={'User-Agent': self.user_agent},
                )
                
                final_url = response.url
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'text/html' in content_type:
                        return response.status_code, response.text, final_url
                    else:
                        return response.status_code, None, final_url
                
                return response.status_code, None, final_url
                
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return 0, None, url
    
    def convert_to_markdown(self, url: str) -> Optional[str]:
        """
        Convert web page at URL to Markdown.
        
        Args:
            url: URL to convert
            
        Returns:
            Markdown content as string, or None if conversion failed
        """
        self.logger.info(f"Fetching content from {url}")
        
        status_code, html_content, final_url = self.fetch_content(url)
        
        if status_code != 200 or not html_content:
            self.logger.error(f"Failed to fetch content from {url} (status: {status_code})")
            return None
        
        if final_url != url:
            self.logger.info(f"Redirected from {url} to {final_url}")
        
        try:
            # Check if HTML has substantial content
            html_length = len(html_content)
            self.logger.debug(f"HTML content length: {html_length} characters")
            
            # Convert HTML to Markdown
            markdown_content = self.html_converter.handle(html_content)
            
            # Check if markdown conversion produced content
            markdown_length = len(markdown_content.strip())
            self.logger.debug(f"Markdown content length: {markdown_length} characters")
            
            if markdown_length == 0:
                self.logger.warning(
                    f"Markdown conversion produced empty content. "
                    f"This might be a JavaScript-rendered page. "
                    f"Try using --use-browser flag."
                )
                # Try to extract text directly from HTML as fallback
                markdown_content = self._extract_text_fallback(html_content)
                if len(markdown_content.strip()) == 0:
                    markdown_content = "\n*Note: This page appears to be a Single Page Application (SPA) that loads content via JavaScript. Use --use-browser flag to render the full content.*\n"
            
            # Add metadata header
            metadata = f"# {self._extract_title(html_content)}\n\n"
            metadata += f"**Source URL:** {final_url}\n\n"
            metadata += "---\n\n"
            
            return metadata + markdown_content
            
        except Exception as e:
            self.logger.error(f"Error converting to markdown: {e}")
            return None
    
    def _extract_title(self, html_content: str) -> str:
        """
        Extract title from HTML content.
        
        Args:
            html_content: HTML content
            
        Returns:
            Page title or default title
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
        except Exception:
            pass
        
        return "Untitled"
    
    def _extract_text_fallback(self, html_content: str) -> str:
        """
        Fallback method to extract text from HTML when html2text fails.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text content
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            self.logger.debug(f"Fallback text extraction failed: {e}")
            return ""
    
    def convert_to_markdown_file(self, url: str, output_file: str) -> bool:
        """
        Convert URL to Markdown and save to file.
        
        Args:
            url: URL to convert
            output_file: Path to output markdown file
            
        Returns:
            True if successful, False otherwise
        """
        markdown_content = self.convert_to_markdown(url)
        
        if markdown_content is None:
            return False
        
        try:
            # Ensure parent directory exists
            from pathlib import Path
            parent_dir = Path(output_file).parent
            if parent_dir:
                parent_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Markdown saved to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving markdown to {output_file}: {e}")
            return False
    
    def close(self):
        """Close browser if used."""
        if self.browser_fetcher:
            self.browser_fetcher.stop()
