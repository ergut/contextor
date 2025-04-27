"""
Tree structure generation for Contextor.

This module provides functionality to generate tree-like directory
structures with support for gitignore-style exclusions and Git tracking status.
"""

from pathlib import Path
import os

def format_name(path, is_last, is_git_tracked=False):
    """Format the name with proper tree symbols and Git tracking indicator."""
    prefix = '└── ' if is_last else '├── '
    suffix = '/' if path.is_dir() else ''
    git_marker = ' ✓' if is_git_tracked else ''
    return prefix + path.name + suffix + git_marker

def generate_tree(path, spec=None, prefix='', git_tracked_files=None):
    """Generate tree-like directory structure string with gitignore-style exclusions"""
    from contextor.utils import should_exclude  # Import here to avoid circular imports
    
    path = Path(path).resolve()
    if not path.exists():
        return []

    entries = []

    if not prefix:
        entries.append(str(path))

    items = []
    try:
        for item in path.iterdir():
            if not should_exclude(item, path, spec):
                items.append(item)
    except PermissionError:
        return entries

    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

    for index, item in enumerate(items):
        is_last = index == len(items) - 1
        
        # Check if file is Git-tracked when git_tracked_files is provided
        is_git_tracked = False
        if git_tracked_files is not None:
            abs_path = str(item.resolve())
            is_git_tracked = abs_path in git_tracked_files

        if prefix:
            entries.append(prefix + format_name(item, is_last, is_git_tracked))
        else:
            entries.append(format_name(item, is_last, is_git_tracked))

        if item.is_dir():
            extension = '    ' if is_last else '│   '
            new_prefix = prefix + extension
            entries.extend(generate_tree(item, spec, new_prefix, git_tracked_files))

    return entries