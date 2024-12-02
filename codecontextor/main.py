"""
File Merger with Tree Structure and Token Estimation

A Python script that merges multiple files into a single output file while including
a tree-like directory structure at the beginning. The script supports .gitignore patterns
and additional exclude patterns for excluding files and directories from the tree output.

Features:
- Merge multiple files with custom headers
- Generate tree structure of directories
- Support for .gitignore patterns and additional exclude patterns
- Custom prefix text support
- Multiple input methods (direct file list or file containing paths)
- Automatic inclusion of all files when no specific files are provided
- Smart selection of important files
- Clear listing of included files

Usage:
    python script.py --files file1.txt file2.txt --output merged.txt
    python script.py --files-list files.txt --prefix "My Project Files"
    python script.py --prefix-file prefix.txt --directory ./project --no-gitignore
    python script.py --exclude-file exclude.txt
    python script.py --directory ./project  # Will include all files
    python script.py --smart-select  # Will include only important files

Author: Salih Ergüt
"""

import os
import argparse
from pathlib import Path
import pathspec
from datetime import datetime
import re

def estimate_tokens(text):
    """Estimate the number of tokens in text using word-based approximation"""
    # Split on whitespace and punctuation
    words = re.findall(r'\w+|[^\w\s]', text)
    # Use 0.75 as a conservative ratio (most GPT models average 0.75 tokens per word)
    return int(len(words) / 0.75)

def write_conversation_header(outfile, project_path, total_tokens=None):
    """Write a header explaining how to use this file in conversations"""
    header = f"""# Project Context File
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project Path: {project_path}"""

    if total_tokens is not None:
        header += f"\nEstimated Tokens: {total_tokens:,}"

    header += """

## How to Use This File
1. The tree structure below shows ALL available files in the project
2. Some key files are included in full after the tree
3. During conversation, you can request the contents of any file shown in the tree

## Available Files
"""
    outfile.write(header)

def write_included_files_section(outfile, files, base_path):
    """Write a section listing all included files"""
    outfile.write("""
## Files Included in Full
The following files are included in their entirety in this context:

""")
    
    for file_path in files:
        # Convert to relative path for cleaner output
        try:
            rel_path = os.path.relpath(file_path, base_path)
            outfile.write(f"- {rel_path}\n")
        except ValueError:
            outfile.write(f"- {file_path}\n")
    
    outfile.write("""
Note for humans: To modify this selection for future runs, copy these paths to a text file and use:
codecontextor --files-list your_file.txt

""")

def parse_patterns_file(patterns_file_path):
    """Parse a patterns file and return a list of patterns"""
    if not os.path.exists(patterns_file_path):
        return []

    with open(patterns_file_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return patterns

def should_exclude(path, base_path, spec):
    """Check if path should be excluded based on combined patterns"""
    if spec is None:
        return False
    try:
        rel_path = path.relative_to(base_path)
        rel_path_str = str(rel_path).replace(os.sep, '/')
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

        if prefix:
            entries.append(prefix + format_name(item, is_last))
        else:
            entries.append(format_name(item, is_last))

        if item.is_dir():
            extension = '    ' if is_last else '│   '
            new_prefix = prefix + extension
            entries.extend(generate_tree(item, spec, new_prefix))

    return entries

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

def calculate_total_size(file_paths):
    """Calculate total size of files in bytes"""
    total_size = 0
    for file_path in file_paths:
        try:
            total_size += os.path.getsize(file_path)
        except (OSError, IOError):
            continue
    return total_size

def ask_user_confirmation(total_size_mb):
    """Ask user for confirmation if total size is large"""
    print(f"\nWarning: You're about to include all files in the directory.")
    print(f"Total size of files to be included: {total_size_mb:.2f} MB")
    response = input("Do you want to continue? [y/N]: ").lower()
    return response in ['y', 'yes']

def add_file_header(file_path):
    """Add descriptive header before file content"""
    return f"""
{'='*80}
File: {file_path}
Size: {os.path.getsize(file_path)} bytes
Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""

def merge_files(file_paths, output_file='merged_file.txt', directory=None, 
                use_gitignore=True, exclude_file=None, estimate_tokens_flag=False,
                smart_select=False, prefix_file=None, appendix_file=None):
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

        if file_paths is None:
            if smart_select:
                print("\nUsing smart file selection (including only key files)...")
            else:
                print("\nNo files specified. This will include all files in the directory (respecting .gitignore).")
            
            all_files = get_all_files(directory, spec, smart_select)
            total_size = calculate_total_size(all_files)
            total_size_mb = total_size / (1024 * 1024)
            
            if not ask_user_confirmation(total_size_mb):
                print("Operation cancelled by user.")
                return
            
            file_paths = all_files
            print(f"Including {len(file_paths)} files from directory...")

        # Initialize content for token estimation
        full_content = ""
        
        # First pass to collect all content if token estimation is needed
        if estimate_tokens_flag:
            tree_output = '\n'.join(generate_tree(Path(directory), spec))
            full_content += tree_output + "\n\n"
            full_content += "## Included File Contents\nThe following files are included in full:\n\n"
            
            for file_path in file_paths:
                if file_path.strip().startswith('#'):
                    continue

                if not os.path.exists(file_path):
                    continue

                try:
                    if os.path.getsize(file_path) > 10 * 1024 * 1024:
                        continue

                    full_content += add_file_header(file_path)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        full_content += infile.read()
                    full_content += '\n\n'
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")
            
            total_tokens = estimate_tokens(full_content)
        else:
            total_tokens = None

        # Now write the actual output file
        with open(output_file, 'w', encoding='utf-8') as outfile:

            # Write prefix if provided
            if prefix_file and os.path.exists(prefix_file):
                with open(prefix_file, 'r', encoding='utf-8') as pf:
                    outfile.write(pf.read())
                    outfile.write("\n\n")

            write_conversation_header(outfile, directory, total_tokens)
            tree_output = '\n'.join(generate_tree(Path(directory), spec))
            outfile.write(f"\n{tree_output}\n\n")
            
            # Add section listing included files
            write_included_files_section(outfile, file_paths, directory)
            
            outfile.write("""## Included File Contents
The following files are included in full:

""")

            for file_path in file_paths:
                if file_path.strip().startswith('#'):
                    continue

                if not os.path.exists(file_path):
                    print(f"Warning: File not found - {file_path}")
                    continue

                try:
                    if os.path.getsize(file_path) > 10 * 1024 * 1024:
                        print(f"Warning: Skipping large file ({file_path}) - size exceeds 10MB")
                        continue

                    outfile.write(add_file_header(file_path))
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write('\n\n')
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")

            if appendix_file and os.path.exists(appendix_file):
                outfile.write("\n# Appendix\n")
                with open(appendix_file, 'r') as af:
                    outfile.write(af.read())

        if total_tokens:
            print(f"\nEstimated token count: {total_tokens:,}")
        print(f"Successfully created context file: {output_file}")

    except Exception as e:
        print(f"Error creating context file: {str(e)}")

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
    
def main():
    parser = argparse.ArgumentParser(
        description='Create a project context file for LLM conversations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Include all files in current directory (will ask for confirmation)
  %(prog)s

  # Use smart file selection to automatically pick important files
  %(prog)s --smart-select

  # Include specific files from a project
  %(prog)s --directory ./my_project --files main.py config.yaml

  # Use a list of files from files.txt
  %(prog)s --files-list files.txt --output context.txt

  # Exclude specific patterns and estimate tokens
  %(prog)s --exclude-file exclude.txt --estimate-tokens

Notes:
  - If no files are specified, all files in directory will be included (with confirmation)
  - Files larger than 10MB are automatically skipped
  - The .gitignore patterns are respected by default
""")

    # File selection options
    file_group = parser.add_argument_group('file selection arguments')
    file_group.add_argument(
        '--files', 
        nargs='+', 
        help='Space-separated list of files to include in full (e.g., --files main.py config.yaml)'
    )
    file_group.add_argument(
        '--files-list', 
        type=str, 
        help='Path to a text file containing list of files to include (one file per line)'
    )
    file_group.add_argument(
        '--smart-select',
        action='store_true',
        help='Automatically select important files like entry points, configs, and docs'
    )

    context_group = parser.add_argument_group('context arguments')
    context_group.add_argument(
        '--prefix-file',
        type=str,
        help='File containing essential context to add at the start'
    )
    context_group.add_argument(
        '--appendix-file',
        type=str,
        help='File containing supplementary information to add at the end'
    )

    
    # Output options
    output_group = parser.add_argument_group('output arguments')
    output_group.add_argument(
        '--output', 
        type=str, 
        default='project_context.txt',
        help='Name of the output file (default: project_context.txt)'
    )
    output_group.add_argument(
        '--estimate-tokens', 
        action='store_true',
        help='Calculate and show estimated token count in the output file'
    )

    # Directory and exclusion options
    dir_group = parser.add_argument_group('directory and exclusion arguments')
    dir_group.add_argument(
        '--directory', 
        type=str, 
        help='Root directory to analyze (default: current directory)'
    )
    dir_group.add_argument(
        '--no-gitignore', 
        action='store_true',
        help='Ignore .gitignore patterns when scanning directory'
    )
    dir_group.add_argument(
        '--exclude-file', 
        type=str, 
        help='Path to a file containing additional exclude patterns (uses .gitignore syntax)'
    )

    args = parser.parse_args()

    files_to_merge = None
    if args.files_list:
        files_to_merge = read_files_from_txt(args.files_list)
    elif args.files:
        files_to_merge = args.files

    merge_files(
        files_to_merge, 
        args.output, 
        args.directory, 
        not args.no_gitignore, 
        args.exclude_file,
        args.estimate_tokens,
        args.smart_select,
        prefix_file=args.prefix_file,
        appendix_file=args.appendix_file,
    )

if __name__ == "__main__":
    main()