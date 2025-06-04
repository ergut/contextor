import os
import subprocess
import re
from pathlib import Path

DEFAULT_EXCLUSIONS = {
    '.git/',                  # Git metadata
    '.conda/',                # Conda metadata
    '.venv/',                 # Virtual environment
    'venv/',                  # Virtual environment
    'node_modules/',          # NPM dependencies 
    '__pycache__/',           # Python cache
    '*.pyc',                  # Python compiled files
    '.idea/',                 # JetBrains IDE config
    '.vscode/',               # VS Code config
    'dist/',                  # Common build output
    'build/',                 # Common build output 
    'target/',                # Maven/other build output
    '.DS_Store',              # macOS metadata
    '.pytest_cache/',         # Pytest cache
    '.coverage/',             # Coverage reports
    'coverage/',              # Coverage reports (alternate location)
    'tmp/',                   # Temporary files
    'temp/',                  # Temporary files (alternate name)
    '.next/',                 # Next.js build output
    '.nuxt/',                 # Nuxt.js build output
    'out/',                   # Common output directory
    '.sass-cache/',           # Sass compilation cache
    '__tests__/__snapshots__/', # Jest snapshots
    '.ipynb_checkpoints/',    # Jupyter notebook checkpoints
    '*.lock'                  # Lock files like package-lock.json or yarn.lock    
}


def should_exclude(path, base_path, spec):
    """Check if path should be excluded based on combined patterns and defaults"""
    # First check against our hardcoded defaults
    try:
        rel_path = path.relative_to(base_path)
        rel_path_str = str(rel_path).replace(os.sep, '/')
        if path.is_dir():
            rel_path_str += '/'
            
        # Check against hardcoded exclusions first
        for pattern in DEFAULT_EXCLUSIONS:
            if pattern.endswith('/'):
                # Directory match - check if path is inside this directory
                if rel_path_str == pattern or rel_path_str.startswith(pattern):
                    return True
                # Also check if any parent directory matches
                if '/' in rel_path_str:
                    parts = rel_path_str.split('/')
                    for i in range(len(parts)):
                        parent_path = '/'.join(parts[:i+1]) + '/'
                        if parent_path == pattern:
                            return True
            elif '*' in pattern:
                # Simple wildcard matching
                pattern_parts = pattern.split('*')
                if len(pattern_parts) == 2:
                    if rel_path_str.startswith(pattern_parts[0]) and rel_path_str.endswith(pattern_parts[1]):
                        return True
            else:
                # Exact file match
                if rel_path_str == pattern:
                    return True
        
        # Then check against the provided spec
        if spec is not None:
            return spec.match_file(rel_path_str)
    except ValueError:
        pass
    
    return False

def is_binary_file(file_path):
    """Check if a file is likely to be binary based on extension or content"""
    # First check extension
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.bin', '.exe', '.dll',
        '.so', '.dylib', '.class', '.jar', '.pyc'
    }
    
    if any(file_path.lower().endswith(ext) for ext in binary_extensions):
        return True
        
    # If extension check is inconclusive, look at file content
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk  # Null bytes typically indicate binary content
    except (IOError, PermissionError):
        return True  # If we can't read it, best to assume it's binary

def is_git_repo(path):
    """Check if directory is a Git repository."""
    return os.path.isdir(os.path.join(path, '.git'))

def get_git_tracked_files(path):
    """Get set of Git-tracked files in repository."""
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--full-name'], 
            cwd=path, 
            stdout=subprocess.PIPE, 
            text=True,
            check=True
        )
        # Convert all paths to normalized absolute paths
        return set(os.path.normpath(os.path.abspath(os.path.join(path, f))) 
                  for f in result.stdout.splitlines())
    except (subprocess.SubprocessError, FileNotFoundError):
        # Git command failed or git not installed
        return set()
    
def estimate_tokens(text):
    """Estimate the number of tokens in text using word-based approximation"""
    # Split on whitespace and punctuation
    words = re.findall(r'\w+|[^\w\s]', text)
    # Use 0.75 as a conservative ratio (most GPT models average 0.75 tokens per word)
    return int(len(words) / 0.75)


def is_signature_file(file_path):
    """Check if file type is supported for signature extraction."""
    return (file_path.endswith('.py') or 
            file_path.lower().endswith(('.md', '.markdown')) or
            file_path.lower().endswith(('.js', '.jsx', '.ts', '.tsx')) or
            file_path.lower().endswith('.sql'))


def scan_project_files(directory, spec=None, git_only_signatures=True):
    """Single pass through project to categorize all files.
    
    Args:
        directory: Project directory path
        spec: gitignore spec for exclusions
        git_only_signatures: Whether to only include Git-tracked files for signatures
        
    Returns:
        dict with 'all_files', 'signature_candidates', 'git_tracked'
    """
    all_files = []
    signature_candidates = []
    
    # Get git tracking info once if needed
    git_tracked = set()
    if is_git_repo(directory):
        git_tracked = get_git_tracked_files(directory)
    
    # Single os.walk with directory filtering
    for root, dirnames, filenames in os.walk(directory):
        # Filter directories in-place to prevent walking into excluded dirs
        # Check each directory and remove excluded ones
        filtered_dirs = []
        for d in dirnames:
            dir_path = Path(os.path.join(root, d))
            if not should_exclude(dir_path, directory, spec):
                filtered_dirs.append(d)
        dirnames[:] = filtered_dirs
        
        for filename in filenames:
            file_path = os.path.join(root, filename)
            abs_path = os.path.abspath(file_path)
            
            # Skip if excluded by gitignore patterns
            if should_exclude(Path(file_path), directory, spec):
                continue

            # Skip binary files 
            if is_binary_file(file_path):
                continue
                
            # Skip files larger than 10MB
            try:
                if Path(file_path).stat().st_size > 10 * 1024 * 1024:
                    print(f"Warning: Skipping large file ({file_path}) - size exceeds 10MB")
                    continue
            except OSError:
                continue
            
            # Add to all_files (for interactive picker)
            all_files.append(file_path)
            
            # Check if it's a signature candidate
            if is_signature_file(file_path):
                # If git_only_signatures, check git tracking
                if not git_only_signatures or abs_path in git_tracked:
                    signature_candidates.append(file_path)
    
    return {
        'all_files': sorted(all_files),
        'signature_candidates': sorted(signature_candidates),
        'git_tracked': git_tracked
    }