# Web Crawler Project

## Overview
A Python-based web crawler that crawls a seed domain, discovers outbound links, and saves them to organized text files locally.

## Project Structure
- `crawler.py`: Main crawler script with CLI interface
- `crawled_links/`: Output directory for discovered links (created automatically)
- `README.md`: Usage documentation

## Recent Changes
- **October 19, 2025**: Initial project setup
  - Installed Python 3.11 with requests and beautifulsoup4
  - Created web crawler with domain-focused crawling logic
  - Implemented polite crawling with configurable delays
  - Added comprehensive error handling and progress tracking
  - Created output system for categorized link files

## Usage
Run the crawler with:
```bash
python crawler.py <seed_url> [options]
```

Example:
```bash
python crawler.py https://example.com --max-pages 50 --delay 1.0
```

## Dependencies
- Python 3.11
- requests: HTTP requests
- beautifulsoup4: HTML parsing

## Architecture
- **WebCrawler class**: Core crawling logic
  - URL normalization and validation
  - Domain-aware link filtering
  - BFS-based crawling queue
  - Error-tolerant page fetching
  - Link extraction and categorization
  
- **Output files**:
  - `all_links.txt`: All discovered links
  - `internal_links.txt`: Same-domain links
  - `external_links.txt`: Outbound links
  - `visited_pages.txt`: Crawled pages
  - `link_sources.txt`: Link provenance tracking
