**Project Goal:**

To crawl online developer documentation specified in a tree-structure markdown file and maintain an up-to-date, structured set of offline markdown files containing the documentation content.

**Project Scope:**

1.  **URL Content Extraction and Markdown Conversion**

    - Develop a script to:
      - Crawl a list of URLs and output a markdown file for each website page.
      - For each retrieved page:
        - Preserve the heading hierarchy of the original content.
        - Do NOT remove any content between section headers.
        - Replace all relative path URLs with full path URLs.
        - Preserve all external links as markdown references.
        - Process all image links (regardless of format, e.g., SVG, PNG, JPG) referenced on the webpage:
          - Identify the image URL and any associated alt/reference text from the HTML.
          - Do **not** download the image file.
          - Preserve the original image reference as a standard Markdown image link: `![alt text](image URL)`.
        - Preserve "Last Updated" data verbatim.
      - For each markdown file:
        - Add the webpage full path URL to the end of the file.
        - Determine a base name, preferably from the H1 of the first URL, falling back to the domain name (e.g., `<h1>` or `<website_name>`). Let's call this `<base_name>`.
        - Create a root output folder `output_docs/` if it doesn't exist.
        - Check off the webpage URL and add a timestamp in `output_docs/<base_name>_scrape_checklist.md` after file completion.
        - Save the completed file in its `output_docs/<base_name>_docs` folder.
      - For each website scrape initiated, maintain within the `output_docs/` folder:
        - A single `<base_name>_docs` folder (no sub folders within this).
        - A `<base_name>_scrape_checklist.md` crawler task tracker.
        - Processed markdown files within the `<base_name>_docs` folder containing:
          - Original content structure
          - Preserved image references as Markdown links
          - Source URL reference
      - Accept as a terminal input (with input validation) a URL to a GitHub repository raw file (or similar raw text source).
      - **Input File Format Requirement:** The file at the URL **must** contain a tree structure where each line representing a URL to crawl follows the exact format: `[TREE_PREFIX][SPACE][URL]`.
        - `[TREE_PREFIX]` can be any non-whitespace characters (e.g., `├──`, `└──`, `│  `).
        - `[SPACE]` is one or more whitespace characters.
        - `[URL]` is the full, valid HTTP/HTTPS URL to be crawled.
        - Example valid line: `├── https://www.hacs.xyz/docs/publish/start/`
        - Lines not matching this format will be ignored.
      - After accepting a valid terminal input, determine the `<base_name>` and create/overwrite the content of `output_docs/<base_name>_scrape_checklist.md` with a checklist of the URLs extracted from the tree structure diagram.
      - During execution, display a progress bar in the terminal indicating the number of URLs successfully processed out of the total (e.g., "Processed Y of X URLs").

2.  **Architectural Assumptions**

    - **File Handling**:

      - Output files overwrite existing files by default
      - No versioning/history tracking required
      - Local filesystem is primary storage medium

    - **Interface Priorities**:

      - CLI as primary user interface for providing the input URL (pointing to the tree structure markdown file).
      - No GUI/web interface planned.

    - **Output Standards**:

      - Markdown as sole output format
      - Tables preferred over other data representations
      - Image links preserved as standard Markdown `![alt](url)`

    - **Operational Constraints**:
      - No cloud storage integration
      - No authentication requirements
      - Limited error recovery capabilities

3.  **Automation**

    - No automated execution is currently planned. Execution is manual via CLI.

4.  **Output**

    - A public GitHub repository containing:
      - The scripts for the content extraction functions.
      - An empty `output_docs/` folder (contents are generated locally).
    - `.gitignore` file containing all usual exclusions and also:
      - `output_docs/`: The entire directory containing generated checklists and markdown files.

5.  **Error Handling**
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
      4.  **Logging:**
          - Implement comprehensive logging to track the execution of the scripts.
          - Log informational messages, warnings, and errors.
          - Use a structured logging format (e.g., JSON) for easier analysis.
