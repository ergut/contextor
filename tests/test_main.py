"""Test main functionality of Contextor"""
import pytest
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from pathspec import PathSpec
from contextor.utils import should_exclude
from contextor.main import (
    generate_tree,
    parse_patterns_file,
    merge_files,
    calculate_total_size,
    get_all_files,
    read_files_from_txt,
)
from contextor.cli import parse_args

@pytest.fixture
def test_dir():
    """Create a temporary test directory with sample files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test directory structure
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "tests"))
        os.makedirs(os.path.join(tmp_dir, "docs"))
        
        # Create test files
        files = {
            "src/main.py": "print('main')",
            "src/utils.py": "def util(): pass",
            "tests/test_main.py": "def test_main(): pass",
            "docs/README.md": "# Documentation",
            ".gitignore": "*.pyc\n__pycache__/",
        }
        
        for path, content in files.items():
            full_path = os.path.join(tmp_dir, path)
            with open(full_path, 'w') as f:
                f.write(content)
                
        yield tmp_dir

def test_generate_tree(test_dir):
    """Test tree structure generation"""
    tree = generate_tree(test_dir)
    
    expected_dirs = ['src/', 'tests/', 'docs/']
    for dir_name in expected_dirs:
        assert any(dir_name in line for line in tree), f"Directory {dir_name} not found in tree"
    
    expected_files = ['main.py', 'utils.py', 'test_main.py', 'README.md']
    for file_name in expected_files:
        assert any(file_name in line for line in tree), f"File {file_name} not found in tree"

def test_parse_patterns_file(test_dir):
    """Test parsing of pattern files"""
    patterns_file = os.path.join(test_dir, "patterns.txt")
    test_patterns = "*.pyc\n#Comment\n\n__pycache__/"
    
    with open(patterns_file, 'w') as f:
        f.write(test_patterns)
    
    patterns = parse_patterns_file(patterns_file)
    assert len(patterns) == 2, "Expected 2 patterns"
    assert "*.pyc" in patterns, "*.pyc pattern not found"
    assert "__pycache__/" in patterns, "__pycache__/ pattern not found"
    assert "#Comment" not in patterns, "Comment was incorrectly included"

def test_should_exclude(test_dir):
    """Test file exclusion logic"""
    patterns = ["*.pyc", "__pycache__/"]
    spec = PathSpec.from_lines('gitwildmatch', patterns)
    
    test_cases = [
        ("test.pyc", True),
        ("test.py", False),
        ("__pycache__/cache.txt", True),
        ("src/main.py", False)
    ]
    
    for filename, should_be_excluded in test_cases:
        test_file = Path(test_dir) / filename
        result = should_exclude(test_file, test_dir, spec)
        assert result == should_be_excluded, f"Wrong exclusion for {filename}"

def test_calculate_total_size(test_dir):
    """Test file size calculation"""
    files = [
        os.path.join(test_dir, "src/main.py"),
        os.path.join(test_dir, "src/utils.py")
    ]
    total_size = calculate_total_size(files)
    assert total_size > 0, "Total size should be greater than 0"

def test_get_all_files(test_dir):
    """Test getting all files respecting exclusions"""
    patterns = ["*.pyc", "__pycache__/"]
    spec = PathSpec.from_lines('gitwildmatch', patterns)
    
    files = get_all_files(test_dir, spec)
    expected_files = ['main.py', 'utils.py', 'test_main.py', 'README.md']
    
    for expected in expected_files:
        assert any(expected in f for f in files), f"Expected file {expected} not found"

@pytest.mark.parametrize('input_response', ['y', 'yes'])
def test_merge_files_all_files(test_dir, input_response):
    """Test merging all files in directory"""
    output_file = os.path.join(test_dir, "output.txt")
    
    with patch('builtins.input', return_value=input_response):
        merge_files(None, output_file, test_dir)
    
    assert os.path.exists(output_file), "Output file was not created"
    
    with open(output_file, 'r') as f:
        content = f.read()
        required_content = [
            "Project Context File",
            "src/main.py",
            "tests/test_main.py"
        ]
        for text in required_content:
            assert text in content, f"Missing required content: {text}"

def test_merge_files_specific_files(test_dir):
    """Test merging specific files"""
    output_file = os.path.join(test_dir, "output.txt")
    files_to_merge = [
        os.path.join(test_dir, "src/main.py"),
        os.path.join(test_dir, "docs/README.md")
    ]
    
    # Don't include signatures when testing specific files
    merge_files(files_to_merge, output_file, test_dir, include_signatures=False)
    
    with open(output_file, 'r') as f:
        content = f.read()
        assert "print('main')" in content, "main.py content missing"
        assert "# Documentation" in content, "README.md content missing"
        assert "def util()" not in content, "utils.py content shouldn't be included"

@pytest.mark.parametrize('test_content,expected_files', [
    ("""
    # Test files list
    src/main.py
    - src/utils.py
      - tests/test_main.py  
    docs/README.md
      plain_file.txt
    - with_dash.txt
    """,
    ['src/main.py', 'src/utils.py', 'tests/test_main.py', 
     'docs/README.md', 'plain_file.txt', 'with_dash.txt']),
], ids=['mixed_format_list'])  # Add this ids parameter
def test_read_files_from_txt_formats(test_dir, test_content, expected_files):
    """Test reading files list with different formats"""
    file_list_path = os.path.join(test_dir, "files_list.txt")
    
    with open(file_list_path, 'w') as f:
        f.write(test_content)
    
    files = read_files_from_txt(file_list_path)
    assert files == expected_files, "Files list not parsed correctly"
    assert len(files) == len(expected_files), "Not all files were parsed"

def test_read_files_from_txt_empty_and_comments(test_dir):
    """Test reading files list with empty lines and comments"""
    file_list_path = os.path.join(test_dir, "files_list_with_comments.txt")
    test_content = """
    # This is a comment
    - file1.txt

    # Another comment
      - file2.txt  

    file3.txt
    # End comment
    """
    
    with open(file_list_path, 'w') as f:
        f.write(test_content)
    
    files = read_files_from_txt(file_list_path)
    expected_files = ['file1.txt', 'file2.txt', 'file3.txt']
    assert files == expected_files, "Files list not parsed correctly"

def test_read_files_from_txt_error_handling(test_dir):
    """Test error handling when reading files list"""
    non_existent_file = os.path.join(test_dir, "does_not_exist.txt")
    files = read_files_from_txt(non_existent_file)
    assert files == [], "Should return empty list for non-existent file"

def test_pip_install_editable(tmp_path):
    """Test pip install -e . works correctly"""
    # Create minimal package structure
    pkg_dir = tmp_path / "test_package"
    pkg_dir.mkdir()
    
    # Create pyproject.toml
    with open(pkg_dir / "pyproject.toml", "w") as f:
        f.write("""
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test_package"
version = "0.1.0"
description = "Test package"
""")
    
    # Create setup.py
    with open(pkg_dir / "setup.py", "w") as f:
        f.write("""
from setuptools import setup, find_packages
setup(name="test_package", packages=find_packages())
""")

    # Create package
    (pkg_dir / "test_package").mkdir()
    (pkg_dir / "test_package" / "__init__.py").touch()
    
    # Run pip install -e
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=pkg_dir,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Installation failed:\n{result.stderr}"

def test_cli_parser_no_prefix_appendix():
    """Test that prefix_file and appendix_file options are removed"""
    # Test with minimal arguments
    test_args = parse_args(['--directory', '.'])
    assert not hasattr(test_args, 'prefix_file'), "prefix_file option should not exist"
    assert not hasattr(test_args, 'appendix_file'), "appendix_file option should not exist"

def test_cli_signature_options():
    """Test new signature-related CLI options"""
    test_args = parse_args(['--no-signatures', '--max-signature-files', '10', '--all-signatures'])
    assert test_args.no_signatures
    assert test_args.max_signature_files == 10
    assert test_args.all_signatures

def test_cli_git_options():
    """Test Git-related CLI options"""
    test_args = parse_args(['--no-git-markers'])
    assert test_args.no_git_markers