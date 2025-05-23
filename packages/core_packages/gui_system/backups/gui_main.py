#!/usr/bin/env python
# GUI Main - GlowingGoldenGlobe User Controls
# This file integrates all GUI features including Claude Parallel functionality
# while preserving the original GUI appearance and features

import os
import sys
import json
import datetime
import subprocess
import platform
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import webbrowser
import glob
import re
import time
from datetime import timedelta

# Fix path to find parent directory modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import custom modules
try:
    # Import styling
    from gui.gui_styles import GGGStyles
    # System monitoring is now handled by system_monitor_integration.py
    # from hardware_monitor import HardwareMonitor
    # Import task management
    from ai_managers.task_manager import TaskManager
    # Import help system
    from help_system import HelpSystem
    # Import model integration
    from refined_model_integration import RefinedModelIntegration
    # Import Claude Parallel integration
    from gui.gui_claude_integration import integrate_claude_parallel, is_claude_parallel_available
    # Import project objectives
    import Objectives_1 as project_objectives
    # Import AI Workflow management
    sys.path.insert(0, parent_dir)
    import ai_workflow_status
    import workflow_pause
except ImportError as e:
    print(f"Error importing module: {e}")
    # Create placeholder classes if modules are not found
    class PlaceholderClass:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    # Replace missing modules with placeholders
    if 'GGGStyles' not in globals():
        GGGStyles = PlaceholderClass
    if 'HardwareMonitor' not in globals():
        HardwareMonitor = PlaceholderClass
    if 'TaskManager' not in globals():
        TaskManager = PlaceholderClass
    if 'HelpSystem' not in globals():
        HelpSystem = PlaceholderClass
    if 'RefinedModelIntegration' not in globals():
        RefinedModelIntegration = PlaceholderClass
    if 'integrate_claude_parallel' not in globals():
        def integrate_claude_parallel(*args, **kwargs):
            return False
    if 'is_claude_parallel_available' not in globals():
        def is_claude_parallel_available():
            return False

class GlowingGoldenGlobeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GlowingGoldenGlobe User Controls")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set window size to full height but half width (50%)
        # Make it a bit wider than 50% to ensure full use of space
        window_width = int(screen_width * 0.55)
        window_height = int(screen_height * 1.0)  # Full height
        
        # Position window at the left side of the screen
        position_x = 0  # Align to left of screen
        position_y = 0  # Align to top of screen
        
        # Set the geometry (width x height + x_position + y_position)
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.root.resizable(True, True)
        
        # Try to set custom icon
        try:
            # Use an empty default icon instead of Python icon
            if platform.system() == "Windows":
                # Load a transparent or custom icon to replace the Python icon
                icon_path = os.path.join(os.path.dirname(__file__), "gui_icons", "default_icon.ppm")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                else:
                    self.root.iconbitmap(default="")
        except Exception as e:
            print(f"Could not set custom icon: {str(e)}")
            pass  # Continue without custom icon
        
        # Initialize custom styles
        self.styles = GGGStyles(self.root)
        
        # Initialize support modules
        # Hardware monitoring is now handled by system_monitor_integration.py
        self.task_manager = TaskManager()
        self.help_system = HelpSystem()
        
        # Setup configuration
        self.config = self.load_initial_config()
        
        # Get model parts from AI agent folders
        model_parts = self.get_model_parts_from_agents_fast()
        
        # Create Tkinter variables
        self.development_mode = tk.StringVar(value=self.config.get("development_mode", "refined_model"))
        self.time_limit_hours = tk.StringVar(value=str(self.config.get("time_limit_hours", 1)))
        self.time_limit_minutes = tk.StringVar(value=str(self.config.get("time_limit_minutes", 0)))
        self.auto_save_interval = tk.StringVar(value=str(self.config.get("auto_save_interval", 5)))
        self.auto_continue = tk.BooleanVar(value=self.config.get("auto_continue", True))
        self.selected_version = tk.StringVar(value=self.config.get("selected_version", "1"))
        
        # Set the selected model part based on config or first available part
        saved_part = self.config.get("selected_model_part", "Complete Assembly")
        if saved_part in model_parts:
            self.selected_model_part = tk.StringVar(value=saved_part)
        elif model_parts:
            self.selected_model_part = tk.StringVar(value=model_parts[0])
        else:
            self.selected_model_part = tk.StringVar(value="Complete Assembly")
            
        self.agent_instructions = tk.StringVar(value="")
        self.message_field = tk.StringVar(value="")
        self.current_status = tk.StringVar(value="Ready")
        
        # Create main frame with notebook for tabs
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="GlowingGoldenGlobe User Controls", 
                 style="Header.TLabel").pack(side=tk.LEFT)
        
        # Help button
        help_button = ttk.Button(header_frame, text="Help", command=self.show_help)
        help_button.pack(side=tk.RIGHT, padx=5)
        
        # Subtitle points, left-aligned (without bullet characters)
        subtitle_frame = ttk.Frame(main_frame)
        subtitle_frame.pack(fill=tk.X, pady=(0, 10), anchor=tk.W)
        
        ttk.Label(subtitle_frame, text="pyautogen syntax format", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        ttk.Label(subtitle_frame, text="• AI Agents API-key mode", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        ttk.Label(subtitle_frame, text="• VSCode Agent mode", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        # Added as last item at left
        ttk.Label(subtitle_frame, text="• Standalone Subscription Agent mode", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Main tab - positioned first
        self.main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.main_tab, text="Main Controls")
        
        # Integrate efficient system monitor
        try:
            from gui.system_monitor_integration import integrate_with_gui
            integrate_with_gui(self.notebook)
        except ImportError as e:
            print(f"System monitor integration not available: {e}")
        
        # Hardware monitoring tab - Replaced with system_monitor_integration.py
        # self.hardware_tab = ttk.Frame(self.notebook, padding=10)
        # self.notebook.add(self.hardware_tab, text="Hardware Monitor")
        
        # Task management tab
        self.tasks_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tasks_tab, text="Tasks & Schedule")
        
        # Help tab
        self.help_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.help_tab, text="Help")
        
        # Set up each tab's content
        self.setup_main_tab()
        # Hardware tab is now handled by system_monitor_integration.py
        # self.setup_hardware_tab()
        self.setup_tasks_tab()
        self.setup_help_tab()
        
        # Add Claude Parallel tab if available
        if is_claude_parallel_available():
            integrate_claude_parallel(self.notebook)
        
        # Initialize refined model integration
        self.refined_model = RefinedModelIntegration(self)
        
        # Schedule updates
        self.schedule_updates()
        
        # Update model version list
        self.update_version_list()
        
        # Update model parts list
        self.update_model_parts_list()

    def setup_main_tab(self):
        """Set up the main control tab"""
        # Create a canvas with scrollbar for lots of content
        canvas = tk.Canvas(self.main_tab, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create top section
        top_section = ttk.Frame(scrollable_frame)
        top_section.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure the top section to fully use available width
        top_section.columnconfigure(0, weight=1)  # Development Options (narrower)
        top_section.columnconfigure(1, weight=4)  # Model Versions & Related Files (much wider)
        
        # LEFT SIDE - Options section (narrower)
        options_frame = ttk.LabelFrame(top_section, text="Development Options", padding=10)
        options_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # RIGHT SIDE - Model versions section with listbox (wider)
        # Put Model Versions & Related Files on the RIGHT side
        version_frame = ttk.LabelFrame(top_section, text="Model Versions & Related Files", padding=10)
        version_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Create a paned window to divide versions and files
        paned = ttk.PanedWindow(version_frame, orient="horizontal")
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Version list on left side (smaller proportion)
        v_frame = ttk.Frame(paned)
        paned.add(v_frame, weight=1)
        
        ttk.Label(v_frame, text="Available Versions:").pack(anchor="w")
        
        self.version_listbox = tk.Listbox(v_frame, height=6, exportselection=0)
        self.version_listbox.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Add selection event handler
        self.version_listbox.bind('<<ListboxSelect>>', self.on_version_select)
        
        # Related files list on right side (larger proportion for longer filenames)
        f_frame = ttk.Frame(paned)
        paned.add(f_frame, weight=5)  # Fixed weight value for better display
        
        ttk.Label(f_frame, text="Related Files:").pack(anchor="w")
        
        # Create frame for listbox with scrollbars
        files_frame = ttk.Frame(f_frame)
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add horizontal and vertical scrollbars
        h_scrollbar = ttk.Scrollbar(files_frame, orient="horizontal")
        v_scrollbar = ttk.Scrollbar(files_frame, orient="vertical")
        
        # Create listbox with horizontal scrolling enabled
        self.files_listbox = tk.Listbox(files_frame, height=6, 
                                      xscrollcommand=h_scrollbar.set,
                                      yscrollcommand=v_scrollbar.set)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.files_listbox.xview)
        v_scrollbar.config(command=self.files_listbox.yview)
        
        # Place scrollbars and listbox using grid
        self.files_listbox.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        files_frame.rowconfigure(0, weight=1)
        files_frame.columnconfigure(0, weight=1)
        
        # Double click to open file
        self.files_listbox.bind('<Double-1>', self.open_selected_file)
        
        # Development mode options
        ttk.Label(options_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Add help tooltip to Refined Model
        refined_frame = ttk.Frame(mode_frame)
        refined_frame.pack(anchor="w", fill=tk.X)
        
        ttk.Radiobutton(refined_frame, text="Refined Model", 
                        variable=self.development_mode, value="refined_model").pack(side=tk.LEFT)
        
        info_button = ttk.Button(refined_frame, text="?", width=2,
                                command=lambda: messagebox.showinfo("Refined Model", 
                                                                  "Refined models are enhanced versions optimized for production. These models undergo additional validation and quality control steps to ensure they meet specific operational requirements."))
        info_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(mode_frame, text="Versioned Model", 
                        variable=self.development_mode, value="versioned_model").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Testing Only", 
                        variable=self.development_mode, value="testing_only").pack(anchor="w")
        
        # Time limit
        ttk.Label(options_frame, text="Time Limit:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        time_frame = ttk.Frame(options_frame)
        time_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Entry(time_frame, textvariable=self.time_limit_hours, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text=" hours").pack(side=tk.LEFT)
        ttk.Entry(time_frame, textvariable=self.time_limit_minutes, width=5).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(time_frame, text=" minutes").pack(side=tk.LEFT)
        
        # Auto-continue checkbox
        ttk.Checkbutton(options_frame, text="Auto-continue after time limit", 
                        variable=self.auto_continue).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Auto-save interval
        ttk.Label(options_frame, text="Auto-save every:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        save_frame = ttk.Frame(options_frame)
        save_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Entry(save_frame, textvariable=self.auto_save_interval, width=5).pack(side=tk.LEFT)
        ttk.Label(save_frame, text=" minutes").pack(side=tk.LEFT)
        
        # Version selection
        ttk.Label(options_frame, text="Model Version:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        self.version_frame = ttk.Frame(options_frame)
        self.version_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        versions = self.get_available_versions()
        self.version_dropdown = ttk.Combobox(self.version_frame, textvariable=self.selected_version, 
                                            values=versions, width=5)
        self.version_dropdown.pack(side=tk.LEFT)
        
        # Version and model parts refresh button
        ttk.Button(self.version_frame, text="Refresh All", 
                  command=self.refresh_all_data, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # Model part selection - auto-populated based on AI Agent folder roles
        ttk.Label(options_frame, text="Model Part:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        
        part_frame = ttk.Frame(options_frame)
        part_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Get model parts based on AI Agent folder roles
        model_parts = self.get_model_parts_from_agents()
        self.part_dropdown = ttk.Combobox(part_frame, textvariable=self.selected_model_part,
                                         values=model_parts, width=25)
        self.part_dropdown.pack(side=tk.LEFT)
        
        # Add event binding for when a model part is selected
        self.part_dropdown.bind('<<ComboboxSelected>>', self.on_model_part_select)
        
        # Save settings button
        ttk.Button(options_frame, text="Save Settings", 
                  command=self.save_settings).grid(row=6, column=1, sticky="e", padx=5, pady=10)
        
        # MIDDLE SECTION - Create middle section for message and actions
        middle_section = ttk.Frame(scrollable_frame)
        middle_section.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure columns with weights for proportional sizing
        middle_section.columnconfigure(0, weight=2)  # Message section (wider)
        middle_section.columnconfigure(1, weight=3)  # Action section (even wider)
        
        # Message section with instruction field (LEFT side of middle section)
        message_frame = ttk.LabelFrame(middle_section, text="Message & Instructions", padding=10)
        message_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ttk.Label(message_frame, text="Enter message or instructions:").pack(anchor="w", padx=5, pady=(5, 2))
        
        # Message text area
        self.message_text = tk.Text(message_frame, height=5, width=50, wrap="word")
        self.message_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Set initial text from variable
        if self.message_field.get():
            self.message_text.insert("1.0", self.message_field.get())
        
        # Button frame
        button_frame = ttk.Frame(message_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Send Message", 
                  command=self.send_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", 
                  command=lambda: self.message_text.delete("1.0", "end")).pack(side=tk.LEFT)
        
        # Action buttons frame (RIGHT side of middle section)
        action_frame = ttk.LabelFrame(middle_section, text="Actions", padding=10)
        action_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Grid of buttons for actions
        actions = [
            ("Start New Session", self.start_new_session),
            ("Resume Session", self.resume_session),
            ("Open in Blender", self.open_in_blender),
            ("Run Simulation", self.run_simulation),
            ("View Logs", self.view_logs),
            ("Show To-Do List", self.show_todo_list)
        ]
        
        # Create grid layout for action buttons
        for i, (text, command) in enumerate(actions):
            row = i // 3
            col = i % 3
            ttk.Button(action_frame, text=text, 
                      command=command).grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid columns to have equal width
        for i in range(3):
            action_frame.columnconfigure(i, weight=1)
            
        # Add AI Workflow buttons section
        ai_workflow_section = ttk.LabelFrame(scrollable_frame, text="AI Workflow Control", padding=10)
        ai_workflow_section.pack(fill=tk.X, pady=10)
        
        # Create AI Workflow buttons frame
        ai_workflow_frame = ttk.Frame(ai_workflow_section)
        ai_workflow_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add workflow status indicator
        self.workflow_status = tk.StringVar(value="Status: Not Running")
        
        ttk.Label(ai_workflow_frame, text="Control:").pack(side=tk.LEFT, padx=(0, 10))
        self.start_button = ttk.Button(ai_workflow_frame, text="Start", 
                                      command=self.start_ai_workflow,
                                      style='Primary.TButton')
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(ai_workflow_frame, text="Pause", 
                                      command=self.pause_ai_workflow,
                                      style='Secondary.TButton', state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.quit_button = ttk.Button(ai_workflow_frame, text="Quit", 
                                    command=self.quit_ai_workflow,
                                    style='Secondary.TButton', state=tk.DISABLED)
        self.quit_button.pack(side=tk.LEFT, padx=5)
        
        # Status indicator and agent count
        ttk.Label(ai_workflow_frame, textvariable=self.workflow_status).pack(side=tk.LEFT, padx=(20, 0))
        
        # Add agent statistics frame
        agent_stats_frame = ttk.Frame(ai_workflow_section)
        agent_stats_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Agent count indicators
        self.active_agents = tk.StringVar(value="0 active")
        self.paused_agents = tk.StringVar(value="0 paused")
        self.total_agents = tk.StringVar(value="0 total")
        
        ttk.Label(agent_stats_frame, text="Agents:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(agent_stats_frame, textvariable=self.active_agents).pack(side=tk.LEFT, padx=5)
        ttk.Label(agent_stats_frame, textvariable=self.paused_agents).pack(side=tk.LEFT, padx=5)
        ttk.Label(agent_stats_frame, textvariable=self.total_agents).pack(side=tk.LEFT, padx=5)
            
        # BOTTOM SECTION - Status section at the bottom (not top)
        status_section = ttk.LabelFrame(scrollable_frame, text="System Status", padding=10)
        status_section.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        
        # Create status grid with 2 columns
        status_grid = ttk.Frame(status_section)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Current status
        ttk.Label(status_grid, text="Current State:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=2)
        ttk.Label(status_grid, textvariable=self.current_status).grid(row=0, column=1, sticky="w", pady=2)
        
        # AI Agent Status
        ttk.Label(status_grid, text="AI Agents:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=2)
        ttk.Label(status_grid, text="5 agents ready").grid(row=1, column=1, sticky="w", pady=2)
        
        # Current task
        ttk.Label(status_grid, text="Current Task:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=2)
        ttk.Label(status_grid, text="None").grid(row=2, column=1, sticky="w", pady=2)
        
        # Current time
        ttk.Label(status_grid, text="Current Time:").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=2)
        self.time_display = ttk.Label(status_grid, text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.time_display.grid(row=3, column=1, sticky="w", pady=2)
        
        # Schedule time updates
        self.update_time()

    def setup_hardware_tab(self):
        """Set up the hardware monitoring tab - REPLACED with system_monitor_integration.py"""
        # This function is now replaced by the system_monitor_integration module
        pass
        
        # Create system info section
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Get system info
        system_info = self.hardware_monitor.get_system_summary()
        
        # Display system info
        ttk.Label(info_frame, text=f"Platform: {system_info.get('platform', 'Unknown')}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Processor: {system_info.get('processor', 'Unknown')}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Memory: {system_info.get('total_memory_gb', 'Unknown')} GB").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Disk: {system_info.get('total_disk_gb', 'Unknown')} GB").pack(anchor=tk.W, pady=2)
        
        # Create resource display
        resource_frame = ttk.LabelFrame(main_frame, text="Current Usage", padding="10")
        resource_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # CPU usage - with Task Manager style display
        cpu_frame = ttk.Frame(resource_frame)
        cpu_frame.pack(fill=tk.X, pady=5)
        
        self.cpu_label = ttk.Label(cpu_frame, text="CPU: 0%", width=30, anchor="w")
        self.cpu_label.pack(side=tk.LEFT)
        
        # Add Task Manager-like usage level indicator
        self.cpu_level = ttk.Label(cpu_frame, text="Normal", foreground="green")
        self.cpu_level.pack(side=tk.RIGHT)
        
        self.cpu_progress = ttk.Progressbar(resource_frame, length=400, mode='determinate')
        self.cpu_progress.pack(fill=tk.X, pady=(0, 10))
        
        # Memory usage
        self.memory_label = ttk.Label(resource_frame, text="Memory: 0%")
        self.memory_label.pack(anchor=tk.W, pady=5)
        
        self.memory_progress = ttk.Progressbar(resource_frame, length=400, mode='determinate')
        self.memory_progress.pack(fill=tk.X, pady=(0, 10))
        
        # Disk usage
        self.disk_label = ttk.Label(resource_frame, text="Disk: 0%")
        self.disk_label.pack(anchor=tk.W, pady=5)
        
        self.disk_progress = ttk.Progressbar(resource_frame, length=400, mode='determinate')
        self.disk_progress.pack(fill=tk.X, pady=(0, 10))
        
        # Refresh button
        ttk.Button(main_frame, text="Refresh", 
                  command=self.update_resource_display).pack(pady=(0, 10))
        
        # Start monitoring
        self.update_resource_display()

    def setup_tasks_tab(self):
        """Set up the task management tab"""
        # Create main frame
        main_frame = ttk.Frame(self.tasks_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Task Manager", 
                 style='Title.TLabel').pack(pady=(0, 20))
        
        # Task list section
        task_frame = ttk.LabelFrame(main_frame, text="Current Tasks", padding="10")
        task_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for tasks
        self.task_tree = ttk.Treeview(task_frame, columns=('Status', 'Priority', 'Created'), 
                                     show='tree headings')
        self.task_tree.heading('#0', text='Task')
        self.task_tree.heading('Status', text='Status')
        self.task_tree.heading('Priority', text='Priority')
        self.task_tree.heading('Created', text='Created')
        
        # Configure column widths
        self.task_tree.column('#0', width=300)
        self.task_tree.column('Status', width=100)
        self.task_tree.column('Priority', width=100)
        self.task_tree.column('Created', width=150)
        
        # Add scrollbar
        task_scrollbar = ttk.Scrollbar(task_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.task_tree.pack(side="left", fill="both", expand=True)
        task_scrollbar.pack(side="right", fill="y")
        
        # Task controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Add Task", 
                  command=self.add_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Mark Complete", 
                  command=self.complete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Remove Task", 
                  command=self.remove_task).pack(side=tk.LEFT, padx=5)
        
        # Scheduled tasks section
        schedule_frame = ttk.LabelFrame(main_frame, text="Scheduled Tasks", padding="10")
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for scheduled tasks
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=('Time', 'Type', 'Status'), 
                                         show='tree headings')
        self.schedule_tree.heading('#0', text='Description')
        self.schedule_tree.heading('Time', text='Scheduled Time')
        self.schedule_tree.heading('Type', text='Type')
        self.schedule_tree.heading('Status', text='Status')
        
        # Configure column widths
        self.schedule_tree.column('#0', width=300)
        self.schedule_tree.column('Time', width=150)
        self.schedule_tree.column('Type', width=100)
        self.schedule_tree.column('Status', width=100)
        
        # Add scrollbar
        schedule_scrollbar = ttk.Scrollbar(schedule_frame, orient="vertical", command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.schedule_tree.pack(side="left", fill="both", expand=True)
        schedule_scrollbar.pack(side="right", fill="y")
        
        # Schedule controls
        ttk.Button(main_frame, text="Refresh Tasks", 
                  command=self.refresh_tasks).pack(pady=(10, 0))
        
        # Load initial tasks
        self.refresh_tasks()

    def setup_help_tab(self):
        """Set up the help system tab"""
        # Create main frame
        main_frame = ttk.Frame(self.help_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Help & Documentation", 
                 style='Title.TLabel').pack(pady=(0, 20))
        
        # Split view with topics and content
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Topics frame on left
        topics_frame = ttk.LabelFrame(paned, text="Topics")
        
        # Content frame on right
        content_frame = ttk.LabelFrame(paned, text="Content")
        
        # Add frames to paned window
        paned.add(topics_frame, weight=1)
        paned.add(content_frame, weight=3)
        
        # Topics listbox
        self.topics_listbox = tk.Listbox(topics_frame)
        self.topics_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Content text widget
        self.help_content = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD)
        self.help_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Populate topics
        help_topics = [
            "Getting Started",
            "Main Controls",
            "Hardware Monitor",
            "Task Management",
            "Model Versions",
            "Claude Parallel Integration",
            "Simulation",
            "Troubleshooting",
            "FAQ"
        ]
        
        for topic in help_topics:
            self.topics_listbox.insert(tk.END, topic)
        
        # Bind selection event
        self.topics_listbox.bind('<<ListboxSelect>>', self.on_topic_select)
        
        # Select first topic
        self.topics_listbox.select_set(0)
        self.on_topic_select(None)

    def update_time(self):
        """Update the time display in the status section"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if hasattr(self, 'time_display'):
            self.time_display.config(text=current_time)
        # Schedule next update
        self.root.after(1000, self.update_time)
    
    def update_status_section(self):
        """Update the status section with current information"""
        # Update agent and task status info
        # This can be expanded later to show more detailed information
        self.update_time()

    def load_initial_config(self):
        """Load the configuration from file, or create default if not present"""
        config_path = os.path.join(os.path.dirname(__file__), "agent_mode_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Return default configuration
        return {
            "development_mode": "refined_model",
            "time_limit_hours": 1,
            "time_limit_minutes": 0,
            "auto_save_interval": 5,
            "auto_continue": True,
            "selected_version": "1",
            "refined_models": []  # List of refined model versions
        }
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            # Get message text
            message_text = self.message_text.get("1.0", tk.END).strip()
            
            # Update config with current values
            self.config["development_mode"] = self.development_mode.get()
            self.config["time_limit_hours"] = int(self.time_limit_hours.get())
            self.config["time_limit_minutes"] = int(self.time_limit_minutes.get())
            self.config["auto_save_interval"] = int(self.auto_save_interval.get())
            self.config["auto_continue"] = self.auto_continue.get()
            self.config["selected_version"] = self.selected_version.get()
            self.config["selected_model_part"] = self.selected_model_part.get()
            self.config["message"] = message_text
            
            # Save to file
            config_path = os.path.join(os.path.dirname(__file__), "agent_mode_config.json")
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
                
            messagebox.showinfo("Success", "Settings saved successfully.")
            self.current_status.set("Settings saved")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            self.current_status.set(f"Error: {str(e)}")
            return False

    def get_available_versions(self):
        """Get list of available model versions by scanning directories"""
        versions = []
        
        try:
            # Check for version files in various locations
            patterns = [
                "micro_robot_composite_part_v*.json",
                "model_versions/v*/micro_robot_composite_part_v*.json",
                "AI_Agent_1/micro_robot_composite_part_v*.json"
            ]
            
            for pattern in patterns:
                full_pattern = os.path.join(parent_dir, pattern)
                for file in glob.glob(full_pattern):
                    # Extract version number from filename
                    match = re.search(r'_v(\d+)\.', file)
                    if match:
                        versions.append(match.group(1))
            
            # Sort versions numerically
            versions = sorted(list(set(versions)), key=int)
            
            # If no versions found, provide defaults
            if not versions:
                versions = ["1", "2", "3"]
                
            return versions
            
        except Exception as e:
            print(f"Error getting available versions: {str(e)}")
            return ["1", "2", "3"]  # Default if error

    def update_version_list(self):
        """Update the version list in the UI"""
        # Clear current list
        self.version_listbox.delete(0, tk.END)
        
        # Get available versions
        versions = self.get_available_versions()
        
        # Update dropdown
        self.version_dropdown.config(values=versions)
        
        # Add to listbox
        for version in versions:
            status = self.check_model_status(version)
            self.version_listbox.insert(tk.END, f"Version {version}: {status}")
        
        # Update selected version if needed
        if not self.selected_version.get() in versions and versions:
            self.selected_version.set(versions[0])
    
    def refresh_all_data(self):
        """Refresh all data elements - versions and model parts"""
        try:
            # Update version list
            self.update_version_list()
            
            # Update model parts list
            self.update_model_parts_list()
            
            # Update status message
            self.current_status.set("Version list and model parts refreshed")
        except Exception as e:
            print(f"Error refreshing data: {str(e)}")
            self.current_status.set("Error refreshing data")
            
    def get_model_parts_from_agents_fast(self):
        """Get model parts based on AI Agent folder roles (faster version for initialization)"""
        model_parts = ["Complete Assembly"]  # Default option
        
        try:
            # Check for AI Agent folders - Use shorter names for dropdown display
            agent_roles = {
                "AI_Agent_1": "Micro-Robot",
                "AI_Agent_2": "Torso",
                "AI_Agent_3": "Head",
                "AI_Agent_4": "Arms",
                "AI_Agent_5": "Hands"
            }
            
            # Make shorter entries and store the component mapping for later use
            self.agent_components = {
                "AI_Agent_1": ["Core", "Actuators", "Sensors", "Power"],
                "AI_Agent_2": ["Chest", "Back", "Abdomen", "Waist"],
                "AI_Agent_3": ["Neck", "Skull", "Face", "Jaw"],
                "AI_Agent_4": ["Shoulders", "Upper Arms", "Elbows", "Forearms"],
                "AI_Agent_5": ["Wrists", "Palms", "Fingers", "Thumbs"]
            }
            
            # Store the full component details for display
            self.component_details = {
                "Micro-Robot": {
                    "Core": "Central processing and structural foundation",
                    "Actuators": "Motion control and mechanical drivers",
                    "Sensors": "Environmental and positional detection",
                    "Power": "Energy storage and distribution system"
                },
                "Torso": {
                    "Chest": "Upper torso structural frame",
                    "Back": "Posterior support and attachment points",
                    "Abdomen": "Central body flexible connection",
                    "Waist": "Lower torso articulation point"
                },
                "Head": {
                    "Neck": "Head support and rotation mechanism",
                    "Skull": "Protective housing for control systems",
                    "Face": "Sensory and communication interface",
                    "Jaw": "Articulated lower facial structure"
                },
                "Arms": {
                    "Shoulders": "Upper limb connection points",
                    "Upper Arms": "Main arm segments",
                    "Elbows": "Mid-arm articulation joints",
                    "Forearms": "Lower arm segments"
                },
                "Hands": {
                    "Wrists": "Hand attachment and rotation point",
                    "Palms": "Central hand structure",
                    "Fingers": "Articulated grasping digits",
                    "Thumbs": "Opposable manipulation digits"
                }
            }
            
            # Store a mapping of parts to their agent folders
            self.part_to_agent = {}
            
            # Add only main categories to the dropdown
            for agent_folder, role in agent_roles.items():
                if os.path.exists(os.path.join(parent_dir, agent_folder)):
                    model_parts.append(role)
                    self.part_to_agent[role] = agent_folder
            
            return model_parts
            
        except Exception as e:
            print(f"Error getting model parts (fast): {str(e)}")
            return ["Complete Assembly", "Micro-Robot", "Torso", "Head", "Arms", "Hands"]
            
    def get_model_parts_from_agents(self):
        """Get model parts based on AI Agent folder roles"""
        # Use the same implementation as the fast version for consistency
        return self.get_model_parts_from_agents_fast()
            
    def update_model_parts_list(self):
        """Update the model parts dropdown list"""
        # Get model parts
        model_parts = self.get_model_parts_from_agents()
        
        # Update dropdown
        self.part_dropdown.config(values=model_parts)
        
        # Keep current selection if possible, otherwise select first item
        if not self.selected_model_part.get() in model_parts and model_parts:
            self.selected_model_part.set(model_parts[0])
            
        self.current_status.set("Model parts refreshed")

    def check_model_status(self, version):
        """Check the status of a model version"""
        try:
            # Check various status indicators
            status_files = [
                f"requirements_met_v{version}.flag",
                f"simulation_complete_v{version}.flag",
                f"AI_Agent_1/version_v{version}_*.flag",
            ]
            
            for status_file in status_files:
                full_pattern = os.path.join(parent_dir, status_file)
                if glob.glob(full_pattern):
                    return "Complete"
            
            # Check if work in progress
            progress_files = [
                f"micro_robot_composite_part_v{version}.blend",
                f"AI_Agent_1/task_{version}_*.blend"
            ]
            
            for progress_file in progress_files:
                full_pattern = os.path.join(parent_dir, progress_file)
                if glob.glob(full_pattern):
                    return "Not Finalized"
                    
            return "Not Created"
        except Exception as e:
            print(f"Error checking model status: {str(e)}")
            return "Unknown"

    def on_version_select(self, event):
        """Handle version selection and update related files"""
        # Clear the files listbox
        self.files_listbox.delete(0, tk.END)
        
        # Get selected version
        selection = self.version_listbox.curselection()
        if not selection:
            return
            
        selected_text = self.version_listbox.get(selection[0])
        version = selected_text.split()[1].rstrip(":")
        
        # Update the version dropdown
        self.selected_version.set(version)
        
        # Find related files for this version
        related_files = self.find_related_files(version)
        
        # Add files to the listbox
        for file in related_files:
            self.files_listbox.insert(tk.END, file)
            
    def on_model_part_select(self, event):
        """Handle model part selection from dropdown"""
        try:
            selected_part = self.selected_model_part.get()
            
            if selected_part == "Complete Assembly":
                # For complete assembly, show all available parts
                self.update_related_files_with_message("Complete Assembly includes all component parts")
                return
                
            # Update the related files list with component parts
            if hasattr(self, 'component_details') and selected_part in self.component_details:
                # Clear the current files list
                self.files_listbox.delete(0, tk.END)
                
                # Add header for component parts
                self.files_listbox.insert(tk.END, f"--- {selected_part} Components ---")
                
                # Add each component with its description
                for component, description in self.component_details[selected_part].items():
                    self.files_listbox.insert(tk.END, f"{component}")
                    self.files_listbox.insert(tk.END, f"  • {description}")
                    
                # Add a spacer
                self.files_listbox.insert(tk.END, "")
                
                # Find and add related files for this part
                agent_folder = self.part_to_agent.get(selected_part)
                if agent_folder:
                    self.files_listbox.insert(tk.END, f"--- Related Files ---")
                    
                    # Look for files related to this part
                    related_files = self.find_files_for_model_part(selected_part, agent_folder)
                    
                    if related_files:
                        for file in related_files:
                            self.files_listbox.insert(tk.END, os.path.basename(file))
                    else:
                        self.files_listbox.insert(tk.END, "No related files found")
                
                self.current_status.set(f"Component parts for {selected_part} displayed")
            else:
                self.update_related_files_with_message(f"No component details found for {selected_part}")
                
        except Exception as e:
            print(f"Error handling model part selection: {str(e)}")
            self.current_status.set("Error displaying component parts")
            
    def find_files_for_model_part(self, part_name, agent_folder):
        """Find files related to a specific model part"""
        try:
            files = []
            
            # Check agent output directory
            agent_output_dir = os.path.join(parent_dir, agent_folder, "agent_outputs")
            if os.path.exists(agent_output_dir):
                # Look for files with the model part name in them
                base_part_name = part_name.lower().replace("-", "_").replace(" ", "_")
                
                # Check for common file extensions
                for ext in ['.blend', '.fbx', '.stl', '.obj', '.glb', '.json', '.png', '.jpg']:
                    pattern = os.path.join(agent_output_dir, f"*{base_part_name}*{ext}")
                    files.extend(glob.glob(pattern))
                    
                    # Also check with underscores in different positions
                    pattern = os.path.join(agent_output_dir, f"*_{base_part_name}*{ext}")
                    files.extend(glob.glob(pattern))
            
            # Check general output directories
            general_output_dirs = [
                os.path.join(parent_dir, "outputs"),
                os.path.join(parent_dir, "agent_outputs"),
                os.path.join(parent_dir, "model_versions")
            ]
            
            for output_dir in general_output_dirs:
                if os.path.exists(output_dir):
                    base_part_name = part_name.lower().replace("-", "_").replace(" ", "_")
                    
                    for ext in ['.blend', '.fbx', '.stl', '.obj', '.glb', '.json', '.png', '.jpg']:
                        pattern = os.path.join(output_dir, f"*{base_part_name}*{ext}")
                        files.extend(glob.glob(pattern))
            
            return sorted(set(files))  # Remove duplicates
            
        except Exception as e:
            print(f"Error finding files for model part: {str(e)}")
            return []
            
    def update_related_files_with_message(self, message):
        """Update related files list with a message"""
        self.files_listbox.delete(0, tk.END)
        self.files_listbox.insert(tk.END, message)

    def find_related_files(self, version):
        """Find files related to a specific model version"""
        related_files = []
        
        try:
            # File patterns to search for
            patterns = [
                f"*v{version}*.blend",
                f"*v{version}*.json",
                f"*v{version}*.fbx",
                f"*v{version}*.obj",
                f"*v{version}*.stl",
                f"*v{version}*.gltf",
                f"*v{version}*.png",
                f"*_v{version}_*.py"
            ]
            
            # Directories to search
            dirs = [
                parent_dir,
                os.path.join(parent_dir, "AI_Agent_1"),
                os.path.join(parent_dir, "model_versions"),
                os.path.join(parent_dir, "agent_outputs")
            ]
            
            # Find matching files
            for directory in dirs:
                if os.path.exists(directory):
                    for pattern in patterns:
                        full_pattern = os.path.join(directory, pattern)
                        for file in glob.glob(full_pattern):
                            related_files.append(os.path.basename(file))
            
            # Remove duplicates and sort
            related_files = sorted(list(set(related_files)))
            
            return related_files
            
        except Exception as e:
            print(f"Error finding related files: {str(e)}")
            return []

    def open_selected_file(self, event):
        """Open the selected file from the related files list"""
        selection = self.files_listbox.curselection()
        if not selection:
            return
            
        filename = self.files_listbox.get(selection[0])
        
        # Find the file
        try:
            # Directories to search
            dirs = [
                parent_dir,
                os.path.join(parent_dir, "AI_Agent_1"),
                os.path.join(parent_dir, "model_versions"),
                os.path.join(parent_dir, "agent_outputs")
            ]
            
            for directory in dirs:
                full_path = os.path.join(directory, filename)
                if os.path.exists(full_path):
                    # Open the file based on its extension
                    if filename.endswith(".blend"):
                        self.open_blender_file(full_path)
                    elif filename.endswith((".png", ".jpg", ".jpeg")):
                        self.open_image_file(full_path)
                    elif filename.endswith((".json", ".py", ".txt", ".md")):
                        self.open_text_file(full_path)
                    else:
                        # Use system default application
                        if platform.system() == "Windows":
                            os.startfile(full_path)
                        else:
                            subprocess.Popen(["xdg-open", full_path])
                    
                    self.current_status.set(f"Opened {filename}")
                    return
                    
            messagebox.showinfo("File Not Found", f"Could not locate {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening file: {str(e)}")

    def open_blender_file(self, filepath):
        """Open a file in Blender"""
        try:
            if platform.system() == "Windows":
                # Try to find Blender in common locations
                blender_paths = [
                    r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
                    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
                    r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
                ]
                
                blender_exe = None
                for path in blender_paths:
                    if os.path.exists(path):
                        blender_exe = path
                        break
                        
                if blender_exe:
                    subprocess.Popen([blender_exe, filepath])
                else:
                    # Try to use system association
                    os.startfile(filepath)
            else:
                # On Linux/Mac, try to use blender command
                subprocess.Popen(["blender", filepath])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open in Blender: {str(e)}")

    def open_image_file(self, filepath):
        """Open an image file"""
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            else:
                subprocess.Popen(["xdg-open", filepath])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")

    def open_text_file(self, filepath):
        """Open a text file in a viewer window"""
        try:
            # Create a new window
            text_window = tk.Toplevel(self.root)
            text_window.title(f"File Viewer - {os.path.basename(filepath)}")
            text_window.geometry("800x600")
            
            # Text widget with scrollbar
            text_frame = ttk.Frame(text_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            # Load the file content
            with open(filepath, 'r') as f:
                content = f.read()
                text_widget.insert(tk.END, content)
            
            # Make read-only
            text_widget.config(state=tk.DISABLED)
            
            # Close button
            ttk.Button(text_window, text="Close", 
                      command=text_window.destroy).pack(pady=10)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open text file: {str(e)}")

    def update_resource_display(self):
        """Update resource usage display"""
        try:
            usage = self.hardware_monitor.get_hardware_info()
            
            # Update CPU - apply slight visual correction to match Task Manager better
            cpu_percent = usage.get('cpu_percent', 0)
            # Display value is formatted to match Task Manager's representation
            self.cpu_label.config(text=f"CPU: {cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            # Update CPU level indicator like Task Manager
            if cpu_percent < 30:
                self.cpu_level.config(text="Very Low", foreground="green")
            elif cpu_percent < 60:
                self.cpu_level.config(text="Normal", foreground="green")
            elif cpu_percent < 80:
                self.cpu_level.config(text="Medium", foreground="orange")
            elif cpu_percent < 90:
                self.cpu_level.config(text="High", foreground="orange")
            else:
                self.cpu_level.config(text="Very High", foreground="red")
            
            # Update Memory - use raw memory values for more accuracy
            memory_percent = usage.get('memory_percent', 0)
            memory_used_gb = usage.get('memory_total', 0) / (1024**3) - usage.get('memory_available', 0) / (1024**3)
            memory_total_gb = usage.get('memory_total', 0) / (1024**3)
            if memory_total_gb > 0:
                self.memory_label.config(text=f"Memory: {memory_percent:.1f}% ({memory_used_gb:.1f}/{memory_total_gb:.1f} GB)")
            else:
                self.memory_label.config(text=f"Memory: {memory_percent:.1f}%")
            self.memory_progress['value'] = memory_percent
            
            # Update Disk
            disk_percent = usage.get('disk_percent', 0)
            disk_used_gb = (usage.get('disk_total', 0) - usage.get('disk_free', 0)) / (1024**3)
            disk_total_gb = usage.get('disk_total', 0) / (1024**3)
            if disk_total_gb > 0:
                self.disk_label.config(text=f"Disk: {disk_percent:.1f}% ({disk_used_gb:.1f}/{disk_total_gb:.1f} GB)")
            else:
                self.disk_label.config(text=f"Disk: {disk_percent:.1f}%")
            self.disk_progress['value'] = disk_percent
            
        except Exception as e:
            print(f"Error updating resource display: {str(e)}")
        
        # Schedule next update
        self.root.after(5000, self.update_resource_display)  # Update every 5 seconds

    def refresh_tasks(self):
        """Refresh both task lists"""
        # Clear task tree
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Clear schedule tree
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # Load tasks from task manager
        tasks = self.task_manager.get_all_tasks()
        for task in tasks:
            self.task_tree.insert('', 'end', 
                                 text=task.get('description', 'Unnamed task'),
                                 values=(task.get('status', 'pending'),
                                        task.get('priority', 'medium'),
                                        task.get('created_at', '')))
        
        # Load scheduled tasks
        scheduled_tasks = self.get_scheduled_tasks()
        for task in scheduled_tasks:
            self.schedule_tree.insert('', 'end',
                                     text=task.get('description', 'Unnamed task'),
                                     values=(task.get('time', 'Unknown'),
                                            task.get('type', 'Unknown'),
                                            task.get('status', 'pending')))
        
        self.current_status.set("Tasks refreshed")

    def get_scheduled_tasks(self):
        """Get scheduled tasks from files"""
        scheduled_tasks = []
        
        try:
            # Check for scheduled tasks in different locations
            schedule_files = [
                os.path.join(parent_dir, "scheduled_tasks.json"),
                os.path.join(parent_dir, "model_testing_schedule.json"),
                os.path.join(parent_dir, "project_tasks.json")
            ]
            
            for file_path in schedule_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            scheduled_tasks.extend(data)
                        elif isinstance(data, dict) and 'tasks' in data:
                            scheduled_tasks.extend(data['tasks'])
            
            return scheduled_tasks
            
        except Exception as e:
            print(f"Error getting scheduled tasks: {str(e)}")
            return []

    def add_task(self):
        """Add a new task"""
        # Create a dialog for task entry
        task_dialog = tk.Toplevel(self.root)
        task_dialog.title("Add New Task")
        task_dialog.geometry("400x300")
        task_dialog.transient(self.root)
        task_dialog.grab_set()
        
        # Task description
        ttk.Label(task_dialog, text="Task Description:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        description = tk.Text(task_dialog, height=5, width=40)
        description.pack(padx=10, pady=(0, 10))
        
        # Priority selection
        ttk.Label(task_dialog, text="Priority:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        priority = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(task_dialog, textvariable=priority, 
                                     values=["low", "medium", "high"])
        priority_combo.pack(padx=10, pady=(0, 10))
        
        # Save button
        def save_task():
            desc = description.get("1.0", tk.END).strip()
            if not desc:
                messagebox.showwarning("Warning", "Task description cannot be empty")
                return
                
            # Create task
            task = {
                "description": desc,
                "priority": priority.get(),
                "status": "pending",
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Add to task manager
            self.task_manager.add_task(task)
            
            # Refresh display
            self.refresh_tasks()
            
            # Close dialog
            task_dialog.destroy()
            
            self.current_status.set("Task added")
        
        # Button frame
        button_frame = ttk.Frame(task_dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=task_dialog.destroy).pack(side=tk.LEFT, padx=5)

    def complete_task(self):
        """Mark the selected task as complete"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a task to mark as complete")
            return
            
        # Get the selected item
        item = selection[0]
        
        # Update in tree view
        self.task_tree.set(item, "Status", "completed")
        
        # Update in task manager
        # Note: In a real implementation, we would need to track task IDs
        
        self.current_status.set("Task marked as complete")

    def remove_task(self):
        """Remove the selected task"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a task to remove")
            return
            
        # Ask for confirmation
        if not messagebox.askyesno("Confirm", "Are you sure you want to remove this task?"):
            return
            
        # Get the selected item
        item = selection[0]
        
        # Remove from tree view
        self.task_tree.delete(item)
        
        # Would also remove from task manager in a full implementation
        
        self.current_status.set("Task removed")

    def on_topic_select(self, event):
        """Handle help topic selection"""
        # Clear content
        self.help_content.delete("1.0", tk.END)
        
        # Get selected topic
        selection = self.topics_listbox.curselection()
        if not selection:
            return
            
        topic = self.topics_listbox.get(selection[0])
        
        # Load content for this topic
        content = self.get_help_content(topic)
        
        # Display content
        self.help_content.insert(tk.END, content)
        self.help_content.config(state=tk.DISABLED)

    def get_help_content(self, topic):
        """Get help content for a specific topic"""
        # Basic help content
        help_content = {
            "Getting Started": """
# Getting Started with GlowingGoldenGlobe

Welcome to the GlowingGoldenGlobe Agent Control System!

## Quick Start

1. Set your desired time limit using the hours and minutes fields
2. Click "Start New Session" to begin a new model development session
3. Monitor progress in the Model Versions list
4. Use the action buttons to interact with your models

## Basic Workflow

1. **Starting a Session**: Configure time limits and click "Start New Session"
2. **Monitoring Progress**: Watch the version list for status updates
3. **Viewing Results**: Use "Open in Blender" or "View Logs" to see outputs
4. **Running Simulations**: Select a version and click "Run Simulation"

## Tips

- Use shorter time limits for testing
- Check the resource monitor to ensure optimal performance
- Review logs regularly to track progress
""",
            "Main Controls": """
# Main Controls

The Main Controls tab provides access to the core functionality of the GlowingGoldenGlobe system:

## Development Options

- **Mode Selection**: Choose between Refined Model, Versioned Model, or Testing Only
- **Time Limit**: Set hours and minutes for the development session
- **Auto-continue**: Automatically continue after the time limit is reached
- **Auto-save**: Set interval in minutes for automatic saving
- **Model Version**: Select which version to work with
- **Model Part**: Choose a specific component of the model

## Message & Instructions

Use this section to send messages or instructions to the AI agents. These messages can include:

- Special processing instructions
- Custom parameters
- Task descriptions
- Testing criteria

## Model Versions & Related Files

- **Version List**: Shows all available model versions with their status
- **Related Files**: Shows all files associated with the selected version
- Double-click on a file to open it

## Actions

- **Start New Session**: Begin a new development session
- **Resume Session**: Continue a previous session
- **Open in Blender**: Open the selected model in Blender
- **Run Simulation**: Execute a simulation of the selected model
- **View Logs**: View development and simulation logs
- **Show To-Do List**: Display the project to-do list
""",
            "Hardware Monitor": """
# Hardware Monitor

The Hardware Monitor tab provides real-time information about system resources:

## System Information

Displays basic information about your system:
- Platform (OS)
- Processor
- Memory
- Disk space

## Current Usage

Shows real-time monitoring of:
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage

Each resource is displayed with both a numerical percentage and a progress bar for visual reference.

## Why This Matters

Monitoring system resources helps ensure optimal performance during model development and simulation:

- High CPU usage may indicate complex calculations are in progress
- High memory usage could lead to slowdowns or crashes
- Disk space is important for storing model files and simulation data

## Refresh Rate

The display updates automatically every 5 seconds, but you can click the "Refresh" button to update immediately.
""",
            "Task Management": """
# Task Management

The Tasks & Schedule tab helps you organize and track development activities:

## Current Tasks

This section shows all active tasks with their:
- Description
- Status (pending, in-progress, completed)
- Priority (low, medium, high)
- Creation date

You can:
- Add new tasks
- Mark tasks as complete
- Remove tasks

## Scheduled Tasks

This section shows scheduled operations such as:
- Automated tests
- Regular simulations
- Model evaluations
- Backup operations

Each scheduled task includes:
- Description
- Scheduled time
- Task type
- Current status

## Task Organization

Tasks help organize development activities:
1. Break down complex operations into manageable steps
2. Track progress across multiple development sessions
3. Ensure important activities aren't forgotten
4. Prioritize work based on project needs
""",
            "Claude Parallel Integration": """
# Claude Parallel Integration

The Claude Parallel feature allows you to run multiple AI agent tasks simultaneously:

## What is Claude Parallel?

Claude Parallel is a system that:
- Manages concurrent execution of multiple AI agent tasks
- Optimizes resource allocation across different tasks
- Tracks task status and results
- Provides a unified interface for task management

## Key Features

- **Task Queue**: Add AI tasks to a queue for processing
- **Priority Management**: Assign different priorities to tasks
- **Resource Monitoring**: Prevents system overload
- **Parallel Execution**: Run compatible tasks simultaneously
- **Result Tracking**: View and analyze task results

## Usage Workflow

1. Start the Claude Parallel Manager from the tab
2. Add tasks to the queue
3. Monitor execution progress
4. View results as tasks complete

## Benefits

- Faster overall processing by utilizing idle resources
- More efficient agent utilization
- Better organization of complex workflows
- Reduced waiting time for model evaluations
""",
            "Model Versions": """
# Model Versions

The model versioning system helps track development progress:

## Version Numbering

- Versions are numbered sequentially (1, 2, 3, etc.)
- Higher numbers indicate newer versions
- Each version is a complete snapshot of the model at a specific development stage

## Version Status

Versions can have three statuses:
- **Not Created**: Initial state before creation
- **Not Finalized**: Active development
- **Complete**: Finished and validated

## Related Files

Each model version includes several related files:
- `.blend`: Blender 3D model files
- `.json`: Model configuration and metadata
- `.fbx/.obj/.stl`: Exported model formats
- `.png`: Rendered images
- `.py`: Custom scripts for this version

## Version Management

Good practices for model versioning:
1. Create new versions for significant changes
2. Include descriptive metadata with each version
3. Test all versions thoroughly
4. Keep track of version differences
5. Include a reason for each new version
""",
            "Simulation": """
# Simulation

The simulation system allows you to test models in simulated environments:

## Simulation Types

- **Physics Simulation**: Test physical properties and interactions
- **Agent Behavior**: Test AI agent control and decision making
- **Environmental Testing**: Test models in different environments
- **Load Testing**: Test models under different load conditions

## Running a Simulation

To run a simulation:
1. Select a model version
2. Click "Run Simulation" in the Main Controls tab
3. Configure simulation parameters if prompted
4. Wait for the simulation to complete
5. Review the results

## Simulation Results

Simulation results include:
- Performance metrics
- Error reports
- Visual renders
- Log files

## Advanced Simulations

For more complex simulations:
- Use the Claude Parallel system for multi-agent simulations
- Adjust simulation parameters for specific tests
- Enable enhanced physics for detailed physical interactions
- Use external tools like Blender for visual verification
""",
            "Troubleshooting": """
# Troubleshooting

Common issues and solutions:

## Application Startup Issues

**Problem**: GUI fails to start
**Solution**: Check Python environment and dependencies

**Problem**: Missing modules error
**Solution**: Install required packages using pip

## Model Loading Issues

**Problem**: Cannot find model files
**Solution**: Check file paths and ensure files exist

**Problem**: Model version doesn't appear
**Solution**: Refresh version list or check file naming

## Simulation Problems

**Problem**: Simulation fails to start
**Solution**: Check hardware resources and file permissions

**Problem**: Simulation crashes
**Solution**: Lower physics detail or check logs for errors

## Hardware Resource Issues

**Problem**: High CPU/memory usage
**Solution**: Close other applications or adjust resource settings

**Problem**: Disk space warning
**Solution**: Clean up temporary files or old model versions

## For Additional Help

1. Check log files in the project directory
2. Review the Help section thoroughly
3. Search for specific error messages
4. Try restarting the application
""",
            "FAQ": """
# Frequently Asked Questions

## General Questions

**Q: What is GlowingGoldenGlobe?**
A: It's an AI agent system for developing and testing 3D models with integrated tools for simulation and evaluation.

**Q: What hardware is recommended?**
A: A modern multi-core CPU, 16GB+ RAM, and a dedicated GPU for complex simulations.

## Model Development

**Q: How do I create a new model version?**
A: Start a new session and select a new version number. The system will create it automatically.

**Q: Can I export models to other formats?**
A: Yes, models can be exported to FBX, OBJ, STL, and GLTF formats.

## Claude Integration

**Q: What is Claude Parallel?**
A: It's a system for running multiple AI agent tasks simultaneously.

**Q: How many parallel tasks can I run?**
A: This depends on your hardware resources, but typically 3-5 tasks can run concurrently.

## Performance

**Q: Why is my simulation running slowly?**
A: This could be due to insufficient hardware resources, complex models, or too many concurrent tasks.

**Q: How can I improve performance?**
A: Close other applications, reduce simulation detail, or upgrade hardware components.
"""
        }
        
        # Return content for this topic or a default message
        return help_content.get(topic, f"Help content for '{topic}' coming soon...")

    def show_help(self):
        """Show help window or navigate to Help tab"""
        # Switch to help tab
        self.notebook.select(self.help_tab)

    def send_message(self):
        """Send the message entered in the message field"""
        # Get message text
        message = self.message_text.get("1.0", tk.END).strip()
        
        if not message:
            messagebox.showinfo("Empty Message", "Please enter a message to send")
            return
        
        # Store in variable
        self.message_field.set(message)
        
        # In a real implementation, this would send the message to the AI agent
        # For now, just show a confirmation and clear the field
        messagebox.showinfo("Message Sent", "Message sent to AI agent system")
        
        # Clear message field
        self.message_text.delete("1.0", tk.END)
        
        # Update status
        self.current_status.set("Message sent")

    def start_new_session(self):
        """Start a new development session"""
        try:
            # Validate inputs
            time_limit_hours = int(self.time_limit_hours.get())
            time_limit_minutes = int(self.time_limit_minutes.get())
            
            if time_limit_hours < 0 or time_limit_minutes < 0:
                messagebox.showerror("Invalid Input", "Time limit must be positive")
                return
                
            # Calculate total seconds
            total_seconds = time_limit_hours * 3600 + time_limit_minutes * 60
            
            # Get message if any
            message = self.message_field.get()
            
            # Save settings
            self.save_settings()
            
            # Run the agent (in a full implementation, this would start the AI agent)
            messagebox.showinfo("Session Started", 
                              f"Starting new development session with time limit: {time_limit_hours}h {time_limit_minutes}m")
            
            # Update status
            self.current_status.set("New session started")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for time limit")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {str(e)}")

    def resume_session(self):
        """Resume a previous session"""
        # Get available versions
        versions = self.get_available_versions()
        
        # Find versions in progress
        in_progress = []
        for version in versions:
            if self.check_model_status(version) == "Not Finalized":
                in_progress.append(version)
        
        if not in_progress:
            messagebox.showinfo("No Sessions", "No not-finalized sessions found to resume")
            return
        
        # If multiple, ask which one to resume
        version_to_resume = in_progress[0]
        if len(in_progress) > 1:
            # Create a dialog to select version
            dialog = tk.Toplevel(self.root)
            dialog.title("Resume Session")
            dialog.geometry("300x200")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Select version to resume:").pack(pady=(10, 5))
            
            # Create listbox
            version_list = tk.Listbox(dialog, height=len(in_progress))
            version_list.pack(fill=tk.X, padx=10, pady=5)
            
            # Populate listbox
            for version in in_progress:
                version_list.insert(tk.END, f"Version {version}")
            
            # Select first item
            version_list.selection_set(0)
            
            # Buttons
            def on_select():
                nonlocal version_to_resume
                selection = version_list.curselection()
                if selection:
                    # Extract version number
                    version_to_resume = in_progress[selection[0]]
                dialog.destroy()
                
                # Resume the session
                self._do_resume_session(version_to_resume)
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Resume", command=on_select).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Wait for dialog
            return
        
        # Resume the single session
        self._do_resume_session(version_to_resume)

    def _do_resume_session(self, version):
        """Actually resume the session for the given version"""
        # Update selected version
        self.selected_version.set(version)
        
        # In a real implementation, this would restart the AI agent
        messagebox.showinfo("Session Resumed", f"Resuming session for Version {version}")
        
        # Update status
        self.current_status.set(f"Resumed session for Version {version}")

    def run_simulation(self):
        """Run simulation for the current version"""
        # Get current version
        version = self.selected_version.get()
        
        # In a real implementation, this would start the simulation
        messagebox.showinfo("Simulation", f"Starting simulation for Version {version}")
        
        # Update status
        self.current_status.set(f"Running simulation for Version {version}")

    def open_in_blender(self):
        """Open the selected model version in Blender"""
        # Get current version
        version = self.selected_version.get()
        
        # Find Blender files for this version
        blend_files = []
        patterns = [
            f"*v{version}*.blend",
            f"*_{version}*.blend"
        ]
        
        # Directories to search
        dirs = [
            parent_dir,
            os.path.join(parent_dir, "AI_Agent_1"),
            os.path.join(parent_dir, "model_versions"),
            os.path.join(parent_dir, "agent_outputs")
        ]
        
        # Search for blend files
        for directory in dirs:
            if os.path.exists(directory):
                for pattern in patterns:
                    full_pattern = os.path.join(directory, pattern)
                    found_files = glob.glob(full_pattern)
                    blend_files.extend(found_files)
        
        # If no files found
        if not blend_files:
            messagebox.showinfo("No Blender Files", f"No Blender files found for version {version}")
            return
        
        # If multiple files found, ask which one to open
        blend_file = blend_files[0]
        if len(blend_files) > 1:
            # Create a dialog to select file
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Blender File")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Multiple Blender files found. Please select one:").pack(pady=(10, 5))
            
            # Create listbox
            file_list = tk.Listbox(dialog, height=10)
            file_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Populate listbox
            for file in blend_files:
                file_list.insert(tk.END, os.path.basename(file))
            
            # Select first item
            file_list.selection_set(0)
            
            # Buttons
            def on_select():
                nonlocal blend_file
                selection = file_list.curselection()
                if selection:
                    # Get selected index
                    index = selection[0]
                    blend_file = blend_files[index]
                dialog.destroy()
                
                # Open the file in Blender
                self.open_blender_file(blend_file)
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Open", command=on_select).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Return here - will continue after dialog closes
            return
        
        # Open the single file in Blender
        self.open_blender_file(blend_file)

    def view_logs(self):
        """View logs for the current version"""
        # Get current version
        version = self.selected_version.get()
        
        # Check for log files
        log_files = [
            os.path.join(parent_dir, "model_development_log.md"),
            os.path.join(parent_dir, "AI_Agent_1", "model_development_log.md"),
            os.path.join(parent_dir, f"simulation_log_v{version}.txt")
        ]
        
        # Find first available log file
        log_file = None
        for file in log_files:
            if os.path.exists(file):
                log_file = file
                break
        
        if not log_file:
            messagebox.showinfo("No Logs", "No log files found for this version")
            return
        
        # Open log file in viewer
        self.open_text_file(log_file)

    def show_todo_list(self):
        """Show the to-do list"""
        # Check for to-do file
        todo_files = [
            os.path.join(parent_dir, "To Do_Daily.txt"),
            os.path.join(parent_dir, "project_tasks.md")
        ]
        
        # Find first available to-do file
        todo_file = None
        for file in todo_files:
            if os.path.exists(file):
                todo_file = file
                break
        
        if not todo_file:
            messagebox.showinfo("No To-Do List", "No to-do list file found")
            return
        
        # Open to-do file in viewer
        self.open_text_file(todo_file)
    

    def schedule_updates(self):
        """Schedule periodic updates"""
        # Update version list every 30 seconds
        def update_versions():
            self.update_version_list()
            self.root.after(30000, update_versions)
        
        # Schedule first update
        self.root.after(30000, update_versions)
        
        # Update workflow status immediately if needed
        self._start_workflow_status_updates()
    
    def _start_workflow_status_updates(self):
        """Start periodic workflow status updates"""
        self._update_workflow_status()
        
    def _update_workflow_status(self):
        """Update the AI workflow status display"""
        try:
            # Get current state
            current_state = ai_workflow_status.get_workflow_state()
            
            # Update status text
            if current_state == ai_workflow_status.STATE_RUNNING:
                self.workflow_status.set("Status: Running")
                self.start_button.config(state=tk.DISABLED)
                self.pause_button.config(state=tk.NORMAL)
                self.quit_button.config(state=tk.NORMAL)
            elif current_state == ai_workflow_status.STATE_PAUSED:
                self.workflow_status.set("Status: Paused")
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.quit_button.config(state=tk.NORMAL)
            else:  # STATE_STOPPED
                self.workflow_status.set("Status: Not Running")
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.quit_button.config(state=tk.DISABLED)
            
            # Update agent counts
            agent_counts = ai_workflow_status.get_agent_count()
            self.active_agents.set(f"{agent_counts['active']} active")
            self.paused_agents.set(f"{agent_counts['paused']} paused")
            self.total_agents.set(f"{agent_counts['total']} total")
            
            # Detect running agents if needed
            if current_state == ai_workflow_status.STATE_RUNNING and agent_counts['active'] == 0:
                # Try to detect active agents that might not be registered
                active_agents = ai_workflow_status.detect_active_agents()
                if active_agents:
                    self.active_agents.set(f"{len(active_agents)} active (detected)")
                    self.total_agents.set(f"{len(active_agents) + agent_counts['paused'] + agent_counts['terminated']} total")
            
            # Get workflow statistics if available
            if current_state in [ai_workflow_status.STATE_RUNNING, ai_workflow_status.STATE_PAUSED]:
                stats = ai_workflow_status.get_workflow_stats()
                if 'elapsed_formatted' in stats:
                    # Add runtime to status display
                    current_status = self.workflow_status.get()
                    self.workflow_status.set(f"{current_status} - Runtime: {stats['elapsed_formatted']}")
        except Exception as e:
            print(f"Error updating workflow status: {str(e)}")
        finally:
            # Schedule next update if workflow is active
            if current_state in [ai_workflow_status.STATE_RUNNING, ai_workflow_status.STATE_PAUSED]:
                self.root.after(5000, self._update_workflow_status)  # Update every 5 seconds
            else:
                # Schedule a single update in 30 seconds to check for changes
                self.root.after(30000, self._update_workflow_status)
                
    def start_ai_workflow(self):
        """Start the AI workflow
        
        This function initializes and starts the AI Workflow system, enabling
        communication between multiple AI agents.
        """
        try:
            # Get current state
            current_state = ai_workflow_status.get_workflow_state()
            
            if current_state == ai_workflow_status.STATE_RUNNING:
                messagebox.showinfo("Already Running", "AI Workflow is already running.")
                return
                
            # Collect workflow parameters from UI
            workflow_params = {
                "development_mode": self.development_mode.get(),
                "model_version": self.selected_version.get(),
                "model_part": self.selected_model_part.get(),
                "time_limit_hours": int(self.time_limit_hours.get()),
                "time_limit_minutes": int(self.time_limit_minutes.get()),
                "auto_continue": self.auto_continue.get()
            }
            
            # Start the workflow
            success = ai_workflow_status.start_ai_workflow(workflow_params)
            
            if success:
                # Update UI
                self.workflow_status.set("Status: Running")
                self.start_button.config(state=tk.DISABLED)
                self.pause_button.config(state=tk.NORMAL)
                self.quit_button.config(state=tk.NORMAL)
                self.current_status.set("AI Workflow started")
                
                # Start periodic status updates
                self._start_workflow_status_updates()
                
                messagebox.showinfo("Success", "AI Workflow started successfully")
            else:
                messagebox.showerror("Error", "Failed to start AI Workflow")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error starting AI Workflow: {str(e)}")
            print(f"Error starting AI Workflow: {str(e)}")
            
    def pause_ai_workflow(self):
        """Pause the AI workflow
        
        This function pauses all active AI agents in the workflow system.
        Agents will detect the pause state and halt execution until resumed.
        """
        try:
            # Get current state
            current_state = ai_workflow_status.get_workflow_state()
            
            if current_state != ai_workflow_status.STATE_RUNNING:
                messagebox.showinfo("Not Running", "AI Workflow is not running, cannot pause.")
                return
                
            # Pause the workflow
            success = ai_workflow_status.pause_ai_workflow()
            
            if success:
                # Update UI
                self.workflow_status.set("Status: Paused")
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.quit_button.config(state=tk.NORMAL)
                self.current_status.set("AI Workflow paused")
                
                messagebox.showinfo("Success", "AI Workflow paused successfully")
            else:
                messagebox.showerror("Error", "Failed to pause AI Workflow")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error pausing AI Workflow: {str(e)}")
            print(f"Error pausing AI Workflow: {str(e)}")
            
    def quit_ai_workflow(self):
        """Stop/terminate the AI workflow
        
        This function stops all AI agents and terminates the workflow system.
        Agents will detect the termination state and exit gracefully.
        """
        try:
            # Get current state
            current_state = ai_workflow_status.get_workflow_state()
            
            if current_state == ai_workflow_status.STATE_STOPPED:
                messagebox.showinfo("Not Running", "AI Workflow is already stopped.")
                return
                
            # Confirm termination
            if not messagebox.askyesno("Confirm", "Are you sure you want to terminate all AI Workflow agents?\n\nThis will stop all running processes."):
                return
                
            # Stop the workflow
            success = ai_workflow_status.stop_ai_workflow()
            
            if success:
                # Update UI
                self.workflow_status.set("Status: Not Running")
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.quit_button.config(state=tk.DISABLED)
                self.active_agents.set("0 active")
                self.paused_agents.set("0 paused")
                self.total_agents.set("0 total")
                self.current_status.set("AI Workflow terminated")
                
                messagebox.showinfo("Success", "AI Workflow terminated successfully")
            else:
                messagebox.showerror("Error", "Failed to terminate AI Workflow")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error terminating AI Workflow: {str(e)}")
            print(f"Error terminating AI Workflow: {str(e)}")

def main():
    root = tk.Tk()
    app = GlowingGoldenGlobeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Log the error
        log_path = os.path.join(os.path.dirname(__file__), "gui_launcher_error.txt")
        with open(log_path, "a") as log:
            log.write(f"{datetime.datetime.now()}: {str(e)}\n")
        # Show error dialog
        import tkinter.messagebox as msgbox
        msgbox.showerror("Error", f"An error occurred: {str(e)}\nSee gui_launcher_error.txt for details.")
        raise