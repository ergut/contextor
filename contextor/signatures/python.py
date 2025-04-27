"""
Python signature extraction module for Contextor.

This module uses the ast (Abstract Syntax Tree) module to extract
function signatures, class definitions, and method signatures from Python files.
"""

import ast
from typing import Dict, List, Any, Optional

def get_python_signatures(file_path: str) -> Dict[str, Any]:
    """Extract Python file structure including imports, classes, and functions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            return {"error": "Could not parse Python file due to syntax error"}
    
    result = {
        "imports": [],
        "classes": [],
        "functions": [],
        "variables": []
    }
    
    for node in ast.iter_child_nodes(tree):
        # Collect imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for name in node.names:
                    result["imports"].append(f"import {name.name}")
            else:  # ImportFrom
                module = node.module or ""
                for name in node.names:
                    result["imports"].append(f"from {module} import {name.name}")
        
        # Collect global variables
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result["variables"].append(f"{target.id}")
        
        # Collect functions
        elif isinstance(node, ast.FunctionDef):
            args = []
            defaults_start = len(node.args.args) - len(node.args.defaults)
            
            for i, arg in enumerate(node.args.args):
                arg_str = arg.arg
                # Add type annotation if available
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                
                # Add default value if available
                if i >= defaults_start:
                    default_index = i - defaults_start
                    arg_str += f" = {ast.unparse(node.args.defaults[default_index])}"
                
                args.append(arg_str)
            
            # Handle varargs and kwargs
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")
            
            # Collect return type annotation if available
            return_annotation = ""
            if node.returns:
                return_annotation = f" -> {ast.unparse(node.returns)}"
            
            decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
            decorators_str = "\n".join(decorators) + "\n" if decorators else ""
            
            func_signature = f"{decorators_str}def {node.name}({', '.join(args)}){return_annotation}:"
            result["functions"].append({
                "name": node.name,
                "signature": func_signature,
                "docstring": ast.get_docstring(node)
            })
        
        # Collect classes
        elif isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "bases": [ast.unparse(base) for base in node.bases],
                "methods": [],
                "docstring": ast.get_docstring(node)
            }
            
            # Get class-level decorators
            decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
            class_info["decorators"] = decorators
            
            # Extract methods within the class
            for class_node in ast.iter_child_nodes(node):
                if isinstance(class_node, ast.FunctionDef):
                    method_args = []
                    defaults_start = len(class_node.args.args) - len(class_node.args.defaults)
                    
                    for i, arg in enumerate(class_node.args.args):
                        # Skip 'self' or 'cls' in the output
                        if i == 0 and arg.arg in ('self', 'cls'):
                            continue
                            
                        arg_str = arg.arg
                        # Add type annotation if available
                        if arg.annotation:
                            arg_str += f": {ast.unparse(arg.annotation)}"
                        
                        # Add default value if available
                        if i >= defaults_start:
                            default_index = i - defaults_start
                            arg_str += f" = {ast.unparse(class_node.args.defaults[default_index])}"
                        
                        method_args.append(arg_str)
                    
                    # Handle varargs and kwargs
                    if class_node.args.vararg:
                        method_args.append(f"*{class_node.args.vararg.arg}")
                    if class_node.args.kwarg:
                        method_args.append(f"**{class_node.args.kwarg.arg}")
                    
                    # Collect return type annotation if available
                    return_annotation = ""
                    if class_node.returns:
                        return_annotation = f" -> {ast.unparse(class_node.returns)}"
                    
                    method_decorators = [f"@{ast.unparse(d)}" for d in class_node.decorator_list]
                    method_decorators_str = "\n    ".join(method_decorators) + "\n    " if method_decorators else ""
                    
                    method_signature = f"    {method_decorators_str}def {class_node.name}({', '.join(method_args)}){return_annotation}:"
                    class_info["methods"].append({
                        "name": class_node.name,
                        "signature": method_signature,
                        "docstring": ast.get_docstring(class_node)
                    })
            
            result["classes"].append(class_info)
    
    return result

def format_python_signatures(signatures: Dict[str, Any]) -> str:
    """Format Python signatures into a readable string."""
    if "error" in signatures:
        return f"Error: {signatures['error']}"
    
    formatted = []
    
    # Format imports
    if signatures["imports"]:
        formatted.append("# Imports")
        formatted.extend(signatures["imports"])
        formatted.append("")
    
    # Format global variables
    if signatures["variables"]:
        formatted.append("# Global Variables")
        formatted.extend(signatures["variables"])
        formatted.append("")
    
    # Format functions
    if signatures["functions"]:
        formatted.append("# Functions")
        for func in signatures["functions"]:
            formatted.append(func["signature"])
            if func["docstring"]:
                formatted.append(f'    """{func["docstring"]}"""')
            formatted.append("")
    
    # Format classes
    if signatures["classes"]:
        formatted.append("# Classes")
        for cls in signatures["classes"]:
            base_str = f"({', '.join(cls['bases'])})" if cls["bases"] else ""
            decorator_str = "\n".join(cls["decorators"]) + "\n" if cls["decorators"] else ""
            formatted.append(f"{decorator_str}class {cls['name']}{base_str}:")
            
            if cls["docstring"]:
                formatted.append(f'    """{cls["docstring"]}"""')
            
            if cls["methods"]:
                for method in cls["methods"]:
                    formatted.append(method["signature"])
                    if method["docstring"]:
                        formatted.append(f'        """{method["docstring"]}"""')
                    formatted.append("")
            else:
                formatted.append("    pass")
            formatted.append("")
    
    return "\n".join(formatted)

def process_python_file(file_path: str) -> str:
    """Process a Python file and return formatted signatures."""
    try:
        signatures = get_python_signatures(file_path)
        return format_python_signatures(signatures)
    except Exception as e:
        return f"Error processing file: {str(e)}"