#!/usr/bin/env python
"""
GlowingGoldenGlobe Enhanced GUI Launcher

This script provides an easy way to launch the enhanced Agent Mode GUI
without modifying the original implementation. It gives users a choice
between the original and enhanced versions.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform

def launch_original():
    """Launch the original GUI implementation"""
    try:
        # Try the new location first, then fall back to the old location
        new_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_main.py")
        old_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_mode_gui.py")
        
        if os.path.exists(new_path):
            if platform.system() == "Windows":
                subprocess.Popen(["python", new_path], shell=True)
            else:
                subprocess.Popen(["python3", new_path], shell=True)
            launcher_window.destroy()
        elif os.path.exists(old_path):
            if platform.system() == "Windows":
                subprocess.Popen(["python", old_path], shell=True)
            else:
                subprocess.Popen(["python3", old_path], shell=True)
            launcher_window.destroy()
        else:
            messagebox.showerror("Error", "Original GUI file not found!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch original GUI: {str(e)}")

def launch_enhanced():
    """Launch the enhanced GUI implementation"""
    try:
        # Try the new location first, then fall back to the old location
        new_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_enhanced.py")
        old_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_mode_gui_enhanced.py")
        
        if os.path.exists(new_path):
            if platform.system() == "Windows":
                subprocess.Popen(["python", new_path], shell=True)
            else:
                subprocess.Popen(["python3", new_path], shell=True)
            launcher_window.destroy()
        elif os.path.exists(old_path):
            if platform.system() == "Windows":
                subprocess.Popen(["python", old_path], shell=True)
            else:
                subprocess.Popen(["python3", old_path], shell=True)
            launcher_window.destroy()
        else:
            messagebox.showerror("Error", "Enhanced GUI file not found!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch enhanced GUI: {str(e)}")

def show_differences():
    """Show the key differences between the original and enhanced versions"""
    differences = """
Key Enhancements in the Enhanced GUI:

1. Fixed Import Issues
   - Changed 'from task_manager import TaskManager' to 'from ai_managers.task_manager import TaskManager'

2. Enhanced Status Display
   - Status updates now shown in the status bar instead of popup windows
   - Process status, runtime, and remaining time are displayed in real-time

3. Time Limit Options
   - Added minutes option for time limits (not just hours)
   - Improved validation of time inputs

4. Model Version Display Improvements
   - Enhanced status display to show "not-built/in-progress/date-completed"
   - Dates are displayed for model creation, modification, and simulation completion

5. Related Model Parts
   - When a model part is selected, shows other versions of the same part
   - Displays related parts based on naming patterns
   - Shows additional details about selected parts

6. Status Bar Updates
   - Added process timer showing elapsed time and remaining time
   - Dynamic status updates during operations
   - Color-coded status messages (green for success, red for errors, blue for information)
"""
    differences_window = tk.Toplevel(launcher_window)
    differences_window.title("Enhanced GUI Differences")
    differences_window.geometry("640x480")
    
    scroll_frame = ttk.Frame(differences_window)
    scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    text_widget = tk.Text(scroll_frame, wrap=tk.WORD, height=20, width=80)
    scrollbar = ttk.Scrollbar(scroll_frame, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    text_widget.insert(tk.END, differences)
    text_widget.config(state=tk.DISABLED)
    
    close_button = ttk.Button(differences_window, text="Close", command=differences_window.destroy)
    close_button.pack(pady=10)

# Create the launcher window
launcher_window = tk.Tk()
launcher_window.title("GlowingGoldenGlobe GUI Launcher")
launcher_window.geometry("500x300")

# Add header
header_frame = ttk.Frame(launcher_window)
header_frame.pack(fill=tk.X, pady=20)
header_label = ttk.Label(header_frame, text="GlowingGoldenGlobe GUI Launcher", font=("Arial", 16, "bold"))
header_label.pack()

# Add info text
info_text = """
Please select which version of the Agent Mode GUI you'd like to launch.
The enhanced version includes improved status display, time limit options,
and better model version information.
"""
info_label = ttk.Label(launcher_window, text=info_text, wraplength=400, justify=tk.CENTER)
info_label.pack(pady=10)

# Add buttons
button_frame = ttk.Frame(launcher_window)
button_frame.pack(pady=20)

original_button = ttk.Button(button_frame, text="Launch Original GUI", command=launch_original, width=20)
original_button.grid(row=0, column=0, padx=10, pady=10)

enhanced_button = ttk.Button(button_frame, text="Launch Enhanced GUI", command=launch_enhanced, width=20)
enhanced_button.grid(row=0, column=1, padx=10, pady=10)

differences_button = ttk.Button(launcher_window, text="View Differences", command=show_differences)
differences_button.pack(pady=10)

# Start the application
launcher_window.mainloop()
