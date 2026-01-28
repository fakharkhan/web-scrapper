"""Unit tests for URL Manager."""

import unittest
from scraper.url_manager import URLManager


class TestURLManager(unittest.TestCase):
    """Test cases for URLManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = URLManager()
    
    def test_normalize_url_removes_fragment(self):
        """Test that URL normalization removes fragments."""
        url = "https://example.com/page#section"
        normalized = self.manager.normalize_url(url)
        self.assertEqual(normalized, "https://example.com/page")
    
    def test_normalize_url_lowercases_scheme(self):
        """Test that URL normalization lowercases scheme."""
        url = "HTTPS://example.com/page"
        normalized = self.manager.normalize_url(url)
        self.assertEqual(normalized, "https://example.com/page")
    
    def test_normalize_url_lowercases_hostname(self):
        """Test that URL normalization lowercases hostname."""
        url = "https://EXAMPLE.COM/page"
        normalized = self.manager.normalize_url(url)
        self.assertEqual(normalized, "https://example.com/page")
    
    def test_normalize_url_resolves_relative(self):
        """Test that relative URLs are resolved with base URL."""
        url = "/page"
        base = "https://example.com"
        normalized = self.manager.normalize_url(url, base)
        self.assertEqual(normalized, "https://example.com/page")
    
    def test_add_to_queue_adds_url(self):
        """Test that URLs are added to queue."""
        result = self.manager.add_to_queue("https://example.com", "", 0)
        self.assertTrue(result)
        self.assertEqual(self.manager.queue_size(), 1)
    
    def test_add_to_queue_deduplicates(self):
        """Test that duplicate URLs are not added to queue."""
        self.manager.add_to_queue("https://example.com", "", 0)
        result = self.manager.add_to_queue("https://example.com", "", 0)
        self.assertFalse(result)
        self.assertEqual(self.manager.queue_size(), 1)
    
    def test_add_to_queue_normalizes_before_deduplication(self):
        """Test that URLs are normalized before deduplication."""
        self.manager.add_to_queue("https://example.com/page", "", 0)
        # Same URL with fragment should not be added
        result = self.manager.add_to_queue("https://example.com/page#section", "", 0)
        self.assertFalse(result)
        self.assertEqual(self.manager.queue_size(), 1)
    
    def test_get_next_url_returns_bfs_order(self):
        """Test that get_next_url returns URLs in BFS order."""
        self.manager.add_to_queue("https://example.com/1", "", 0)
        self.manager.add_to_queue("https://example.com/2", "", 0)
        
        url1, _, _ = self.manager.get_next_url()
        url2, _, _ = self.manager.get_next_url()
        
        self.assertEqual(url1, "https://example.com/1")
        self.assertEqual(url2, "https://example.com/2")
    
    def test_mark_visited_tracks_visited_urls(self):
        """Test that mark_visited tracks visited URLs."""
        url = "https://example.com"
        self.manager.mark_visited(url)
        self.assertTrue(self.manager.is_visited(url))
    
    def test_is_visited_normalizes_url(self):
        """Test that is_visited normalizes URL before checking."""
        self.manager.mark_visited("https://example.com/page")
        # Should find visited even with fragment
        self.assertTrue(self.manager.is_visited("https://example.com/page#section"))
    
    def test_get_stats_returns_correct_stats(self):
        """Test that get_stats returns correct statistics."""
        self.manager.add_to_queue("https://example.com/1", "", 0)
        self.manager.add_to_queue("https://example.com/2", "", 0)
        self.manager.mark_visited("https://example.com/1")
        
        stats = self.manager.get_stats()
        
        self.assertEqual(stats['discovered_count'], 2)
        self.assertEqual(stats['visited_count'], 1)
        self.assertEqual(stats['queue_size'], 1)


if __name__ == '__main__':
    unittest.main()
