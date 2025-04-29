"""
SQL signature extraction module for Contextor.

This module uses regex patterns to extract table and view definitions
from SQL files, providing a high-level overview of database schema.
"""

import re
from typing import Dict, List, Any

# Regex patterns for SQL objects
TABLE_PATTERN = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`|\[|")?(\w+)(?:`|\]|")?',
    re.IGNORECASE
)

VIEW_PATTERN = re.compile(
    r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:`|\[|")?(\w+)(?:`|\]|")?',
    re.IGNORECASE
)

def get_sql_signatures(file_path: str) -> Dict[str, Any]:
    """Extract SQL schema objects including tables and views."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        signatures = {
            "tables": [],
            "views": []
        }
        
        # Extract table names
        table_matches = TABLE_PATTERN.finditer(content)
        signatures["tables"] = [match.group(1) for match in table_matches]
        
        # Extract view names
        view_matches = VIEW_PATTERN.finditer(content)
        signatures["views"] = [match.group(1) for match in view_matches]
        
        return signatures
        
    except Exception as e:
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