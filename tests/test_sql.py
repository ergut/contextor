"""
Tests for SQL signature extraction.
"""

import pytest
import os
import tempfile
from contextor.signatures.sql import (
    get_sql_signatures,
    format_sql_signatures,
    process_sql_file
)

@pytest.fixture
def sql_file():
    """Create a temporary SQL file for testing."""
    content = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);

CREATE VIEW active_users AS
SELECT * FROM users WHERE active = 1;

CREATE OR REPLACE VIEW premium_users AS
SELECT * FROM users WHERE subscription_type = 'premium';

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""
    
    with tempfile.NamedTemporaryFile(suffix='.sql', delete=False, mode='w') as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    os.unlink(temp_file)

def create_test_file(content):
    """Helper to create a test file with given content."""
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(content)
    return path

def test_get_sql_signatures(sql_file):
    """Test extraction of SQL tables and views."""
    signatures = get_sql_signatures(sql_file)
    
    assert len(signatures["tables"]) == 2
    assert "users" in signatures["tables"]
    assert "orders" in signatures["tables"]
    
    assert len(signatures["views"]) == 2
    assert "active_users" in signatures["views"]
    assert "premium_users" in signatures["views"]

def test_format_sql_signatures(sql_file):
    """Test formatting of SQL signatures."""
    signatures = get_sql_signatures(sql_file)
    formatted = format_sql_signatures(signatures)
    
    assert "# Tables" in formatted
    assert "- users" in formatted
    assert "- orders" in formatted
    assert "# Views" in formatted
    assert "- active_users" in formatted
    assert "- premium_users" in formatted

def test_process_sql_file(sql_file):
    """Test the full SQL file processing."""
    result = process_sql_file(sql_file)
    
    # Check if all objects are included in the output
    assert "Tables" in result
    assert "users" in result
    assert "orders" in result
    assert "Views" in result
    assert "active_users" in result
    assert "premium_users" in result

def test_process_sql_file_error_handling():
    """Test error handling in SQL file processing."""
    result = process_sql_file("nonexistent.sql")
    assert "Error:" in result
    assert "No such file or directory" in result

def test_view_with_template_variables():
    """Test that views with template variables are properly extracted."""
    sql_content = '''
    CREATE OR REPLACE VIEW `${PROJECT_ID}.${DATASET}.view_name`
    AS SELECT * FROM table;
    '''
    file_path = create_test_file(sql_content)
    try:
        signatures = get_sql_signatures(file_path)
        assert len(signatures["views"]) == 1
        assert "${PROJECT_ID}.${DATASET}.view_name" in signatures["views"]
    finally:
        os.remove(file_path)

def test_table_with_template_variables():
    """Test that tables with template variables are properly extracted."""
    sql_content = 'CREATE OR REPLACE TABLE `${PROJECT_ID}.${DATASET}.table_name` PARTITION BY date CLUSTER BY id AS SELECT * FROM other_table;'
    file_path = create_test_file(sql_content)
    try:
        signatures = get_sql_signatures(file_path)
        assert len(signatures["tables"]) == 1
        assert "${PROJECT_ID}.${DATASET}.table_name" in signatures["tables"]
    finally:
        os.remove(file_path)