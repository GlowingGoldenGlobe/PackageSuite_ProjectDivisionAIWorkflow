#!/usr/bin/env python
"""
Create a simple placeholder icon using basic Python
Creates a PPM file that can be converted or used as a placeholder
"""

import os

def create_ppm_icon(filename, size=32):
    """Create a simple PPM format icon with a white triangle on black background"""
    
    # PPM header
    header = f"P3\n{size} {size}\n255\n"
    
    # Create pixel data
    pixels = []
    center_x = size // 2
    
    for y in range(size):
        row = []
        for x in range(size):
            # Create a simple triangle shape
            # Triangle: top at center, widening towards bottom
            margin = size // 8
            top_y = margin
            bottom_y = size - margin
            
            if y >= top_y and y <= bottom_y:
                # Calculate triangle width at this y position
                progress = (y - top_y) / (bottom_y - top_y)
                half_width = int(progress * (size // 2 - margin))
                
                if abs(x - center_x) <= half_width:
                    # Inside triangle - white pixel
                    row.append("255 255 255")
                else:
                    # Outside triangle - black pixel
                    row.append("0 0 0")
            else:
                # Outside triangle bounds - black pixel
                row.append("0 0 0")
        
        pixels.append(" ".join(row))
    
    # Combine header and pixels
    content = header + "\n".join(pixels)
    
    # Write to file
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Created: {filename}")

# Create the gui_icons directory if it doesn't exist
icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_icons")
os.makedirs(icon_dir, exist_ok=True)

# Create placeholder icons
create_ppm_icon(os.path.join(icon_dir, "default_icon.ppm"), 32)
create_ppm_icon(os.path.join(icon_dir, "default_icon_large.ppm"), 64)

print(f"\nPlaceholder icons created in: {icon_dir}")
print("Note: These are PPM format files - basic image format that can be converted to other formats if needed")