# CodeContextor Testing Guide

This document describes the testing setup and procedures for the CodeContextor project.

## Running Tests

### Basic Usage

```bash
# Run all tests with detailed output
python -m unittest tests/test_main.py -v

# Run specific test case
python -m unittest tests/test_main.py TestCodeContextor.test_generate_tree
```

## Test Coverage

The test suite covers all major functionality of CodeContextor:

### 1. Directory Tree Generation
- Verifies correct structure generation
- Checks for presence of all directories and files
- Validates tree formatting

### 2. Pattern Parsing and File Exclusion
- Tests .gitignore pattern parsing
- Validates file exclusion logic
- Tests handling of comments and empty lines

### 3. File Operations
- Tests file size calculation
- Verifies file collection with exclusions
- Tests file merging operations

### 4. Error Handling
- Tests handling of missing files
- Validates size limit enforcement
- Checks user confirmation flow

## Test Output

Each test provides detailed output showing:
- Test case being executed
- Files and directories being created
- Patterns being matched
- Success/failure status for each check

Example output format:
```
================================================================================
Starting CodeContextor Tests
================================================================================

Setting up test environment...
Created temporary test directory: /tmp/tmpxxx
Created test file: src/main.py
Created test file: src/utils.py
...
----------------------------------------

TEST: Generating directory tree structure
----------------------------------------
Checking if all directories are present in tree:
- Directory 'src/': ✓
- Directory 'tests/': ✓
...

Cleaning up temporary directory: /tmp/tmpxxx
================================================================================
```

## Adding New Tests

When adding new functionality to CodeContextor, please ensure:

1. Add corresponding test cases in `tests/test_main.py`
2. Follow the existing test structure and naming conventions
3. Include detailed output messages for clarity
4. Add both positive and negative test cases
5. Update this documentation if adding new test categories

## Test Structure

Tests are organized in the `TestCodeContextor` class with:
- `setUp`: Creates temporary test environment
- `tearDown`: Cleans up after each test
- Individual test methods for each functionality
- Detailed print statements for debugging
- Clear visual separators between tests

## Running Tests During Development

During development, you can:
1. Run specific test: `python -m unittest tests/test_main.py -k test_name`
2. Run with increased verbosity: `python -m unittest -v tests/test_main.py`
3. Debug with print statements (already included in test suite)

## Common Issues

1. Temporary Directory Cleanup
   - If tests fail, check if temporary directories are being cleaned up
   - Manual cleanup might be needed if tests crash unexpectedly

2. File Permissions
   - Ensure proper permissions on test directories
   - Some tests might fail without sufficient permissions

3. Platform-Specific Issues
   - Path separators might differ between Windows and Unix
   - File size calculations might vary slightly

## Contributing New Tests

When contributing new tests:
1. Follow the existing format with clear sections
2. Include detailed print statements
3. Add both success and failure cases
4. Document any new test patterns
5. Ensure cleanup works correctly