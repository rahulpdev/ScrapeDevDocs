#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main script for crawling developer documentation based on a markdown tree
structure. Fetches content, processes HTML, handles images (including SVG
to Mermaid conversion), and saves structured markdown files.
"""

import argparse
import logging
import sys
import requests
import re  # Added for regex URL extraction
import os  # Added for directory creation
from urllib.parse import urlparse, urljoin  # Added urljoin back
from bs4 import BeautifulSoup  # Added BeautifulSoup
from markdownify import markdownify  # Added markdownify
import threading  # Added threading
import queue  # Added queue
import time  # Added for potential sleep/backoff later
from datetime import datetime # Added for milliseconds timestamp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pythonjsonlogger import jsonlogger  # Added for structured logging
from tqdm import tqdm  # Added for progress bar
# Placeholder for fcntl (if needed later for locking)

# --- Constants ---
# TODO: Move configuration like retry counts, backoff factor, etc. here


# --- Logging Setup ---

def setup_logging():
    """Sets up structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set root logger level

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    logHandler = logging.StreamHandler(sys.stdout)
    # Add filter to ensure only logs from this script are processed if needed
    # formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s
    #  %(message)s')
    # More detailed format including potential extra fields
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d %(error_code)s %(url)s %(details)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    # Disable propagation if other libraries also configure root logger
    # logger.propagate = False

    # Test log
    logging.info("Structured JSON logging initialized.")


# --- Helper Functions ---


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape developer documentation from a list specified in "
        "a markdown tree URL."
    )
    parser.add_argument(
        "tree_url",
        help="URL to the raw markdown file containing the URL tree structure."
    )
    # TODO: Add arguments for output directory, log file, etc. if needed
    return parser.parse_args()


def fetch_url_content(url):
    """Fetches content from a given URL with retry logic."""
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor (e.g., 1s, 2s, 4s)
        status_forcelist=[500, 502, 503, 504],  # Status codes to retry on
        # Use allowed_methods instead of method_whitelist
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logging.info(f"Fetching content from: {url}")
    try:
        response = session.get(url, timeout=10)  # Use the session
        # Raise HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()
        logging.info(f"Successfully fetched content from: {url}")
        return response.text
    except requests.exceptions.Timeout as e:
        logging.error(
            f"Timeout fetching {url}: {e}",
            extra={'url': url, 'error_code': 1001}
            )
        return None
    except requests.exceptions.ConnectionError as e:
        logging.error(
            f"Connection error fetching {url}: {e}",
            extra={'url': url, 'error_code': 1002}
            )
        return None
    except requests.exceptions.HTTPError as e:
        # Log HTTP errors but potentially continue if needed (e.g., 404
        #  is handled later)
        logging.warning(
            f"HTTP error fetching {url}: {e.response.status_code}",
            extra={
                'url': url,
                'error_code': 1003,
                'status_code': e.response.status_code
                }
            )
        return None  # Or return response if 404 needs specific handling
    except requests.exceptions.RequestException as e:
        # Catch other potential request exceptions
        logging.error(
            f"General request error fetching {url}: {e}",
            extra={'url': url, 'error_code': 1000}
            )  # Generic network error
        return None


def extract_urls_from_tree(markdown_content):
    """Extracts URLs from a tree structure format (e.g., '├── URL')."""
    logging.info("Extracting URLs from tree structure file...")
    urls = []
    for line in markdown_content.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        # Assume the URL is the last part of the line
        potential_url = parts[-1]
        if potential_url.startswith("http://") or potential_url.startswith("https://"):
            # Basic validation check
            if validate_url(potential_url):  # Use existing validation
                urls.append(potential_url)
            else:
                logging.warning(
                    f"Ignoring invalid URL format found in line: {line}"
                    )
        # Optional: Add logging for lines that don't seem to contain a URL if
        #  needed else:
        #     logging.debug(f"Line does not end with a URL: {line}")

    if not urls:
        logging.warning(
            "No URLs extracted from the tree structure file. Check format."
            )
    else:
        logging.info(f"Extracted {len(urls)} URLs using regex.")
    return urls


def validate_url(url):
    """Validates the format of a URL."""
    # TODO: Implement more robust validation if needed (Phase 3/4)
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_website_name(url):
    """Extracts a usable website name from a URL."""
    try:
        parsed_url = urlparse(url)
        # Use netloc (domain name), replace dots with underscores for
        #  filesystem safety
        name = parsed_url.netloc.replace('.', '_')
        return name
    except Exception as e:
        logging.error(f"Could not derive website name from URL {url}: {e}")
        return "default_website"  # Fallback name


def generate_safe_filename(url):
    """Generates a filesystem-safe filename from a URL."""
    parsed_url = urlparse(url)
    # Start with path, remove leading/trailing slashes
    filename = parsed_url.path.strip('/')
    if not filename:
        # Use a part of the netloc if path is empty (e.g., root URL)
        filename = parsed_url.netloc.replace('.', '_')
    # Replace slashes with underscores
    filename = filename.replace('/', '_')
    # Remove or replace other potentially problematic characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Add .md extension if not present
    if not filename.endswith('.md'):
        filename += ".md"
    # Handle potential emptiness after replacements
    if not filename or filename == ".md":
        filename = "index.md"  # Default for root or problematic URLs
    return filename


def generate_checklist_file(website_name, urls):
    """Creates or overwrites the checklist markdown file."""
    filename = f"{website_name}_scrape_checklist.md"
    logging.info(f"Generating checklist file: {filename}")
    try:
        # Ensure checklist file is in the root, not the docs folder
        filepath = os.path.join(".", filename)  # Explicitly place in CWD
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Scrape Checklist for {website_name}\n\n")
            f.write("URLs to process:\n\n")
            for url_item in urls:
                f.write(f"- [ ] {url_item}\n")
        logging.info(f"Successfully created checklist file: {filename}")
        return True
    except IOError as e:
        logging.error(
            f"Error writing checklist file {filepath}: {e}",
            extra={'filepath': filepath, 'error_code': 5002}
            )
        return False


# --- Checklist Update Function ---


def update_checklist_file(checklist_filepath, url_to_check, lock):
    """Atomically updates the checklist file to mark a URL as done."""
    logging.debug(f"Attempting to update checklist for: {url_to_check}")
    with lock:
        logging.debug(
            f"Acquired lock for checklist file: {checklist_filepath}"
            )
        try:
            lines = []
            found = False
            # Read the current checklist content
            with open(checklist_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find the line and update it
            for i, line in enumerate(lines):
                # Match the line specifically containing the URL
                if line.strip() == f"- [ ] {url_to_check}":
                    timestamp_ms = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # Format with milliseconds
                    lines[i] = f"- [x] {url_to_check}  # Processed: {timestamp_ms}\n"
                    found = True
                    logging.info(
                        f"Marked URL as done in checklist: {url_to_check}"
                        )
                    break  # Stop after finding the first match

            if not found:
                logging.warning(
                    f"URL not found in checklist or already marked: {url_to_check}"
                    )

            # Write the modified content back
            with open(checklist_filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        except FileNotFoundError:
            logging.error(
                f"Checklist file not found during update: {checklist_filepath}",
                extra={'filepath': checklist_filepath, 'error_code': 5004}
                )
        except IOError as e:
            logging.error(
                f"IOError updating checklist file {checklist_filepath}: {e}",
                extra={'filepath': checklist_filepath, 'error_code': 5002}
                )  # Assuming write error
        except Exception as e:
            logging.error(
                f"Unexpected error updating checklist {checklist_filepath}: {e}",
                exc_info=True,
                extra={'filepath': checklist_filepath, 'error_code': 9001}
                )
        finally:
            logging.debug(
                f"Released lock for checklist file: {checklist_filepath}"
                )


# --- URL Processing Function ---


def process_single_url(
        url,
        website_name,
        output_dir,
        checklist_filepath,
        checklist_lock
        ):
    """Fetches, processes, and saves content for a single URL. 
    Updates checklist on success."""
    logging.info(f"Processing URL: {url}")

    success = False  # Track overall success for this URL
    html_content = fetch_url_content(url)
    if not html_content:
        # fetch_url_content already logged the specific error
        logging.warning(f"Skipping URL due to fetch error: {url}")
        return False  # Indicate failure, checklist not updated

    try:
        soup = BeautifulSoup(html_content, 'lxml')

        # --- Foundational Step: Convert Links ---
        for a_tag in soup.find_all('a', href=True):
            original_href = a_tag['href']
            absolute_href = urljoin(url, original_href)
            a_tag['href'] = absolute_href
            # logging.debug(f"Converted link: {original_href} -> {absolute_href}")  # Optional debug

        # --- Phase 3, Step 1: Handle Images (including SVG placeholders) ---
        image_placeholders = {}
        for img_tag in soup.find_all('img'):
            original_src = img_tag.get('src')
            if not original_src:
                continue  # Skip images without src

            absolute_src = urljoin(url, original_src)
            # Default alt text if missing
            alt_text = img_tag.get('alt', 'image')
            placeholder = f"__IMAGE_PLACEHOLDER_{absolute_src}__"
            # Default to standard markdown
            markdown_output = f"![{alt_text}]({absolute_src})"

            # Check if it's an SVG
            if absolute_src.lower().endswith(".svg"):
                logging.info(f"Identified potential SVG: {absolute_src}")
                # Attempt to fetch SVG content
                # Re-use fetch function
                svg_content = fetch_url_content(absolute_src)
                if svg_content:
                    # TODO: Implement custom SVG to Mermaid text conversion here.
                    # This likely involves parsing svg_content using libraries
                    # like svgpathtools or xml.etree.ElementTree to understand
                    # the structure and generate Mermaid syntax.
                    # For now, we assume conversion fails and use the fallback.
                    conversion_successful = False  # Placeholder variable
                    mermaid_text = ""  # Placeholder variable

                    if conversion_successful:
                        # Future: Use the converted Mermaid text
                        # markdown_output = f"```mermaid\n{mermaid_text}\n```"
                        # logging.info(f"Successfully converted SVG to
                        #  Mermaid: {absolute_src}")
                        pass  # Keep placeholder logic for now
                    else:
                        # Fallback: Use standard markdown image tag (already default)
                        logging.warning(
                            f"SVG to Mermaid conversion failed or not implemented for: {absolute_src}. Using fallback."
                            )
                else:
                    logging.error(
                        f"Failed to fetch SVG content for: {absolute_src}. Using fallback."
                        )
                    # Fallback: Use standard markdown image tag
                    #  (already default)

            # Store the final markdown representation (either standard tag or
            #  future Mermaid)
            image_placeholders[placeholder] = markdown_output

            # Replace the img tag in the soup with the placeholder text
            img_tag.replace_with(placeholder)
            logging.debug(
                f"Replaced img tag {original_src} with placeholder {placeholder}"
                )

        # --- Phase 2, Step 1: Convert HTML Body to Markdown ---
        # Using markdownify to preserve structure (headings, lists,
        #  code blocks etc.) Link and image tag replacements were
        #  done *before* this step.
        markdown_content = "No content found."  # Default
        html_to_convert = ""
        if soup.body:
            html_to_convert = str(soup.body)
        else:
            logging.warning(
                f"No <body> tag found in {url}. Attempting conversion from root."
                )
            html_to_convert = str(soup)  # Fallback

        if html_to_convert:
            try:
                markdown_content = markdownify(
                    html_to_convert,
                    heading_style="ATX"
                    )
                logging.info(
                    f"Successfully converted HTML body to Markdown for {url}"
                    )
            except Exception as md_err:
                logging.error(
                    f"Markdownify conversion failed for {url}: {md_err}",
                    exc_info=True,
                    extra={'url': url, 'error_code': 7001}
                    )
                # Indicate failure in output
                markdown_content = "[Markdown conversion failed]"
        else:
            logging.error(
                f"No HTML content found to convert for {url}",
                extra={'url': url, 'error_code': 7002}
                )

        # --- Post-processing: Replace Image Placeholders ---
        processed_content = markdown_content
        for placeholder, markdown_image_tag in image_placeholders.items():
            processed_content = processed_content.replace(
                placeholder,
                markdown_image_tag
                )
            logging.debug(
                f"Replaced placeholder {placeholder} with Markdown image tag."
                )

        # --- Prepare Final Output ---
        processed_content += f"\n\n---\n*Source URL: {url}*"

        # --- Save Output ---
        filename = generate_safe_filename(url)
        filepath = os.path.join(output_dir, filename)

        logging.info(f"Saving processed content to: {filepath}")
        try:
            # --- Phase 2: Implement Write Queue (Simplified: Direct write for now) ---
            # TODO: Implement a proper write queue later if direct writing causes issues.
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            logging.info(f"Successfully saved: {filepath}")
            success = True  # Mark as successful *before* checklist update
        except IOError as e:
            logging.error(
                f"Error writing file {filepath}: {e}",
                extra={'filepath': filepath, 'error_code': 5002}
                )
            success = False  # Indicate failure

    except Exception as e:
        # Catching generic Exception is broad,
        #  consider more specific ones later
        logging.error(
            f"Error processing HTML for {url}: {e}",
            exc_info=True,
            extra={'url': url, 'error_code': 9001})  # General processing error
        success = False  # Indicate failure

    # --- Update Checklist (only if processing and saving succeeded) ---
    if success:
        update_checklist_file(checklist_filepath, url, checklist_lock)

    return success


# --- Worker Function ---


def worker(
        url_queue,
        website_name,
        output_dir,
        checklist_filepath,
        checklist_lock,
        pbar
        ):
    """
    Worker thread function to process URLs from the queue and update progress
    bar.
    """
    while True:  # Keep running until queue is empty
        try:
            url = url_queue.get_nowait()  # Get URL without blocking
            logging.debug(
                f"Worker {threading.current_thread().name} processing {url}"
                )
            try:
                process_single_url(
                    url,
                    website_name,
                    output_dir,
                    checklist_filepath,
                    checklist_lock
                    )
            except Exception as process_err:
                # Log errors during processing within the worker to avoid
                #  losing them
                logging.error(
                    f"Error in process_single_url for {url} within worker {threading.current_thread().name}: {process_err}",
                    exc_info=True,
                    extra={'url': url, 'error_code': 9001}
                    )
            finally:
                # Ensure task_done is called regardless of success/failure in
                #  process_single_url
                url_queue.task_done()  # Signal that this task is complete
                pbar.update(1)  # Update progress bar for this completed task
            # Optional: Add a small delay to avoid overwhelming servers
            # time.sleep(0.1)
        except queue.Empty:
            # Queue is empty, thread can exit
            logging.debug(
                f"Worker {threading.current_thread().name} found queue empty."
                )
            break
        except Exception as e:
            # Log unexpected errors in the worker loop itself
            logging.error(
                f"Unexpected error in worker {threading.current_thread().name}: {e}",
                exc_info=True
                )
            # We might still need task_done here if the error happened before
            # getting an item. However, the current logic gets item first, so
            # this might not be reachable easily. If an error occurs *after*
            # getting an item but before task_done, the finally block handles
            # it.


# --- Main Execution ---


def main():
    """Main execution function."""
    setup_logging()
    args = parse_arguments()

    logging.info(f"Starting scrape process for URL tree: {args.tree_url}")

    # 1. Fetch the markdown tree content
    markdown_content = fetch_url_content(args.tree_url)
    if not markdown_content:
        # fetch_url_content already logged the error with code
        logging.critical(
            "Failed to fetch markdown tree content. Exiting.",
            extra={'url': args.tree_url, 'error_code': 6001}
            )
        sys.exit(1)

    # 2. Extract URLs from the tree
    target_urls = extract_urls_from_tree(markdown_content)
    if not target_urls:
        logging.critical(
            "No URLs extracted from the markdown tree. Exiting.",
            extra={'error_code': 6003}
            )
        sys.exit(1)

    # 3. Validate extracted URLs (optional step shown here)
    valid_urls = [url for url in target_urls if validate_url(url)]
    invalid_count = len(target_urls) - len(valid_urls)
    if invalid_count > 0:
        logging.warning(
            f"Found {invalid_count} invalid URL formats in the input tree.",
            extra={'invalid_count': invalid_count}
            )
    if not valid_urls:
        logging.critical(
            "No valid URLs found after validation. Exiting.",
            extra={'error_code': 6003}
            )
        sys.exit(1)

    # 4. Derive website name from the *first valid target URL*
    website_name = get_website_name(valid_urls[0])
    logging.info(f"Derived website name: {website_name}")

    # 5. Generate the checklist file in the root directory
    checklist_filename = f"{website_name}_scrape_checklist.md"
    # Get full path for locking
    checklist_filepath = os.path.join(".", checklist_filename)
    if not generate_checklist_file(website_name, valid_urls):
        # generate_checklist_file logs the specific error
        logging.critical(
            "Failed to generate checklist file. Exiting.",
            extra={'error_code': 5002}
            )
        sys.exit(1)

    # 6. Create the output directory for markdown files
    output_dir = f"{website_name}_docs"
    try:
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_dir}")
    except OSError as e:
        logging.critical(
            f"Failed to create output directory {output_dir}: {e}. Exiting.",
            extra={'directory': output_dir, 'error_code': 5002}
            )
        sys.exit(1)

    logging.info("Setup complete. Starting concurrent URL processing.")

    # --- Phase 2 & 3: Concurrency Setup & Progress Bar ---
    url_queue = queue.Queue()
    checklist_lock = threading.Lock()
    threads = []
    num_worker_threads = 5  # Configurable number of threads
    total_urls = len(valid_urls)

    # Initialize tqdm progress bar
    pbar = tqdm(total=total_urls, desc="Processing URLs", unit="url")

    # Populate the queue
    for url_item in valid_urls:
        url_queue.put(url_item)

    logging.info(f"Populated URL queue with {total_urls} URLs.")

    # Start worker threads
    for i in range(num_worker_threads):
        thread = threading.Thread(
            target=worker,
            # Pass the progress bar instance to the worker
            args=(
                url_queue,
                website_name,
                output_dir,
                checklist_filepath,
                checklist_lock,
                pbar
                ),
            name=f"Worker-{i+1}",
            # Allows main thread to exit even if workers are blocked
            daemon=True
        )
        threads.append(thread)
        thread.start()
        logging.debug(f"Started thread: {thread.name}")

    # Wait for all tasks in the queue to be processed
    logging.info("Waiting for all URLs to be processed...")
    # Blocks until all items are processed (task_done called for each item)
    url_queue.join()

    # Close the progress bar
    pbar.close()
    logging.info(
        "All URLs processed. Concurrency and progress bar phase complete."
        )
    # Note: Since threads are daemons, they will exit automatically when the
    #  main thread finishes.
    # If non-daemon threads were used, we would need:
    # for thread in threads:
    #     thread.join()

    logging.info("Scraping process finished.")


if __name__ == "__main__":
    main()
