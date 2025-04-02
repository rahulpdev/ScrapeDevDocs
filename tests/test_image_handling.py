import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add project root to sys.path to allow importing scrape_docs
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the function to test AFTER modifying sys.path
# Need to mock dependencies before importing if they are used at module level
# For now, assume dependencies are primarily used within functions
from scrape_docs import process_single_url, generate_safe_filename # noqa: E402

# --- Test Setup ---

BASE_URL = "http://example.com/docs/page1.html"
OUTPUT_DIR = "output_docs/example_com_docs"
CHECKLIST_PATH = "output_docs/example_com_scrape_checklist.md"

# Mock checklist lock
mock_lock = MagicMock()

# --- Test Cases ---

@pytest.mark.parametrize(
    "img_html, expected_markdown_part",
    [
        # Test case 1: PNG image with alt text
        ('<img src="images/logo.png" alt="Company Logo">', '![Company Logo](http://example.com/docs/images/logo.png)'),
        # Test case 2: SVG image with alt text
        ('<img src="/images/diagram.svg" alt="Architecture Diagram">', '![Architecture Diagram](http://example.com/images/diagram.svg)'),
        # Test case 3: JPG image, relative path
        ('<img src="../assets/photo.jpg" alt="User Photo">', '![User Photo](http://example.com/assets/photo.jpg)'),
        # Test case 4: Image with no alt text
        ('<img src="icon.gif">', '![](http://example.com/docs/icon.gif)'),
        # Test case 5: Image with empty alt text
        ('<img src="empty.webp" alt="">', '![](http://example.com/docs/empty.webp)'),
        # Test case 6: Image with absolute URL source
        ('<img src="https://cdn.example.com/image.png" alt="CDN Image">', '![CDN Image](https://cdn.example.com/image.png)'),
        # Test case 7: Image with special characters in alt text (should be sanitized)
        ('<img src="special.png" alt="[Special] (Chars)">', '![Special Chars](http://example.com/docs/special.png)'),
        # Test case 8: Image tag with no src
        ('<img alt="No Source">', ''), # Should produce no image markdown
    ]
)
@patch('scrape_docs.fetch_url_content')
@patch('scrape_docs.update_checklist_file')
@patch('builtins.open', new_callable=MagicMock)
def test_uniform_image_handling(mock_open, mock_update_checklist, mock_fetch, img_html, expected_markdown_part):
    """
    Tests that process_single_url handles various image types uniformly,
    generating standard Markdown and not fetching image content.
    """
    # --- Arrange ---
    # Mock fetch_url_content to return the HTML containing the image tag
    # It should only be called once for the main page URL
    mock_fetch.return_value = f"<html><body><p>Some text</p>{img_html}<p>More text</p></body></html>"

    # Dynamically generate the expected filename using the actual function
    expected_filename = generate_safe_filename(BASE_URL)
    expected_filepath = os.path.join(OUTPUT_DIR, expected_filename)

    # --- Act ---
    result = process_single_url(BASE_URL, "example_com", OUTPUT_DIR, CHECKLIST_PATH, mock_lock)

    # --- Assert ---
    # 1. Check that fetch_url_content was called ONLY for the BASE_URL, not image URLs
    mock_fetch.assert_called_once_with(BASE_URL)

    # 2. Check if the function indicates success (returns non-None tuple)
    assert isinstance(result, tuple), "process_single_url should return a tuple"
    assert result[0] == expected_filepath, f"Expected filepath {expected_filepath}, got {result[0]}"
    assert result[1] is not None, "Returned content should not be None"
    returned_content = result[1]

    # 3. Check the returned content contains the expected image markdown
    # mock_open should NOT have been called as writing is deferred
    mock_open.assert_not_called()

    # Check if the expected markdown part is in the returned content
    if expected_markdown_part:
        assert expected_markdown_part in returned_content
    else:
        # If no markdown is expected (e.g., img tag with no src), ensure no ![...] is present
        # The decompose step should remove the tag entirely before markdownify
        assert "![" not in returned_content

    # 4. Check that the checklist was updated (as content generation succeeded)
    mock_update_checklist.assert_called_once_with(CHECKLIST_PATH, BASE_URL, mock_lock)

@patch('scrape_docs.fetch_url_content')
@patch('scrape_docs.update_checklist_file')
@patch('builtins.open', new_callable=MagicMock)
def test_no_image_download_attempt(mock_open, mock_update_checklist, mock_fetch):
    """
    Explicitly tests that fetch_url_content is not called for image URLs.
    """
    # --- Arrange ---
    html_with_images = """
    <html><body>
      <img src="image1.png" alt="Image 1">
      <img src="/images/image2.svg" alt="Image 2">
      <img src="https://external.com/image3.jpg" alt="Image 3">
    </body></html>
    """
    mock_fetch.return_value = html_with_images

    # --- Act ---
    process_single_url(BASE_URL, "example_com", OUTPUT_DIR, CHECKLIST_PATH, mock_lock)

    # --- Assert ---
    # Check fetch was called exactly once, only for the base URL
    mock_fetch.assert_called_once_with(BASE_URL)

    # Verify it wasn't called for any of the image URLs
    image_urls = [
        "http://example.com/docs/image1.png",
        "http://example.com/images/image2.svg",
        "https://external.com/image3.jpg"
    ]
    # Correct indentation for loop
    for img_url in image_urls:
        assert call(img_url) not in mock_fetch.call_args_list

    # Check checklist was updated
    mock_update_checklist.assert_called_once()
    # Check file write did NOT happen
    mock_open.assert_not_called()
