# ScrapeDocs

## Overview

ScrapeDocs is a Python script designed to crawl online developer documentation specified in a tree-structure markdown file. It fetches the content from each URL, processes the HTML to preserve structure and handle image links uniformly, and saves the output as structured markdown files locally. It uses concurrency to process multiple URLs efficiently and features a command-line interface.

## Key Features

- Crawls URLs listed in a remote markdown file with a specific tree structure.
- Extracts HTML content from specified URLs.
- Converts HTML content to Markdown, preserving headings and structure.
- Handles all `<img>` tags uniformly: extracts `alt` text and absolute `src` URL, representing them as standard Markdown links (`![alt](url)`). Does **not** download image files.
- Uses threading for concurrent processing of multiple URLs.
- Uses a dedicated write queue for atomic file saving.
- Provides a terminal progress bar during execution.
- Generates a checklist file to track processed URLs.
- Organizes output into a structured directory based on the source site.
- Configurable via command-line arguments (output directory, log level, number of workers).

## Badges

_(Add relevant badges here, e.g., build status, coverage, license)_

## Table of Contents

- [ScrapeDocs](#scrapedocs)
  - [Overview](#overview)
  - [Key Features](#key-features)
  - [Badges](#badges)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [How it Works](#how-it-works)
  - [FAQs](#faqs)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace with actual URL when available
    cd ScrapeDocs
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt # Assumes requirements.txt exists or will be created
    ```
    _(Note: Ensure Python 3.10+ is installed.)_

## Usage

Run the script from the command line, providing the URL to the raw markdown file containing the URL tree structure:

```bash
python scrape_docs.py <url_to_markdown_tree_file> [options]
```

**Required Argument:**

- `tree_url`: The full HTTP/HTTPS URL to the raw text/markdown file containing the list of URLs to scrape, formatted as a tree (e.g., `├── https://...`).

**Optional Arguments:**

- `-o OUTPUT_DIR`, `--output-dir OUTPUT_DIR`: Specify the root directory for output files (checklists and docs folders). Defaults to `output_docs/`.
- `-l LOG_LEVEL`, `--log-level LOG_LEVEL`: Set the logging level. Choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Defaults to `INFO`.
- `-w NUM_WORKERS`, `--num-workers NUM_WORKERS`: Set the number of concurrent worker threads for processing URLs. Defaults to `5`.

**Example:**

```bash
python scrape_docs.py https://raw.githubusercontent.com/user/repo/main/docs_tree.md -o my_scraped_docs -l DEBUG -w 10
```

## How it Works

1.  The script takes a URL pointing to a markdown file as input.
2.  It fetches and parses this file, extracting all valid URLs listed in the specified tree format (`[PREFIX] URL`).
3.  It determines a base name for the website being scraped (from the first URL's H1 tag or domain name).
4.  It creates an output directory structure (`<output_dir>/<base_name>_docs/`) and a checklist file (`<output_dir>/<base_name>_scrape_checklist.md`).
5.  It uses multiple worker threads to concurrently process the extracted URLs:
    - Each worker fetches the HTML content of a URL.
    - It parses the HTML using BeautifulSoup.
    - Relative links (`<a>` hrefs) are converted to absolute URLs.
    - Image tags (`<img>`) are processed to extract `src` and `alt` attributes, convert `src` to absolute URLs, and replace the `<img>` tag with a standard Markdown link (`![alt](url)`). Invalid `<img>` tags (e.g., missing `src`) are removed.
    - The processed HTML body is converted to Markdown using `markdownify`.
    - The final Markdown content (including the source URL) and its target filepath are placed onto a write queue.
6.  A dedicated writer thread reads from the write queue and saves the processed Markdown content to the appropriate file, ensuring atomic writes.
7.  The checklist file is updated atomically as each URL is successfully processed.
8.  A progress bar is displayed in the terminal.

## FAQs

- **Q: Why aren't images downloaded?**
  - A: The requirement is to preserve the _reference_ to the image via its URL and alt text in Markdown format, not to create an offline copy of the images themselves. This keeps the scope focused on text content and avoids large storage requirements.
- **Q: What format must the input file follow?**
  - A: Each line representing a URL to crawl must follow the exact format: `[TREE_PREFIX][SPACE][URL]`, e.g., `├── https://example.com/page`. Lines not matching this are ignored.

## Contributing

_(Add contribution guidelines here if applicable)_

## License

_(Specify the project license here, e.g., MIT License)_
