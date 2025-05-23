#!/usr/bin/env python
"""
Integration Module for Claude Parallel GUI

This module integrates the Claude Parallel GUI with the main GlowingGoldenGlobe GUI.
It adds a Claude Parallel Execution tab to the main interface and handles the initialization
of the Claude Parallel Manager.

Usage:
    from gui_claude_integration import integrate_claude_parallel
    integrate_claude_parallel(notebook)
"""

import os
import sys
import logging
from tkinter import ttk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui_claude_integration.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GUIClaudeIntegration")

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Try to import required modules
try:
    from gui.claude_parallel_gui import ClaudeParallelGUI
except ImportError:
    logger.error("Failed to import ClaudeParallelGUI")
    ClaudeParallelGUI = None

def integrate_claude_parallel(notebook):
    """
    Integrate the Claude Parallel GUI with the main GlowingGoldenGlobe GUI.
    
    Args:
        notebook: The ttk.Notebook widget to add the tab to
        
    Returns:
        bool: True if integration was successful, False otherwise
    """
    logger.info("Integrating Claude Parallel GUI with main GUI")
    
    if not ClaudeParallelGUI:
        logger.error("ClaudeParallelGUI module not available")
        return False
    
    try:
        # Create a frame for the tab
        tab_frame = ttk.Frame(notebook)
        
        # Initialize the Claude Parallel GUI inside this frame
        gui = ClaudeParallelGUI(tab_frame)
        
        # Add the tab to the notebook
        notebook.add(tab_frame, text="Claude Parallel")
        
        logger.info("Claude Parallel GUI integrated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error integrating Claude Parallel GUI: {e}")
        return False

def check_claude_parallel_available():
    """
    Check if the Claude Parallel system is available.
    
    Returns:
        bool: True if Claude Parallel system is available, False otherwise
    """
    # Check for required files
    required_files = [
        "claude_parallel_manager.py",
        "claude_task_executor.py",
        "claude_parallel_integration.py",
        "ai_agent_detector.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(BASE_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.warning(f"Claude Parallel system is missing files: {', '.join(missing_files)}")
        return False
    
    return True

# These functions can be called by the main GUI to check if Claude Parallel is available
# and to add the Claude Parallel tab to the main GUI
def is_claude_parallel_available():
    """
    Check if the Claude Parallel system is available.
    
    Returns:
        bool: True if available, False otherwise
    """
    return check_claude_parallel_available()

def add_claude_parallel_tab(notebook):
    """
    Add the Claude Parallel tab to the main GUI.
    
    Args:
        notebook: The ttk.Notebook widget to add the tab to
        
    Returns:
        bool: True if successful, False otherwise
    """
    return integrate_claude_parallel(notebook)