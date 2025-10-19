# Web Crawler

A Python-based web crawler that discovers and saves outbound links from a seed domain.

## Features

- **Domain-focused crawling**: Crawls pages within a seed domain and discovers all linked pages
- **Link discovery**: Extracts and categorizes internal and external links
- **Polite crawling**: Implements delays between requests and proper user-agent headers
- **Error handling**: Gracefully handles timeouts, HTTP errors, and network issues
- **Progress tracking**: Real-time console output showing crawling progress
- **Organized output**: Saves results to multiple categorized files

## Installation

Dependencies are already installed:
- requests
- beautifulsoup4

## Usage

### Basic Usage

```bash
python crawler.py https://example.com
```

### Advanced Options

```bash
# Crawl up to 50 pages with 0.5 second delay
python crawler.py https://example.com --max-pages 50 --delay 0.5

# Save to custom output directory
python crawler.py https://blog.example.com --output my_results
```

### Command-line Arguments

- `seed_url` (required): The starting URL to crawl
- `--max-pages`: Maximum number of pages to crawl (default: 100)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--output`: Output directory for results (default: crawled_links)

## Output Files

The crawler saves results to the output directory with these files:

- `all_links.txt`: All unique links discovered during the crawl
- `internal_links.txt`: Links within the same domain
- `external_links.txt`: Outbound links to other domains
- `visited_pages.txt`: All pages that were actually crawled
- `link_sources.txt`: Shows which pages each link was found on

## Example

```bash
python crawler.py https://example.com --max-pages 20 --delay 1.5
```

This will:
1. Start crawling from https://example.com
2. Visit up to 20 pages on the same domain
3. Wait 1.5 seconds between each request
4. Save all discovered links to the `crawled_links/` directory

## How It Works

1. Starts with the seed URL
2. Fetches the page content
3. Extracts all links from the page
4. Adds internal links (same domain) to the crawl queue
5. Records all links (both internal and external)
6. Repeats until max pages reached or queue is empty
7. Saves all results to organized text files

## Notes

- The crawler only follows links within the same domain
- External links are discovered but not crawled
- Respects the `--delay` setting for polite crawling
- Can be interrupted with Ctrl+C (results will still be saved)
