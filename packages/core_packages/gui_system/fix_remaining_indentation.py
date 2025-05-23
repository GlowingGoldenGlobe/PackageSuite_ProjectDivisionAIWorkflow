#!/usr/bin/env python
"""
Fix remaining indentation issues in gui_main.py
"""

import re

def fix_file():
    with open('gui_main.py', 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check for for loops without proper indentation
        if line.strip().startswith('for ') and line.strip().endswith(':'):
            fixed_lines.append(line)
            # Check next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() and not next_line.startswith(' ' * (len(line) - len(line.lstrip()) + 4)):
                    # Fix indentation
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(' ' * (indent + 4) + next_line.lstrip())
                    continue
        
        # Check for elif/else without proper indentation
        elif (line.strip().startswith('elif ') or line.strip() == 'else:') and line.strip().endswith(':'):
            fixed_lines.append(line)
            # Skip empty lines
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                fixed_lines.append(lines[j])
                j += 1
            
            # Check actual next line with content
            if j < len(lines):
                next_line = lines[j]
                if next_line.strip():
                    indent = len(line) - len(line.lstrip())
                    if not next_line.startswith(' ' * (indent + 4)):
                        # Fix indentation
                        fixed_lines.append(' ' * (indent + 4) + next_line.lstrip())
                        # Mark that we've processed this line
                        lines[j] = ''  # Clear it so we skip it later
                        continue
        
        # Regular line processing
        if line or i == len(lines) - 1:  # Keep empty lines and last line
            fixed_lines.append(line)
    
    # Write back
    with open('gui_main.py', 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed remaining indentation issues")

if __name__ == "__main__":
    fix_file()