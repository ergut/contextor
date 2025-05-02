"""
Command-line interface for Contextor.

This module handles parsing command-line arguments and setting up
the configuration for the main Contextor functionality.
"""

import argparse
import os
import pathspec
import sys
import tomli
from pathlib import Path

from contextor.main import (
    parse_patterns_file,
    merge_files,
)
from contextor.selection import (
    run_interactive_picker,
    read_scope_file,
    write_scope_file,
    get_all_files,
    is_important_file,
)

def get_version():
    """Get version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            return tomli.load(f)["project"]["version"]
    except (FileNotFoundError, KeyError, tomli.TOMLDecodeError):
        return "1.4.1"  # Fallback to current version

def parse_args(args=None):
    """Parse command line arguments"""
    # Use args if provided, otherwise use sys.argv[1:]

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="""
Create a context file from your codebase that's perfect for AI conversations.

Features:
  - Interactive file selection (default)
  - Tree view of project structure
  - File signature extraction
  - .gitignore support
  - Clipboard integration
  - Smart file selection
  - Scope file for reuse
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in interactive mode (default)
  %(prog)s

  # Use a saved selection from .contextor_scope file without interactive picking
  %(prog)s --use-scope

  # Use custom scope file
  %(prog)s --scope-file my_custom_scope.txt

  # Include specific files from a project (skips interactive mode)
  %(prog)s --directory ./my_project --files main.py config.yaml

  # Prevent updating the scope file after selection
  %(prog)s --no-update-scope
  
  # Exclude specific patterns in addition to .gitignore
  %(prog)s --exclude-file exclude_patterns.txt

  # Custom output file name (default is project_context.md)
  %(prog)s --output my_context.md
    
  # Disable file signature extraction
  %(prog)s --no-signatures
  
  # Limit the number of files included in the signatures section
  %(prog)s --max-signature-files 10

  # Set maximum heading depth for Markdown TOC extraction
  %(prog)s --md-heading-depth 2


Notes:
  - Interactive file selection is the default mode
  - Selected files are saved to .contextor_scope for future use
  - Files larger than 10MB are automatically skipped
  - Binary files are automatically excluded
  - .gitignore patterns are respected by default
  
""")

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {get_version()}'
    )

    # File selection options
    file_group = parser.add_argument_group('file selection arguments')
    file_group.add_argument(
        '--files', 
        nargs='+', 
        help='Space-separated list of files to include in full (e.g., --files main.py config.yaml)'
    )
    
    # Scope options (new primary way to select files)
    scope_group = parser.add_argument_group('scope arguments')
    scope_group.add_argument(
        '--scope-file',
        type=str,
        help='Path to scope file containing list of files to include (default: .contextor_scope)'
    )
    scope_group.add_argument(
        '--use-scope',
        action='store_true',
        help='Use scope file without interactive selection'
    )
    scope_group.add_argument(
        '--no-update-scope',
        action='store_true',
        help='Do not update scope file after selection'
    )

    # Signature options
    signature_group = parser.add_argument_group('signature extraction arguments')
    signature_group.add_argument(
        '--no-signatures',
        action='store_true',
        help='Disable file signature extraction'
    )
    signature_group.add_argument(
        '--max-signature-files',
        type=int,
        default=20,
        help='Maximum number of files to include in signatures section (default: unlimited)'
    )
    signature_group.add_argument(
        '--md-heading-depth',
        type=int,
        default=3,
        choices=range(1, 7),
        help='Maximum heading depth for Markdown TOC extraction (1-6, default: 3)'
    )
    signature_group.add_argument(
        '--all-signatures',
        action='store_true',
        help='Extract signatures from all Python/Markdown files, not just Git-tracked ones'
    )
    signature_group.add_argument(
        '--no-git-markers',
        action='store_true',
        help='Disable Git tracking indicators in the directory tree'
    )

    # Output options
    output_group = parser.add_argument_group('output arguments')
    output_group.add_argument(
        '--output', 
        type=str, 
        default='project_context.md',
        help='Name of the output file (default: project_context.md)'
    )


    # Directory and exclusion options
    directory_group = parser.add_argument_group('directory and exclusion arguments')
    directory_group.add_argument(
        '--directory',
        type=str,
        default='.',
        help='Project directory (default: current directory)'
    )
    directory_group.add_argument(
        '--no-gitignore',
        action='store_true',
        help='Do not use .gitignore patterns'
    )
    directory_group.add_argument(
        '--exclude-file',
        type=str,
        help='File containing additional patterns to exclude'
    )

    return parser.parse_args(args)

def run_cli():
    """Run the command-line interface."""    
    args = parse_args()
    
    # Create the directory and spec objects first
    directory = args.directory or os.getcwd()
    patterns = []

    if not args.no_gitignore:
        gitignore_path = os.path.join(directory, '.gitignore')
        gitignore_patterns = parse_patterns_file(gitignore_path)
        patterns.extend(gitignore_patterns)

    if args.exclude_file:
        exclude_patterns = parse_patterns_file(args.exclude_file)
        patterns.extend(exclude_patterns)

    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns) if patterns else None
 
    # Determine scope file path
    scope_file = args.scope_file or '.contextor_scope'
    scope_file_exists = os.path.exists(scope_file)

    # Handle file selection based on options
    files_to_merge = None

    if args.files:
        # Explicitly specified files
        files_to_merge = args.files
    elif args.use_scope and scope_file_exists:
        # Non-interactive mode with scope file
        print(f"\n✓ Using files from scope file: {scope_file}")
        files_to_merge = read_scope_file(scope_file, directory)
        if not files_to_merge:
            print("Warning: No valid files found in scope file.")
            return
    elif args.use_scope and not scope_file_exists:
        print(f"Error: Scope file not found: {scope_file}")
        print("Run without --use-scope to create an interactive selection.")
        return
    else:
        # Interactive mode - either use scope file contents for pre-selection
        # or fall back to smart selection if no scope file
        preselected_files = []
        if scope_file_exists:
            preselected_files = read_scope_file(scope_file, directory)
            print(f"\n✓ Loaded {len(preselected_files)} files from scope file for pre-selection.")
        else:
            # No scope file - pre-select smart files instead
            all_files = get_all_files(directory, spec, smart_select=False)
            preselected_files = [f for f in all_files if is_important_file(f)]
            print(f"\n✓ Preselected {len(preselected_files)} important files.")
        
        print("✓ Scanning project files...")
        # Run interactive picker with preselection
        files_to_merge = run_interactive_picker(directory, spec, preselected_files)
        
        # Update scope file unless told not to
        if not args.no_update_scope:
            write_scope_file(scope_file, files_to_merge, directory)

    merge_files(
        files_to_merge, 
        args.output, 
        args.directory, 
        not args.no_gitignore,
        args.exclude_file,
        include_signatures=not args.no_signatures,
        max_signature_files=args.max_signature_files,
        md_heading_depth=args.md_heading_depth,
        git_only_signatures=not args.all_signatures,
        no_git_markers=args.no_git_markers,
    )

if __name__ == "__main__":
    run_cli()