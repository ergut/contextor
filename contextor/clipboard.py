"""
Clipboard utilities for Contextor.

This module provides functionality for copying content to the
system clipboard with appropriate size checks and error handling.
"""

import os
import pyperclip

def copy_to_clipboard(file_path, max_mb=2):
    """Copy the contents of a file to the system clipboard with size safeguards"""
    size_mb = os.path.getsize(file_path) / (1024*1024)
    if size_mb > max_mb:
        ans = input(f'Context file is {size_mb:.1f} MB – copy anyway? [y/N] ').lower()
        if ans not in ('y', 'yes'):
            return False
    try:
        with open(file_path, 'r', encoding='utf-8') as fp:
            pyperclip.copy(fp.read())
        print('✓ Project scope copied to clipboard.')
        return True
    except pyperclip.PyperclipException as err:
        # Typical on fresh Linux boxes without xclip/xsel
        print(f'⚠️  Clipboard unavailable ({err}).\n'
              'Install xclip or xsel and try again, or open the file manually.')
        return False