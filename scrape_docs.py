#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main script for crawling developer documentation based on a markdown tree
structure. Fetches content, processes HTML, handles images uniformly,
and saves structured markdown files using a write queue.
"""

import argparse
import logging
import sys
import requests
import re  # Added for regex URL extraction
import os  # Added for directory creation
from urllib.parse import urlparse, urljoin  # Added urljoin back
from bs4 import BeautifulSoup  # Added BeautifulSoup
# from markdownify import markdownify # Replaced with html2text
import html2text # Added html2text
import threading  # Added threading
import queue  # Added queue
from datetime import datetime  # Added for milliseconds timestamp
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


def sanitize_for_filename(text):
    """Removes or replaces characters unsafe for filenames/directory names."""
    # Remove leading/trailing whitespace
    text = text.strip()
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Remove characters that are problematic in filenames across OSes
    text = re.sub(r'[<>:"/\\|?*&%\'!,;=\[\]{}()]+', '', text)
    # Limit length to avoid issues (e.g., 100 chars)
    return text[:100]


def get_h1_from_url(url):
    """Fetches a URL, extracts and sanitizes the first H1 tag content."""
    logging.info(f"Attempting to fetch H1 from first URL: {url}")
    html_content = fetch_url_content(url)
    if not html_content:
        logging.warning(f"Could not fetch content for H1 extraction from {url}. Falling back.")
        return None  # Indicate failure

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        h1_tag = soup.find('h1')
        # Use get_text() for robustness instead of .string
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)
            sanitized_h1 = sanitize_for_filename(h1_text)
            if sanitized_h1:
                logging.info(f"Extracted and sanitized H1: '{sanitized_h1}' from {url}")
                return sanitized_h1
            else:
                logging.warning(f"H1 tag found but resulted in empty sanitized string from {url}. Falling back.")
                return None
        else:
            logging.warning(f"No H1 tag found or H1 tag is empty in {url}. Falling back.")
            return None
    except Exception as e:
        # Simplified logging call
        logging.error(f"Error parsing HTML for H1 extraction from {url}: {e} [EC:7003]", exc_info=True)
        return None


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
    parser.add_argument(
        "-o", "--output-dir",
        default="output_docs",
        help="Root directory to save checklists and documentation folders (default: output_docs)"
    )
    parser.add_argument(
        "-l", "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )
    parser.add_argument(
        "-w", "--num-workers",
        type=int,
        default=5,
        help="Number of concurrent worker threads (default: 5)"
    )
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
        # Explicitly decode using UTF-8, replacing errors
        content = response.content.decode('utf-8', errors='replace')
        logging.info(f"Successfully fetched and decoded content from: {url}")
        return content
    except requests.exceptions.Timeout as e:
        # Simplified logging
        logging.error(f"Timeout fetching {url}: {e} [EC:1001]")
        return None
    except requests.exceptions.ConnectionError as e:
        # Simplified logging
        logging.error(f"Connection error fetching {url}: {e} [EC:1002]")
        return None
    except requests.exceptions.HTTPError as e:
        # Log HTTP errors but potentially continue if needed (e.g., 404
        #  is handled later)
        # Simplified logging
        logging.warning(f"HTTP error fetching {url}: {e.response.status_code} [EC:1003]")
        return None  # Or return response if 404 needs specific handling
    except requests.exceptions.RequestException as e:
        # Catch other potential request exceptions
        # Simplified logging
        logging.error(f"General request error fetching {url}: {e} [EC:1000]")
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
        # Log the error with a specific code if needed
        # Simplified logging
        logging.error(f"Could not derive website name from URL {url}: {e} [EC:6004]")
        return "fallback_domain_name"  # Fallback name


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


def generate_checklist_file(base_name, filepath, urls):
    """Creates or overwrites the checklist markdown file at the specified path."""
    # filename is now derived externally and passed via filepath
    logging.info(f"Generating checklist file: {filepath}")
    try:
        # Filepath now includes the output_docs directory
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Scrape Checklist for {base_name}\n\n")  # Use base_name for title
            f.write("URLs to process:\n\n")
            for url_item in urls:
                f.write(f"- [ ] {url_item}\n")
        logging.info(f"Successfully created checklist file: {filepath}")  # Log full path
        return True
    except IOError as e:
        # Simplified logging
        logging.error(f"Error writing checklist file {filepath}: {e} [EC:5002]")
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
                    timestamp_ms = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Format with milliseconds
                    lines[i] = f"- [x] {url_to_check}  # Processed: {timestamp_ms}\n"  # Fixed E261/E262
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
            # Simplified logging
            logging.error(f"Checklist file not found during update: {checklist_filepath} [EC:5004]")
        except IOError as e:
            # Simplified logging
            logging.error(f"IOError updating checklist file {checklist_filepath}: {e} [EC:5002]")
        except Exception as e:
            # Simplified logging
            logging.error(f"Unexpected error updating checklist {checklist_filepath}: {e} [EC:9001]", exc_info=True)
        finally:
            logging.debug(
                f"Released lock for checklist file: {checklist_filepath}"
                )


# --- URL Processing Function ---


def process_single_url(
        url,
        base_name,  # Keep for consistency, though not used directly here now
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

        # --- Refactored Image Handling (Uniform) ---
        # image_placeholders = {} # No longer needed
        for img_tag in soup.find_all('img'):
            original_src = img_tag.get('src')
            if not original_src:
                logging.warning(f"Skipping img tag with no src in {url}")
                continue  # Skip images without src

            absolute_src = urljoin(url, original_src)
            # Default alt text if missing, sanitize for Markdown
            alt_text = img_tag.get('alt', '')
            # Basic sanitization for alt text (e.g., remove brackets that might break Markdown)
            alt_text = alt_text.replace('[', '').replace(']', '').replace('(', '').replace(')', '')

            # Generate standard Markdown image link for ALL images
            markdown_image_tag = f"![{alt_text}]({absolute_src})"
            logging.debug(f"Generated Markdown for image: {markdown_image_tag}")

            # Replace the img tag in the soup *directly* with the final markdown tag
            # This avoids placeholder replacement issues after markdownify
            img_tag.replace_with(markdown_image_tag)
            logging.debug(
                f"Replaced img tag {original_src} with Markdown: {markdown_image_tag}"
                )

        # --- Remove any remaining img tags (e.g., those without src) BEFORE markdownify ---
        # Note: The previous loop already skipped tags without src, but decompose handles any stragglers
        # or tags that might be generated differently.
        for img_tag in soup.find_all('img'):
            # Correct indentation
            logging.warning(f"Removing unexpected remaining img tag: {img_tag}")
            img_tag.decompose() # Remove the tag from the soup

        # --- Convert HTML Body to Markdown ---
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
                # Initialize html2text converter
                h = html2text.HTML2Text()
                # Configure options if needed (e.g., h.ignore_links = True)
                # By default, html2text handles tables well.
                h.body_width = 0 # Prevent line wrapping
                markdown_content = h.handle(html_to_convert)
                logging.info(
                    f"Successfully converted HTML body to Markdown using html2text for {url}"
                    )
            except Exception as h2t_err:
                # Simplified logging
                logging.error(f"html2text conversion failed for {url}: {h2t_err} [EC:7001]", exc_info=True)
                # Indicate failure in output
                markdown_content = "[Markdown conversion failed]"
        else:
            # Simplified logging
            logging.error(f"No HTML content found to convert for {url} [EC:7002]")

        # --- Post-processing: No longer needed as replacement happens before markdownify ---
        processed_content = markdown_content

        # --- Prepare Final Output ---
        processed_content += f"\n\n---\n*Source URL: {url}*"

        # --- Save Output ---
        filename = generate_safe_filename(url)
        filepath = os.path.join(output_dir, filename)

        # Mark success *before* checklist update, indicating content generation success
        success = True

    except Exception as e:
        # Catching generic Exception is broad,
        #  consider more specific ones later
        # Simplified logging
        logging.error(f"Error processing HTML for {url}: {e} [EC:9001]", exc_info=True)
        success = False  # Indicate failure

    # --- Update Checklist (only if content generation succeeded) ---
    if success:
        update_checklist_file(checklist_filepath, url, checklist_lock)
        # Return filepath and content for the writer queue
        return filepath, processed_content
    else:
        # Return None if processing failed before content generation
        # Return None if processing failed before content generation
        return None, None


# --- Writer Thread Function ---

def writer_thread(write_queue):
    """Worker thread to write processed content to files."""
    while True:
        item = write_queue.get()
        if item is None:
            logging.info("Writer thread received sentinel. Exiting.")
            write_queue.task_done()
            break  # Sentinel value received, exit loop

        filepath, content = item
        logging.info(f"Writer thread saving content to: {filepath}")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Writer thread successfully saved: {filepath}")
        except IOError as e:
            # Simplified logging
            logging.error(f"Writer thread error writing file {filepath}: {e} [EC:5002]")
        except Exception as e:
             # Catch unexpected errors during write
             logging.error(f"Writer thread unexpected error writing {filepath}: {e} [EC:9002]", exc_info=True)
        finally:
            write_queue.task_done() # Signal task completion


# --- Worker Function ---


def worker(
        url_queue,
        base_name,  # Use base_name instead of website_name
        output_dir,
        checklist_filepath,
        checklist_lock,
        pbar,
        write_queue # Add write_queue argument
): # noqa: E111, E114, E117 Align closing parenthesis with def
    """
    Worker thread function to process URLs from the queue, pass results to the
    write queue, and update progress bar.
    """
    while True:  # Keep running until queue is empty
        try:
            url = url_queue.get_nowait()  # Get URL without blocking
            logging.debug(
                f"Worker {threading.current_thread().name} processing {url}"
                )
            try:
                # Process the URL to get filepath and content
                filepath, content = process_single_url(
                    url,
                    base_name,  # Pass base_name
                    output_dir,
                    checklist_filepath,
                    checklist_lock
                    ) # Align closing parenthesis with first argument
                # If processing was successful, put the result in the write queue
                if filepath and content:
                    write_queue.put((filepath, content))
                    logging.debug(f"Worker {threading.current_thread().name} added {filepath} to write queue.")
                # If process_single_url returned (None, None), it means processing failed
                # and was already logged within that function. Checklist wasn't updated.

            except Exception as process_err:
                # Log errors during processing within the worker itself (e.g., issues calling process_single_url)
                #  losing them
                # Simplified logging
                logging.error(f"Error in process_single_url for {url} within worker {threading.current_thread().name}: {process_err} [EC:9001]", exc_info=True)
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

    logging.info(f"Starting scrape process for URL tree: {args.tree_url}") # Reverted log message

    # 1. Fetch the markdown tree content
    markdown_content = fetch_url_content(args.tree_url)
    if not markdown_content:
        # fetch_url_content already logged the error with code
        # Simplified logging
        logging.critical(f"Failed to fetch markdown tree content from {args.tree_url}. Exiting. [EC:6001]")
        sys.exit(1)

    # 2. Extract URLs from the tree
    target_urls = extract_urls_from_tree(markdown_content)
    if not target_urls:
        # Simplified logging
        logging.critical("No URLs extracted from the markdown tree. Exiting. [EC:6003]")
        sys.exit(1)

    # 3. Validate extracted URLs (optional step shown here)
    valid_urls = [url for url in target_urls if validate_url(url)]
    invalid_count = len(target_urls) - len(valid_urls)
    if invalid_count > 0:
        # Simplified logging
        logging.warning(f"Found {invalid_count} invalid URL formats in the input tree.")
    if not valid_urls:
        # Simplified logging
        logging.critical("No valid URLs found after validation. Exiting. [EC:6003]")
        sys.exit(1)

    # 4. Get Base Name (H1 or Fallback) and Define Output Paths
    base_name = get_h1_from_url(valid_urls[0])
    if not base_name:
        logging.warning("H1 extraction failed, falling back to domain name.")
        base_name = get_website_name(valid_urls[0]) # Fallback
    logging.info(f"Using base name for outputs: {base_name}")

    output_root_dir = "output_docs"
    try:
        os.makedirs(output_root_dir, exist_ok=True)
        logging.info(f"Ensured root output directory exists: {output_root_dir}")
    except OSError as e:
        # Simplified logging
        # Simplified logging
        logging.critical(f"Failed to create root output directory {output_root_dir}: {e}. Exiting. [EC:5002]")
        sys.exit(1)

    checklist_filename = f"{base_name}_scrape_checklist.md"
    checklist_filepath = os.path.join(output_root_dir, checklist_filename)  # Path includes output_root_dir
    output_dir = os.path.join(output_root_dir, f"{base_name}_docs")  # Path includes output_root_dir

    # 5. Generate the checklist file in the new location
    if not generate_checklist_file(base_name, checklist_filepath, valid_urls):  # Pass new args
        # generate_checklist_file logs the specific error
        # Simplified logging
        logging.critical(f"Failed to generate checklist file at {checklist_filepath}. Exiting. [EC:5002]")
        sys.exit(1)

    # 6. Create the specific output directory for markdown files
    # output_dir is already defined above
    try:
        os.makedirs(output_dir, exist_ok=True)  # Use the new output_dir path
        logging.info(f"Ensured specific output directory exists: {output_dir}")
    except OSError as e:
        # Simplified logging
        # Simplified logging
        # Simplified logging
        # Simplified logging
        logging.critical(f"Failed to create output directory {output_dir}: {e}. Exiting. [EC:5002]")
        sys.exit(1)

    logging.info("Setup complete. Starting concurrent URL processing.")

    # --- Concurrency Setup: URL Queue, Write Queue, Locks, Threads ---
    url_queue = queue.Queue()
    write_queue = queue.Queue() # Create the write queue
    checklist_lock = threading.Lock()
    worker_threads = [] # Rename for clarity
    num_worker_threads = 5  # Configurable number of threads
    total_urls = len(valid_urls)

    # Initialize tqdm progress bar
    pbar = tqdm(total=total_urls, desc="Processing URLs", unit="url")

    # Populate the queue
    for url_item in valid_urls:
        url_queue.put(url_item)

    logging.info(f"Populated URL queue with {total_urls} URLs.")

    # Start the writer thread
    writer = threading.Thread(target=writer_thread, args=(write_queue,), name="WriterThread", daemon=True)
    writer.start()
    logging.info("Started writer thread.")

    # Start worker threads
    for i in range(num_worker_threads):
        thread = threading.Thread(
            target=worker,
            args=(
                url_queue,
                base_name,
                output_dir,
                checklist_filepath,
                checklist_lock,
                pbar,
                write_queue # Pass write_queue to workers
            ),
            name=f"Worker-{i+1}",
            daemon=True
        )
        worker_threads.append(thread)
        thread.start()
        logging.debug(f"Started thread: {thread.name}")

    # Wait for all URLs to be processed by workers
    logging.info("Waiting for all URLs to be processed by workers...")
    url_queue.join()
    logging.info("All URLs processed by workers.")

    # Signal writer thread to exit by sending sentinel
    logging.info("Signaling writer thread to exit...")
    write_queue.put(None)

    # Wait for the writer queue to be empty
    logging.info("Waiting for writer queue to empty...")
    write_queue.join()
    logging.info("Writer queue empty.")

    # Wait for the writer thread to finish (optional as it's daemon, but good practice)
    # writer.join() # Not strictly necessary for daemon thread

    # Close the progress bar
    pbar.close()
    logging.info("Scraping process finished.")


if __name__ == "__main__":
    main()
