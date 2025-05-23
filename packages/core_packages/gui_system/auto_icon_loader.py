#!/usr/bin/env python
"""
Auto Icon Loader - Finds and loads icon files for the GUI
"""

import os
import glob

def find_icon_file(search_dirs=None):
    """
    Find an icon file in the specified directories.
    
    Args:
        search_dirs: List of directories to search. If None, searches common locations.
    
    Returns:
        Path to the icon file if found, None otherwise
    """
    if search_dirs is None:
        # Default search directories
        base_dir = os.path.dirname(os.path.abspath(__file__))
        search_dirs = [
            base_dir,  # Current directory (gui/)
            os.path.join(base_dir, "gui_icons"),  # gui/gui_icons/
            os.path.join(base_dir, "icons"),  # gui/icons/
            os.path.join(base_dir, "images"),  # gui/images/
            os.path.join(base_dir, "assets"),  # gui/assets/
            os.path.dirname(base_dir),  # Parent directory
        ]
    
    # Common icon file patterns
    icon_patterns = [
        "*.ico",
        "ggg_icon.*",
        "icon.*",
        "logo.*",
        "app_icon.*",
        "favicon.*"
    ]
    
    # Search for icon files
    for dir_path in search_dirs:
        if os.path.exists(dir_path):
            for pattern in icon_patterns:
                files = glob.glob(os.path.join(dir_path, pattern))
                for file in files:
                    # Prefer .ico files for Windows
                    if file.endswith('.ico'):
                        return file
            
            # If no .ico found, look for other image formats
            for pattern in icon_patterns:
                files = glob.glob(os.path.join(dir_path, pattern))
                for file in files:
                    if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        return file
    
    # If no icon found, use default placeholder
    print("No icon files found. Using default placeholder icon...")
    default_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_icons", "default_icon.ppm")
    if os.path.exists(default_icon_path):
        return default_icon_path
    
    return None


def update_gui_icon_path(gui_file_path=None):
    """
    Update the GUI main file with the found icon path.
    
    Args:
        gui_file_path: Path to the GUI main file. If None, uses default.
    """
    if gui_file_path is None:
        gui_file_path = os.path.join(os.path.dirname(__file__), "gui_main.py")
    
    icon_path = find_icon_file()
    
    if icon_path:
        print(f"Found icon file: {icon_path}")
        
        # Read the GUI file
        with open(gui_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the icon loading section
        icon_section_start = content.find("# Try to set custom icon")
        if icon_section_start != -1:
            # Find the try block
            try_block_start = content.find("try:", icon_section_start)
            if try_block_start != -1:
                # Find the except block
                except_block_start = content.find("except", try_block_start)
                if except_block_start != -1:
                    # Replace the try block content
                    indent = "        "  # 8 spaces for proper indentation
                    new_try_content = f'''# Try to set custom icon
        try:
            icon_path = r"{icon_path}"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)'''
                    
                    # Find the end of the try section
                    section_end = content.find("# Initialize custom styles", icon_section_start)
                    if section_end != -1:
                        # Extract the original except block
                        except_section = content[except_block_start:section_end].strip()
                        
                        # Reconstruct the entire section
                        new_section = f"{new_try_content}\n        {except_section}\n\n        "
                        
                        # Replace the section in the content
                        before = content[:icon_section_start]
                        after = content[section_end:]
                        content = before + new_section + after
                        
                        # Write back to file
                        with open(gui_file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"Updated {gui_file_path} with icon path: {icon_path}")
                        return True
    else:
        print("No icon file found in standard locations")
        print("Searched directories:")
        for dir_path in [os.path.dirname(os.path.abspath(__file__)),
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_icons"),
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons"),
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "images"),
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")]:
            print(f"  - {dir_path}")
    
    return False


if __name__ == "__main__":
    # Check current icon files
    print("Searching for icon files...")
    icon_file = find_icon_file()
    
    if icon_file:
        print(f"\nFound icon: {icon_file}")
        
        # Ask user if they want to update the GUI file
        response = input("\nWould you like to update gui_main.py with this icon path? (y/n): ")
        if response.lower() == 'y':
            update_gui_icon_path()
    else:
        print("\nNo icon files found. Please add an icon file to one of these locations:")
        print("  - gui/")
        print("  - gui/gui_icons/")
        print("  - gui/icons/")
        print("  - gui/images/")
        print("  - gui/assets/")