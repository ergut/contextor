# Testing Guide

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -e .
```

## Running Tests

Basic test run:
```bash
pytest
```

Options:
```bash
pytest -v           # Verbose output
pytest -vv          # Extra verbose
pytest -n auto      # Parallel execution
pytest tests/specific_test.py  # Run specific test file
```

## Coverage Reports

View coverage in terminal:
```bash
pytest --cov=contextor
```

Generate HTML report:
```bash
pytest --cov=contextor --cov-report=html
```
Open `htmlcov/index.html` to view detailed coverage report.

## Adding New Tests

1. Create test files in `tests/` directory
2. Use pytest fixtures for setup/teardown
3. Follow existing patterns for similar tests
4. Run coverage to ensure new code is tested

Example test:
```python
def test_new_feature(test_dir):
    """Test description"""
    result = your_function()
    assert result == expected, "Helpful error message"
```

## Configuration

Project uses `pytest.ini` for configuration:
- Test discovery in `tests/` directory
- Coverage reporting enabled
- Colored output
- Verbose mode by default

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Pull requests to main
- Push to main branch
- Release tags