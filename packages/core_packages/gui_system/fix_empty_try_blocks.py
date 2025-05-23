#!/usr/bin/env python
"""Fix empty try blocks in gui_main.py"""

import re

# Read the file
with open('gui_main.py', 'r') as f:
    content = f.read()

# Pattern to find empty try blocks
# This matches try: followed immediately by except
pattern = r'(\s*)try:\s*\n\s*except'

# Function to replace empty try blocks
def fix_empty_try(match):
    indent = match.group(1)
    return f'{indent}try:\n{indent}    pass\n{indent}except'

# Fix all empty try blocks
fixed_content = re.sub(pattern, fix_empty_try, content)

# Write back
with open('gui_main.py', 'w') as f:
    f.write(fixed_content)

print("Fixed empty try blocks in gui_main.py")