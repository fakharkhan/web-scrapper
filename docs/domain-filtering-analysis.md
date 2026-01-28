# Domain Filtering Analysis & Improvements

## Problem Analysis

### Issue Identified

The scraper was crawling **external URLs** (like `fonts.bunny.net`, `bunny.net`, `docs.bunny.net`) when the intention was to only crawl **internal URLs** from the seed domain (`softpyramid.dev`).

### Root Cause

1. **Default Behavior**: The crawler allowed ALL domains by default
   - In `scraper/filters.py`, the `is_allowed_domain()` method returns `True` when `allowed_domains` is empty
   - This means if `--allowed-domains` is not specified, the crawler follows links to any domain

2. **What Happened in Your Crawl**:
   ```
   Seed: https://softpyramid.dev (depth 0)
   ↓
   Found: https://fonts.bunny.net (depth 1) - EXTERNAL
   ↓
   Crawled fonts.bunny.net → found bunny.net links (depth 2)
   ↓
   Crawled bunny.net → found more bunny.net links (depth 3)
   ```

3. **Result**: 116 URLs scraped, but only ~13 are from `softpyramid.dev`. The rest are from external domains.

## Solution Implemented

### 1. Auto-Detect Seed Domain (Default Behavior)

**New Default**: The scraper now **automatically restricts crawling to the seed domain(s)** by default.

- Extracts domain(s) from seed URLs automatically
- Uses them as `allowed_domains` if `--allowed-domains` is not specified
- Logs the auto-detected domains for transparency

**Example**:
```bash
python main.py --seed-urls https://softpyramid.dev --max-urls 100
# Now automatically restricts to softpyramid.dev only
```

### 2. New `--allow-external` Flag

Added a flag to explicitly allow external domain crawling when needed:

```bash
# Allow external domains (old behavior)
python main.py --seed-urls https://softpyramid.dev --max-urls 100 --allow-external
```

### 3. Improved Domain Matching

Enhanced domain matching logic to:
- Handle `www.` prefix correctly
- Support subdomains properly (e.g., `sub.example.com` matches `example.com`)
- More robust domain extraction

## Usage Examples

### Internal-Only Crawling (Default - Recommended)
```bash
# Automatically restricts to softpyramid.dev
python main.py --seed-urls https://softpyramid.dev --max-urls 100 --max-depth 3
```

### Allow External Domains
```bash
# Crawl external domains too
python main.py --seed-urls https://softpyramid.dev --max-urls 100 --allow-external
```

### Custom Domain Whitelist
```bash
# Specify multiple allowed domains
python main.py --seed-urls https://softpyramid.dev --max-urls 100 \
  --allowed-domains softpyramid.dev,www.softpyramid.dev
```

## Expected Behavior After Fix

With the default behavior (internal-only):

1. **Seed URL**: `https://softpyramid.dev` (depth 0)
2. **Finds**: Links on softpyramid.dev page
3. **Filters Out**: 
   - `https://fonts.bunny.net` ❌ (external)
   - `https://bunny.net` ❌ (external)
4. **Crawls Only**: 
   - `https://softpyramid.dev/*` ✅ (internal)
   - `https://www.softpyramid.dev/*` ✅ (subdomain of seed)

## Benefits

1. **Predictable Behavior**: By default, only crawls the seed domain
2. **Efficient**: Doesn't waste time/resources on external sites
3. **Focused Results**: Output contains only relevant internal links
4. **Flexible**: Can still allow external domains when needed with `--allow-external`
5. **Transparent**: Logs auto-detected domains so you know what's being restricted

## Migration Guide

### Old Behavior (Before Fix)
```bash
# This crawled ALL domains
python main.py --seed-urls https://softpyramid.dev --max-urls 100
```

### New Behavior (After Fix)
```bash
# This crawls ONLY softpyramid.dev (default)
python main.py --seed-urls https://softpyramid.dev --max-urls 100

# To get old behavior (all domains):
python main.py --seed-urls https://softpyramid.dev --max-urls 100 --allow-external
```

## Technical Details

### Domain Extraction Logic

The `extract_domain()` function:
- Parses URL using `urllib.parse`
- Extracts `netloc` (domain + port)
- Removes port if present
- Removes `www.` prefix for cleaner matching
- Returns lowercase domain

### Domain Matching Logic

The `is_allowed_domain()` function now:
- Handles `www.` prefix normalization
- Supports exact domain matches
- Supports subdomain matches (e.g., `sub.example.com` matches `example.com`)
- Case-insensitive matching

## Recommendations

1. **Use default behavior** (internal-only) for most use cases
2. **Specify `--allowed-domains`** if you need multiple specific domains
3. **Use `--allow-external`** only when you explicitly need to crawl external sites
4. **Monitor logs** to see which domains are being auto-detected and filtered
