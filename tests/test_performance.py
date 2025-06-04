"""
Integration tests for performance optimizations in Contextor.

Tests the single-walk refactor that eliminates duplicate os.walk() calls.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import pathspec

from contextor.utils import scan_project_files
from contextor.main import parse_patterns_file
from contextor.selection import is_important_file


class TestPerformanceOptimizations:
    """Test performance-related optimizations."""
    
    @pytest.fixture
    def large_test_project(self):
        """Create a test project with excluded directories that should be skipped."""
        temp_dir = tempfile.mkdtemp(prefix="contextor_perf_test_")
        
        # Create directory structure with excludable dirs
        dirs = [
            "src", "tests", "docs",
            "node_modules/package1", "node_modules/package2/nested",
            ".git/objects", ".git/refs", 
            "build/dist", "build/temp",
            "__pycache__"
        ]
        
        for dir_name in dirs:
            os.makedirs(os.path.join(temp_dir, dir_name), exist_ok=True)
        
        # Create files in both included and excluded directories
        files = {
            # Should be included
            "README.md": "# Test Project",
            "main.py": "def main(): pass",
            "src/app.py": "class App: pass",
            "src/utils.py": "def helper(): return True", 
            "tests/test_main.py": "import unittest",
            "docs/guide.md": "# Guide\n## Section",
            "package.json": '{"name": "test"}',
            
            # Should be excluded
            "node_modules/package1/index.js": "// excluded",
            "node_modules/package2/nested/lib.js": "// excluded", 
            ".git/config": "# git config",
            ".git/objects/abc123": "git object",
            "build/dist/output.js": "// build output",
            "build/temp/cache.tmp": "temp file",
            "__pycache__/module.pyc": "bytecode",
        }
        
        for file_path, content in files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Create .gitignore
        gitignore_content = """
node_modules/
build/
*.pyc
__pycache__/
.git/
"""
        with open(os.path.join(temp_dir, ".gitignore"), 'w') as f:
            f.write(gitignore_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_scan_project_files_excludes_directories(self, large_test_project):
        """Test that scan_project_files properly excludes directories."""
        # Create gitignore spec
        gitignore_patterns = parse_patterns_file(os.path.join(large_test_project, ".gitignore"))
        spec = pathspec.PathSpec.from_lines('gitwildmatch', gitignore_patterns)
        
        # Scan the project
        result = scan_project_files(large_test_project, spec, git_only_signatures=False)
        
        # Convert to relative paths for easier checking
        all_files_rel = [os.path.relpath(f, large_test_project) for f in result['all_files']]
        
        # Should include these files
        expected_files = [
            ".gitignore", "README.md", "main.py", "package.json",
            "src/app.py", "src/utils.py", "tests/test_main.py", "docs/guide.md"
        ]
        
        for expected in expected_files:
            assert expected in all_files_rel, f"{expected} should be included"
        
        # Should NOT include these directories/files
        excluded_patterns = ["node_modules/", ".git/", "build/", "__pycache__/"]
        
        for pattern in excluded_patterns:
            excluded_files = [f for f in all_files_rel if f.startswith(pattern)]
            assert len(excluded_files) == 0, f"Files matching {pattern} should be excluded: {excluded_files}"
    
    def test_signature_candidates_categorization(self, large_test_project):
        """Test that signature candidates are properly categorized."""
        gitignore_patterns = parse_patterns_file(os.path.join(large_test_project, ".gitignore"))
        spec = pathspec.PathSpec.from_lines('gitwildmatch', gitignore_patterns)
        
        result = scan_project_files(large_test_project, spec, git_only_signatures=False)
        
        signature_files_rel = [os.path.relpath(f, large_test_project) for f in result['signature_candidates']]
        
        # Should include these as signature candidates
        expected_signatures = ["README.md", "main.py", "src/app.py", "src/utils.py", "tests/test_main.py", "docs/guide.md"]
        
        for expected in expected_signatures:
            assert expected in signature_files_rel, f"{expected} should be a signature candidate"
        
        # Should NOT include these
        assert "package.json" not in signature_files_rel, "JSON files should not be signature candidates"
        assert ".gitignore" not in signature_files_rel, "Gitignore should not be signature candidate"
    
    def test_important_file_detection(self):
        """Test important file detection for smart selection."""
        important_files = [
            "/path/to/main.py",
            "/path/to/app.py", 
            "/path/to/README.md",
            "/path/to/package.json",
            "/path/to/requirements.txt",
            "/path/to/index.js"
        ]
        
        not_important_files = [
            "/path/to/some_module.py",
            "/path/to/helper.py",
            "/path/to/random.txt",
            "/path/to/data.csv"
        ]
        
        for file_path in important_files:
            assert is_important_file(file_path), f"{file_path} should be detected as important"
        
        for file_path in not_important_files:
            assert not is_important_file(file_path), f"{file_path} should not be detected as important"
    
    def test_directory_filtering_performance(self, large_test_project):
        """Test that directory filtering prevents walking into excluded dirs."""
        import time
        
        gitignore_patterns = parse_patterns_file(os.path.join(large_test_project, ".gitignore"))
        spec = pathspec.PathSpec.from_lines('gitwildmatch', gitignore_patterns)
        
        # Add more nested directories to make the test meaningful
        deep_dirs = [
            "node_modules/deep/very/deeply/nested/structure",
            ".git/objects/pack/very/deep/structure"  
        ]
        
        for deep_dir in deep_dirs:
            full_path = os.path.join(large_test_project, deep_dir)
            os.makedirs(full_path, exist_ok=True)
            # Add a file in the deep directory
            with open(os.path.join(full_path, "file.txt"), 'w') as f:
                f.write("deep file")
        
        start_time = time.time()
        result = scan_project_files(large_test_project, spec, git_only_signatures=False)
        elapsed_time = time.time() - start_time
        
        # Should complete quickly (under 1 second even with deep structures)
        assert elapsed_time < 1.0, f"Scan took too long: {elapsed_time:.3f}s"
        
        # Should not find any files in excluded deep directories
        all_files_rel = [os.path.relpath(f, large_test_project) for f in result['all_files']]
        deep_excluded_files = [f for f in all_files_rel if "very/deeply" in f or "very/deep" in f]
        assert len(deep_excluded_files) == 0, f"Should not find files in deep excluded dirs: {deep_excluded_files}"