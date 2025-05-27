#!/usr/bin/env python3
"""
Fixed version of Interleaving Status Indicator that uses grid geometry
to avoid conflicts with middle_section's grid layout

GEOMETRY MANAGER FIX: Original version caused "cannot use geometry manager pack 
inside frame which already has slaves managed by grid" error.

Solution discovered using /docs/Richard_Isaac_Craddock_Procedural_Problem_Solving_Method.md
For future GUI additions, see /docs/Procedure_for_Upgrading_the_GUI.md

Key fix: When adding to a parent that uses grid, the component must also use grid.
"""

import tkinter as tk
from tkinter import ttk

def add_status_indicators_fixed(parent_frame, row=1, column=0, columnspan=2):
    """
    Add status indicators using grid geometry manager
    
    Args:
        parent_frame: The parent frame (should be using grid for its children)
        row: Grid row to place the indicator
        column: Grid column to place the indicator  
        columnspan: How many columns to span
    """
    # Create container frame and use grid
    container = ttk.Frame(parent_frame)
    container.grid(row=row, column=column, columnspan=columnspan, 
                   sticky="ew", padx=5, pady=10)
    
    # Create a simple status label for now
    status_frame = ttk.LabelFrame(container, text="Interleaving Status", padding=5)
    status_frame.pack(fill=tk.X)  # Can use pack inside container
    
    # Status content
    status_label = ttk.Label(status_frame, 
                           text="🟢 Interleaving Enabled | Active: Div_AI_Agent_Focus_1, Div_AI_Agent_Focus_3",
                           font=("Arial", 9))
    status_label.pack(pady=5)
    
    return container