# Fixing Empty Markdown Content

## Problem

If your markdown file has the title and metadata but no actual content, it's likely because the website is a **Single Page Application (SPA)** that loads content via JavaScript.

## Solution

Use the `--use-browser` flag to render JavaScript:

```bash
python main.py --to-markdown https://softpyramid.com --use-browser
```

## Why This Happens

Modern websites (especially React, Vue, Angular apps) often:
1. Load a minimal HTML shell from the server
2. Execute JavaScript to fetch and render the actual content
3. Display content only after JavaScript runs

When you fetch the page with `requests` (static HTML), you only get the shell, not the rendered content.

## How to Identify

Signs that you need browser mode:
- ✅ Title is extracted correctly
- ✅ Metadata is present
- ❌ Content is empty or minimal
- ❌ Only sees basic HTML structure

## Examples

### Without Browser (Static HTML)
```bash
python main.py --to-markdown https://softpyramid.com
```
**Result**: Empty content (only title/metadata)

### With Browser (JavaScript Rendering)
```bash
python main.py --to-markdown https://softpyramid.com --use-browser
```
**Result**: Full content with all text, links, and formatting

## Installation

If you haven't installed Playwright yet:

```bash
pip install playwright
playwright install chromium
```

## Other Improvements

The converter now:
- Detects when content is empty
- Warns you if it might be a SPA
- Provides fallback text extraction
- Shows helpful messages in the output

## Troubleshooting

### Still Empty After Using Browser?

1. **Increase timeout**: Some pages load slowly
   ```bash
   python main.py --to-markdown https://example.com --use-browser --timeout 60
   ```

2. **Check if page requires authentication**: The scraper doesn't handle login

3. **Verify the URL**: Make sure the URL is accessible

4. **Check logs**: Look for error messages in the output

### Browser Mode Not Working?

1. **Install Playwright**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Check installation**:
   ```bash
   playwright --version
   ```

3. **Try different browser**:
   ```bash
   playwright install firefox
   ```

## Best Practice

For modern websites, always use browser mode:

```bash
python main.py --to-markdown <URL> --use-browser
```

This ensures you get the full rendered content, not just the HTML shell.
