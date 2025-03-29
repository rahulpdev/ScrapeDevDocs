# Current Task

## Context

- Memory Bank documentation complete and up-to-date
- All architecture decisions finalized and documented
- Current documentation versions:
  - project_brief.md: v1.0
  - codebase_summary.md: v1.4
  - tech_stack.md: v1.7
  - project_tracker.md: v1.8
  - current_task.md: v1.4

## Next Steps

### SVG Processing Implementation

1. **Architecture Diagram Analysis**

   - Parse complex SVG diagrams (e.g., Home Assistant architecture)
   - Extract nodes and connections
   - Identify text labels and relationships
   - Handle nested components (minimum 5 levels)
   - Support text extraction from:
     - Text elements
     - Title attributes
     - Data attributes

2. **Conversion Pipeline**

   - SVG to Mermaid.js conversion
   - Preserve semantic relationships
   - Generate hierarchical structure
   - Output formats:
     - Mermaid.js markdown
     - JSON structure
     - Graphviz DOT format
   - Output to docs/architecture/ directory

3. **Testing & Validation**
   - Verify accuracy of converted diagrams
   - Test with multiple diagram types:
     - Flowcharts
     - State machines
     - Component diagrams
   - Conversion fidelity tests:
     - Round-trip SVG->Mermaid->SVG
     - Semantic equivalence checks
     - Visual regression testing
   - Fallback strategies:
     - Manual review for complex diagrams
     - Alternative text descriptions
     - Original SVG preservation option

### Navigation Crawler Implementation

- Input processing:
  - Read from urls.txt or CSV files
  - Support multiple URL columns in CSV
  - Validate and normalize URLs
  - Handle redirects (max depth: 5)
- Menu tree generation:
  - Parse HTML navigation elements
  - Build hierarchical structure
  - Output to docs/menus/ directory as markdown

### Infrastructure Setup

- Logging:
  - Configure Python logging module
  - Set up log rotation
  - Error severity levels
  - JSON format for structured logging
- Error handling:
  - Implement circuit breaker pattern
  - Configure Sentry.io alerts
  - Add retry logic for HTTP requests
  - CSV-specific error handling:
    - Per-row error tracking
    - Validation continues despite errors
    - Detailed error messages with line numbers

### Content Extractor Preparation

- Content extraction rules:
  - Preserve heading hierarchy
  - Process images:
    - For flowchart diagrams: convert to mermaid
    - For other images: include URL, reference and alt text
  - Replace relative URLs with absolute
  - Maintain external links
  - Include last updated timestamp
  - Add page URL at file end
- Output structure:
  - Single folder per site (no subfolders)
  - Checklist file per site
  - Input requirements:
    - Must be URL pointing to markdown file
    - Example: https://example.com/scrape_website_menumap.md
