#!/usr/bin/env python
"""
Fix all indentation issues in gui_main.py
"""

import re

# Read the file
with open('gui_main.py', 'r') as f:
    lines = f.readlines()

# Fix specific known indentation issues
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix indented lines that should follow elif/else statements
    if i > 0 and ('elif' in lines[i-1] or 'else:' in lines[i-1]):
        # Check if next line is not properly indented
        if i < len(lines) and lines[i].strip() and not lines[i].startswith((' ' * 4, '\t')):
            # Get the base indentation from the elif/else line
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            # Add proper indentation (base + 4 spaces)
            fixed_line = ' ' * (prev_indent + 4) + lines[i].lstrip()
            fixed_lines.append(fixed_line)
            i += 1
            continue
    
    # Fix subprocess.call lines that might be misaligned
    if 'subprocess.call' in line and not line.strip().startswith('subprocess.call'):
        # Check previous line for context
        if i > 0:
            prev_line = lines[i-1]
            if 'elif' in prev_line or 'else:' in prev_line:
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                fixed_line = ' ' * (prev_indent + 4) + line.lstrip()
                fixed_lines.append(fixed_line)
                i += 1
                continue
    
    # Fix 'raise' statements that might be misaligned
    if line.strip().startswith('raise') and i > 0:
        prev_line = lines[i-1]
        if 'if' in prev_line:
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            fixed_line = ' ' * (prev_indent + 4) + line.lstrip()
            fixed_lines.append(fixed_line)
            i += 1
            continue
    
    fixed_lines.append(line)
    i += 1

# Write back
with open('gui_main.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation issues in gui_main.py")