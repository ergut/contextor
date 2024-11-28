import unittest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from codecontextor.main import (
    generate_tree,
    parse_patterns_file,
    should_exclude,
    merge_files,
    calculate_total_size,
    get_all_files
)

class TestCodeContextor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Print header at the start of all tests"""
        print("\n" + "="*80)
        print("Starting CodeContextor Tests")
        print("="*80)

    def setUp(self):
        """Set up test environment before each test"""
        print("\nSetting up test environment...")
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        print(f"Created temporary test directory: {self.test_dir}")
        
        # Create a sample directory structure
        self.create_test_files()
        print("Created test file structure")
        print("-"*80)  # Separator after setup
        
    def tearDown(self):
        """Clean up after each test"""
        print(f"\nCleaning up temporary directory: {self.test_dir}")
        shutil.rmtree(self.test_dir)
        print("="*80)  # Major separator between test cases
        
    def create_test_files(self):
        """Create a test directory structure"""
        # Create directories
        os.makedirs(os.path.join(self.test_dir, "src"))
        os.makedirs(os.path.join(self.test_dir, "tests"))
        os.makedirs(os.path.join(self.test_dir, "docs"))
        
        # Create some test files
        files = {
            "src/main.py": "print('main')",
            "src/utils.py": "def util(): pass",
            "tests/test_main.py": "def test_main(): pass",
            "docs/README.md": "# Documentation",
            ".gitignore": "*.pyc\n__pycache__/",
        }
        
        for path, content in files.items():
            full_path = os.path.join(self.test_dir, path)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"Created test file: {path}")

    def test_generate_tree(self):
        """Test tree structure generation"""
        print("\nTEST: Generating directory tree structure")
        print("-"*40)  # Subsection separator
        tree = generate_tree(self.test_dir)
        
        print("Checking if all directories are present in tree:")
        # Check if all directories are present
        for dir_name in ['src/', 'tests/', 'docs/']:
            present = any(dir_name in line for line in tree)
            print(f"- Directory '{dir_name}': {'✓' if present else '✗'}")
            self.assertTrue(present, f"Directory {dir_name} not found in tree")
        
        print("\nChecking if all files are present in tree:")
        print("-"*40)  # Subsection separator
        # Check if all files are present
        for file_name in ['main.py', 'utils.py', 'test_main.py', 'README.md']:
            present = any(file_name in line for line in tree)
            print(f"- File '{file_name}': {'✓' if present else '✗'}")
            self.assertTrue(present, f"File {file_name} not found in tree")

    def test_parse_patterns_file(self):
        """Test parsing of pattern files"""
        print("\nTEST: Parsing pattern files")
        print("-"*40)  # Subsection separator
        patterns_file = os.path.join(self.test_dir, "patterns.txt")
        test_patterns = "*.pyc\n#Comment\n\n__pycache__/"
        
        print(f"Writing test patterns to {patterns_file}:")
        print(test_patterns)
        
        with open(patterns_file, 'w') as f:
            f.write(test_patterns)
        
        patterns = parse_patterns_file(patterns_file)
        print("\nParsed patterns:")
        print("-"*40)  # Subsection separator
        for pattern in patterns:
            print(f"- {pattern}")
        
        self.assertEqual(len(patterns), 2, "Expected 2 patterns")
        self.assertIn("*.pyc", patterns, "*.pyc pattern not found")
        self.assertIn("__pycache__/", patterns, "__pycache__/ pattern not found")
        self.assertNotIn("#Comment", patterns, "Comment was incorrectly included")

    def test_should_exclude(self):
        """Test file exclusion logic"""
        print("\nTEST: Testing file exclusion patterns")
        print("-"*40)  # Subsection separator
        from pathspec import PathSpec
        
        patterns = ["*.pyc", "__pycache__/"]
        print("Testing patterns:", patterns)
        spec = PathSpec.from_lines('gitwildmatch', patterns)
        
        # Test files that should be excluded
        test_cases = [
            ("test.pyc", True),
            ("test.py", False),
            ("__pycache__/cache.txt", True),
            ("src/main.py", False)
        ]
        
        print("\nChecking file exclusions:")
        print("-"*40)  # Subsection separator
        for filename, should_be_excluded in test_cases:
            test_file = Path(self.test_dir) / filename
            result = should_exclude(test_file, self.test_dir, spec)
            print(f"- {filename}: {'Should be excluded' if should_be_excluded else 'Should be included'}")
            print(f"  Result: {'Excluded' if result else 'Included'} {'✓' if result == should_be_excluded else '✗'}")
            self.assertEqual(result, should_be_excluded)

    def test_calculate_total_size(self):
        """Test file size calculation"""
        print("\nTEST: Calculating total file size")
        print("-"*40)  # Subsection separator
        files = [
            os.path.join(self.test_dir, "src/main.py"),
            os.path.join(self.test_dir, "src/utils.py")
        ]
        
        print("Calculating size for files:")
        for file in files:
            print(f"- {os.path.basename(file)}")
        
        total_size = calculate_total_size(files)
        print("-"*40)  # Subsection separator
        print(f"Total size calculated: {total_size} bytes")
        self.assertGreater(total_size, 0)

    def test_get_all_files(self):
        """Test getting all files respecting exclusions"""
        print("\nTEST: Getting all files with exclusions")
        print("-"*40)  # Subsection separator
        from pathspec import PathSpec
        
        patterns = ["*.pyc", "__pycache__/"]
        print("Using exclude patterns:", patterns)
        spec = PathSpec.from_lines('gitwildmatch', patterns)
        
        files = get_all_files(self.test_dir, spec)
        
        print("\nFiles found:")
        print("-"*40)  # Subsection separator
        for f in files:
            print(f"- {os.path.relpath(f, self.test_dir)}")
        
        # Check expected files
        expected_files = ['main.py', 'utils.py', 'test_main.py', 'README.md']
        print("\nChecking for expected files:")
        print("-"*40)  # Subsection separator
        for expected in expected_files:
            found = any(expected in f for f in files)
            print(f"- {expected}: {'✓' if found else '✗'}")
            self.assertTrue(found, f"Expected file {expected} not found")

    @patch('builtins.input', return_value='y')
    def test_merge_files_all_files(self, mock_input):
        """Test merging all files in directory"""
        print("\nTEST: Merging all files in directory")
        print("-"*40)  # Subsection separator
        output_file = os.path.join(self.test_dir, "output.txt")
        print(f"Output file: {output_file}")
        
        merge_files(None, output_file, self.test_dir)
        
        print("\nChecking output file:")
        print("-"*40)  # Subsection separator
        self.assertTrue(os.path.exists(output_file), "Output file was not created")
        print("- File exists: ✓")
        
        with open(output_file, 'r') as f:
            content = f.read()
            checks = [
                ("Project Context File", "Header"),
                ("src/main.py", "Source directory"),
                ("tests/test_main.py", "Tests directory")
            ]
            print("\nChecking content:")
            print("-"*40)  # Subsection separator
            for text, description in checks:
                found = text in content
                print(f"- {description}: {'✓' if found else '✗'}")
                self.assertIn(text, content)

    def test_merge_files_specific_files(self):
        """Test merging specific files"""
        print("\nTEST: Merging specific files")
        print("-"*40)  # Subsection separator
        output_file = os.path.join(self.test_dir, "output.txt")
        files_to_merge = [
            os.path.join(self.test_dir, "src/main.py"),
            os.path.join(self.test_dir, "docs/README.md")
        ]
        
        print("Files to merge:")
        for f in files_to_merge:
            print(f"- {os.path.relpath(f, self.test_dir)}")
        
        merge_files(files_to_merge, output_file, self.test_dir)
        
        print("\nChecking output file contents:")
        print("-"*40)  # Subsection separator
        with open(output_file, 'r') as f:
            content = f.read()
            checks = [
                ("print('main')", "main.py content", True),
                ("# Documentation", "README.md content", True),
                ("def util():", "utils.py content", False)
            ]
            for text, description, should_exist in checks:
                found = text in content
                print(f"- {description}: {'✓' if found == should_exist else '✗'}")
                if should_exist:
                    self.assertIn(text, content)
                else:
                    self.assertNotIn(text, content)

if __name__ == '__main__':
    unittest.main(verbosity=2)