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
from .javascript import process_js_file
from .sql import process_sql_file

from contextor.utils import (
    should_exclude, 
    is_binary_file,
    is_git_repo,
    get_git_tracked_files,
)

def is_python_file(file_path: str) -> bool:
    """Check if file is a Python file."""
    return file_path.endswith('.py')

def is_markdown_file(file_path: str) -> bool:
    """Check if file is a Markdown file."""
    return file_path.lower().endswith(('.md', '.markdown'))

def is_js_ts_file(file_path: str) -> bool:
    """Check if file is a JavaScript or TypeScript file."""
    return file_path.lower().endswith(('.js', '.jsx', '.ts', '.tsx'))

def is_sql_file(file_path: str) -> bool:
    """Check if file is a SQL file."""
    return file_path.lower().endswith('.sql')

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
    elif is_js_ts_file(file_path):
        return process_js_file(file_path)
    elif is_sql_file(file_path):
        return process_sql_file(file_path)
    else:
        # Not a supported file type
        return None

def get_signature_files(directory: str, 
                        included_files: List[str], 
                        spec=None, 
                        max_files: Optional[int] = None,
                        git_only: bool = True,
                        ) -> List[str]:
    """Get list of files for signature extraction.
    
    Args:
        directory: Project directory 
        included_files: List of files already included in full
        spec: gitignore spec for exclusions
        max_files: Maximum number of files to include (None for unlimited)
        git_only: Whether to only include Git-tracked files
        
    Returns:
        List of file paths for signature extraction
    """
    # Convert included_files to a set for O(1) lookups
    included_set = set(os.path.abspath(f) for f in included_files)
    
    signature_files = []
    
    # Add Git tracking check
    git_tracked = set()
    if git_only and is_git_repo(directory):
        git_tracked = get_git_tracked_files(directory)
    
    # Priority lists to sort files by importance
    important_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.sql']
    
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            abs_path = os.path.abspath(file_path)
            
            # Skip if already included in full (this check must come first)
            if abs_path in included_set:
                continue

            # Skip if excluded by gitignore patterns
            if should_exclude(Path(file_path), directory, spec):
                continue

            # Skip binary files 
            if is_binary_file(file_path):
                continue

            # Skip if not git-tracked (using absolute path for comparison)
            if git_only and is_git_repo(directory):
                if abs_path not in git_tracked:
                    continue
                
            # Only include supported file types
            if not (is_python_file(file_path) or is_markdown_file(file_path) 
                   or is_js_ts_file(file_path) or is_sql_file(file_path)):
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
    
    # Apply limit if specified and git_only is True (don't limit when --all-signatures is used)
    if max_files is not None and max_files >= 0 and git_only:
        total_available = len(signature_files)
        signature_files = signature_files[:max_files]
        if total_available > max_files:
            print(f"Note: Found {total_available} files for signature extraction, but only including {max_files} due to max-signature-files limit.")
            print(f"      Use --max-signature-files option to include more signatures if needed.")
        else:
            print(f"Found {len(signature_files)} files for signature extraction.")
    else:
        print(f"Found {len(signature_files)} files for signature extraction.")
    
    return signature_files

def generate_signatures_section(directory: str,
                              included_files: List[str],
                              spec=None,
                              max_files: Optional[int] = None,
                              md_depth: int = 3,
                              git_only: bool = True) -> tuple[str, bool]:
    """Generate the File Signatures section content.
    
    Args:
        directory: Project directory
        included_files: List of files already included in full
        spec: gitignore spec object
        max_files: Maximum number of signature files to include 
        md_depth: Maximum depth for Markdown headings
        git_only: Whether to only include Git-tracked files
        
    Returns:
        Tuple of (signature content string, whether signatures were generated)
    """
    signature_files = get_signature_files(directory, included_files, spec, max_files, git_only)
    
    if not signature_files:
        return "", False
        
    content = [
        "\n## File Signatures",
        "The following files are not included in full, but their structure is provided:",
        ""
    ]
    
    for file_path in signature_files:
        rel_path = os.path.relpath(file_path, directory)
        content.extend([
            f"\n### {rel_path}",
            "```"
        ])
        
        signatures = process_file_signatures(file_path, md_depth)
        if signatures:
            content.append(signatures)
        else:
            content.append("File type not supported for signature extraction.")
            
        content.append("```\n")
    
    return "\n".join(content), True