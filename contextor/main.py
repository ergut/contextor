"""
File Merger with Tree Structure and Token Estimation

A Python script that merges multiple files into a single output file while including
a tree-like directory structure at the beginning.
"""

import os, sys
from pathlib import Path
import pathspec
from datetime import datetime
import re
import pyperclip

from contextor.signatures import process_file_signatures, get_signature_files, generate_signatures_section
from contextor.utils import (
    is_git_repo,
    get_git_tracked_files,
    estimate_tokens,
)
from contextor.selection import get_all_files
from contextor.tree import generate_tree
from contextor.clipboard import copy_to_clipboard

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
    files from the project tree.
    
    If you need additional files, please suggest a specific command like:
    `contextor --no-signatures --files file1.py file2.py`
    I can run this locally and paste the results."

3. Then ask your questions about the project
-----------------------------------------------
""")

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
    outfile.write("\n")

def parse_patterns_file(patterns_file_path):
    """Parse a patterns file and return a list of patterns"""
    if not os.path.exists(patterns_file_path):
        return []

    with open(patterns_file_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return patterns

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
                use_gitignore=True, exclude_file=None,
                include_signatures=True, max_signature_files=None, 
                md_heading_depth=3, git_only_signatures=True, 
                no_git_markers=False):
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
            print("\nNo files specified. This will include all files in the directory (respecting .gitignore).")
            
            all_files = get_all_files(directory, spec)
            total_size = calculate_total_size(all_files)
            total_size_mb = total_size / (1024 * 1024)
            
            if not ask_user_confirmation(total_size_mb):
                print("Operation cancelled by user.")
                return
            
            file_paths = all_files
            print(f"Including {len(file_paths)} files from directory...")

        # Initialize content for token estimation
        full_content = ""

        # Generate tree output
        git_tracked_files = None
        if is_git_repo(directory):
            git_tracked_files = get_git_tracked_files(directory)
        tree_output = '\n'.join(generate_tree(Path(directory), spec, git_tracked_files=git_tracked_files))
        full_content += tree_output + "\n\n"

        # Add file contents
        full_content += "## Included File Contents\nThe following files are included in full:\n\n"
        for file_path in file_paths:
            if file_path.strip().startswith('#'):
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
        
        # Generate signatures section if enabled
        signatures_content = ""
        has_signatures = False
        if include_signatures:
            signatures_content, has_signatures = generate_signatures_section(
                directory,
                file_paths,
                spec,
                max_signature_files,
                md_heading_depth,
                git_only_signatures
            )
            full_content += signatures_content

        total_tokens = estimate_tokens(full_content)

        # Now write the actual output file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Write the conversation header
            write_conversation_header(outfile, directory, total_tokens, has_signatures)
            
            # Write the tree structure
            tree_output = '\n'.join(generate_tree(Path(directory), spec, '', git_tracked_files))
            outfile.write(f"\n{tree_output}\n\n")
            
            # Add section listing included files
            write_included_files_section(outfile, file_paths, directory)
            
            # Write file contents
            outfile.write("## Included File Contents\nThe following files are included in full:\n\n")

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
            
            # Write signatures section
            if signatures_content:
                outfile.write(signatures_content)

        if total_tokens:
            print(f"\n✓ Estimated token count: {total_tokens:,}")
        print(f"✅ Successfully created context file: {output_file}")

        # Always copy to clipboard by default
        copy_to_clipboard(output_file)
        print_usage_tips()

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

if __name__ == "__main__":
    # Inform users that this isn't the right way to run the tool anymore
    print("Note: Running contextor directly from main.py is deprecated.")
    print("Please use 'contextor' or 'python -m contextor' instead.")
    
    # Import and call the new entry point for backwards compatibility
    from contextor.cli import run_cli
    run_cli()