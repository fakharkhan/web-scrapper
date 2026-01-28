"""Unit tests for URL Filter."""

import unittest
from scraper.filters import URLFilter


class TestURLFilter(unittest.TestCase):
    """Test cases for URLFilter."""
    
    def test_should_ignore_scheme_mailto(self):
        """Test that mailto: scheme is ignored."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_scheme("mailto:test@example.com"))
    
    def test_should_ignore_scheme_tel(self):
        """Test that tel: scheme is ignored."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_scheme("tel:+1234567890"))
    
    def test_should_ignore_scheme_javascript(self):
        """Test that javascript: scheme is ignored."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_scheme("javascript:void(0)"))
    
    def test_should_ignore_scheme_http_allowed(self):
        """Test that http: scheme is allowed."""
        filter_obj = URLFilter()
        self.assertFalse(filter_obj.should_ignore_scheme("http://example.com"))
    
    def test_should_ignore_scheme_https_allowed(self):
        """Test that https: scheme is allowed."""
        filter_obj = URLFilter()
        self.assertFalse(filter_obj.should_ignore_scheme("https://example.com"))
    
    def test_should_ignore_extension_pdf(self):
        """Test that .pdf extension is ignored."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_extension("https://example.com/file.pdf"))
    
    def test_should_ignore_extension_jpg(self):
        """Test that .jpg extension is ignored."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_extension("https://example.com/image.jpg"))
    
    def test_should_ignore_extension_case_insensitive(self):
        """Test that extension checking is case insensitive."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.should_ignore_extension("https://example.com/file.PDF"))
    
    def test_is_allowed_domain_no_whitelist(self):
        """Test that all domains are allowed when no whitelist is set."""
        filter_obj = URLFilter()
        self.assertTrue(filter_obj.is_allowed_domain("https://anydomain.com"))
    
    def test_is_allowed_domain_whitelist_match(self):
        """Test that whitelisted domain is allowed."""
        filter_obj = URLFilter(allowed_domains=["example.com"])
        self.assertTrue(filter_obj.is_allowed_domain("https://example.com/page"))
    
    def test_is_allowed_domain_whitelist_subdomain(self):
        """Test that subdomain of whitelisted domain is allowed."""
        filter_obj = URLFilter(allowed_domains=["example.com"])
        self.assertTrue(filter_obj.is_allowed_domain("https://www.example.com/page"))
    
    def test_is_allowed_domain_whitelist_not_match(self):
        """Test that non-whitelisted domain is not allowed."""
        filter_obj = URLFilter(allowed_domains=["example.com"])
        self.assertFalse(filter_obj.is_allowed_domain("https://otherdomain.com/page"))
    
    def test_matches_deny_pattern_regex(self):
        """Test that regex deny patterns work."""
        filter_obj = URLFilter(deny_patterns=[r"/admin/.*"])
        self.assertTrue(filter_obj.matches_deny_pattern("https://example.com/admin/users"))
    
    def test_matches_deny_pattern_substring(self):
        """Test that substring deny patterns work."""
        filter_obj = URLFilter(deny_patterns=["/private/"])
        self.assertTrue(filter_obj.matches_deny_pattern("https://example.com/private/page"))
    
    def test_is_valid_url_passes_all_checks(self):
        """Test that is_valid_url applies all filters."""
        filter_obj = URLFilter()
        # Valid URL should pass
        self.assertTrue(filter_obj.is_valid_url("https://example.com/page"))
    
    def test_is_valid_url_fails_scheme_check(self):
        """Test that is_valid_url fails on invalid scheme."""
        filter_obj = URLFilter()
        self.assertFalse(filter_obj.is_valid_url("mailto:test@example.com"))
    
    def test_is_valid_url_fails_extension_check(self):
        """Test that is_valid_url fails on ignored extension."""
        filter_obj = URLFilter()
        self.assertFalse(filter_obj.is_valid_url("https://example.com/file.pdf"))
    
    def test_is_valid_url_fails_domain_check(self):
        """Test that is_valid_url fails on non-whitelisted domain."""
        filter_obj = URLFilter(allowed_domains=["example.com"])
        self.assertFalse(filter_obj.is_valid_url("https://otherdomain.com/page"))
    
    def test_is_valid_url_fails_deny_pattern(self):
        """Test that is_valid_url fails on deny pattern match."""
        filter_obj = URLFilter(deny_patterns=["/private/"])
        self.assertFalse(filter_obj.is_valid_url("https://example.com/private/page"))


if __name__ == '__main__':
    unittest.main()
