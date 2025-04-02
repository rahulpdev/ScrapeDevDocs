# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-04-02

### Added

- Initial script structure (`scrape_docs.py`) with basic argument parsing (`argparse`).
- Functionality to fetch content from a remote markdown file containing a URL tree.
- URL extraction from the tree structure format.
- Basic URL validation.
- Checklist file generation (`<base_name>_scrape_checklist.md`).
- Basic HTML fetching and parsing (BeautifulSoup, lxml).
- Relative to absolute URL conversion for links (`<a>` tags).
- Structured JSON logging setup (`pythonjsonlogger`).
- Retry logic for URL fetching (`requests.Session`, `urllib3.util.retry`).
- Basic error handling with defined error codes (`dev_docs/error_codes.md`).
- HTML to Markdown conversion using `markdownify`.
- Concurrent URL processing using `threading` and `queue.Queue`.
- Atomic checklist file updates using `threading.Lock`.
- Uniform image handling: Extracts `alt` and absolute `src` for all `<img>` tags, represents as `![alt](url)`, does not download images. Removes `<img>` tags without `src`.
- Terminal progress bar using `tqdm`.
- Output directory structuring (`output_docs/<base_name>_docs/`).
- Base name determination from H1 or domain name.
- Unit tests for image handling (`tests/test_image_handling.py`).
- Flake8 configuration (`.flake8`) with specific ignores.
- Dedicated writer thread and queue (`writer_thread`, `write_queue`) for atomic file saving.
- Command-line arguments for output directory (`--output-dir`), log level (`--log-level`), and number of workers (`--num-workers`).
- Initial `README.md`.
- Initial `CHANGELOG.md` (this file).

### Changed

- **Major:** Refactored image handling to treat all image types uniformly, removing previous SVG-specific conversion logic.
- Simplified logging calls by removing `extra` dict and incorporating info into message strings.
- Refactored concurrency model from direct writes in workers to using a dedicated writer thread/queue.

### Removed

- SVG-to-Mermaid conversion logic and related dependencies (`Mermaid.js CLI`, `svgpathtools`, `svgwrite`).
- Placeholders used for image replacement during HTML processing.

### Fixed

- Various Flake8 indentation errors (E123, E111, E114, E117 - now ignored via config/noqa).
- Pytest failures related to mock usage and placeholder replacement logic.
