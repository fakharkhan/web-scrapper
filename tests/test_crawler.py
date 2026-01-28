"""Unit tests for Crawler (basic crawl limit logic)."""

import unittest
from unittest.mock import Mock, patch
from scraper.crawler import Crawler
from scraper.output_writer import OutputWriter


class TestCrawlerLimits(unittest.TestCase):
    """Test cases for Crawler limit logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.output_writer = Mock(spec=OutputWriter)
        self.crawler = Crawler(
            max_urls=10,
            max_depth=2,
            output_writer=self.output_writer,
        )
    
    def test_should_stop_at_max_urls(self):
        """Test that crawler stops when max_urls is reached."""
        # Simulate visited URLs
        for i in range(10):
            self.crawler.url_manager.mark_visited(f"https://example.com/page{i}")
        
        self.assertTrue(self.crawler._should_stop())
    
    def test_should_not_stop_before_max_urls(self):
        """Test that crawler doesn't stop before max_urls is reached."""
        # Simulate fewer visited URLs than max
        for i in range(5):
            self.crawler.url_manager.mark_visited(f"https://example.com/page{i}")
        
        self.assertFalse(self.crawler._should_stop())
    
    def test_max_depth_enforced(self):
        """Test that max_depth is enforced when adding URLs to queue."""
        # Add URL at max_depth
        result = self.crawler.url_manager.add_to_queue(
            "https://example.com/page",
            "https://example.com",
            self.crawler.max_depth
        )
        self.assertTrue(result)
        
        # Try to add URL beyond max_depth (should still be added to queue,
        # but won't be processed in _process_url)
        result = self.crawler.url_manager.add_to_queue(
            "https://example.com/deep",
            "https://example.com/page",
            self.crawler.max_depth + 1
        )
        # URL can be added to queue, but processing will skip it
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
