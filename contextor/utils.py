import os
import subprocess
import re

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
                # Directory match
                if rel_path_str == pattern or rel_path_str.startswith(pattern):
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
