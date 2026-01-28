# Link-Only Web Scraper

A link-only web scraper (crawler) that starts from one or more seed URLs and collects hyperlinks only, without scraping page content. The system crawls efficiently, safely, and deterministically, stopping based on configurable limits.

## Features

- **Link-only extraction**: Collects only hyperlinks, no page content
- **Dual crawl limits**: Supports both max URLs (required) and max depth (default: 3)
- **URL normalization**: Removes fragments, normalizes casing, resolves relative URLs
- **Smart filtering**: Filters by domain, file extensions, deny patterns
- **Rate limiting**: Configurable requests per second to be polite to servers
- **Robots.txt support**: Respects robots.txt by default
- **Multiple output formats**: CSV, JSON, or SQLite
- **Incremental writing**: Output is written as URLs are discovered
- **Concurrent crawling**: Configurable concurrent requests for performance
- **SPA Support**: Optional browser mode (Playwright) for JavaScript-rendered pages and Single Page Applications
- **Markdown Conversion**: Convert any web page to Markdown format (supports both static and JavaScript-rendered pages)
- **Organized Output**: Files are automatically organized into domain-based folders for easy management

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone or navigate to the project directory:
```bash
cd web-scrapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) For SPA/JavaScript support, install Playwright:
```bash
pip install playwright
playwright install chromium
```

Note: `html2text` is automatically installed for markdown conversion support.

## Usage

### Basic Usage

```bash
python main.py --seed-urls https://example.com --max-urls 100
```

### With Depth Limit

```bash
python main.py --seed-urls https://example.com --max-urls 100 --max-depth 2
```

### With Domain Restriction

```bash
python main.py --seed-urls https://example.com --max-urls 100 --allowed-domains example.com
```

### Multiple Seed URLs

```bash
python main.py --seed-urls https://example.com,https://example.org --max-urls 200
```

### JSON Output

```bash
python main.py --seed-urls https://example.com --max-urls 100 --output-format JSON --output-file links.json
```

### SQLite Output

```bash
python main.py --seed-urls https://example.com --max-urls 100 --output-format SQLite --output-file links.db
```

### SPA/JavaScript Support

For Single Page Applications (React, Vue, Angular) that render content via JavaScript:

```bash
python main.py --seed-urls https://example-spa.com --max-urls 100 --use-browser
```

See [SPA Support Documentation](docs/spa-support.md) for detailed information.

### Markdown Conversion

Convert any web page to Markdown format:

```bash
# Basic conversion
python main.py --to-markdown https://example.com/article

# With browser mode (for SPAs)
python main.py --to-markdown https://spa-site.com --use-browser

# Specify output file
python main.py --to-markdown https://example.com/article --output-file article.md
```

The converter extracts:
- Page title
- Text content
- Links (preserved as markdown links)
- Images (preserved as markdown images)
- Headings, lists, and other formatting

Output includes metadata (source URL, title) and the converted content in clean Markdown format.

## Command-Line Arguments

### Required Arguments

- `--seed-urls`: Comma-separated list of seed URLs to start crawling from
- `--max-urls`: Maximum number of URLs to collect (n - Mode A)

### Optional Arguments

- `--max-depth`: Maximum crawl depth from seed URLs (default: 3) - Mode B
- `--allowed-domains`: Comma-separated list of allowed domains (whitelist)
- `--deny-patterns`: Comma-separated list of regex patterns or substrings to deny
- `--max-concurrent`: Maximum concurrent requests (default: 5)
- `--timeout`: Request timeout in seconds (default: 10)
- `--rate-limit`: Global requests per second (default: 1.0)
- `--user-agent`: Custom user agent string (default: WebScraper/1.0)
- `--respect-robots`: Respect robots.txt (default: True)
- `--no-respect-robots`: Do not respect robots.txt
- `--follow-redirects`: Follow HTTP redirects (default: True)
- `--no-follow-redirects`: Do not follow HTTP redirects
- `--output-format`: Output format - CSV, JSON, or SQLite (default: CSV)
- `--output-file`: Output file path (default: output.csv/json/db based on format)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--use-browser`: Use browser (Playwright) to render JavaScript for SPAs (default: False). Requires: `pip install playwright && playwright install`
- `--browser-wait-for`: What to wait for when using browser - load, domcontentloaded, networkidle, or commit (default: networkidle)

## Understanding Crawl Limits

The scraper supports two crawl limit modes:

### Mode A: Max URLs (Required)

The `--max-urls` parameter sets the maximum number of unique URLs to collect. The crawler stops when this limit is reached.

**Example:**
```bash
python main.py --seed-urls https://example.com --max-urls 50
```
This will collect up to 50 unique URLs and then stop.

### Mode B: Max Depth (Optional, Default: 3)

The `--max-depth` parameter sets the maximum crawl depth from seed URLs. Depth 0 is the seed URL itself, depth 1 is links found on seed URLs, depth 2 is links found on depth 1 pages, etc.

**Example:**
```bash
python main.py --seed-urls https://example.com --max-urls 1000 --max-depth 2
```
This will crawl up to depth 2 (seed → links on seed → links on those pages) but will stop if 1000 URLs are collected first.

### Combined Limits

If both limits are set, crawling stops when **either** condition is met:
- Maximum URLs collected, OR
- Maximum depth reached

## Output Organization

All output files are automatically organized into domain-based folders:

```
output/
├── example.com/
│   ├── example.com.csv
│   ├── article-page.md
│   └── ...
├── other-domain.com/
│   ├── other-domain.com.json
│   └── ...
└── ...
```

This makes it easy to:
- Keep files organized by domain
- Find files for specific websites
- Manage multiple crawls without file conflicts
- Clean up old crawls by domain

You can customize the base output directory with `--output-dir`:

```bash
python main.py --seed-urls https://example.com --max-urls 100 --output-dir my-outputs
```

## Output Format

### CSV Format

The CSV output includes the following columns:
- `url`: Discovered URL
- `source_url`: URL where this link was found
- `depth`: Depth from seed URL (0 = seed)
- `timestamp`: ISO format timestamp when URL was discovered
- `status_code`: HTTP status code (if available)
- `redirect_target`: Final URL after redirects (if applicable)

### JSON Format

The JSON output is an array of objects with the same fields as CSV:
```json
[
  {
    "url": "https://example.com/page",
    "source_url": "https://example.com",
    "depth": 1,
    "timestamp": "2026-01-27T10:30:00.123456",
    "status_code": 200
  }
]
```

### SQLite Format

The SQLite database contains a `links` table with columns:
- `url` (PRIMARY KEY)
- `source_url`
- `depth`
- `timestamp`
- `status_code`
- `redirect_target`

## Filtering

### Domain Filtering

Only crawl URLs from specified domains:
```bash
python main.py --seed-urls https://example.com --max-urls 100 --allowed-domains example.com,www.example.com
```

### Deny Patterns

Exclude URLs matching patterns (regex or substring):
```bash
python main.py --seed-urls https://example.com --max-urls 100 --deny-patterns "/admin/.*,/private/"
```

### Automatic Filtering

The scraper automatically filters out:
- Non-HTTP(S) schemes (mailto:, tel:, javascript:, etc.)
- Common file extensions (.pdf, .jpg, .png, .zip, etc.)

## Examples

### Example 1: Basic Crawl

```bash
python main.py \
  --seed-urls https://example.com \
  --max-urls 100 \
  --max-depth 3 \
  --output-format CSV \
  --output-file example_links.csv
```

### Example 2: Fast Crawl with Higher Concurrency

```bash
python main.py \
  --seed-urls https://example.com \
  --max-urls 500 \
  --max-concurrent 10 \
  --rate-limit 2.0 \
  --timeout 5
```

### Example 3: Restricted Domain Crawl

```bash
python main.py \
  --seed-urls https://example.com \
  --max-urls 200 \
  --allowed-domains example.com \
  --deny-patterns "/api/.*,/admin/.*" \
  --output-format JSON
```

## Testing

Run unit tests:

```bash
python -m pytest tests/
```

Or using unittest:

```bash
python -m unittest discover tests
```

## Project Structure

```
web-scrapper/
├── scraper/
│   ├── __init__.py
│   ├── url_manager.py          # URL normalization, deduplication, queue
│   ├── crawler.py              # Main crawler engine
│   ├── filters.py              # URL filtering logic
│   ├── rate_limiter.py         # Rate limiting per domain/global
│   ├── robots_checker.py       # robots.txt validation
│   ├── output_writer.py        # CSV/JSON/SQLite writers
│   └── logger.py               # Logging configuration
├── tests/
│   ├── test_url_manager.py
│   ├── test_filters.py
│   ├── test_crawler.py
│   └── test_output_writer.py
├── main.py                     # CLI entry point
├── requirements.txt
└── README.md
```

## Error Handling

The scraper handles errors gracefully:
- **Network errors**: Logged and skipped, crawl continues
- **4xx/5xx responses**: Logged with status code, marked as visited
- **Timeouts**: Logged and skipped
- **Invalid HTML**: Parsed with best effort, links extracted where possible
- **Redirect loops**: Detected and handled by requests library

## Performance

- Handles 10,000+ URLs efficiently
- Configurable concurrency for I/O-bound operations
- Incremental output writing prevents data loss
- Memory-efficient queue and visited set management

## Limitations

- Only processes publicly accessible pages (no authentication)
- Only extracts links from HTML (no JavaScript-rendered content)
- Does not download files (PDFs, images, etc.)
- Does not bypass CAPTCHAs

## License

This project is provided as-is for educational and development purposes.

## Sample Output

### CSV Sample

```csv
url,source_url,depth,timestamp,status_code,redirect_target
https://example.com/page1,https://example.com,1,2026-01-27T10:30:00.123456,200,
https://example.com/page2,https://example.com,1,2026-01-27T10:30:01.234567,200,
https://example.com/sub/page,https://example.com/page1,2,2026-01-27T10:30:02.345678,200,
```

### JSON Sample

```json
[
  {
    "url": "https://example.com/page1",
    "source_url": "https://example.com",
    "depth": 1,
    "timestamp": "2026-01-27T10:30:00.123456",
    "status_code": 200
  },
  {
    "url": "https://example.com/page2",
    "source_url": "https://example.com",
    "depth": 1,
    "timestamp": "2026-01-27T10:30:01.234567",
    "status_code": 200
  }
]
```
