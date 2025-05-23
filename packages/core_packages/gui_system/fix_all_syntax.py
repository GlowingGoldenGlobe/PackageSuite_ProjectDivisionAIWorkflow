"""
Script to fix syntax errors in the GUI main file
"""

import re

# Path to the main GUI file
gui_path = r"c:\Users\yerbr\glowinggoldenglobe_venv\gui\gui_main.py"

# Read the entire file
with open(gui_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Correct the class name
content = content.replace("class gui_main.py:", "class MainGUI:")

# Fix 2: Fix the for loop syntax error near line 2485
# Look for the pattern where for loop is on the same line as a comment
pattern = r"# Find the key for this path\s+for key, val"
replacement = "# Find the key for this path\n            for key, val"
content = re.sub(pattern, replacement, content)

# Fix 3: Make sure there are proper newlines between variable declarations around line 91
lines = content.split('\n')
for i in range(len(lines)):
    if ")        self." in lines[i]:
        parts = lines[i].split(")")
        if len(parts) == 2:
            lines[i] = parts[0] + ")"
            lines.insert(i + 1, "        self." + parts[1].strip())

content = '\n'.join(lines)

# Write the fixed content back to the file
with open(gui_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Syntax errors fixed in", gui_path)
