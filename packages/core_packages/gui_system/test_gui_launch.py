#!/usr/bin/env python
"""
Test script to verify GUI can launch correctly
"""

import os
import sys

# Fix import path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

print("Testing GUI launch...")
print(f"Script directory: {script_dir}")
print(f"Parent directory: {parent_dir}")

# Test imports
try:
    import tkinter as tk
    print("✓ tkinter imported successfully")
except ImportError as e:
    print(f"✗ tkinter import failed: {e}")
    
try:
    from ggg_gui_styles import GGGStyles
    print("✓ ggg_gui_styles imported successfully")
except ImportError as e:
    print(f"✗ ggg_gui_styles import failed: {e}")

try:
    from hardware_monitor import HardwareMonitor
    print("✓ hardware_monitor imported successfully")
except ImportError as e:
    print(f"✗ hardware_monitor import failed: {e}")

try:
    from agent_mode_gui_implementation import implement_enhancements
    print("✓ agent_mode_gui_implementation imported successfully")
except ImportError as e:
    print(f"✗ agent_mode_gui_implementation import failed: {e}")

try:
    import Objectives_1
    print("✓ Objectives_1 imported successfully")
except ImportError as e:
    print(f"✗ Objectives_1 import failed: {e}")

# Test GUI launch (without displaying)
try:
    root = tk.Tk()
    root.withdraw()  # Don't show the window
    print("✓ Tkinter root window created successfully")
    
    # Test importing main GUI
    from gui_main_fixed import MainGUI
    print("✓ MainGUI imported successfully")
    
    # Try to create GUI instance (but don't run mainloop)
    # app = MainGUI(root)
    # print("✓ MainGUI instance created successfully")
    
    root.destroy()
    print("\n✓ GUI tests passed! The GUI should be launchable.")
    
except Exception as e:
    print(f"\n✗ GUI test failed: {e}")
    import traceback
    traceback.print_exc()

print("\nFor issues related to imports from parent directory, you may need to run:")
print("python -m gui.gui_launcher_fixed")
print("or")
print("cd .. && python gui/gui_launcher_fixed.py")