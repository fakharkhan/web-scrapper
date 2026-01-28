"""Filter Module: URL filtering logic."""

import re
from urllib.parse import urlparse
from typing import List, Optional


class URLFilter:
    """Filters URLs based on schemes, extensions, domains, and patterns."""
    
    # Default file extensions to ignore
    DEFAULT_IGNORED_EXTENSIONS = [
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.mp4', '.mp3', '.avi', '.mov', '.wmv',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.exe', '.dmg', '.deb', '.rpm',
    ]
    
    # Schemes to ignore
    IGNORED_SCHEMES = ['mailto', 'tel', 'javascript', 'data', 'file']
    
    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        deny_patterns: Optional[List[str]] = None,
        ignored_extensions: Optional[List[str]] = None,
    ):
        """
        Initialize URL filter.
        
        Args:
            allowed_domains: List of allowed domains (whitelist). If None, all domains allowed.
            deny_patterns: List of regex patterns or substrings to deny
            ignored_extensions: List of file extensions to ignore. If None, uses defaults.
        """
        self.allowed_domains = allowed_domains or []
        self.deny_patterns = deny_patterns or []
        self.ignored_extensions = ignored_extensions or self.DEFAULT_IGNORED_EXTENSIONS
        
        # Compile regex patterns for deny_patterns
        self.compiled_patterns = []
        for pattern in self.deny_patterns:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                # If pattern is not valid regex, treat as substring
                self.compiled_patterns.append(pattern)
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL passes all filters.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid and should be crawled
        """
        # Check scheme
        if self.should_ignore_scheme(url):
            return False
        
        # Check file extension
        if self.should_ignore_extension(url):
            return False
        
        # Check domain whitelist
        if not self.is_allowed_domain(url):
            return False
        
        # Check deny patterns
        if self.matches_deny_pattern(url):
            return False
        
        return True
    
    def should_ignore_scheme(self, url: str) -> bool:
        """
        Check if URL scheme should be ignored.
        
        Args:
            url: URL to check
            
        Returns:
            True if scheme should be ignored
        """
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        return scheme in self.IGNORED_SCHEMES or (scheme not in ['http', 'https'])
    
    def should_ignore_extension(self, url: str) -> bool:
        """
        Check if URL has an ignored file extension.
        
        Args:
            url: URL to check
            
        Returns:
            True if extension should be ignored
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check if path ends with any ignored extension
        for ext in self.ignored_extensions:
            if path.endswith(ext.lower()):
                return True
        
        return False
    
    def is_allowed_domain(self, url: str) -> bool:
        """
        Check if URL domain is in allowed domains list.
        
        Args:
            url: URL to check
            
        Returns:
            True if domain is allowed (or no whitelist configured)
        """
        # If no whitelist, allow all domains
        if not self.allowed_domains:
            return True
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Check if domain matches any allowed domain
        for allowed in self.allowed_domains:
            allowed_lower = allowed.lower()
            # Remove 'www.' prefix for comparison
            allowed_clean = allowed_lower[4:] if allowed_lower.startswith('www.') else allowed_lower
            domain_clean = domain[4:] if domain.startswith('www.') else domain
            
            # Exact match
            if domain_clean == allowed_clean:
                return True
            
            # Subdomain match: domain must end with '.' + allowed_domain
            # e.g., 'sub.example.com' matches 'example.com'
            if domain_clean.endswith('.' + allowed_clean):
                return True
        
        return False
    
    def matches_deny_pattern(self, url: str) -> bool:
        """
        Check if URL matches any deny pattern.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL matches a deny pattern
        """
        for pattern in self.compiled_patterns:
            if isinstance(pattern, re.Pattern):
                # Regex pattern
                if pattern.search(url):
                    return True
            else:
                # Substring pattern
                if pattern.lower() in url.lower():
                    return True
        
        return False
