"""URL Manager: Handles normalization, deduplication, and queue management."""

from collections import deque
from urllib.parse import urlparse, urlunparse, urljoin
from typing import Optional, Tuple


class URLManager:
    """Manages URL normalization, deduplication, and crawling queue."""
    
    def __init__(self):
        """Initialize URL manager with empty queue and visited set."""
        self.queue: deque = deque()  # Queue of (url, source_url, depth) tuples
        self.visited: set = set()  # Set of normalized URLs that have been visited
        self.discovered: set = set()  # Set of all discovered URLs (for stats)
        self.stats = {
            'queued': 0,
            'visited': 0,
            'discovered': 0,
        }
    
    def normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        Normalize URL according to specification.
        
        - Resolve relative URLs to absolute if base_url provided
        - Remove fragments (#section)
        - Normalize trailing slashes (keep as-is for now, but ensure consistency)
        - Normalize scheme and hostname casing (lowercase)
        
        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Normalized absolute URL
        """
        # Resolve relative URLs
        if base_url:
            url = urljoin(base_url, url)
        
        # Parse URL
        parsed = urlparse(url)
        
        # Normalize scheme and hostname to lowercase
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove fragment
        fragment = ''
        
        # Reconstruct URL without fragment
        normalized = urlunparse((
            scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            fragment
        ))
        
        return normalized
    
    def add_to_queue(self, url: str, source_url: str, depth: int) -> bool:
        """
        Add URL to queue if not already visited.
        
        Args:
            url: URL to add
            source_url: URL where this link was discovered
            depth: Depth from seed URL
            
        Returns:
            True if URL was added, False if already visited
        """
        normalized = self.normalize_url(url, source_url if source_url else None)
        
        # Check if already visited
        if normalized in self.visited:
            return False
        
        # Check if already in queue (avoid duplicates in queue)
        if normalized in self.discovered:
            return False
        
        # Add to queue and discovered set
        self.queue.append((normalized, source_url, depth))
        self.discovered.add(normalized)
        self.stats['queued'] += 1
        self.stats['discovered'] += 1
        
        return True
    
    def get_next_url(self) -> Optional[Tuple[str, str, int]]:
        """
        Get next URL from queue (BFS order).
        
        Returns:
            Tuple of (url, source_url, depth) or None if queue is empty
        """
        if not self.queue:
            return None
        
        url, source_url, depth = self.queue.popleft()
        return url, source_url, depth
    
    def mark_visited(self, url: str) -> None:
        """
        Mark URL as visited.
        
        Args:
            url: URL to mark as visited
        """
        normalized = self.normalize_url(url)
        if normalized not in self.visited:
            self.visited.add(normalized)
            self.stats['visited'] += 1
    
    def is_visited(self, url: str) -> bool:
        """
        Check if URL has been visited.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL has been visited
        """
        normalized = self.normalize_url(url)
        return normalized in self.visited
    
    def get_stats(self) -> dict:
        """
        Get crawl statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            **self.stats,
            'queue_size': len(self.queue),
            'visited_count': len(self.visited),
            'discovered_count': len(self.discovered),
        }
    
    def queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
    
    def has_urls(self) -> bool:
        """Check if there are URLs in the queue."""
        return len(self.queue) > 0
