"""Robots.txt Checker: Validates robots.txt rules."""

import requests
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Optional


class RobotsChecker:
    """Checks and caches robots.txt rules per domain."""
    
    def __init__(self, user_agent: str = 'WebScraper/1.0', respect_robots: bool = True):
        """
        Initialize robots.txt checker.
        
        Args:
            user_agent: User agent string for robots.txt checking
            respect_robots: Whether to respect robots.txt (if False, always returns True)
        """
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.robots_cache: dict = {}  # Domain -> RobotFileParser
        self.failed_domains: set = set()  # Domains where robots.txt fetch failed
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL can be fetched, False if disallowed
        """
        if not self.respect_robots:
            return True
        
        domain = self._get_domain(url)
        
        # If we previously failed to fetch robots.txt for this domain, allow by default
        if domain in self.failed_domains:
            return True
        
        # Get or fetch robots.txt parser for this domain
        parser = self._get_robots_parser(domain)
        
        if parser is None:
            # Failed to fetch robots.txt, allow by default
            return True
        
        # Check if URL is allowed
        return parser.can_fetch(self.user_agent, url)
    
    def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """
        Get robots.txt parser for domain (with caching).
        
        Args:
            domain: Domain name
            
        Returns:
            RobotFileParser instance or None if fetch failed
        """
        # Return cached parser if available
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        # Try to fetch robots.txt
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            response = requests.get(robots_url, timeout=5, allow_redirects=True)
            response.raise_for_status()
            
            # Create parser and read robots.txt content
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.read()
            
            # Cache parser
            self.robots_cache[domain] = parser
            return parser
            
        except Exception:
            # Failed to fetch robots.txt - mark domain and return None
            self.failed_domains.add(domain)
            return None
    
    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name (without port)
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return domain
