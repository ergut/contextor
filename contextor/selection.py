"""
File selection module for Contextor.

This module handles file selection through interactive picking,
scope file management, and identifying important files for
smart selection.
"""

import os
import sys
from pathlib import Path

from contextor.utils import should_exclude, is_binary_file


def is_important_file(file_path):
    """Determine if a file is likely to be important based on predefined rules."""
    path_lower = str(file_path).lower()
    
    # Entry points
    if any(file in path_lower for file in [
        "main.py", "app.py", "index.py", "server.py",
        "main.js", "index.js", "app.js",
        "main.go", "main.rs", "main.cpp"
    ]):
        return True
    
    # Configuration files
    if any(path_lower.endswith(ext) for ext in [
        ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg",
        "requirements.txt", "package.json", "cargo.toml", "go.mod"
    ]):
        return True
    
    # Documentation
    if any(doc in path_lower for doc in [
        "readme", "contributing", "changelog", "license",
        "documentation", "docs/", "wiki/"
    ]):
        return True
    
    return False


def get_all_files(directory, spec, smart_select=False):
    """Get list of all files in directory that aren't excluded by spec"""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(os.path.join(root, filename))
            
            # Skip if excluded by gitignore patterns
            if should_exclude(file_path, directory, spec):
                continue

            # Skip binary files
            if is_binary_file(str(file_path)):
                continue
                            
            # Skip files larger than 10MB
            try:
                if file_path.stat().st_size > 10 * 1024 * 1024:
                    print(f"Warning: Skipping large file ({file_path}) - size exceeds 10MB")
                    continue
            except OSError:
                continue
            
            # Apply smart selection if enabled
            if smart_select and not is_important_file(file_path):
                continue
                
            files.append(str(file_path))
    
    return sorted(files)


def read_scope_file(scope_file_path, directory):
    """Read file paths from a scope file.
    
    Supports both absolute paths and paths relative to project directory.
    Ignores comments and empty lines.
    """
    if not os.path.exists(scope_file_path):
        return []
        
    try:
        with open(scope_file_path, 'r', encoding='utf-8') as f:
            result = []
            for line in f:
                # Skip empty lines and comments
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                    
                # Remove bullet point if present and strip again
                cleaned_line = stripped_line.lstrip('- ').strip()
                if not cleaned_line:  # Skip if empty after cleaning
                    continue
                    
                # Remove inline comments
                if '#' in cleaned_line:
                    cleaned_line = cleaned_line.split('#')[0].strip()
                
                # Handle relative paths (convert to absolute)
                if not os.path.isabs(cleaned_line):
                    cleaned_line = os.path.join(directory, cleaned_line)
                    
                # Normalize path
                normalized_path = os.path.normpath(cleaned_line)
                
                if os.path.exists(normalized_path):  # Only add if exists
                    result.append(normalized_path)
                else:
                    print(f"Warning: File in scope not found - {cleaned_line}")
                    
            return result
    except Exception as e:
        print(f"Error reading scope file: {str(e)}")
        return []


def write_scope_file(scope_file_path, file_paths, directory):
    """Write selected file paths to a scope file, using relative paths.
    
    Creates a nice, readable format with comments.
    """
    try:
        with open(scope_file_path, 'w', encoding='utf-8') as f:
            f.write("# Contextor Scope File\n")
            f.write("# Contains files to include in context generation\n")
            f.write("# Paths are relative to project root\n\n")
            
            # Group files by directory for better organization
            file_groups = {}
            for file_path in file_paths:
                try:
                    # Convert to relative path
                    rel_path = os.path.relpath(file_path, directory)
                    dir_name = os.path.dirname(rel_path) or '.'
                    if dir_name not in file_groups:
                        file_groups[dir_name] = []
                    file_groups[dir_name].append(rel_path)
                except ValueError:
                    # If we can't get a relative path, use the absolute
                    f.write(f"{file_path}\n")
            
            # Write grouped files with directory headers
            for group in sorted(file_groups.keys()):
                if group != '.':
                    f.write(f"\n# {group}/\n")
                else:
                    f.write("\n# Root directory\n")
                    
                for rel_path in sorted(file_groups[group]):
                    f.write(f"{rel_path}\n")
                    
        print(f"✓ Scope file updated: {scope_file_path}")
        return True
    except Exception as e:
        print(f"Error writing scope file: {str(e)}")
        return False


def run_interactive_picker(directory, spec, preselected_files=None):
    """Allow user to interactively select files to include in the context"""
    import questionary
    from questionary import Separator
    
    print("\nScanning project files...")

    all_files = get_all_files(directory, spec, smart_select=False)
    
    # Create a list of important files for highlighting
    important_files = [f for f in all_files if is_important_file(f)]
    
    # If we have preselected files, use those instead of important_files
    # for determining what's checked by default
    if preselected_files:
        checked_files = preselected_files
    else:
        checked_files = important_files
    
    # Group files by directory for better organization
    file_groups = {}
    for file_path in all_files:
        rel_path = os.path.relpath(file_path, directory)
        dir_name = os.path.dirname(rel_path) or '.'
        if dir_name not in file_groups:
            file_groups[dir_name] = []
        file_groups[dir_name].append(file_path)
    
    # Sort directories and files within directories
    sorted_groups = sorted(file_groups.keys())
    
    # Build choices list
    choices = []
    for group in sorted_groups:
        # Add a separator for each directory
        choices.append(Separator(f"--- {group} ---"))
        
        # Add files in this directory
        for file_path in sorted(file_groups[group]):
            rel_path = os.path.relpath(file_path, directory)
            
            # Mark files as selected if in preselected_files or important
            is_checked = file_path in checked_files
            
            # Add a ✨ indicator for smart-selected files
            file_display = rel_path
            if file_path in important_files and preselected_files:
                file_display = f"{rel_path} ✨"  # Star indicator for smart files
                
            choices.append(questionary.Choice(
                file_display,
                value=file_path,
                checked=is_checked
            ))
    
    try:
        # Show interactive selection dialog
        selected_files = questionary.checkbox(
            "Select files to include in your context:",
            choices=choices,
            instruction="Use arrows to move, <space> to select, <a> to toggle all, <i> to invert, <Enter> to confirm, Ctrl+C to cancel"
        ).ask()
        
        if selected_files is None:  # This happens when user cancels
            print("Selection cancelled. Exiting...")
            sys.exit(0)
            
        return selected_files
            
    except KeyboardInterrupt:
        print("\nSelection cancelled. Exiting...")
        sys.exit(0)


def read_files_from_txt(file_path):
    """Read list of files from a text file.
    
    Supports both plain paths and bullet-point format:
        path/to/file.txt
        - path/to/another_file.py
        
    Ignores:
        - Empty lines
        - Comment lines (starting with #)
        - Lines that become empty after stripping
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            result = []
            for line in f:
                # Skip empty lines and comments
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                    
                # Remove bullet point if present and strip again
                cleaned_line = stripped_line.lstrip('- ').strip()
                if cleaned_line:  # Add only non-empty lines
                    result.append(cleaned_line)
                    
            return result
    except Exception as e:
        print(f"Error reading file list: {str(e)}")
        return []