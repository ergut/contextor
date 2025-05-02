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
    """Extract import and export statements using regex."""
    imports = []
    exports = []
    
    # Match imports/exports at start of line or with whitespace before
    import_pattern = re.compile(r'^\s*import\s+.*?["\'].*?["\'];?\s*$', re.MULTILINE)
    export_pattern = re.compile(r'^\s*export\s+(?:default\s+)?.*?(?:{.*?}|\w+.*?);?\s*$', re.MULTILINE)
    
    # Extract imports
    for match in import_pattern.finditer(content):
        imports.append(match.group().strip())
    
    # Extract exports
    for match in export_pattern.finditer(content):
        exports.append(match.group().strip())
        
    return {
        "imports": imports,
        "exports": exports
    }

def extract_functions(content: str) -> List[Dict[str, str]]:
    """Extract function declarations using regex."""
    functions = []
    
    # Match function declarations
    patterns = [
        # Standard and exported functions (async optional)
        (r'^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*{', 'function'),
        # Arrow functions (including async)
        (r'^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', 'arrow_function'),
        # Class methods (including async)
        (r'^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', 'method')
    ]
    
    for pattern, func_type in patterns:
        regex = re.compile(pattern, re.MULTILINE)
        for match in regex.finditer(content):
            if func_type != 'method' or not any(m in content[:match.start()] for m in ['class', 'interface']):
                functions.append({
                    "name": match.group(1),
                    "signature": match.group().strip(),
                    "type": func_type
                })
    
    return functions

def extract_classes(content: str) -> List[Dict[str, Any]]:
    """Extract class declarations using regex."""
    classes = []
    
    # Match only top-level class declarations
    class_pattern = re.compile(
        r'^(?:\s*|export\s+(?:default\s+)?)'  # Start of line with optional export
        r'class\s+(\w+)'                      # Class name
        r'(?:\s+extends\s+([^{]+))?\s*{',     # Optional extends
        re.MULTILINE
    )
    
    # Very simple method pattern
    method_pattern = re.compile(
        r'(?:^|\s+)'                          # Start of line or whitespace
        r'(?!\/[\/\*])'                       # Not a comment
        r'(?:(?:public|private|protected|static|async)\s+)*'  # Optional modifiers
        r'([a-zA-Z_$][\w$]*)'                # Method name
        r'\s*\([^)]*\)\s*{',                 # Parameters and opening brace
        re.MULTILINE
    )
    
    # Find all top-level class declarations
    for match in class_pattern.finditer(content):
        class_name = match.group(1)
        extends_clause = match.group(2)
        start_pos = match.end()
        
        # Clean up extends clause
        extends = extends_clause.strip() if extends_clause else None
        
        # Find matching closing brace for class
        brace_count = 1
        end_pos = start_pos
        for i in range(start_pos, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i
                    break
        
        # Extract class body
        class_body = content[start_pos:end_pos]
        
        # Extract methods from class body
        methods = []
        for method_match in method_pattern.finditer(class_body):
            method_name = method_match.group(1)
            method_line = method_match.group().strip()
            
            # Skip if it's a reserved word
            if method_name not in {'if', 'for', 'while', 'switch', 'catch', 'class', 'function', 'return'}:
                methods.append({
                    "name": method_name,
                    "signature": method_line
                })
        
        # Check if it's a React component
        is_react = bool(extends and any(base in extends for base in ['React.Component', 'Component']))
        
        # Get the full class declaration line
        class_decl = content[match.start():start_pos].strip()
        
        classes.append({
            "name": class_name,
            "signature": class_decl,
            "extends": extends,
            "methods": methods,
            "is_react_component": is_react
        })
    
    return classes

def extract_classes_with_parser(content: str) -> List[Dict[str, Any]]:
    """Extract class declarations using JavaScript parser."""
    classes = []
    
    try:
        # Parse the content
        parsed = pyjsparser.parse(content)
        body = parsed.get('body', [])
        
        # Process each top-level node
        for node in body:
            # Check for class declarations
            if node.get('type') == 'ClassDeclaration':
                class_info = {
                    'name': node.get('id', {}).get('name', ''),
                    'methods': [],
                    'signature': f"class {node.get('id', {}).get('name', '')} {{",
                    'is_react_component': False
                }
                
                # Check for extends
                if node.get('superClass'):
                    super_name = node.get('superClass', {}).get('name', '')
                    if super_name:
                        class_info['extends'] = super_name
                        class_info['signature'] = f"class {class_info['name']} extends {super_name} {{"
                        # Check if it's a React component
                        if super_name in ['React.Component', 'Component']:
                            class_info['is_react_component'] = True
                
                # Extract methods from body
                for body_item in node.get('body', {}).get('body', []):
                    if body_item.get('type') == 'MethodDefinition':
                        method_name = body_item.get('key', {}).get('name', '')
                        method_info = {
                            'name': method_name,
                            'signature': f"{method_name}() {{"
                        }
                        class_info['methods'].append(method_info)
                
                classes.append(class_info)
                
            # Also check for exported class declarations
            elif node.get('type') == 'ExportDefaultDeclaration' or node.get('type') == 'ExportNamedDeclaration':
                declaration = node.get('declaration', {})
                if declaration.get('type') == 'ClassDeclaration':
                    # Process similar to above
                    # [similar processing code]
                    pass
    
    except Exception as e:
        print(f"Error parsing with JavaScript parser: {str(e)}")
        return []
        
    return classes

def extract_react_functional_components(content: str) -> List[Dict[str, str]]:
    """Extract React functional components."""
    components = []
    
    # Patterns for React components
    patterns = [
        # Arrow function components with JSX
        r'^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)(?::\s*React\.?FC[^=]*)?'
        r'\s*=\s*(?:\([^)]*\)|[^=]*)\s*=>\s*(?:\(\s*)?(?:<[^>]+>|{)',
        
        # Function declaration components with JSX
        r'^\s*(?:export\s+(?:default\s+)?)?function\s+(\w+)(?::\s*React\.?FC[^(]*)?'
        r'\s*\([^)]*\)\s*(?::\s*(?:JSX\.Element|React\.ReactNode))?\s*{\s*(?:return\s*)?(?:<[^>]+>|{)'
    ]
    
    for pattern in patterns:
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
        for match in regex.finditer(content):
            components.append({
                "name": match.group(1),
                "signature": match.group().strip()
            })
    
    return components

def extract_typescript_interfaces(content: str) -> List[Dict[str, str]]:
    """Extract TypeScript interfaces."""
    interfaces = []
    
    # Match interface declarations
    interface_pattern = re.compile(
        r'^\s*(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+[^{]+)?\s*{'
        r'(?:[^{}]*|\{[^{}]*\})*}',
        re.MULTILINE | re.DOTALL
    )
    
    for match in interface_pattern.finditer(content):
        interfaces.append({
            "name": match.group(1),
            "signature": match.group().split('{')[0].strip() + '{'
        })
    
    return interfaces

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
            formatted.append(comp["signature"])
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
        return format_js_signatures(get_js_signatures(file_path))
    except Exception as e:
        return f"Error processing JavaScript/TypeScript file: {str(e)}"

def get_js_signatures(file_path: str) -> Dict[str, Any]:
    """Extract JS/TS file structure including imports, classes, and functions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine file type and features
    is_typescript = file_path.lower().endswith(('.ts', '.tsx'))
    has_jsx = bool(file_path.lower().endswith(('.jsx', '.tsx')) or '<' in content and '>' in content)
    
    result = {
        "imports": [],
        "exports": [],
        "functions": [],
        "classes": [],
        "react_components": [],
        "file_type": "TypeScript" if is_typescript else "JavaScript",
        "has_jsx": has_jsx
    }
    
    # Extract content using regex
    imports_exports = extract_imports_exports(content)
    result["imports"] = imports_exports["imports"]
    result["exports"] = imports_exports["exports"]
    result["functions"] = extract_functions(content)
    result["classes"] = extract_classes(content)
    
    # Handle React-specific structures
    if has_jsx:
        result["react_components"] = extract_react_functional_components(content)
    
    # Handle TypeScript-specific structures
    if is_typescript:
        result["interfaces"] = extract_typescript_interfaces(content)
    
    return result