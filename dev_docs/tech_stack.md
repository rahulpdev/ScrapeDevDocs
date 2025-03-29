# Technology Stack

## Core Components

1. **HTML Processing**

   - BeautifulSoup4 (v4.12.0)
     - Robust HTML parsing
     - Handles malformed markup
     - XPath-like navigation
   - cheerio (v1.0.7)
     - Fast HTML parsing and manipulation
     - jQuery-like syntax
     - Server-side DOM implementation
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
     - New validation features:
       - URL validation with whitespace trimming
       - Line number tracking for errors
       - Non-blocking error handling
       - Navigation selector column presence check

3. **URL Validation**

   - Python's urlparse with custom extensions
   - Explicit handling for 30+ common TLDs (fixed list)
   - Special cases for CMS paths (WordPress, Drupal)
   - Maximum redirect depth: 5
   - Explicitly excludes:
     - Cyclic redirect detection
     - TLD list updates
     - Internationalized domain name handling

4. **Content Conversion**

   - Mermaid.js CLI (v10.6.1)
     - SVG to markdown conversion
     - Diagram generation
   - svg2mermaid (v2.4.1)
     - Specialized SVG to Mermaid conversion
     - Architecture diagram detection
     - Node/edge extraction
   - Pandoc (v3.1.6)
     - Fallback content conversion
     - Format normalization

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
     - Output formats:
       - Mermaid.js markdown
       - JSON structure
       - Graphviz DOT format

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
  - New CSV-specific error handling:
    - Per-row error tracking
    - Validation continues despite errors
    - Detailed error messages with line numbers

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

2. **Markdown as Output**

   - Portable
   - Version control friendly
   - Easy to transform

3. **GitHub Actions**

   - Native integration
   - No additional costs
   - Easy maintenance

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
