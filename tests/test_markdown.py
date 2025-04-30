"""
Tests for Markdown TOC extraction.
"""

import pytest
import os
import tempfile
from contextor.signatures.markdown import (
    extract_markdown_toc,
    format_markdown_toc
)

@pytest.fixture
def md_file():
    """Create a temporary Markdown file for testing."""
    content = """# Main Title

## Section 1
Some content

### Subsection 1.1
More content

## Section 2

### Subsection 2.1
Content here

#### Deep heading
Too deep by default

Alternative Title
================

Alternative Section
------------------
"""
    
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w') as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    os.unlink(temp_file)

def test_extract_markdown_toc_hash_style(md_file):
    """Test extraction of hash-style (#) headings."""
    toc = extract_markdown_toc(md_file)
    
    assert "- Main Title" in toc
    assert "    - Section 1" in toc
    assert "        - Subsection 1.1" in toc
    assert "    - Section 2" in toc
    assert "        - Subsection 2.1" in toc
    assert "Deep heading" not in toc  # Should be excluded by default max_depth=3

def test_extract_markdown_toc_underline_style(md_file):
    """Test extraction of underline-style (=== and ---) headings."""
    toc = extract_markdown_toc(md_file)
    
    assert "- Alternative Title" in toc
    assert "    - Alternative Section" in toc

def test_extract_markdown_toc_max_depth(md_file):
    """Test different max_depth values."""
    # Test with depth 1
    toc = extract_markdown_toc(md_file, max_depth=1)
    assert "- Main Title" in toc
    assert "Section 1" not in toc
    
    # Test with depth 4
    toc = extract_markdown_toc(md_file, max_depth=4)
    assert "            - Deep heading" in toc

def test_extract_markdown_toc_empty():
    """Test handling of empty or invalid files."""
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w') as f:
        f.write("Just some text\nNo headings here\n")
        temp_file = f.name
    
    try:
        toc = extract_markdown_toc(temp_file)
        assert "No headings found in document." in toc
    finally:
        os.unlink(temp_file)

def test_extract_markdown_toc_error_handling():
    """Test error handling for non-existent files."""
    toc = extract_markdown_toc("nonexistent.md")
    assert "Error extracting TOC:" in toc

def test_format_markdown_toc(md_file):
    """Test the full markdown TOC formatting."""
    result = format_markdown_toc(md_file)
    
    assert result.startswith("Table of Contents:")
    assert "- Main Title" in result
    assert "    - Section 1" in result
    assert "        - Subsection 1.1" in result