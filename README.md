# ICMR STW Crawler

A specialized web crawler designed to download **Standard Treatment Workflow (STW)** PDF documents from the [ICMR website](https://www.icmr.gov.in/).

## Features

- **Targeted Crawling**: Recursively scans the ICMR website starting from the STW section.
- **Smart Filtering**: Specifically downloads only STW-related PDFs, filtering out circulars, tenders, and other irrelevant documents.
- **Metadata Generation**: Creates a JSON metadata file for each downloaded PDF, containing the source URL and timestamp.
- **Resilient**: Handles network timeouts, duplicate URLs, and invalid links gracefully.

## Prerequisites

- Python 3.8 or higher

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Devaguru11/icmr-stw-crawler.git
   cd icmr-stw-crawler
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the crawler using the following command:

```bash
python src/crawler.py
```
This might take 1-2 min to start saving the files into `data/`

## Output Structure

The crawler organizes the output in the `data/` directory:

- `data/downloads/`: Contains the downloaded PDF files.
- `data/metadata/`: Contains corresponding JSON metadata files for each PDF.
- `crawler.log`: Logs of the crawling process.

## Configuration

You can adjust configuration variables in `src/crawler.py` if needed:

- `START_URL`: Entry point for the crawler.
- `MAX_PAGES`: Maximum number of pages to crawl (Safety limit).
- `MIN_FILE_SIZE`: Minimum size of PDFs to download (default: 50KB).
