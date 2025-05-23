#!/usr/bin/env python
"""
Diagnostic script to identify GUI launch issues
"""
import os
import sys
import importlib
import traceback

# Fix import path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

print("GlowingGoldenGlobe GUI Diagnostics")
print("==================================\n")

print(f"Python Version: {sys.version}")
print(f"Working Directory: {os.getcwd()}")
print(f"Script Directory: {script_dir}")
print(f"Parent Directory: {parent_dir}\n")

# Test basic imports
print("Testing Basic Imports:")
basic_imports = ['tkinter', 'json', 'datetime', 'threading']
for module in basic_imports:
    try:
        importlib.import_module(module)
        print(f"✓ {module} - OK")
    except ImportError as e:
        print(f"✗ {module} - FAILED: {e}")

print("\nTesting Project Imports:")
project_imports = [
    'ggg_gui_styles',
    'hardware_monitor',
    'help_system',
    'refined_model_integration',
    'auto_refiner_integration',
    'model_notification_system',
    'Objectives_1',
    'agent_mode_gui_implementation'
]

for module in project_imports:
    try:
        importlib.import_module(module)
        print(f"✓ {module} - OK")
    except ImportError as e:
        print(f"✗ {module} - FAILED: {e}")

print("\nTesting AI Managers Imports:")
ai_managers = [
    'ai_managers.task_manager',
    'ai_managers.refined_model_manager',
    'ai_managers.project_ai_manager'
]

for module in ai_managers:
    try:
        importlib.import_module(module)
        print(f"✓ {module} - OK")
    except ImportError as e:
        print(f"✗ {module} - FAILED: {e}")

print("\nTesting GUI Creation:")
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    print("✓ Tkinter root window created")
    
    # Test GGGStyles
    try:
        from ggg_gui_styles import GGGStyles
        styles = GGGStyles(root)
        print("✓ GGGStyles initialized")
    except Exception as e:
        print(f"✗ GGGStyles failed: {e}")
    
    # Test MainGUI import
    try:
        from gui_main import MainGUI
        print("✓ MainGUI imported successfully")
        
        # Try to create instance
        try:
            app = MainGUI(root)
            print("✓ MainGUI instance created")
        except Exception as e:
            print(f"✗ MainGUI instantiation failed: {e}")
            traceback.print_exc()
    except Exception as e:
        print(f"✗ MainGUI import failed: {e}")
        traceback.print_exc()
    
    root.destroy()
    
except Exception as e:
    print(f"✗ GUI test failed: {e}")
    traceback.print_exc()

print("\nDiagnostics complete.")
print("\nRecommendations:")
print("1. Use Launch_GUI_Safe.bat for a version that handles missing imports")
print("2. Use Launch_GUI_Fixed.bat for a minimal working GUI")
print("3. Check gui_launcher_error_log.txt for detailed error logs")