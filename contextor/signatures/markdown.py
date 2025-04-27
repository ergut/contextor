"""
Markdown TOC extraction module for Contextor.

This module extracts the table of contents structure from Markdown files
by identifying headings and their hierarchy.
"""

import re
from typing import List, Tuple

def extract_markdown_toc(file_path: str, max_depth: int = 3) -> str:
    """Extract a table of contents from a Markdown file.
    
    Args:
        file_path: Path to the Markdown file
        max_depth: Maximum heading depth to include (1-6)
    
    Returns:
        Formatted table of contents string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all headings using regex
        # This pattern matches both # style and underline style headings
        heading_pattern = re.compile(
            r'^(#{1,6})\s+(.+?)(?:\s+#{1,6})?$|'  # #-style headings
            r'^([^\n]+)\n([=\-]+)$',              # underline-style headings
            re.MULTILINE
        )
        
        headings = []
        
        for match in heading_pattern.finditer(content):
            if match.group(1):  # #-style heading
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((level, text))
            else:  # underline-style heading
                level = 1 if match.group(4)[0] == '=' else 2
                text = match.group(3).strip()
                headings.append((level, text))
        
        # Filter by max depth and format
        toc_lines = []
        
        for level, text in headings:
            if level <= max_depth:
                # Create anchor from heading text
                anchor = text.lower().replace(' ', '-')
                # Remove non-alphanumeric characters except dashes
                anchor = re.sub(r'[^\w\-]', '', anchor)
                
                indent = '    ' * (level - 1)
                toc_lines.append(f"{indent}- {text}")
        
        if not toc_lines:
            return "No headings found in document."
        
        return "\n".join(toc_lines)
    
    except Exception as e:
        return f"Error extracting TOC: {str(e)}"

def format_markdown_toc(file_path: str, max_depth: int = 3) -> str:
    """Format a markdown TOC with heading indicators."""
    toc = extract_markdown_toc(file_path, max_depth)
    
    # Add header to the TOC
    header = "Table of Contents:\n"
    return header + toc