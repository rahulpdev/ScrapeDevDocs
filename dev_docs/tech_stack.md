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

2. **HTTP Client & File Processing**

   - Requests (v2.31.0)
     - Simplified HTTP operations
     - Session persistence
     - Automatic retry logic
   - urllib3 (v2.0.7)
     - Connection pooling
     - SSL verification
   - Python csv module
     - CSV file parsing
     - Header row handling
     - Type conversion

3. **Content Conversion**
   - Mermaid.js CLI (v10.6.1)
     - SVG to markdown conversion
     - Diagram generation
   - Pandoc (v3.1.6)
     - Fallback content conversion
     - Format normalization

## Infrastructure

- **Execution Environment**

  - Python 3.10.12
    - Type hint support
    - Pattern matching
    - Performance improvements
  - GitHub Actions
    - Ubuntu-latest runner
    - Scheduled triggers (daily at 00:00 UTC)
    - Artifact caching (7 day retention)
    - Workflow configuration:
      - Runs Function 1 (Navigation Crawler)
      - Input: urls.txt from repo root
      - Output: \*\_menumap.md files
      - Timeout: 30 minutes

- **Error Handling**
  - Structured logging (JSON)
  - Sentry.io integration
  - Circuit breaker pattern

## Development Tooling

- **Testing**

  - Pytest (v8.0.0)
  - Hypothesis (v6.92.0)
  - Coverage.py (v7.3.2)

- **Code Quality**
  - Black (v23.12.0)
  - Flake8 (v6.1.0)
  - Mypy (v1.7.1)

## Architectural Decisions

1. **Python Over Node.js**

   - Better HTML parsing libraries
   - Simpler deployment
   - Existing team expertise

2. **Markdown as Output**

   - Portable
   - Version control friendly
   - Easy to transform

3. **GitHub Actions**
   - Native integration
   - No additional costs
   - Easy maintenance
