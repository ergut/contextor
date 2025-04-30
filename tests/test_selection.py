"""
Tests for file selection functionality.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from pathspec import PathSpec
from contextor.selection import (
    is_important_file,
    get_all_files,
    read_scope_file,
    write_scope_file,
    run_interactive_picker,
    read_files_from_txt
)

@pytest.fixture
def test_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test directory structure
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "config"))
        os.makedirs(os.path.join(tmp_dir, "docs"))
        
        # Create test files
        files = {
            "src/main.py": "def main(): pass",
            "src/utils.py": "def util(): pass",
            "config/settings.yaml": "key: value",
            "docs/README.md": "# Documentation",
            ".env": "SECRET=123",
            "package.json": '{"name": "test"}',
        }
        
        for path, content in files.items():
            full_path = os.path.join(tmp_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
                
        yield tmp_dir

def test_is_important_file():
    """Test detection of important files."""
    # Test entry points
    assert is_important_file("src/main.py")
    assert is_important_file("app.py")
    assert is_important_file("index.js")
    assert is_important_file("server.py")
    
    # Test config files
    assert is_important_file("config.yaml")
    assert is_important_file("package.json")
    assert is_important_file("requirements.txt")
    
    # Test documentation
    assert is_important_file("README.md")
    assert is_important_file("docs/contributing.md")
    assert is_important_file("CHANGELOG.md")
    
    # Test non-important files
    assert not is_important_file("temp.txt")
    assert not is_important_file("data.csv")
    assert not is_important_file("test_utils.py")

def test_get_all_files(test_project):
    """Test file collection with exclusions."""
    patterns = ["*.env", "__pycache__/"]
    spec = PathSpec.from_lines('gitwildmatch', patterns)
    
    # Test normal collection
    files = get_all_files(test_project, spec)
    assert any("main.py" in f for f in files)
    assert any("settings.yaml" in f for f in files)
    assert not any(".env" in f for f in files)  # Should be excluded
    
    # Test smart selection
    smart_files = get_all_files(test_project, spec, smart_select=True)
    assert any("main.py" in f for f in smart_files)  # Important file
    assert any("package.json" in f for f in smart_files)  # Important file
    assert not any("utils.py" in f for f in smart_files)  # Not important

def test_read_scope_file(test_project):
    """Test reading files from scope file."""
    scope_content = """
    # Files to include
    src/main.py
    - config/settings.yaml
      docs/README.md  # With comment
    """
    
    scope_file = os.path.join(test_project, ".contextor_scope")
    with open(scope_file, 'w') as f:
        f.write(scope_content)
    
    files = read_scope_file(scope_file, test_project)
    assert len(files) == 3
    assert any("main.py" in f for f in files)
    assert any("settings.yaml" in f for f in files)
    assert any("README.md" in f for f in files)

def test_write_scope_file(test_project):
    """Test writing files to scope file."""
    scope_file = os.path.join(test_project, ".contextor_scope")
    files = [
        os.path.join(test_project, "src/main.py"),
        os.path.join(test_project, "config/settings.yaml")
    ]
    
    # Write scope file
    success = write_scope_file(scope_file, files, test_project)
    assert success
    
    # Verify content
    with open(scope_file, 'r') as f:
        content = f.read()
        assert "# Contextor Scope File" in content
        assert "src/main.py" in content
        assert "config/settings.yaml" in content
        assert "utils.py" not in content

def test_run_interactive_picker(test_project):
    """Test interactive file selection."""
    mock_choices = [
        os.path.join(test_project, "src/main.py"),
        os.path.join(test_project, "config/settings.yaml")
    ]
    
    with patch('questionary.checkbox') as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = mock_choices
        
        selected = run_interactive_picker(
            test_project,
            PathSpec.from_lines('gitwildmatch', []),
            preselected_files=[]
        )
        
        assert selected == mock_choices
        mock_checkbox.assert_called_once()

def test_run_interactive_picker_with_preselection(test_project):
    """Test interactive picker with preselected files."""
    preselected = [os.path.join(test_project, "src/main.py")]
    mock_choices = [
        os.path.join(test_project, "src/main.py"),
        os.path.join(test_project, "config/settings.yaml")
    ]
    
    with patch('questionary.checkbox') as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = mock_choices
        
        selected = run_interactive_picker(
            test_project,
            PathSpec.from_lines('gitwildmatch', []),
            preselected_files=preselected
        )
        
        assert selected == mock_choices
        # Verify that preselected files were passed to questionary
        call_args = mock_checkbox.call_args[1]
        assert any(choice.checked for choice in call_args['choices']
                  if str(choice.value) == preselected[0])

def test_run_interactive_picker_cancelled(test_project):
    """Test handling of cancelled selection."""
    with patch('questionary.checkbox') as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = None
        
        with pytest.raises(SystemExit):
            run_interactive_picker(
                test_project,
                PathSpec.from_lines('gitwildmatch', []),
                preselected_files=[]
            )