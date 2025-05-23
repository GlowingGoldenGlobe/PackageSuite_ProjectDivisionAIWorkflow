#!/usr/bin/env python
"""
GlowingGoldenGlobe GUI Integration Module for Parallel Execution

This module provides integration between the main GGG GUI and the
Parallel Execution system. It allows the Parallel Execution GUI to
be embedded as a tab within the main GGG GUI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

# Add the base directory to the path for imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Import the Parallel Execution GUI
try:
    from parallel_execution_gui import ParallelExecutionGUI
except ImportError:
    print("Error importing ParallelExecutionGUI")
    
    class ParallelExecutionGUI:
        def __init__(self, root=None, manager=None, standalone=True):
            frame = ttk.Frame(root)
            ttk.Label(frame, text="Parallel Execution Manager not available").pack(pady=20)
            self.frame = frame

# Import the Parallel Execution Manager
try:
    sys.path.append(os.path.join(base_dir, 'ai_managers'))
    from parallel_execution_manager import ParallelExecutionManager
except ImportError:
    print("Error importing ParallelExecutionManager")
    ParallelExecutionManager = None

def create_parallel_tab(notebook):
    """
    Create a tab for parallel execution in the provided notebook.
    
    Args:
        notebook: ttk.Notebook object to add the tab to
        
    Returns:
        The tab Frame containing the parallel execution GUI
    """
    # Create a frame for the tab
    tab_frame = ttk.Frame(notebook)
    
    # Initialize the ParallelExecutionManager
    manager = ParallelExecutionManager() if ParallelExecutionManager else None
    
    # Create the ParallelExecutionGUI
    parallel_gui = ParallelExecutionGUI(
        root=tab_frame,
        manager=manager,
        standalone=False
    )
    
    # Add the tab to the notebook
    notebook.add(tab_frame, text="Parallel Execution")
    
    return tab_frame

def add_parallel_menu_options(menu_bar):
    """
    Add parallel execution options to the menu bar.
    
    Args:
        menu_bar: tk.Menu object to add options to
        
    Returns:
        The submenu containing the parallel execution options
    """
    # Check if Tools menu exists, create if not
    tools_menu = None
    for i in range(menu_bar.index('end') + 1):
        if menu_bar.entrycget(i, 'label') == 'Tools':
            tools_menu = menu_bar.nametowidget(menu_bar.entryconfigure(i, 'menu')[-1])
            break
            
    if not tools_menu:
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
    
    # Create parallel execution submenu
    parallel_menu = tk.Menu(tools_menu, tearoff=0)
    tools_menu.add_cascade(label="Parallel Execution", menu=parallel_menu)
    
    # Add options to submenu
    parallel_menu.add_command(label="Start All Roles", command=_start_all_roles)
    parallel_menu.add_command(label="Stop All Roles", command=_stop_all_roles)
    parallel_menu.add_separator()
    parallel_menu.add_command(label="Launch Standalone GUI", command=_launch_standalone)
    parallel_menu.add_command(label="Check Package Updates", command=_check_updates)
    
    return parallel_menu

def _start_all_roles():
    """Start all roles in the ParallelExecutionManager."""
    try:
        manager = ParallelExecutionManager()
        manager.start_all_roles()
        print("All parallel execution roles started")
    except Exception as e:
        print(f"Error starting roles: {e}")

def _stop_all_roles():
    """Stop all roles in the ParallelExecutionManager."""
    try:
        manager = ParallelExecutionManager()
        manager.stop_all_roles()
        print("All parallel execution roles stopped")
    except Exception as e:
        print(f"Error stopping roles: {e}")

def _launch_standalone():
    """Launch the standalone ParallelExecutionGUI."""
    try:
        subprocess.Popen([sys.executable, "parallel_execution_gui.py"])
    except Exception as e:
        print(f"Error launching parallel execution GUI: {e}")

def _check_updates():
    """Launch the package update checker."""
    try:
        subprocess.Popen([sys.executable, "package_update_checker.py"])
    except Exception as e:
        print(f"Error launching package update checker: {e}")

# Add missing import
import subprocess

# Example usage
if __name__ == "__main__":
    # Create a simple test window
    root = tk.Tk()
    root.title("GGG GUI Integration Test")
    root.geometry("800x600")
    
    # Create a notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create a dummy tab
    dummy_tab = ttk.Frame(notebook)
    notebook.add(dummy_tab, text="Main")
    ttk.Label(dummy_tab, text="This is the main tab").pack(pady=20)
    
    # Create the parallel execution tab
    create_parallel_tab(notebook)
    
    # Create a menu bar
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    # Add File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=root.destroy)
    
    # Add parallel execution menu options
    add_parallel_menu_options(menu_bar)
    
    root.mainloop()
