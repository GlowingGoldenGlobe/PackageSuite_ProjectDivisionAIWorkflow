"""
GlowingGoldenGlobe GUI Styling Module

This module provides enhanced styling for the GGG GUI application,
implementing modern-looking controls and visual effects.
"""

import tkinter as tk
from tkinter import ttk
import platform
from PIL import Image, ImageTk, ImageDraw, ImageFilter

class GGGStyles:
    """Class for managing custom GGG GUI styles"""
    
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        
        # Color scheme
        self.colors = {
            'primary': '#3a7ca5',         # Blue
            'secondary': '#d9b310',       # Gold
            'background': '#f5f5f5',      # Light gray
            'text': '#333333',            # Dark gray for text 
            'light_text': '#555555',      # Lighter text
            'success': '#2e8b57',         # Green
            'warning': '#ff9800',         # Orange
            'error': '#b22222',           # Red
            'border': '#cccccc',          # Border color
        }
        
        # Initialize styles
        self._init_styles()
        
        # Create image resources
        self.images = {}
        self._create_button_images()
        
    def apply_theme(self):
        """Apply the theme to all widgets - added for backward compatibility"""
        # This method already happens in __init__, but exists for compatibility
        self._init_styles()
    
    def _init_styles(self):
        """Initialize ttk styles"""        
        self.style.configure('TFrame', background=self.colors['background'])
        self.style.configure('TLabel', background=self.colors['background'], foreground=self.colors['text'])
        self.style.configure('TButton', background=self.colors['primary'], foreground='black', padding=5)
        
        # Remove focus outline (dotted border) from all widgets
        self.style.configure('TButton', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TCheckbutton', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TRadiobutton', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TCombobox', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TEntry', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TLabelframe', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TNotebook', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TNotebook.Tab', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('Treeview', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TScale', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TProgressbar', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('TPanedwindow', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('Vertical.TScrollbar', focuscolor=self.colors['background'])  # Hide focus border
        self.style.configure('Horizontal.TScrollbar', focuscolor=self.colors['background'])  # Hide focus border
        
        # Ensure button text is clearly visible with good contrast
        self.style.map('TButton', 
                      foreground=[('active', 'black'), ('disabled', '#333333')])
        
        # Explicitly set the button text color to black for better contrast against all backgrounds
        self.style.map('TButton', 
                      foreground=[('active', 'black'), ('disabled', '#333333')],
                      background=[('active', self._adjust_color_brightness(self.colors['primary'], 1.2)),
                                 ('disabled', '#cccccc')])
        
        # Header styles - reduced size from 18 to 16
        self.style.configure('Header.TLabel', 
                           font=('Segoe UI', 16, 'bold'), 
                           foreground=self.colors['primary'])
        
        self.style.configure('Subheader.TLabel', 
                           font=('Segoe UI', 14, 'bold'),
                           foreground=self.colors['primary'])
                           
        # Smaller subtitle style for bullet points
        self.style.configure('SubheaderSmall.TLabel', 
                           font=('Segoe UI', 11, 'normal'),
                           foreground=self.colors['light_text'])
        
        # Button styles
        self.style.configure('Big.TButton', font=('Segoe UI', 12, 'bold'))
        self.style.configure('Primary.TButton', background=self.colors['primary'])
        self.style.configure('Success.TButton', background=self.colors['success'])
        self.style.configure('Warning.TButton', background=self.colors['warning'])
        
        # Fix for Large.TButton with visible text - using bold navy blue for better contrast
        self.style.configure('Large.TButton', 
                           font=('Segoe UI', 12, 'bold'),
                           background=self.colors['primary'],
                           foreground='#000080')
        
        # Status styles for labels
        self.style.configure('Success.TLabel', foreground=self.colors['success'])
        self.style.configure('Warning.TLabel', foreground=self.colors['warning'])
        self.style.configure('Error.TLabel', foreground=self.colors['error'])

    def _create_button_images(self):
        """Create custom button images with gradient and shadow effects"""
        # Button sizes
        sizes = {
            'normal': (120, 30),
            'large': (200, 40)
        }
        
        # Create buttons for different states
        states = ['normal', 'active', 'disabled']
        
        for size_name, dimensions in sizes.items():
            for state in states:
                # Select colors based on state
                if state == 'normal':
                    color1 = self.colors['primary']
                    color2 = self._adjust_color_brightness(self.colors['primary'], 0.8)
                elif state == 'active':
                    color1 = self._adjust_color_brightness(self.colors['primary'], 1.2)
                    color2 = self.colors['primary']
                else:  # disabled
                    color1 = '#aaaaaa'
                    color2 = '#888888'
                
                # Create gradient button
                img = self._create_gradient_button(dimensions[0], dimensions[1], color1, color2)
                  # Add shadow effect for non-disabled states
                if state != 'disabled':
                    img = self._add_shadow(img, 5)  # Increased blur radius to 5
                
                # Store the image
                self.images[f'button_{size_name}_{state}'] = ImageTk.PhotoImage(img)
    
    def _create_gradient_button(self, width, height, color1, color2):
        """Create a button with gradient background"""
        img = Image.new('RGBA', (width, height), color=(0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle with gradient
        r = 12  # Increased corner radius for more rounded corners
        for y in range(height):
            # Calculate color for this line in gradient
            ratio = y / height
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            r_val = int(r1 * (1 - ratio) + r2 * ratio)
            g_val = int(g1 * (1 - ratio) + g2 * ratio)
            b_val = int(b1 * (1 - ratio) + b2 * ratio)
            
            draw.line([(r, y), (width-r, y)], fill=(r_val, g_val, b_val))
          # Make corners rounded by adding transparency
        mask = Image.new('L', (width, height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rectangle([r, 0, width-r, height], fill=255)
        draw_mask.rectangle([0, r, width, height-r], fill=255)
        draw_mask.pieslice([0, 0, r*2, r*2], 180, 270, fill=255)
        draw_mask.pieslice([0, height-r*2, r*2, height], 90, 180, fill=255)
        draw_mask.pieslice([width-r*2, 0, width, r*2], 270, 360, fill=255)
        draw_mask.pieslice([width-r*2, height-r*2, width, height], 0, 90, fill=255)
        
        img.putalpha(mask)
        return img
    
    def _add_shadow(self, img, blur_radius=5):
        """Add shadow effect to an image"""
        # Create shadow (black image with same alpha channel)
        shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.bitmap((0, 0), img.split()[3], fill=(0, 0, 0, 120))  # Increased opacity to 120
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Create a new image with shadow and original
        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        result.paste(shadow, (blur_radius, blur_radius))
        result.paste(img, (0, 0), img)
        
        return result
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _adjust_color_brightness(self, hex_color, factor):
        """Adjust brightness of a hex color by factor (>1 for lighter, <1 for darker)"""
        r, g, b = self._hex_to_rgb(hex_color)        
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def create_custom_button(self, parent, text, command, size='normal'):
        """Create a custom button with gradient and shadow"""
        # Create a frame to hold the button with padding for shadow effect
        frame = ttk.Frame(parent, style='TFrame')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Create a standard ttk Button with enhanced styling
        button = ttk.Button(
            frame,
            text=text,
            command=command,
            style='Large.TButton' if size == 'large' else 'TButton'
        )
        button.grid(row=0, column=0, padx=3, pady=3, sticky="nsew")  # Add padding for shadow effect
        
        return frame
    
    def create_status_indicator(self, parent, status_text, status_type='normal'):
        """Create a status indicator with colored icon"""
        frame = ttk.Frame(parent)
        
        # Determine color based on status type
        if status_type == 'success':
            color = self.colors['success']
        elif status_type == 'warning':
            color = self.colors['warning']
        elif status_type == 'error':
            color = self.colors['error']
        else:
            color = self.colors['text']
        
        # Create status dot
        canvas = tk.Canvas(frame, width=10, height=10, bg=self.colors['background'], highlightthickness=0)
        canvas.create_oval(2, 2, 8, 8, fill=color, outline="")
        canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create status text
        label = ttk.Label(frame, text=status_text, foreground=color)
        label.pack(side=tk.LEFT)
        
        return frame
    
    def create_panel_with_title(self, parent, title, **kwargs):
        """Create a panel with title and styled border"""
        # Main frame
        frame = ttk.Frame(parent, style='TFrame', **kwargs)
        
        # Title frame (raised slightly above the main frame)
        title_frame = ttk.Frame(frame)
        title_frame.pack(anchor='nw', padx=10, pady=(0, 5))
        
        title_label = ttk.Label(title_frame, text=title, style='Subheader.TLabel')
        title_label.pack()
        
        # Content frame (with border)
        content_frame = ttk.Frame(frame, relief='groove', borderwidth=1)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        return content_frame
    
    def set_theme(self, theme_name='default'):
        """Set a predefined theme"""
        if theme_name == 'dark':
            self.colors = {
                'primary': '#2a5980',      # Darker blue
                'secondary': '#b39000',    # Darker gold
                'background': '#2b2b2b',   # Dark gray
                'text': '#e0e0e0',         # Light gray for text
                'light_text': '#aaaaaa',   # Lighter text
                'success': '#2e7d32',      # Dark green
                'warning': '#e65100',      # Dark orange
                'error': '#8b0000',        # Dark red
                'border': '#444444',       # Border color
            }
        elif theme_name == 'light':
            self.colors = {
                'primary': '#4a8cb5',      # Lighter blue
                'secondary': '#e9c320',    # Lighter gold
                'background': '#ffffff',   # White
                'text': '#333333',         # Dark gray for text
                'light_text': '#555555',   # Lighter text
                'success': '#4caf50',      # Light green
                'warning': '#ff9800',      # Orange
                'error': '#f44336',        # Red
                'border': '#e0e0e0',       # Border color
            }
        else:  # default
            self.colors = {
                'primary': '#3a7ca5',      # Blue
                'secondary': '#d9b310',    # Gold
                'background': '#f5f5f5',   # Light gray
                'text': '#333333',         # Dark gray for text
                'light_text': '#555555',   # Lighter text
                'success': '#2e8b57',      # Green
                'warning': '#ff9800',      # Orange
                'error': '#b22222',        # Red
                'border': '#cccccc',       # Border color
            }
        
        # Re-initialize styles with new colors
        self._init_styles()
        
        # Explicitly re-apply focus color configuration since _init_styles is called without checking the theme
        self.style.configure('TButton', focuscolor=self.colors['background'])
        self.style.configure('TCheckbutton', focuscolor=self.colors['background'])
        self.style.configure('TRadiobutton', focuscolor=self.colors['background'])
        self.style.configure('TCombobox', focuscolor=self.colors['background'])
        self.style.configure('TEntry', focuscolor=self.colors['background'])
        self.style.configure('TLabelframe', focuscolor=self.colors['background'])
        self.style.configure('TNotebook', focuscolor=self.colors['background'])
        self.style.configure('TNotebook.Tab', focuscolor=self.colors['background'])
        self.style.configure('Treeview', focuscolor=self.colors['background'])
        self.style.configure('TScale', focuscolor=self.colors['background'])
        self.style.configure('TProgressbar', focuscolor=self.colors['background'])
        self.style.configure('TPanedwindow', focuscolor=self.colors['background'])
        self.style.configure('Vertical.TScrollbar', focuscolor=self.colors['background'])
        self.style.configure('Horizontal.TScrollbar', focuscolor=self.colors['background'])
        
        self._create_button_images()
