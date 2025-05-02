"""
SQL signature extraction module for Contextor.

This module uses regex patterns to extract table and view definitions
from SQL files, providing a high-level overview of database schema.
"""

import re
from typing import Dict, List, Any

# Patterns that handle both backtick and non-backtick quoted identifiers
TABLE_PATTERN = re.compile(
    r'CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`([^`]+)`|(\w+))',
    re.IGNORECASE | re.MULTILINE
)

VIEW_PATTERN = re.compile(
    r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:`([^`]+)`|(\w+))',
    re.IGNORECASE | re.MULTILINE
)

def get_sql_signatures(file_path: str) -> Dict[str, Any]:
    """Extract SQL schema objects including tables and views."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        print(f"SQL Content: {repr(content)}")
        print(f"Table Pattern: {TABLE_PATTERN.pattern}")
        print(f"View Pattern: {VIEW_PATTERN.pattern}")
            
        # Initialize signatures dict
        signatures = {
            "tables": [],
            "views": []
        }
        
        # Extract tables (handle both backtick and non-backtick groups)
        for match in TABLE_PATTERN.finditer(content):
            table_name = match.group(1) or match.group(2)
            if table_name:
                signatures["tables"].append(table_name)
                print(f"Found table: {table_name}")
        
        # Extract views (handle both backtick and non-backtick groups)
        for match in VIEW_PATTERN.finditer(content):
            view_name = match.group(1) or match.group(2)
            if view_name:
                signatures["views"].append(view_name)
                print(f"Found view: {view_name}")
        
        return signatures
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

def format_sql_signatures(signatures: Dict[str, Any]) -> str:
    """Format SQL signatures into a readable string."""
    if "error" in signatures:
        return f"Error: {signatures['error']}"
    
    formatted = []
    
    # Format tables
    if signatures["tables"]:
        formatted.append("# Tables")
        formatted.extend([f"- {table}" for table in sorted(signatures["tables"])])
        formatted.append("")
    
    # Format views
    if signatures["views"]:
        formatted.append("# Views")
        formatted.extend([f"- {view}" for view in sorted(signatures["views"])])
        formatted.append("")
        
    return "\n".join(formatted) if formatted else "No tables or views found"

def process_sql_file(file_path: str) -> str:
    """Process a SQL file and return formatted signatures."""
    try:
        signatures = get_sql_signatures(file_path)
        return format_sql_signatures(signatures)
    except Exception as e:
        return f"Error processing SQL file: {str(e)}"