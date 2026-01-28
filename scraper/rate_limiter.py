"""Rate Limiter: Enforces request rate limits."""

import time
from collections import defaultdict
from threading import Lock
from urllib.parse import urlparse
from typing import Optional


class RateLimiter:
    """Enforces rate limiting per domain and globally."""
    
    def __init__(
        self,
        global_rate_limit: float = 1.0,
        per_domain_rate_limit: Optional[float] = None,
    ):
        """
        Initialize rate limiter.
        
        Args:
            global_rate_limit: Global requests per second
            per_domain_rate_limit: Per-domain requests per second (optional)
        """
        self.global_rate_limit = global_rate_limit
        self.per_domain_rate_limit = per_domain_rate_limit
        
        # Track last request time globally
        self.last_global_request = 0.0
        
        # Track last request time per domain
        self.last_domain_requests: dict = defaultdict(float)
        
        # Lock for thread safety
        self.lock = Lock()
    
    def wait_if_needed(self, url: str) -> None:
        """
        Block until rate limit allows request for this URL.
        
        Args:
            url: URL to check rate limit for
        """
        with self.lock:
            current_time = time.time()
            
            # Calculate minimum time between requests
            global_min_interval = 1.0 / self.global_rate_limit if self.global_rate_limit > 0 else 0
            
            # Check global rate limit
            time_since_global = current_time - self.last_global_request
            if time_since_global < global_min_interval:
                wait_time = global_min_interval - time_since_global
                time.sleep(wait_time)
                current_time = time.time()
            
            # Check per-domain rate limit if configured
            if self.per_domain_rate_limit:
                domain = self._get_domain(url)
                domain_min_interval = 1.0 / self.per_domain_rate_limit
                
                last_domain_request = self.last_domain_requests[domain]
                time_since_domain = current_time - last_domain_request
                
                if time_since_domain < domain_min_interval:
                    wait_time = domain_min_interval - time_since_domain
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # Update timestamps
            self.last_global_request = current_time
            if self.per_domain_rate_limit:
                domain = self._get_domain(url)
                self.last_domain_requests[domain] = current_time
    
    def record_request(self, url: str) -> None:
        """
        Record that a request was made (alternative to wait_if_needed).
        
        This method updates timestamps without blocking.
        Useful if you want to handle rate limiting differently.
        
        Args:
            url: URL that was requested
        """
        with self.lock:
            current_time = time.time()
            self.last_global_request = current_time
            
            if self.per_domain_rate_limit:
                domain = self._get_domain(url)
                self.last_domain_requests[domain] = current_time
    
    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name (lowercase, without port)
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return domain
