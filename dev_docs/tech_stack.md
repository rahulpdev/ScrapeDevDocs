# Technology Stack

## Core Components

1. **HTML Processing**

   - BeautifulSoup4 (v4.12.0)
   - Robust HTML parsing
   - Handles malformed markup
   - XPath-like navigation

- lxml (v4.9.3)
  - Faster parsing backend for BeautifulSoup
  - XPath support for complex queries

2. **HTTP Client & File/Input Processing**

   - Requests (v2.31.0)
     - Simplified HTTP operations
     - Session persistence
     - Automatic retry logic
   - urllib3 (v2.0.7) # Dependency of requests
   - Connection pooling
   - SSL verification

- Standard Python string methods (`split()`, `strip()`) and `urllib.parse`
  - Used for parsing the specific input tree file format (`[TREE_PREFIX][SPACE][URL]`).
  - Extracting URLs line by line.

3. **URL Validation**

   - Python's `urllib.parse` for URL validation and manipulation.
   - Basic validation for input URL format (pointing to the markdown tree file).

4. **Content Conversion**
   - No specific content conversion libraries beyond HTML parsing (BeautifulSoup) and standard Markdown representation.

## Infrastructure

- **Execution Environment**

  - Python 3.10.12
    - Type hint support
    - Pattern matching
    - Performance improvements

- **Error Handling**
  - Structured logging (JSON) with:
    - Severity levels (INFO, WARN, ERROR)
    - Detailed context (e.g., SVG metadata: dimensions, element counts)
    - Performance metrics (e.g., conversion attempt duration)
    - Reference to a defined error code taxonomy (see `dev_docs/error_codes.md`)
  - Sentry.io integration (optional, if needed)
  - Circuit breaker pattern (optional, if needed for external calls)
  - Robust error handling for:
    - Input URL fetching/validation
    - Input file line parsing errors
    - URL extraction/validation errors
    - Content crawling (network, HTML parsing errors via BeautifulSoup)
    - SVG image processing (fetching, custom parser errors, Mermaid CLI errors)
    - File I/O

## Development Tooling

- **Testing**

  - Pytest (v8.0.0)
  - Hypothesis (v6.92.0)
  - Coverage.py (v7.3.2)

- **Code Quality**
  - Black (v23.12.0)
  - Flake8 (v6.1.0)
    - Configuration managed in `.flake8` file in the root directory.
    - Ignores specific codes (W29x, W391, E30x, E501, E2xx) and excludes `.venv`, `output_docs`, `tests`.
  - Mypy (v1.7.1)

## Architectural Decisions

1. **Python Over Node.js**

   - Better HTML parsing libraries
   - Simpler deployment
   - Existing team expertise

2. **Markdown as Primary Format**

3. **Concurrency Strategy**

   - Queue-based write system for atomic file writes (content files).
   - Granular file locking (fcntl) for shared resources:
     - Checklist file updates (`<website name>_scrape_checklist.md`)
     - Log file appends (`<website name>_errors.log`)
   - Thread-per-URL processing (extracted from the input markdown tree) with:
     - Independent error handling for each URL crawl.
     - No shared state between URL processing threads.
   - Automatic cleanup of resources per thread.

- Guarantees:
  - Atomic file writes for content files (via write queue).
  - No partial content file writes visible.
  - Failures during one URL crawl don't stop others.

4. **Image Handling Approach:**
   - Uniform handling for all image types found in `<img>` tags.
   - Extract `src` URL and `alt` text.
   - Convert relative `src` URLs to absolute.
   - Represent images using standard Markdown `![alt](url)`.
   - Do not download image files.
5. **Code Modularity:**
   - **Preference:** Favor small, focused Python modules/files over a single large script.
   - **Rationale:** Improves maintainability, testability, and readability. Allows for clearer separation of concerns (e.g., input parsing, HTML processing, image handling, file writing).
   - **Impact:** Requires careful interface design between modules but leads to a more robust and scalable codebase.
