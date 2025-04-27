"""
Signature extraction module for Contextor.

This module provides functionality to extract structural information
from different file types without including their full content.
"""

from .processor import process_file_signatures, get_signature_files, write_signatures_section

__all__ = [
    'process_file_signatures',
    'get_signature_files', 
    'write_signatures_section'
]