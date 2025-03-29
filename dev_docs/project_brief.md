**Project Goal:**

To regularly crawl online developer documentation and maintain an up-to-date, structured set of offline markdown files containing the documentation. The project must achieve this goal with two independent functions:

- **Function 1 Goal:** Generate a markdown file with a tree structure diagram of the contents of a website's navigation menu.
- **Function 2 Goal:** Crawl a list of URLs and extract the page content from each URL into exactly one markdown file per URL. Each output file must contain both the page content and any converted mermaid diagrams (where applicable). Input must be a URL pointing to a markdown file (e.g. https://example.com/scrape_website_menumap.md).

**Project Scope:**

1.  **Function 1: Navigation Menu Sitemap Generation**

    - Develop a script to:
      - Extract navigation menus using user-provided CSS selectors
      - Comprehensively traverse the navigation menu and all its sub-menus
      - Represent each menu item in a tree structure, using its full path URL.
      - Read website URLs and navigation selectors from a CSV file:
        - First column contains website URLs
        - Second column contains CSS selectors for navigation menus
        - Example format:
          url,css_selector
          https://example.com,.nav-menu
          https://test.com,#main-navigation
      - Produce a unique markdown file (`<website name>_menumap.md`) in the project root folder for each website's menu tree structure diagram.
    - Example output:
      ```
        https://www.example.com/
        ├── https://www.example.com/about/
        ├── https://www.example.com/services/
        │   ├── https://www.example.com/services/website-copywriting/
        │   └── https://www.example.com/services/vip-day/
        ├── https://www.example.com/portfolio/
        │   ├── https://www.example.com/portfolio/modern-loft/
        │   └── https://www.example.com/portfolio/mountain-escape/
        └── https://www.example.com/privacy-policy/
      ```

2.  **Function 2: URL Content Extraction and Markdown Conversion**

    - Develop a script to:
      - Crawl a list of URLs and output a markdown file for each website page.
      - For each retrieved page:
        - Preserve the heading hierarchy of the original content.
        - Do NOT remove any content between section headers.
        - Replace all relative path URLs with full path URLs.
        - Preserve all external links as markdown references.
        - Retrieve all images from image URLs. For each image:
          - If image is SVG format:
            - Attempt conversion to mermaid diagram preserving:
              - Node relationships and hierarchy
              - Connector directions and types
              - Label positioning and content
            - On any conversion failure or invalid SVG:
              - Preserve original image reference with URL and alt text
              - Do not include error notices
              - Do not retain failed conversion attempts
          - For all other image formats (PNG, JPG, etc):
          - Do not retain image files
            - Preserve original image with URL, reference and alt text
        - Preserve "Last Updated" data verbatim.
        - Add the page full path URL to the end of the file.
        - Check off the URL in `<website name>_scrape_checklist.md` after file completion, and add a timestamp.
      - For each URL, maintain:
        - Single `<website name>_docs` folder (no sub folders) in project root
        - `<website name>_scrape_checklist.md` task tracker in project root
        - Processed markdown files containing:
          - Original content structure
          - Converted mermaid diagrams (where applicable)
          - Source URL reference
      - Store each markdown file output in its `<website name>_docs` folder.
      - Accept as a terminal input (with input validation) a URL to a GitHub repository raw file that contains a tree structure markdown diagram, where each branch of the tree is a URL to be crawled.
      - After accepting a valid terminal input, overwrite the content of `<website name>_scrape_checklist.md` with a checklist of the URLs from the tree structure diagram and a file Last Updated timestamp.

3.  **Architectural Assumptions**

    - **File Handling**:

      - Output files overwrite existing files by default
      - No versioning/history tracking required
      - Local filesystem is primary storage medium

    - **Interface Priorities**:

      - CLI as primary user interface
      - Batch processing via CSV files required
      - No GUI/web interface planned

    - **Output Standards**:

      - Markdown as sole output format
      - Tables preferred over other data representations
      - SVG conversion focuses on structural accuracy

    - **Operational Constraints**:
      - No cloud storage integration
      - No authentication requirements
      - Limited error recovery capabilities

4.  **Automation**

    - Implement GitHub Actions to automate Function 1.
    - Schedule the GitHub Actions workflow to run Function 1 daily.

5.  **Output**

    - A public GitHub repository containing:
      - `<website name>_menumap.md`: The sitemap produced by Function 1.
      - The scripts for Function 1 and Function 2.
      - The GitHub Actions workflow configuration.
      - A folder containing the markdown files generated by function 2.
        - Add each folder to .gitignore.
    - .gitignore file containing all usual exlcusions and also:
      - `<website name>_scrape_checklist.md`: Each task tracker produced by Function 2.
      - Each folder containing the markdown files generated by function 2.

6.  **Error Handling**
    - Implement robust error handling for:
      1.  **Network Errors:**
          - Use `try-except` blocks to catch `requests.exceptions.RequestException` during URL fetching.
          - Log error messages, including the URL that caused the error.
          - Implement retry logic with exponential backoff for transient network errors.
          - If a link is broken, log the error, and continue to the next link.
      2.  **HTML Parsing Errors:**
          - Use `try-except` blocks to catch `BeautifulSoup` parsing errors.
          - Log error messages, including the URL and the parsing issue.
          - Use robust HTML selectors to minimize parsing failures.
      3.  **File I/O Errors:**
          - Use `try-except` blocks to catch file I/O errors (e.g., `IOError`).
          - Log error messages, including the file path and the error details.
          - Ensure proper file permissions and directory existence.
      4.  **GitHub Actions Errors:**
          - Monitor GitHub Actions workflow runs for failures.
          - Configure notifications to alert developers of workflow errors.
          - Implement error handling within the GitHub Actions workflow (e.g., using `if` conditions).
      5.  **Logging:**
          - Implement comprehensive logging to track the execution of the scripts.
          - Log informational messages, warnings, and errors.
          - Use a structured logging format (e.g., JSON) for easier analysis.
