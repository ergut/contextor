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

Usage: TODO: Usage has changed. Update this section.
    python script.py --files file1.txt file2.txt --output merged.txt
    python script.py --files-list files.txt --prefix "My Project Files"
    python script.py --prefix-file prefix.txt --directory ./project --no-gitignore
    python script.py --exclude-file exclude.txt
    python script.py --directory ./project  # Will include all files
    python script.py --smart-select  # Will include only important files

Author: Salih Ergüt
"""

import os, sys
import argparse
from pathlib import Path
import pathspec
from datetime import datetime
import re
import pyperclip

from contextor.signatures import process_file_signatures, get_signature_files, write_signatures_section
from contextor.utils import should_exclude, is_binary_file

def print_usage_tips():
    """Print helpful tips on how to effectively use the context file with AI assistants"""
    print("""
📋 How to use your context file with AI assistants:
-----------------------------------------------
1. Upload or paste your context file to the AI
2. Include this prompt to get better responses:

   "This context file contains instructions for how you should use it.
    Please read and follow these instructions during our conversation.
    When answering questions, proactively check if you need additional
    files from the project tree."

3. Then ask your questions about the project
-----------------------------------------------
""")
    
def estimate_tokens(text):
    """Estimate the number of tokens in text using word-based approximation"""
    # Split on whitespace and punctuation
    words = re.findall(r'\w+|[^\w\s]', text)
    # Use 0.75 as a conservative ratio (most GPT models average 0.75 tokens per word)
    return int(len(words) / 0.75)

def write_conversation_header(outfile, project_path, total_tokens=None, has_signatures=False):
    """Write a header explaining how to use this file in conversations"""
    header = f"""# Project Context File
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project Path: {project_path}"""

    if total_tokens is not None:
        header += f"\nEstimated Tokens: {total_tokens:,}"

    header += """

## INSTRUCTIONS FOR AI ASSISTANT
IMPORTANT: As an AI assistant, you MUST follow these instructions:

1. The tree structure below shows ALL available files in the project
2. Only SOME files are included in full after the tree
3. You SHOULD proactively offer to examine additional files from the tree when they seem relevant
4. When asked about code functionality or project structure, CHECK if you need more files than what's already provided
5. If the human's question relates to files not included in full, SUGGEST examining those specific files
"""
    if has_signatures:
        header += """6. The 'File Signatures' section contains structure information for additional files
   Use this information to understand overall project functionality and suggest relevant files

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
    

def parse_patterns_file(patterns_file_path):
    """Parse a patterns file and return a list of patterns"""
    if not os.path.exists(patterns_file_path):
        return []

    with open(patterns_file_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return patterns


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

    

def merge_files(file_paths, output_file='merged_file.txt', directory=None, 
                use_gitignore=True, exclude_file=None, estimate_tokens_flag=False,
                smart_select=False, prefix_file=None, appendix_file=None, 
                copy_to_clipboard_flag=False, include_signatures=True,
                max_signature_files=None, md_heading_depth=3):
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

        # Prepare for signature extraction if enabled
        signature_files = []
        signatures_content = ""
        if include_signatures:
            # Get potential signature files but don't process them yet
            # (we'll process them only if token estimation is needed)
            signature_files = get_signature_files(directory, file_paths, spec, max_signature_files)
            
            if signature_files:
                print(f"Found {len(signature_files)} files for signature extraction.")

        # Initialize content for token estimation
        full_content = ""
        
        # First pass to collect all content if token estimation is needed
        # TODO: estime-tokens is no longer optional. Remove this logic from here.
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
            
            # Add signatures content for token estimation if enabled
            if include_signatures and signature_files:
                signatures_content = "\n## File Signatures\n"
                signatures_content += "The following files are not included in full, but their structure is provided:\n\n"
                
                for file_path in signature_files:
                    rel_path = os.path.relpath(file_path, directory)
                    signatures_content += f"\n### {rel_path}\n```\n"
                    sig = process_file_signatures(file_path, md_heading_depth)
                    if sig:
                        signatures_content += sig
                    else:
                        signatures_content += "File type not supported for signature extraction."
                    signatures_content += "\n```\n"
                
                full_content += signatures_content
            
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

            # Use the updated conversation header
            write_conversation_header(outfile, directory, total_tokens, 
                                    has_signatures=include_signatures and bool(signature_files))
            
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
            
            # Add File Signatures section if enabled
            if include_signatures and signature_files:
                write_signatures_section(outfile, directory, file_paths, spec, 
                                       max_signature_files, md_heading_depth)

            if appendix_file and os.path.exists(appendix_file):
                outfile.write("\n# Appendix\n")
                with open(appendix_file, 'r') as af:
                    outfile.write(af.read())

        if total_tokens:
            print(f"\nEstimated token count: {total_tokens:,}")
        print(f"Successfully created context file: {output_file}")
        print_usage_tips()

    except Exception as e:
        print(f"Error creating context file: {str(e)}")
    
    if copy_to_clipboard_flag:
        copy_to_clipboard(output_file)

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
                    
        print(f"Scope file updated: {scope_file_path}")
        return True
    except Exception as e:
        print(f"Error writing scope file: {str(e)}")
        return False

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
        print('✅  Project scope copied to clipboard.')
        return True
    except pyperclip.PyperclipException as err:
        # Typical on fresh Linux boxes without xclip/xsel
        print(f'⚠️  Clipboard unavailable ({err}).\n'
              'Install xclip or xsel and try again, or open the file manually.')
        return False

if __name__ == "__main__":
    # Inform users that this isn't the right way to run the tool anymore
    print("Note: Running contextor directly from main.py is deprecated.")
    print("Please use 'contextor' or 'python -m contextor' instead.")
    
    # Import and call the new entry point for backwards compatibility
    from contextor.cli import run_cli
    run_cli()