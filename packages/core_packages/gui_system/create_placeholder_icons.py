#!/usr/bin/env python
"""
Create Placeholder Icons for GGG GUI
Creates simple icon images with black background and white pyramid/triangle
"""

import os
from PIL import Image, ImageDraw
import io

def create_pyramid_icon(size=(64, 64), bg_color='black', pyramid_color='white'):
    """
    Create a simple pyramid/triangle icon.
    
    Args:
        size: Tuple of (width, height) for the icon
        bg_color: Background color
        pyramid_color: Color of the pyramid
    
    Returns:
        PIL Image object
    """
    # Create new image
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Calculate pyramid points
    width, height = size
    margin = width // 8  # Add some margin
    
    # Triangle points: top middle, bottom left, bottom right
    points = [
        (width // 2, margin),  # Top point
        (margin, height - margin),  # Bottom left
        (width - margin, height - margin)  # Bottom right
    ]
    
    # Draw filled triangle/pyramid
    draw.polygon(points, fill=pyramid_color)
    
    # Add a subtle 3D effect by drawing edges
    draw.line([points[0], points[1]], fill='lightgray', width=2)
    draw.line([points[0], points[2]], fill='lightgray', width=2)
    draw.line([points[1], points[2]], fill='gray', width=2)
    
    return img


def create_icons(output_dir=None):
    """
    Create placeholder icons in various sizes and formats.
    
    Args:
        output_dir: Directory to save icons. If None, uses gui/gui_icons/
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "gui_icons")
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Icon sizes to create
    sizes = {
        'small': (16, 16),
        'medium': (32, 32),
        'large': (64, 64),
        'xlarge': (128, 128),
        'ico': (48, 48)  # Standard size for .ico files
    }
    
    icons_created = []
    
    # Create icons in different sizes
    for size_name, dimensions in sizes.items():
        img = create_pyramid_icon(dimensions)
        
        # Save as PNG
        png_path = os.path.join(output_dir, f"ggg_icon_{size_name}.png")
        img.save(png_path)
        icons_created.append(png_path)
        print(f"Created: {png_path}")
        
        # Save the medium size as the default icon
        if size_name == 'medium':
            default_path = os.path.join(output_dir, "ggg_icon.png")
            img.save(default_path)
            icons_created.append(default_path)
            print(f"Created: {default_path}")
    
    # Create .ico file (Windows icon)
    try:
        # Create multi-resolution .ico file
        ico_img = create_pyramid_icon((48, 48))
        ico_path = os.path.join(output_dir, "ggg_icon.ico")
        
        # Create additional sizes for .ico file
        ico_sizes = [(16, 16), (32, 32), (48, 48)]
        ico_images = []
        
        for size in ico_sizes:
            ico_images.append(create_pyramid_icon(size))
        
        # Save as .ico with multiple resolutions
        ico_images[2].save(ico_path, format='ICO', sizes=ico_sizes)
        icons_created.append(ico_path)
        print(f"Created: {ico_path}")
    except Exception as e:
        print(f"Warning: Could not create .ico file: {e}")
        # Fallback: save single size .ico
        try:
            ico_img = create_pyramid_icon((32, 32))
            ico_path = os.path.join(output_dir, "ggg_icon.ico")
            ico_img.save(ico_path, format='ICO')
            icons_created.append(ico_path)
            print(f"Created fallback: {ico_path}")
        except Exception as e2:
            print(f"Error creating .ico file: {e2}")
    
    return icons_created


def update_auto_icon_loader():
    """Update the auto_icon_loader.py to include placeholder creation."""
    loader_path = os.path.join(os.path.dirname(__file__), "auto_icon_loader.py")
    
    # Read the current content
    with open(loader_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if placeholder creation is already included
    if "create_placeholder_icons" not in content:
        # Add import at the top
        import_line = "from create_placeholder_icons import create_pyramid_icon, create_icons\n"
        
        # Find where to insert the import
        import_pos = content.find("import glob\n")
        if import_pos != -1:
            content = content[:import_pos + 11] + import_line + content[import_pos + 11:]
        
        # Add placeholder creation in find_icon_file function
        placeholder_code = '''
    # If no icon found, create placeholder icons
    if not icon_files:
        print("No icon files found. Creating placeholder icons...")
        try:
            from create_placeholder_icons import create_icons
            created_icons = create_icons()
            if created_icons:
                # Return the .ico file if created, otherwise the first PNG
                for icon in created_icons:
                    if icon.endswith('.ico'):
                        return icon
                return created_icons[0]
        except ImportError:
            print("Could not import placeholder icon creator")
        except Exception as e:
            print(f"Error creating placeholder icons: {e}")
'''
        
        # Find where to insert the placeholder code
        return_none_pos = content.rfind("return None")
        if return_none_pos != -1:
            content = content[:return_none_pos] + placeholder_code + "\n    " + content[return_none_pos:]
        
        # Write back the updated content
        with open(loader_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {loader_path} with placeholder icon creation")


if __name__ == "__main__":
    print("Creating placeholder icons...")
    icons = create_icons()
    print(f"\nCreated {len(icons)} placeholder icons")
    
    print("\nUpdating auto_icon_loader.py...")
    update_auto_icon_loader()
    
    print("\nPlaceholder icons are ready!")