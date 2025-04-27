"""
JavaScript/TypeScript signature extraction module for Contextor.

This module extracts function signatures, class definitions, and component 
structures from JavaScript and TypeScript files.
"""

import re
from typing import Dict, List, Any, Optional

try:
    import pyjsparser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False

def extract_imports_exports(content: str) -> Dict[str, List[str]]:
    """Extract import and export statements using regex.
    
    This is a fallback method when full parsing isn't available.
    """
    result = {
        "imports": [],
        "exports": []
    }
    
    # Match import statements
    import_pattern = re.compile(r'^import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*)\s+from\s+[\'"]([^\'"]+)[\'"];?|^import\s+[\'"]([^\'"]+)[\'"];?', re.MULTILINE)
    
    for match in import_pattern.finditer(content):
        result["imports"].append(match.group(0).strip())
    
    # Match export statements
    export_pattern = re.compile(r'^export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+\w+', re.MULTILINE)
    export_pattern_named = re.compile(r'^export\s+\{[^}]+\}', re.MULTILINE)
    
    for match in export_pattern.finditer(content):
        result["exports"].append(match.group(0).strip())
    for match in export_pattern_named.finditer(content):
        result["exports"].append(match.group(0).strip())
    
    return result

def extract_functions(content: str) -> List[Dict[str, str]]:
    """Extract function declarations using regex."""
    functions = []
    
    # Match function declarations (standard and arrow functions)
    function_pattern = re.compile(r'^(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*{', re.MULTILINE)
    arrow_function_pattern = re.compile(r'^(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?([^)]*)\)?\s*=>', re.MULTILINE)
    class_method_pattern = re.compile(r'^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', re.MULTILINE)
    
    # Standard functions
    for match in function_pattern.finditer(content):
        func_line = match.group(0).strip()
        func_name = match.group(1)
        functions.append({
            "name": func_name,
            "signature": func_line,
            "type": "function"
        })
    
    # Arrow functions
    for match in arrow_function_pattern.finditer(content):
        func_line = match.group(0).strip()
        func_name = match.group(1)
        functions.append({
            "name": func_name,
            "signature": func_line,
            "type": "arrow_function"
        })
    
    return functions

def extract_classes(content: str) -> List[Dict[str, Any]]:
    """Extract class declarations using regex."""
    classes = []
    
    # Match class declarations
    class_pattern = re.compile(r'^(?:export\s+(?:default\s+)?)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', re.MULTILINE)
    method_pattern = re.compile(r'^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', re.MULTILINE)
    
    for match in class_pattern.finditer(content):
        class_line = match.group(0).strip()
        class_name = match.group(1)
        extends_class = match.group(2)
        
        # Find the end of the class (simplistic approach)
        class_start = match.start()
        class_content = content[class_start:]
        
        # Extract methods
        methods = []
        for method_match in method_pattern.finditer(class_content):
            # Stop if we're likely outside the class
            if method_match.start() > 1000:  # Arbitrary limit to avoid scanning too far
                break
                
            method_line = method_match.group(0).strip()
            method_name = method_match.group(1)
            
            # Skip constructor for React components detection
            if method_name != 'constructor':
                methods.append({
                    "name": method_name,
                    "signature": method_line
                })
        
        # Detect if this might be a React component
        is_react_component = extends_class in ['Component', 'React.Component', 'PureComponent', 'React.PureComponent']
        is_react_component = is_react_component or any(m["name"] == "render" for m in methods)
        
        classes.append({
            "name": class_name,
            "signature": class_line,
            "extends": extends_class,
            "methods": methods,
            "is_react_component": is_react_component
        })
    
    return classes

def extract_react_functional_components(content: str) -> List[Dict[str, str]]:
    """Extract React functional components."""
    components = []
    
    # Look for component patterns
    component_patterns = [
        # const Name = (props) => { return <div>...</div> }
        re.compile(r'^(?:export\s+(?:default\s+)?)?const\s+(\w+)\s*=\s*\((?:props|{[^}]*})\)\s*=>\s*(?:{[\s\S]*?return\s+<|<)', re.MULTILINE),
        
        # function Name(props) { return <div>...</div> }
        re.compile(r'^(?:export\s+(?:default\s+)?)?function\s+(\w+)\s*\((?:props|{[^}]*})\)\s*{[\s\S]*?return\s+<', re.MULTILINE)
    ]
    
    # JSX usage is a good indicator of React components
    jsx_usage = '<' in content and '>' in content
    
    for pattern in component_patterns:
        for match in pattern.finditer(content):
            if jsx_usage:
                comp_line = match.group(0).strip()
                comp_name = match.group(1)
                
                components.append({
                    "name": comp_name,
                    "signature": comp_line,
                    "type": "functional_component"
                })
    
    return components

def extract_typescript_interfaces(content: str) -> List[Dict[str, str]]:
    """Extract TypeScript interfaces."""
    interfaces = []
    
    # Match interface declarations
    interface_pattern = re.compile(r'^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+\w+)?\s*{[^}]*}', re.MULTILINE | re.DOTALL)
    
    for match in interface_pattern.finditer(content):
        interface_text = match.group(0).strip()
        interface_name = match.group(1)
        
        interfaces.append({
            "name": interface_name,
            "signature": interface_text,
            "type": "interface"
        })
    
    return interfaces

def get_js_signatures(file_path: str) -> Dict[str, Any]:
    """Extract JS/TS file structure including imports, classes, and functions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine file type
    is_typescript = file_path.lower().endswith(('.ts', '.tsx'))
    is_jsx = file_path.lower().endswith(('.jsx', '.tsx'))
    
    result = {
        "imports": [],
        "exports": [],
        "functions": [],
        "classes": [],
        "react_components": [],
        "file_type": "TypeScript" if is_typescript else "JavaScript",
        "has_jsx": is_jsx
    }
    
    # Extract content using regex for basic structures
    imports_exports = extract_imports_exports(content)
    result["imports"] = imports_exports["imports"]
    result["exports"] = imports_exports["exports"]
    result["functions"] = extract_functions(content)
    result["classes"] = extract_classes(content)
    
    # Handle React-specific structures
    if is_jsx or '<' in content and '>' in content:
        result["react_components"] = extract_react_functional_components(content)
    
    # Handle TypeScript-specific structures
    if is_typescript:
        result["interfaces"] = extract_typescript_interfaces(content)
    
    return result

def format_js_signatures(signatures: Dict[str, Any]) -> str:
    """Format JS/TS signatures into a readable string."""
    formatted = []
    file_type = signatures["file_type"]
    
    # Add file type header
    formatted.append(f"# {file_type}{' with JSX' if signatures['has_jsx'] else ''} File")
    formatted.append("")
    
    # Format imports
    if signatures["imports"]:
        formatted.append("## Imports")
        for import_stmt in signatures["imports"]:
            formatted.append(import_stmt)
        formatted.append("")
    
    # Format exports
    if signatures["exports"]:
        formatted.append("## Exports")
        for export_stmt in signatures["exports"]:
            formatted.append(export_stmt)
        formatted.append("")
    
    # Format functions
    if signatures["functions"]:
        formatted.append("## Functions")
        for func in signatures["functions"]:
            formatted.append(func["signature"])
        formatted.append("")
    
    # Format React components
    if signatures.get("react_components"):
        formatted.append("## React Components")
        for comp in signatures["react_components"]:
            formatted.append(f"// {comp['name']} Component")
            formatted.append(comp["signature"] + "...")
            formatted.append("")
    
    # Format classes
    if signatures["classes"]:
        formatted.append("## Classes")
        for cls in signatures["classes"]:
            formatted.append(f"// {cls['name']}" + (" React Component" if cls.get("is_react_component") else ""))
            formatted.append(cls["signature"])
            
            if cls["methods"]:
                for method in cls["methods"]:
                    formatted.append(f"  {method['signature']}")
            formatted.append("}")
            formatted.append("")
    
    # Format TypeScript interfaces
    if "interfaces" in signatures and signatures["interfaces"]:
        formatted.append("## TypeScript Interfaces")
        for interface in signatures["interfaces"]:
            formatted.append(interface["signature"])
            formatted.append("")
    
    return "\n".join(formatted)

def process_js_file(file_path: str) -> str:
    """Process a JS/TS file and return formatted signatures."""
    try:
        signatures = get_js_signatures(file_path)
        return format_js_signatures(signatures)
    except Exception as e:
        return f"Error processing JavaScript/TypeScript file: {str(e)}"