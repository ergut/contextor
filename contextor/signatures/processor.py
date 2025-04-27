"""
File signature processor module for Contextor.

This module coordinates the extraction of signatures from different file types,
determines which files should have signatures extracted, and writes the
signatures section to the output file.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set

# Import signature extractors
from .python import process_python_file
from .markdown import format_markdown_toc

from contextor.utils import should_exclude, is_binary_file

def is_python_file(file_path: str) -> bool:
    """Check if file is a Python file."""
    return file_path.endswith('.py')

def is_markdown_file(file_path: str) -> bool:
    """Check if file is a Markdown file."""
    return file_path.lower().endswith(('.md', '.markdown'))

def process_file_signatures(file_path: str, max_depth: int = 3) -> Optional[str]:
    """Process a file and extract signatures based on file type.
    
    Args:
        file_path: Path to the file
        max_depth: Maximum heading depth for Markdown files
        
    Returns:
        Formatted signature string or None if file type not supported
    """
    if is_python_file(file_path):
        return process_python_file(file_path)
    elif is_markdown_file(file_path):
        return format_markdown_toc(file_path, max_depth)
    else:
        # Not a supported file type
        return None

def get_signature_files(directory: str, 
                        included_files: List[str], 
                        spec=None, 
                        max_files: Optional[int] = None) -> List[str]:
    """Get list of files for signature extraction.
    
    Args:
        directory: Project directory 
        included_files: List of files already included in full
        spec: gitignore spec for exclusions
        max_files: Maximum number of files to include (None for unlimited)
        
    Returns:
        List of file paths for signature extraction
    """
    
    # Convert included_files to a set for O(1) lookups
    included_set = set(os.path.abspath(f) for f in included_files)
    
    signature_files = []
    
    # Priority lists to sort files by importance
    important_extensions = ['.py', '.md', '.js', '.ts', '.jsx', '.tsx']
    
    # Keep track of processed files
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            abs_path = os.path.abspath(file_path)
            
            # Skip if already included in full
            if abs_path in included_set:
                continue
                
            # Skip if excluded by gitignore patterns
            if should_exclude(Path(file_path), directory, spec):
                continue

            # Skip binary files
            if is_binary_file(file_path):
                continue
                
            # Only include supported file types
            if not (is_python_file(file_path) or is_markdown_file(file_path)):
                continue
                
            # Add to signature files
            signature_files.append(file_path)
    
    # Sort files by priority (important extensions first)
    def get_priority(file_path):
        _, ext = os.path.splitext(file_path.lower())
        try:
            return important_extensions.index(ext)
        except ValueError:
            return len(important_extensions)
    
    signature_files.sort(key=get_priority)
    
    # Limit the number of files if specified
    if max_files is not None and max_files >= 0:
        signature_files = signature_files[:max_files]
        
    return signature_files

def write_signatures_section(outfile, directory, included_files, spec=None, 
                            max_files=None, md_depth=3):
    """Write the File Signatures section to the output file.
    
    Args:
        outfile: Output file handle
        directory: Project directory
        included_files: List of files already included in full
        spec: gitignore spec object
        max_files: Maximum number of signature files to include 
        md_depth: Maximum depth for Markdown headings
    """
    signature_files = get_signature_files(directory, included_files, spec, max_files)
    
    if not signature_files:
        return
        
    outfile.write("""
## File Signatures
The following files are not included in full, but their structure is provided:

""")
    
    for file_path in signature_files:
        rel_path = os.path.relpath(file_path, directory)
        
        outfile.write(f"""
### {rel_path}
```
""")
        
        signatures = process_file_signatures(file_path, md_depth)
        if signatures:
            outfile.write(signatures)
        else:
            outfile.write("File type not supported for signature extraction.")
            
        outfile.write("```\n")