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
   - urllib3 (v2.0.7)
   - Connection pooling
   - SSL verification

- `markdown` library (Python standard)
  - Parsing the input markdown file containing the URL tree structure.
  - Extracting URLs from the tree.

3. **URL Validation**

   - Python's `urllib.parse` for URL validation and manipulation.
   - Basic validation for input URL format (pointing to the markdown tree file).

4. **Content Conversion**

   - Mermaid.js CLI (v10.6.1)
   - SVG to markdown conversion
   - Diagram generation

5. **SVG Processing**
   - svgpathtools (v1.6.1)
     - Path analysis and manipulation
     - Bounding box calculations
   - svgwrite (v1.4.3)
     - SVG generation and modification
   - Custom SVG parser:
     - Architecture diagram detection
     - Node/edge extraction
     - Text element processing
     - Supports complex examples like:
       - Home Assistant architecture diagrams
       - Flowcharts with nested components
       - State machine visualizations
   - SVG Processing Requirements:
     - Must preserve semantic relationships
     - Handle minimum 5 levels of nesting
     - Support text extraction from:
       - Text elements
       - Title attributes
     - Data attributes
   - Output format:
     - Mermaid.js markdown (integrated into final content)

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
    - Markdown parsing (`markdown` library errors)
    - URL extraction
    - Content crawling (network, HTML parsing errors via BeautifulSoup)
    - SVG image processing (fetching, custom parser errors, Mermaid CLI errors)
    - File I/O

## Development Tooling

- **Testing**

  - Pytest (v8.0.0)
  - Hypothesis (v6.92.0)
  - Coverage.py (v7.3.2)
  - SVG-specific tests:
    - Architecture diagram parsing
    - Node/edge validation
    - Text extraction accuracy
    - Conversion fidelity tests:
      - Round-trip SVG->Mermaid->SVG
      - Semantic equivalence checks
      - Visual regression testing

- **Code Quality**
  - Black (v23.12.0)
  - Flake8 (v6.1.0)
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

4. **SVG Processing Approach**
   - Focus on architecture diagrams first
   - Handle nested components
   - Preserve semantic relationships
   - Support common diagram types:
     - Flowcharts
     - State machines
     - Component diagrams
   - Conversion priorities:
     1. Structural accuracy
     2. Text preservation
     3. Visual fidelity
   - Fallback strategies:
     - Manual review for complex diagrams
     - Alternative text descriptions
     - Original SVG preservation option
5. **Code Modularity:**
   - **Preference:** Favor small, focused Python modules/files over a single large script.
   - **Rationale:** Improves maintainability, testability, and readability. Allows for clearer separation of concerns (e.g., input parsing, HTML processing, image handling, file writing).
   - **Impact:** Requires careful interface design between modules but leads to a more robust and scalable codebase.
