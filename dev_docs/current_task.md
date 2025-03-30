# Current Task

## Context

- Memory Bank documentation complete and up-to-date
- All architecture decisions finalized and documented
- Current documentation versions:
  - project_brief.md: v1.0
  - codebase_summary.md: v1.4
  - tech_stack.md: v1.7
  - project_tracker.md: v1.8
  - current_task.md: v1.6

## Next Steps

### SVG Processing Implementation

1. **Comprehensive Conversion Approach**

   - Extract full SVG content including:
     - Text elements
     - Components and nodes
     - Paths and connections
     - Process steps and architecture elements
   - Attempt conversion to Mermaid diagram format
   - Preserve original SVG as fallback

2. **Implementation Notes**
   - Focus on process/procedure/architecture diagrams
   - Analyze diagram structure for Mermaid conversion
   - Fallback conditions:
     - Non-process diagrams (logos, illustrations)
     - Conversion failures
     - Complex diagrams with unsupported elements

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
