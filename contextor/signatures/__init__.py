"""
Signature extraction module for Contextor.

This module provides functionality to extract structural information
from different file types without including their full content.
"""

from .processor import process_file_signatures, get_signature_files, generate_signatures_section
from .python import process_python_file
from .markdown import format_markdown_toc
from .javascript import process_js_file
from .sql import process_sql_file

__all__ = [
    'process_file_signatures',
    'get_signature_files', 
    'generate_signatures_section',
    'process_python_file',
    'format_markdown_toc',
    'process_js_file',
    'process_sql_file'
]