"""
Simple Duplicate Checker - Token Efficient
Only runs when explicitly called, no auto-recording
"""

import os
import difflib
from pathlib import Path

def quick_duplicate_check(directory=".", show_only=True):
    """
    Quick check for obvious duplicates
    show_only: if True, just prints results without saving anything
    """
    files = list(Path(directory).rglob("*.py")) + \
            list(Path(directory).rglob("*.bat")) + \
            list(Path(directory).rglob("*.sh"))
    
    # Group by similar names
    similar_groups = {}
    
    for i, file1 in enumerate(files):
        for file2 in files[i+1:]:
            similarity = difflib.SequenceMatcher(
                None, file1.name, file2.name
            ).ratio()
            
            if similarity > 0.8:
                base_name = file1.stem.split('_')[0]
                if base_name not in similar_groups:
                    similar_groups[base_name] = set()
                similar_groups[base_name].add(file1.name)
                similar_groups[base_name].add(file2.name)
    
    # Just print results, don't save
    if similar_groups:
        print("Potential duplicates found:")
        for group, files in similar_groups.items():
            print(f"\n{group}:")
            for f in files:
                print(f"  - {f}")
    else:
        print("No obvious duplicates found")
    
    return similar_groups if not show_only else None

if __name__ == "__main__":
    # Only runs when explicitly called
    quick_duplicate_check()