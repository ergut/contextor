"""
File Merger with Tree Structure

A Python script that merges multiple files into a single output file while including
a tree-like directory structure at the beginning. The script supports .gitignore patterns
and additional exclude patterns for excluding files and directories from the tree output.

Features:
- Merge multiple files with custom headers
- Generate tree structure of directories
- Support for .gitignore patterns and additional exclude patterns
- Custom prefix text support
- Multiple input methods (direct file list or file containing paths

Usage:
    python script.py --files file1.txt file2.txt --output merged.txt
    python script.py --files-list files.txt --prefix "My Project Files"
    python script.py --prefix-file prefix.txt --directory ./project --no-gitignore
    python script.py --exclude-file exclude.txt

Author: Salih Ergüt
"""

import os
import argparse
from pathlib import Path
import pathspec
from datetime import datetime

def write_conversation_header(outfile, project_path):
    """Write a header explaining how to use this file in conversations"""
    outfile.write(f"""# Project Context File
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project Path: {project_path}

## How to Use This File
1. The tree structure below shows ALL available files in the project
2. Some key files are included in full after the tree
3. During conversation, you can request the contents of any file shown in the tree

## Available Files
""")

def parse_patterns_file(patterns_file_path):
    """Parse a patterns file and return a list of patterns"""
    if not os.path.exists(patterns_file_path):
        return []

    with open(patterns_file_path, 'r') as f:
        # Don't modify patterns - keep them exactly as they appear in .gitignore
        patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return patterns

def should_exclude(path, base_path, spec):
    """Check if path should be excluded based on combined patterns"""
    if spec is None:
        return False
    try:
        rel_path = path.relative_to(base_path)
        # Convert to forward slashes for consistency
        rel_path_str = str(rel_path).replace(os.sep, '/')
        # Add trailing slash for directories to match .gitignore semantics
        if path.is_dir():
            rel_path_str += '/'
        return spec.match_file(rel_path_str)
    except ValueError:
        return False

def format_name(path, is_last):
    """Format the name with proper tree symbols"""
    prefix = '└── ' if is_last else '├── '
    return prefix + path.name + ('/' if path.is_dir() else '')

def generate_tree(path, spec=None, prefix=''):
    """Generate tree-like directory structure string with gitignore-style exclusions"""
    path = Path(path).resolve()
    if not path.exists():
        return []

    entries = []

    # Add the root directory
    if not prefix:
        entries.append(str(path))

    # Get all valid entries
    items = []
    try:
        for item in path.iterdir():
            if not should_exclude(item, path, spec):
                items.append(item)
    except PermissionError:
        return entries

    # Sort items (directories first, then files)
    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

    # Process all items
    for index, item in enumerate(items):
        is_last = index == len(items) - 1

        if prefix:
            entries.append(prefix + format_name(item, is_last))
        else:
            entries.append(format_name(item, is_last))

        if item.is_dir():
            extension = '    ' if is_last else '│   '
            new_prefix = prefix + extension
            entries.extend(generate_tree(item, spec, new_prefix))

    return entries

def add_file_header(file_path):
    """Add descriptive header before file content"""
    return f"""
{'='*80}
File: {file_path}
Size: {os.path.getsize(file_path)} bytes
Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""

def merge_files(file_paths, output_file='merged_file.txt', directory=None, use_gitignore=True, exclude_file=None):
    """Merge files with conversation-friendly structure"""
    try:
        directory = directory or os.getcwd()
        patterns = []

        if use_gitignore:
            gitignore_path = os.path.join(directory, '.gitignore')
            gitignore_patterns = parse_patterns_file(gitignore_path)
            patterns.extend(gitignore_patterns)

        if exclude_file:
            exclude_patterns = parse_patterns_file(exclude_file)
            patterns.extend(exclude_patterns)

        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns) if patterns else None

        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Write the conversation-friendly header
            write_conversation_header(outfile, directory)

            # Write the full tree structure
            tree_output = '\n'.join(generate_tree(Path(directory), spec))
            outfile.write(f"\n{tree_output}\n\n")
            
            # Separator between tree and included files
            outfile.write("""
## Included File Contents
The following files are included in full:

""")

            # Write included file contents
            for file_path in file_paths:
                if file_path.strip().startswith('#'):
                    continue

                if not os.path.exists(file_path):
                    print(f"Warning: File not found - {file_path}")
                    continue

                outfile.write(add_file_header(file_path))
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write('\n\n')
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")

        print(f"Successfully created context file: {output_file}")

    except Exception as e:
        print(f"Error creating context file: {str(e)}")

def read_files_from_txt(file_path):
    """Read list of files from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file list: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Create a project context file for LLM conversations.')
    parser.add_argument('--files', nargs='+', help='List of files to include in full')
    parser.add_argument('--files-list', type=str, help='Text file containing list of files to include')
    parser.add_argument('--output', type=str, default='project_context.txt', help='Output file name')
    parser.add_argument('--directory', type=str, help='Project directory to generate tree from (default: current directory)')
    parser.add_argument('--no-gitignore', action='store_true', help='Disable .gitignore-based exclusions')
    parser.add_argument('--exclude-file', type=str, help='File containing additional exclude patterns')

    args = parser.parse_args()

    files_to_merge = []
    if args.files_list:
        files_to_merge = read_files_from_txt(args.files_list)
    elif args.files:
        files_to_merge = args.files

    if not files_to_merge:
        print("No files specified to include. Will only generate directory tree.")

    merge_files(files_to_merge, args.output, args.directory, not args.no_gitignore, args.exclude_file)

if __name__ == "__main__":
    main()