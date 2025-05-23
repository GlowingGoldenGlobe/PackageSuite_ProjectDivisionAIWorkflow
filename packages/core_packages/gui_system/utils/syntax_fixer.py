#!/usr/bin/env python
"""
GUI Syntax Fixer Utility

This utility script helps fix common syntax errors in Python files,
particularly those that might occur in GUI-related code.

Usage:
    python syntax_fixer.py <file_path>

Features:
- Fixes unbalanced try/except blocks
- Removes break statements outside loops
- Fixes indentation issues
- Ensures proper class declarations
- Corrects missing function parameters
- Adds missing imports
"""

import sys
import re
import os
import tokenize
import io
from typing import List, Tuple, Dict, Any, Optional

def fix_try_except_blocks(content: str) -> str:
    """Fix unclosed try blocks by adding proper except blocks."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i]
        fixed_lines.append(current_line)
        
        # Check for 'try:' statements
        if re.search(r'^\s*try\s*:', current_line):
            match = re.match(r'^\s*', current_line)
            indent_level = len(match.group() if match else '')
            has_except_or_finally = False
            
            # Look ahead for matching except or finally block
            j = i + 1
            while j < len(lines):
                match_j = re.match(r'^\s*', lines[j])
                if not lines[j].strip():
                    # Empty line, continue
                    j += 1
                    continue
                    
                indent_j = len(match_j.group() if match_j else '')
                if indent_j <= indent_level:
                    # We've reached the end of the try block without finding except/finally
                    break
                
                if re.search(r'^\s{' + str(indent_level) + r'}(?:except|finally)\s*.*:', lines[j]):
                    has_except_or_finally = True
                    break
                j += 1
            
            # If no except or finally found, add one
            if not has_except_or_finally:
                indent_str = ' ' * indent_level
                next_line = f"{indent_str}except Exception as e:"
                fixed_lines.append(next_line)
                fixed_lines.append(f"{indent_str}    print(f\"Error: {{str(e)}}\")")
        
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_indentation_issues(content: str) -> str:
    """Fix common indentation issues in Python code."""
    lines = content.split('\n')
    fixed_lines = []
    
    # Stack to track expected indentation levels
    indent_stack = [0]  # Start with no indentation
    expected_indent = 0
    
    for line_num, line in enumerate(lines):
        if not line.strip():  # Skip empty lines
            fixed_lines.append(line)
            continue
            
        # Get the current indentation level
        current_indent = len(re.match(r'^\s*', line).group())
        
        # Check if this line starts a new block (ending with a colon)
        if re.search(r':\s*$', line.strip()) and not line.strip().startswith('#'):
            # This is a new block, so remember the expected indentation for the next lines
            indent_stack.append(current_indent + 4)
        
        # Check if this line ends a block (e.g., return, break, continue, pass)
        elif (re.search(r'^(\s*)(return|break|continue|pass|raise)\b', line) and 
              line_num + 1 < len(lines) and 
              lines[line_num + 1].strip() and
              not re.search(r'^\s*#', lines[line_num + 1])):
            
            if indent_stack and indent_stack[-1] == current_indent:
                indent_stack.pop()
        
        # If we find a line that looks like it should be the end of a block
        elif (current_indent < indent_stack[-1] and 
              not line.strip().startswith('#') and
              not re.search(r'^\s*(elif|else|except|finally)\s*:', line)):
            
            # Check if this looks like it should be outdented
            while indent_stack and current_indent < indent_stack[-1]:
                indent_stack.pop()
        
        # Check for unexpected indentation that needs to be fixed
        if line.strip() and not line.strip().startswith('#'):
            expected_indent = indent_stack[-1] if indent_stack else 0
            if current_indent > expected_indent and not line.strip().startswith(('elif', 'else', 'except', 'finally')):
                # Fix the indentation
                new_line = ' ' * expected_indent + line.lstrip()
                fixed_lines.append(new_line)
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_break_outside_loop(content: str) -> str:
    """Remove break statements that are outside of loops."""
    lines = content.split('\n')
    in_loop = [False]  # Using a list for mutable state
    fixed_lines = []
    
    for line in lines:
        # Check for loop start
        if re.search(r'^\s*(?:for|while)\s+.*:', line):
            in_loop.append(True)
        
        # Check for loop end (indentation decrease)
        if line.strip() and in_loop[-1] and len(in_loop) > 1:
            current_indent = len(re.match(r'^\s*', line).group())
            prev_indent = len(re.match(r'^\s*', lines[lines.index(line) - 1]).group())
            if current_indent < prev_indent:
                in_loop.pop()
        
        # Skip break statements outside loops
        if re.search(r'^\s*break\s*$', line) and not any(in_loop):
            fixed_lines.append(f"# Removed invalid break: {line}")
            continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_class_declarations(content: str) -> str:
    """Fix improper class declarations."""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Find and fix invalid class declarations
        if re.search(r'^\s*class\s+.*\.py\s*:', line):
            fixed = re.sub(r'class\s+(.*?)\.py\s*:', r'class \1:', line)
            fixed_lines.append(fixed)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def add_missing_imports(content: str) -> str:
    """Add commonly missing imports for GUI code."""
    common_imports = [
        "import os", 
        "import sys",
        "import json", 
        "import tkinter as tk", 
        "import datetime",
        "import platform",
        "import subprocess",
        "import threading"
    ]
    
    if not all(imp in content for imp in common_imports):
        # Add missing imports at the top of the file
        import_block = "\n".join([imp for imp in common_imports if imp not in content])
        
        # If there are already imports, find a good place to insert new ones
        if "import " in content:
            lines = content.split('\n')
            last_import_line = 0
            
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_line = i
            
            # Insert the new imports after the last existing import
            lines.insert(last_import_line + 1, import_block)
            return '\n'.join(lines)
        else:
            # If no imports exist, add them at the top after any comments/docstrings
            lines = content.split('\n')
            
            # Find the first non-comment, non-docstring line
            first_code_line = 0
            in_multiline_comment = False
            
            for i, line in enumerate(lines):
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    in_multiline_comment = not in_multiline_comment
                    continue
                    
                if not in_multiline_comment and not line.strip().startswith('#') and line.strip():
                    first_code_line = i
                    break
            
            # Insert the imports
            lines.insert(first_code_line, import_block)
            return '\n'.join(lines)
    
    return content

def fix_incomplete_function_params(content: str) -> str:
    """Fix functions with incomplete parameter lists."""
    # Identify functions with parameter list issues
    pattern = r'def\s+(\w+)\s*\([^)]*,\s*\):'
    fixed_content = re.sub(pattern, r'def \1():', content)
    return fixed_content

def fix_syntax_errors(file_path: str, output_path: Optional[str] = None) -> bool:
    """
    Fix common syntax errors in a Python file.
    
    Args:
        file_path: Path to the file to fix
        output_path: Optional path to save the fixed file. If None, overwrites the original.
        
    Returns:
        True if successfully fixed, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes - order is important!
        fixed_content = content
        fixed_content = add_missing_imports(fixed_content)        # First add missing imports
        fixed_content = fix_class_declarations(fixed_content)     # Fix class declarations
        fixed_content = fix_indentation_issues(fixed_content)     # Fix indentation 
        fixed_content = fix_try_except_blocks(fixed_content)      # Fix try/except blocks
        fixed_content = fix_break_outside_loop(fixed_content)     # Fix break statements
        fixed_content = fix_incomplete_function_params(fixed_content) # Fix function params
        
        # Write the fixed content
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed file saved to: {output_path}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed file: {file_path}")
        
        return True
    except Exception as e:
        print(f"Error fixing syntax in {file_path}: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python syntax_fixer.py <file_path> [output_path]")
        return
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = fix_syntax_errors(file_path, output_path)
    if success:
        print("Syntax fixing completed successfully")
    else:
        print("Syntax fixing failed")

if __name__ == "__main__":
    main()
