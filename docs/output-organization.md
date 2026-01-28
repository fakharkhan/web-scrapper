# Output Organization by Domain

## Overview

The scraper now automatically organizes all output files into domain-based folders for better file management and organization.

## Directory Structure

All output files are organized as follows:

```
output/
├── example.com/
│   ├── example.com.csv          # Link scraping results
│   ├── example.com.json         # Alternative format
│   ├── article-page.md          # Markdown conversions
│   └── ...
├── softpyramid.dev/
│   ├── softpyramid.dev.csv
│   └── ...
└── other-domain.com/
    └── ...
```

## Benefits

1. **Easy Organization**: Files are automatically grouped by domain
2. **No Conflicts**: Multiple crawls of the same domain don't overwrite each other (unless using same filename)
3. **Easy Cleanup**: Delete entire domain folders to remove all related files
4. **Better Navigation**: Quickly find files for specific websites
5. **Scalability**: Works well even with hundreds of domains

## How It Works

### Link Scraping

When you run:
```bash
python main.py --seed-urls https://example.com --max-urls 100
```

The output file is automatically created at:
```
output/example.com/example.com.csv
```

### Markdown Conversion

When you run:
```bash
python main.py --to-markdown https://example.com/article
```

The markdown file is created at:
```
output/example.com/article.md
```

The filename is derived from the URL path, making it easy to identify the source page.

### Custom Output Directory

You can specify a different base directory:

```bash
python main.py --seed-urls https://example.com --max-urls 100 --output-dir my-crawls
```

This creates:
```
my-crawls/example.com/example.com.csv
```

### Custom Output File

If you specify `--output-file`, the file is saved exactly where you specify, but the parent directory is still created if needed:

```bash
python main.py --seed-urls https://example.com --max-urls 100 --output-file custom/path/file.csv
```

## File Naming

### Link Scraping Files

- Format: `<domain>.<extension>`
- Examples:
  - `example.com.csv`
  - `example.com.json`
  - `example.com.db`

### Markdown Files

- Format: `<url-path>.md` or `<domain>.md` for root pages
- Examples:
  - `article.md` (from `/article`)
  - `blog_post_2024.md` (from `/blog/post-2024`)
  - `example.com.md` (from root `/`)

## Multiple Domains

When crawling multiple domains in one session, each domain gets its own folder:

```bash
python main.py --seed-urls https://example.com,https://other.com --max-urls 100
```

Creates:
```
output/
├── example.com/
│   └── example.com.csv
└── other.com/
    └── other.com.csv
```

## Implementation Details

- Folders are created automatically when needed
- Domain names are sanitized for filesystem compatibility
- Invalid characters (like `/`, `\`, `:`) are replaced with `_`
- The `www.` prefix is removed for cleaner folder names
- All parent directories are created recursively

## Migration

If you have existing output files in the root directory, they will remain there. New files will be organized into domain folders automatically.

To migrate existing files, you can manually move them:
```bash
mkdir -p output/example.com
mv example.com.csv output/example.com/
```

## Best Practices

1. **Use default organization**: Let the scraper organize files automatically
2. **Use `--output-dir` for projects**: Organize different projects into separate base directories
3. **Keep domain folders**: Don't manually reorganize - the structure is designed for easy management
4. **Clean up by domain**: Delete entire domain folders when no longer needed

## Examples

### Basic Usage
```bash
# Creates: output/example.com/example.com.csv
python main.py --seed-urls https://example.com --max-urls 100
```

### Custom Directory
```bash
# Creates: my-data/example.com/example.com.csv
python main.py --seed-urls https://example.com --max-urls 100 --output-dir my-data
```

### Markdown with Organization
```bash
# Creates: output/example.com/article.md
python main.py --to-markdown https://example.com/article
```

### Multiple Formats
```bash
# Creates: output/example.com/example.com.csv
python main.py --seed-urls https://example.com --max-urls 100 --output-format CSV

# Creates: output/example.com/example.com.json
python main.py --seed-urls https://example.com --max-urls 100 --output-format JSON
```

Both files are in the same domain folder, making it easy to compare formats.
