#!/usr/bin/env python3
"""CLI entry point for the link-only web scraper."""

import argparse
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

from scraper.crawler import Crawler
from scraper.output_writer import OutputWriter
from scraper.logger import setup_logger
from scraper.markdown_converter import MarkdownConverter


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Web scraper: collect hyperlinks or convert URLs to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Link scraping - Basic usage
  python main.py --seed-urls https://example.com --max-urls 100

  # Markdown conversion - Basic
  python main.py --to-markdown https://example.com/article

  # Markdown conversion - With browser (for SPAs)
  python main.py --to-markdown https://spa-site.com --use-browser --output-file article.md
        """
    )
    
    # Markdown conversion mode
    parser.add_argument(
        '--to-markdown',
        help='Convert URL to Markdown format (alternative to link scraping)'
    )
    
    # Link scraping arguments (required if not using --to-markdown)
    parser.add_argument(
        '--seed-urls',
        help='Comma-separated list of seed URLs to start crawling from (required for link scraping)'
    )
    parser.add_argument(
        '--max-urls',
        type=int,
        help='Maximum number of URLs to collect (required for link scraping)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum crawl depth from seed URLs (default: 3)'
    )
    parser.add_argument(
        '--allowed-domains',
        help='Comma-separated list of allowed domains (whitelist). If not specified, auto-detected from seed URLs (internal-only crawling)'
    )
    parser.add_argument(
        '--allow-external',
        action='store_true',
        help='Allow crawling external domains (default: False, only crawl seed domain)'
    )
    parser.add_argument(
        '--deny-patterns',
        help='Comma-separated list of regex patterns or substrings to deny'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Maximum concurrent requests (default: 5)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Global requests per second (default: 1.0)'
    )
    parser.add_argument(
        '--user-agent',
        default='WebScraper/1.0',
        help='User agent string (default: WebScraper/1.0)'
    )
    parser.add_argument(
        '--respect-robots',
        action='store_true',
        default=True,
        help='Respect robots.txt (default: True)'
    )
    parser.add_argument(
        '--no-respect-robots',
        dest='respect_robots',
        action='store_false',
        help='Do not respect robots.txt'
    )
    parser.add_argument(
        '--follow-redirects',
        action='store_true',
        default=True,
        help='Follow HTTP redirects (default: True)'
    )
    parser.add_argument(
        '--no-follow-redirects',
        dest='follow_redirects',
        action='store_false',
        help='Do not follow HTTP redirects'
    )
    parser.add_argument(
        '--output-format',
        choices=['CSV', 'JSON', 'SQLite'],
        default='CSV',
        help='Output format (default: CSV)'
    )
    parser.add_argument(
        '--output-file',
        help='Output file path (default: output/<domain>/<domain>.csv/json/db based on seed URL domain and format)'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Base output directory for organizing files by domain (default: output)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--use-browser',
        action='store_true',
        help='Use browser (Playwright) to render JavaScript for SPAs (default: False). Requires: pip install playwright && playwright install'
    )
    parser.add_argument(
        '--browser-wait-for',
        choices=['load', 'domcontentloaded', 'networkidle', 'commit'],
        default='networkidle',
        help='What to wait for when using browser: load, domcontentloaded, networkidle, or commit (default: networkidle)'
    )
    
    return parser.parse_args()


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name (without port, lowercase)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        # Remove 'www.' prefix for cleaner filenames
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return 'output'


def get_domain_folder(domain: str, base_dir: str = "output") -> str:
    """
    Get domain folder path, creating it if it doesn't exist.
    
    Args:
        domain: Domain name
        base_dir: Base directory for outputs (default: "output")
        
    Returns:
        Domain folder path
    """
    # Sanitize domain name for filesystem (remove invalid characters)
    safe_domain = domain.replace('/', '_').replace('\\', '_').replace(':', '_')
    domain_folder = os.path.join(base_dir, safe_domain)
    
    # Create folder if it doesn't exist
    os.makedirs(domain_folder, exist_ok=True)
    
    return domain_folder


def get_output_file(output_format: str, seed_urls: list = None, user_specified: str = None, base_dir: str = "output") -> str:
    """
    Determine output file path, organized by domain folder.
    
    Args:
        output_format: Output format (CSV, JSON, SQLite)
        seed_urls: List of seed URLs to extract domain from
        user_specified: User-specified output file path
        base_dir: Base directory for outputs (default: "output")
        
    Returns:
        Output file path
    """
    if user_specified:
        # If user specified a path, ensure parent directory exists
        parent_dir = os.path.dirname(user_specified)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        return user_specified
    
    # Extract domain from first seed URL
    domain = 'output'
    if seed_urls:
        domain = extract_domain(seed_urls[0])
        # If multiple seed URLs with different domains, use first domain
        # (we'll organize by primary domain)
    
    # Get domain folder
    domain_folder = get_domain_folder(domain, base_dir)
    
    # File extensions based on format
    extensions = {
        'CSV': '.csv',
        'JSON': '.json',
        'SQLITE': '.db',
    }
    
    extension = extensions.get(output_format, '.csv')
    filename = f"{domain}{extension}"
    
    return os.path.join(domain_folder, filename)


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logger
    logger = setup_logger(args.log_level)
    
    # Check if markdown conversion mode
    if args.to_markdown:
        # Markdown conversion mode
        url = args.to_markdown.strip()
        if not url:
            logger.error("Invalid URL provided for markdown conversion")
            sys.exit(1)
        
        # Determine output file (organized by domain folder)
        if args.output_file:
            output_file = args.output_file
            # Ensure parent directory exists
            parent_dir = os.path.dirname(output_file)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        else:
            domain = extract_domain(url)
            base_dir = getattr(args, 'output_dir', 'output')
            domain_folder = get_domain_folder(domain, base_dir)
            # Generate filename from URL path or use domain
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_part = parsed.path.strip('/').replace('/', '_') or 'index'
            # Limit filename length
            if len(path_part) > 50:
                path_part = path_part[:50]
            filename = f"{path_part}.md" if path_part != 'index' else f"{domain}.md"
            output_file = os.path.join(domain_folder, filename)
        
        # Check if browser mode is needed (warn if not using browser for potential SPA)
        if not args.use_browser:
            logger.warning(
                "Note: If the page is a Single Page Application (SPA) that loads content via JavaScript, "
                "use --use-browser flag to render the full content."
            )
        
        # Initialize markdown converter
        try:
            converter = MarkdownConverter(
                use_browser=args.use_browser,
                timeout=args.timeout if hasattr(args, 'timeout') else 30,
                user_agent=args.user_agent if hasattr(args, 'user_agent') else 'WebScraper/1.0',
                logger=logger,
            )
        except ImportError as e:
            logger.error(f"Failed to initialize markdown converter: {e}")
            logger.error("Install html2text with: pip install html2text")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize markdown converter: {e}")
            sys.exit(1)
        
        # Convert to markdown
        try:
            success = converter.convert_to_markdown_file(url, output_file)
            if success:
                logger.info(f"Successfully converted {url} to {output_file}")
                print(f"\nMarkdown saved to: {output_file}")
            else:
                logger.error(f"Failed to convert {url} to markdown")
                sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Conversion interrupted by user")
        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            sys.exit(1)
        finally:
            converter.close()
        
        return
    
    # Link scraping mode (default)
    if not args.seed_urls or not args.max_urls:
        logger.error("For link scraping, --seed-urls and --max-urls are required")
        logger.error("For markdown conversion, use --to-markdown <URL>")
        sys.exit(1)
    
    # Parse seed URLs
    seed_urls = [url.strip() for url in args.seed_urls.split(',') if url.strip()]
    if not seed_urls:
        logger.error("No valid seed URLs provided")
        sys.exit(1)
    
    # Parse allowed domains
    allowed_domains = None
    if args.allowed_domains:
        # User explicitly specified allowed domains
        allowed_domains = [domain.strip() for domain in args.allowed_domains.split(',') if domain.strip()]
    elif not args.allow_external:
        # Auto-detect domains from seed URLs for internal-only crawling
        allowed_domains = []
        seen_domains = set()
        for seed_url in seed_urls:
            domain = extract_domain(seed_url)
            if domain and domain not in seen_domains:
                allowed_domains.append(domain)
                seen_domains.add(domain)
        if allowed_domains:
            logger.info(f"Auto-detected allowed domains (internal-only crawling): {', '.join(allowed_domains)}")
            logger.info("Use --allow-external to crawl external domains, or --allowed-domains to specify custom domains")
    
    # Parse deny patterns
    deny_patterns = None
    if args.deny_patterns:
        deny_patterns = [pattern.strip() for pattern in args.deny_patterns.split(',') if pattern.strip()]
    
    # Determine output file (based on domain if not user-specified)
    output_file = get_output_file(
        args.output_format, 
        seed_urls, 
        args.output_file,
        base_dir=getattr(args, 'output_dir', 'output')
    )
    
    # Initialize output writer
    try:
        output_writer = OutputWriter(output_file, args.output_format)
        logger.info(f"Output will be written to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to initialize output writer: {e}")
        sys.exit(1)
    
    # Initialize crawler
    try:
        crawler = Crawler(
            max_urls=args.max_urls,
            max_depth=args.max_depth,
            allowed_domains=allowed_domains,
            deny_patterns=deny_patterns,
            max_concurrent=args.max_concurrent,
            timeout=args.timeout,
            rate_limit=args.rate_limit,
            user_agent=args.user_agent,
            respect_robots=args.respect_robots,
            follow_redirects=args.follow_redirects,
            use_browser=args.use_browser,
            browser_wait_for=args.browser_wait_for,
            output_writer=output_writer,
            logger=logger,
        )
    except Exception as e:
        logger.error(f"Failed to initialize crawler: {e}")
        output_writer.close()
        sys.exit(1)
    
    # Run crawler
    try:
        summary = crawler.crawl(seed_urls)
        
        # Print summary
        print("\n" + "="*60)
        print("CRAWL SUMMARY")
        print("="*60)
        print(f"Total Discovered: {summary['total_discovered']}")
        print(f"Total Visited: {summary['total_visited']}")
        print(f"Total Fetched: {summary['total_fetched']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Skipped (robots.txt): {summary['skipped_robots']}")
        print(f"Skipped (filters): {summary['skipped_filter']}")
        print(f"Skipped (non-HTML): {summary['skipped_non_html']}")
        print(f"Max URLs Limit: {summary['max_urls_limit']}")
        print(f"Max Depth Limit: {summary['max_depth_limit']}")
        print(f"Output File: {output_file}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Close output writer
        output_writer.close()
        logger.info("Output file closed")


if __name__ == '__main__':
    main()
