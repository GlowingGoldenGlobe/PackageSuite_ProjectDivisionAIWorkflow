#!/usr/bin/env python
"""
Claude Parallel GUI Integration for GlowingGoldenGlobe

This module integrates the Claude Parallel Execution system with the GlowingGoldenGlobe GUI,
providing a graphical interface for managing parallel tasks, monitoring their execution,
and visualizing resource usage.

The GUI allows users to:
1. Start/stop the Claude Parallel Manager
2. View available AI agents (Claude, PyAutoGen, VSCode)
3. Create and schedule parallel tasks
4. Monitor active tasks and resource usage
5. View task history and results
"""

import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("claude_parallel_gui.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ClaudeParallelGUI")

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Try to import required modules
sys.path.append(BASE_DIR)
try:
    from claude_parallel_manager import ClaudeParallelManager
except ImportError:
    logger.error("Failed to import ClaudeParallelManager")
    ClaudeParallelManager = None

try:
    from claude_parallel_integration import ClaudeParallelIntegration
except ImportError:
    logger.error("Failed to import ClaudeParallelIntegration")
    ClaudeParallelIntegration = None

try:
    from ai_agent_detector import AIAgentDetector
except ImportError:
    logger.error("Failed to import AIAgentDetector")
    AIAgentDetector = None

class ClaudeParallelGUI:
    """
    GUI for the Claude Parallel Execution System.
    """
    
    def __init__(self, root=None):
        """Initialize the GUI"""
        # If root is provided, create a tab in the existing window
        # Otherwise create a new window
        self.standalone = root is None
        
        if self.standalone:
            self.root = tk.Tk()
            self.root.title("Claude Parallel Execution System")
            self.root.geometry("900x700")
            self.main_frame = self.root
        else:
            self.root = root
            self.main_frame = ttk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize components
        self.claude_manager = None
        self.integration = None
        self.agent_detector = None
        
        # Initialize GUI variables
        self.status_var = tk.StringVar(value="Initializing...")
        self.active_tasks_var = tk.StringVar(value="0")
        self.queued_tasks_var = tk.StringVar(value="0")
        self.completed_tasks_var = tk.StringVar(value="0")
        self.cpu_var = tk.StringVar(value="0%")
        self.memory_var = tk.StringVar(value="0%")
        self.available_agents_var = tk.StringVar(value="Checking...")
        
        # Task list variables
        self.task_list = []
        self.active_tasks_data = []
        self.completed_tasks_data = []
        
        # Create GUI layout
        self._create_gui()
        
        # Initialize components
        self._initialize_components()
        
        # Start update thread
        self.update_thread_active = True
        self.update_thread = threading.Thread(target=self._update_status_thread)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # If standalone, start the main loop
        if self.standalone:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            self.root.mainloop()
    
    def _create_gui(self):
        """Create the GUI layout"""
        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.tasks_tab = ttk.Frame(self.notebook)
        self.config_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.tasks_tab, text="Tasks")
        self.notebook.add(self.config_tab, text="Configuration")
        
        # Create dashboard tab contents
        self._create_dashboard_tab()
        
        # Create tasks tab contents
        self._create_tasks_tab()
        
        # Create configuration tab contents
        self._create_config_tab()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_dashboard_tab(self):
        """Create the dashboard tab layout"""
        # Control panel frame
        control_frame = ttk.LabelFrame(self.dashboard_tab, text="Control Panel")
        control_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self._start_parallel_system)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop_parallel_system)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.detect_btn = ttk.Button(btn_frame, text="Detect Agents", command=self._detect_agents)
        self.detect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Create a frame for current status
        status_frame = ttk.LabelFrame(self.dashboard_tab, text="System Status")
        status_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Status grid
        tk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="Active Tasks:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.active_tasks_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="Queued Tasks:").grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.queued_tasks_var).grid(row=1, column=3, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="Completed Tasks:").grid(row=1, column=4, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.completed_tasks_var).grid(row=1, column=5, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="CPU Usage:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.cpu_var).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="Memory Usage:").grid(row=2, column=2, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.memory_var).grid(row=2, column=3, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(status_frame, text="Available Agents:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self.available_agents_var).grid(row=3, column=1, sticky=tk.W, padx=10, pady=5, columnspan=5)
        
        # Create frames for active tasks
        task_frame = ttk.LabelFrame(self.dashboard_tab, text="Active Tasks")
        task_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Task treeview
        columns = ("ID", "Type", "Status", "Progress", "Duration")
        self.active_task_tree = ttk.Treeview(task_frame, columns=columns, show="headings")
        
        # Define headings
        for col in columns:
            self.active_task_tree.heading(col, text=col)
            self.active_task_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.active_task_tree.yview)
        self.active_task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.active_task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add popup menu for task actions
        self.task_menu = tk.Menu(self.root, tearoff=0)
        self.task_menu.add_command(label="View Details", command=self._view_task_details)
        self.task_menu.add_command(label="Stop Task", command=self._stop_task)
        
        self.active_task_tree.bind("<Button-3>", self._on_task_right_click)
    
    def _create_tasks_tab(self):
        """Create the tasks tab layout"""
        # Create frame for adding new tasks
        add_task_frame = ttk.LabelFrame(self.tasks_tab, text="Add New Task")
        add_task_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Task input form
        tk.Label(add_task_frame, text="Script Path:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.script_path_var = tk.StringVar()
        path_entry = ttk.Entry(add_task_frame, textvariable=self.script_path_var, width=50)
        path_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        browse_btn = ttk.Button(add_task_frame, text="Browse", command=self._browse_script)
        browse_btn.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        tk.Label(add_task_frame, text="Task Type:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.task_type_var = tk.StringVar(value="utility")
        task_type_combo = ttk.Combobox(add_task_frame, textvariable=self.task_type_var, 
                                        values=["utility", "analysis", "simulation", "blender_task"])
        task_type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        tk.Label(add_task_frame, text="Priority:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.priority_var = tk.IntVar(value=5)
        priority_spin = ttk.Spinbox(add_task_frame, from_=1, to=10, textvariable=self.priority_var, width=5)
        priority_spin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        tk.Label(add_task_frame, text="(1=Highest, 10=Lowest)").grid(row=2, column=2, sticky=tk.W, padx=0, pady=5)
        
        # Add task button
        add_btn = ttk.Button(add_task_frame, text="Add Task", command=self._add_task)
        add_btn.grid(row=3, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Run example tasks button
        examples_btn = ttk.Button(add_task_frame, text="Run Example Tasks", command=self._run_example_tasks)
        examples_btn.grid(row=3, column=2, sticky=tk.W, padx=5, pady=10)
        
        # Create frame for completed tasks
        completed_frame = ttk.LabelFrame(self.tasks_tab, text="Completed Tasks")
        completed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Completed tasks treeview
        columns = ("ID", "Type", "Status", "Duration", "Completed At")
        self.completed_task_tree = ttk.Treeview(completed_frame, columns=columns, show="headings")
        
        # Define headings
        for col in columns:
            self.completed_task_tree.heading(col, text=col)
            self.completed_task_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(completed_frame, orient=tk.VERTICAL, command=self.completed_task_tree.yview)
        self.completed_task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.completed_task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to view details
        self.completed_task_tree.bind("<Double-1>", self._view_completed_task_details)
    
    def _create_config_tab(self):
        """Create the configuration tab layout"""
        # Create frame for configuration
        config_frame = ttk.Frame(self.config_tab)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # System configuration
        system_frame = ttk.LabelFrame(config_frame, text="System Configuration")
        system_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Max parallel tasks
        tk.Label(system_frame, text="Maximum Parallel Tasks:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.max_tasks_var = tk.IntVar(value=5)
        max_tasks_spin = ttk.Spinbox(system_frame, from_=1, to=20, textvariable=self.max_tasks_var, width=5)
        max_tasks_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Resource thresholds
        tk.Label(system_frame, text="CPU Threshold (%):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.cpu_threshold_var = tk.IntVar(value=80)
        cpu_spin = ttk.Spinbox(system_frame, from_=10, to=95, textvariable=self.cpu_threshold_var, width=5)
        cpu_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        tk.Label(system_frame, text="Memory Threshold (%):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.memory_threshold_var = tk.IntVar(value=85)
        memory_spin = ttk.Spinbox(system_frame, from_=10, to=95, textvariable=self.memory_threshold_var, width=5)
        memory_spin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Fallback mode
        tk.Label(system_frame, text="Fallback Mode:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.fallback_mode_var = tk.StringVar(value="supplement")
        fallback_combo = ttk.Combobox(system_frame, textvariable=self.fallback_mode_var, 
                                      values=["supplement", "takeover", "disabled"])
        fallback_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Load and Save buttons
        button_frame = ttk.Frame(system_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        load_btn = ttk.Button(button_frame, text="Load Configuration", command=self._load_config)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(button_frame, text="Save Configuration", command=self._save_config)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        apply_btn = ttk.Button(button_frame, text="Apply Changes", command=self._apply_config)
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        # Task type configuration
        task_type_frame = ttk.LabelFrame(config_frame, text="Task Type Configuration")
        task_type_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Create entries for each task type
        task_types = [
            ("Blender Task", "blender_task", 1),
            ("Simulation", "simulation", 2),
            ("Analysis", "analysis", 3),
            ("Utility", "utility", 5)
        ]
        
        # Create header
        tk.Label(task_type_frame, text="Task Type").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(task_type_frame, text="Max Instances").grid(row=0, column=1, padx=10, pady=5)
        tk.Label(task_type_frame, text="CPU Usage (%)").grid(row=0, column=2, padx=10, pady=5)
        tk.Label(task_type_frame, text="Memory Usage (%)").grid(row=0, column=3, padx=10, pady=5)
        
        # Add entries for each task type
        self.task_type_vars = {}
        for i, (name, key, max_instances) in enumerate(task_types):
            row = i + 1
            
            tk.Label(task_type_frame, text=name).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
            
            # Max instances
            max_var = tk.IntVar(value=max_instances)
            max_spin = ttk.Spinbox(task_type_frame, from_=1, to=10, textvariable=max_var, width=5)
            max_spin.grid(row=row, column=1, padx=10, pady=5)
            
            # CPU usage
            cpu_var = tk.IntVar(value=30 if key == "blender_task" else 20 if key == "simulation" else 15 if key == "analysis" else 10)
            cpu_spin = ttk.Spinbox(task_type_frame, from_=5, to=90, textvariable=cpu_var, width=5)
            cpu_spin.grid(row=row, column=2, padx=10, pady=5)
            
            # Memory usage
            mem_var = tk.IntVar(value=25 if key == "blender_task" else 20 if key == "simulation" else 15 if key == "analysis" else 10)
            mem_spin = ttk.Spinbox(task_type_frame, from_=5, to=90, textvariable=mem_var, width=5)
            mem_spin.grid(row=row, column=3, padx=10, pady=5)
            
            # Store variables
            self.task_type_vars[key] = {"max": max_var, "cpu": cpu_var, "mem": mem_var}
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _initialize_components(self):
        """Initialize the parallel execution components"""
        # Initialize the Agent Detector
        if AIAgentDetector:
            self.agent_detector = AIAgentDetector()
            self._detect_agents()
        
        # Load configuration
        self._load_config()
        
        # Update status bar
        self.status_bar.config(text="Ready - Claude Parallel Execution System initialized")
    
    def _update_status_thread(self):
        """Update status in a separate thread"""
        while self.update_thread_active:
            try:
                if self.claude_manager:
                    status = self.claude_manager.get_status()
                    
                    # Update status variables
                    if status.get("running", False):
                        self.status_var.set("Running")
                    else:
                        self.status_var.set("Stopped")
                    
                    self.active_tasks_var.set(str(status.get("active_tasks", 0)))
                    self.queued_tasks_var.set(str(status.get("queued_tasks", 0)))
                    self.completed_tasks_var.set(str(len(status.get("task_details", {}).get("completed", []))))
                    
                    self.cpu_var.set(f"{status.get('resources', {}).get('cpu_percent', 0):.1f}%")
                    self.memory_var.set(f"{status.get('resources', {}).get('memory_percent', 0):.1f}%")
                    
                    # Update active tasks treeview
                    self._update_active_tasks_tree(status)
                    
                    # Update completed tasks treeview
                    self._update_completed_tasks_tree(status)
                    
            except Exception as e:
                logger.error(f"Error updating status: {e}")
            
            time.sleep(2)  # Update every 2 seconds
    
    def _update_active_tasks_tree(self, status):
        """Update the active tasks treeview"""
        # Get active tasks data
        active_tasks = status.get("task_details", {}).get("active", [])
        
        # Store the active task data for reference
        self.active_tasks_data = active_tasks
        
        # Clear the treeview
        for item in self.active_task_tree.get_children():
            self.active_task_tree.delete(item)
        
        # Add active tasks to the treeview
        for task in active_tasks:
            task_id = task.get("id", "unknown")
            task_type = task.get("task_type", "unknown")
            task_status = task.get("status", "unknown")
            
            # Calculate progress if possible
            progress = "N/A"
            if task.get("start_time"):
                start_time = task.get("start_time", 0)
                current_time = time.time()
                elapsed = current_time - start_time
                progress = f"{elapsed:.1f}s"
            
            # Format values
            values = (
                task_id[:10] + "..." if len(task_id) > 12 else task_id,
                task_type,
                task_status,
                progress,
                "N/A"
            )
            
            self.active_task_tree.insert("", "end", values=values, tags=(task_id,))
    
    def _update_completed_tasks_tree(self, status):
        """Update the completed tasks treeview"""
        # Get completed tasks data
        completed_tasks = status.get("task_details", {}).get("completed", [])
        
        # Only update if the list has changed
        if self.completed_tasks_data == completed_tasks:
            return
        
        # Store the completed task data for reference
        self.completed_tasks_data = completed_tasks
        
        # Clear the treeview
        for item in self.completed_task_tree.get_children():
            self.completed_task_tree.delete(item)
        
        # Add completed tasks to the treeview
        for task in completed_tasks:
            task_id = task.get("id", "unknown")
            task_type = task.get("task_type", "unknown")
            task_status = task.get("status", "unknown")
            
            # Calculate duration if possible
            duration = "N/A"
            if task.get("start_time") and task.get("end_time"):
                start_time = task.get("start_time", 0)
                end_time = task.get("end_time", 0)
                duration = f"{end_time - start_time:.1f}s"
            
            # Format completion time
            completed_at = "N/A"
            if task.get("end_time"):
                completed_at = datetime.fromtimestamp(task.get("end_time")).strftime("%H:%M:%S")
            
            # Format values
            values = (
                task_id[:10] + "..." if len(task_id) > 12 else task_id,
                task_type,
                task_status,
                duration,
                completed_at
            )
            
            self.completed_task_tree.insert("", "end", values=values, tags=(task_id,))
    
    def _start_parallel_system(self):
        """Start the Claude Parallel Manager"""
        if self.claude_manager:
            # Already initialized, just start it
            self.claude_manager.start()
        else:
            # Initialize and start
            try:
                self.claude_manager = ClaudeParallelManager()
                
                # Apply configuration
                self._apply_config_to_manager()
                
                # Start the manager
                self.claude_manager.start()
                
                logger.info("Claude Parallel Manager started")
                self.status_bar.config(text="Claude Parallel Manager started")
                
                # Update button states
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                
            except Exception as e:
                logger.error(f"Error starting Claude Parallel Manager: {e}")
                messagebox.showerror("Error", f"Failed to start Claude Parallel Manager: {e}")
                self.status_bar.config(text=f"Error: {e}")
                return
    
    def _stop_parallel_system(self):
        """Stop the Claude Parallel Manager"""
        if not self.claude_manager:
            return
        
        try:
            self.claude_manager.stop()
            logger.info("Claude Parallel Manager stopped")
            self.status_bar.config(text="Claude Parallel Manager stopped")
            
            # Update button states
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error stopping Claude Parallel Manager: {e}")
            messagebox.showerror("Error", f"Failed to stop Claude Parallel Manager: {e}")
            self.status_bar.config(text=f"Error: {e}")
    
    def _detect_agents(self):
        """Detect available AI agents"""
        if not self.agent_detector:
            self.available_agents_var.set("Agent Detector not available")
            return
        
        try:
            # Detect agents
            available_agents = self.agent_detector.detect_all_agents()
            
            # Format agent list
            agent_names = {
                "claude_code": "Claude Code",
                "pyautogen": "PyAutoGen",
                "vscode_agent": "VSCode Agent"
            }
            
            agent_list = [agent_names.get(agent, agent) for agent in available_agents]
            self.available_agents_var.set(", ".join(agent_list))
            
            # Update status bar
            self.status_bar.config(text=f"Detected {len(available_agents)} available agents")
            
        except Exception as e:
            logger.error(f"Error detecting agents: {e}")
            self.available_agents_var.set(f"Error: {e}")
            self.status_bar.config(text=f"Error detecting agents: {e}")
    
    def _on_task_right_click(self, event):
        """Handle right-click on a task"""
        # Select the item under the cursor
        item = self.active_task_tree.identify_row(event.y)
        if item:
            self.active_task_tree.selection_set(item)
            self.task_menu.post(event.x_root, event.y_root)
    
    def _view_task_details(self):
        """View details of the selected task"""
        selected_items = self.active_task_tree.selection()
        if not selected_items:
            return
        
        # Get task ID from the selected item
        task_id = self.active_task_tree.item(selected_items[0], "values")[0]
        
        # Find task details
        task_details = None
        for task in self.active_tasks_data:
            if task.get("id", "")[:10] == task_id[:10]:
                task_details = task
                break
        
        if not task_details:
            messagebox.showinfo("Task Details", "Task details not found")
            return
        
        # Create a details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Task Details: {task_id}")
        details_window.geometry("500x400")
        
        # Create text widget for details
        text_widget = tk.Text(details_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format and display details
        text_widget.insert(tk.END, f"Task ID: {task_details.get('id', 'N/A')}\n\n")
        text_widget.insert(tk.END, f"Status: {task_details.get('status', 'N/A')}\n")
        text_widget.insert(tk.END, f"Type: {task_details.get('task_type', 'N/A')}\n")
        
        if task_details.get("script_path"):
            text_widget.insert(tk.END, f"Script: {task_details.get('script_path', 'N/A')}\n")
        
        if task_details.get("start_time"):
            start_time = datetime.fromtimestamp(task_details.get("start_time"))
            text_widget.insert(tk.END, f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        text_widget.insert(tk.END, "\nAdditional Information:\n")
        
        # Add any other relevant details
        for key, value in task_details.items():
            if key not in ["id", "status", "task_type", "script_path", "start_time"]:
                text_widget.insert(tk.END, f"{key}: {value}\n")
        
        text_widget.config(state=tk.DISABLED)
    
    def _stop_task(self):
        """Stop the selected task"""
        selected_items = self.active_task_tree.selection()
        if not selected_items:
            return
        
        # Get task ID from the selected item
        task_id = self.active_task_tree.item(selected_items[0], "values")[0]
        
        # Find full task ID
        full_task_id = None
        for task in self.active_tasks_data:
            if task.get("id", "")[:10] == task_id[:10]:
                full_task_id = task.get("id")
                break
        
        if not full_task_id:
            messagebox.showinfo("Stop Task", "Task not found")
            return
        
        # Confirm stop
        if not messagebox.askyesno("Stop Task", f"Are you sure you want to stop task {task_id}?"):
            return
        
        # Stop the task
        if self.claude_manager:
            try:
                success = self.claude_manager.cancel_task(full_task_id)
                if success:
                    self.status_bar.config(text=f"Task {task_id} stopped")
                else:
                    self.status_bar.config(text=f"Failed to stop task {task_id}")
            except Exception as e:
                logger.error(f"Error stopping task: {e}")
                messagebox.showerror("Error", f"Failed to stop task: {e}")
                self.status_bar.config(text=f"Error stopping task: {e}")
    
    def _view_completed_task_details(self, event):
        """View details of a completed task"""
        item = self.completed_task_tree.identify_row(event.y)
        if not item:
            return
        
        # Get task ID from the selected item
        task_id = self.completed_task_tree.item(item, "values")[0]
        
        # Find task details
        task_details = None
        for task in self.completed_tasks_data:
            if task.get("id", "")[:10] == task_id[:10]:
                task_details = task
                break
        
        if not task_details:
            messagebox.showinfo("Task Details", "Task details not found")
            return
        
        # Create a details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Task Details: {task_id}")
        details_window.geometry("500x400")
        
        # Create text widget for details
        text_widget = tk.Text(details_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format and display details
        text_widget.insert(tk.END, f"Task ID: {task_details.get('id', 'N/A')}\n\n")
        text_widget.insert(tk.END, f"Status: {task_details.get('status', 'N/A')}\n")
        text_widget.insert(tk.END, f"Type: {task_details.get('task_type', 'N/A')}\n")
        
        if task_details.get("script_path"):
            text_widget.insert(tk.END, f"Script: {task_details.get('script_path', 'N/A')}\n")
        
        if task_details.get("start_time"):
            start_time = datetime.fromtimestamp(task_details.get("start_time"))
            text_widget.insert(tk.END, f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if task_details.get("end_time"):
            end_time = datetime.fromtimestamp(task_details.get("end_time"))
            text_widget.insert(tk.END, f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if task_details.get("duration"):
            text_widget.insert(tk.END, f"Duration: {task_details.get('duration'):.1f} seconds\n")
        
        if task_details.get("result"):
            text_widget.insert(tk.END, f"\nResult:\n{task_details.get('result')}\n")
        
        if task_details.get("error"):
            text_widget.insert(tk.END, f"\nError:\n{task_details.get('error')}\n")
        
        text_widget.insert(tk.END, "\nAdditional Information:\n")
        
        # Add any other relevant details
        for key, value in task_details.items():
            if key not in ["id", "status", "task_type", "script_path", "start_time", "end_time", "duration", "result", "error"]:
                text_widget.insert(tk.END, f"{key}: {value}\n")
        
        text_widget.config(state=tk.DISABLED)
    
    def _browse_script(self):
        """Browse for a script file"""
        file_path = filedialog.askopenfilename(
            title="Select Script",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.script_path_var.set(file_path)
    
    def _add_task(self):
        """Add a new task to the queue"""
        script_path = self.script_path_var.get()
        task_type = self.task_type_var.get()
        priority = self.priority_var.get()
        
        if not script_path:
            messagebox.showerror("Error", "Script path is required")
            return
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Script file does not exist")
            return
        
        if not self.claude_manager:
            messagebox.showerror("Error", "Claude Parallel Manager is not running")
            return
        
        try:
            # Add the task
            task_id = self.claude_manager.add_script_task(
                script_path=script_path,
                task_type=task_type,
                priority=priority
            )
            
            self.status_bar.config(text=f"Task added with ID: {task_id}")
            
            # Clear the form
            self.script_path_var.set("")
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            messagebox.showerror("Error", f"Failed to add task: {e}")
            self.status_bar.config(text=f"Error adding task: {e}")
    
    def _run_example_tasks(self):
        """Run the example tasks"""
        # Check if manager is running
        if not self.claude_manager:
            messagebox.showerror("Error", "Claude Parallel Manager is not running")
            return
        
        # Check if examples directory exists
        examples_dir = os.path.join(BASE_DIR, "ai_managers", "examples_parallel_run")
        if not os.path.exists(examples_dir):
            messagebox.showerror("Error", "Examples directory not found")
            return
        
        # Find example tasks
        example_tasks = []
        for filename in os.listdir(examples_dir):
            if filename.startswith("parallel_agent") and filename.endswith(".py"):
                example_tasks.append(os.path.join(examples_dir, filename))
        
        if not example_tasks:
            messagebox.showerror("Error", "No example tasks found")
            return
        
        # Ask how many of each to run
        count = simpledialog.askinteger("Run Examples", "How many of each example to run?", initialvalue=1, minvalue=1, maxvalue=5)
        if not count:
            return
        
        # Run the examples
        task_ids = []
        for i in range(count):
            for script_path in example_tasks:
                # Determine agent number from filename
                try:
                    agent_num = int(os.path.basename(script_path).split("_agent")[1].split("_")[0])
                    
                    # Set priority and task type based on agent number
                    if agent_num == 1:
                        priority = 2
                        task_type = "simulation"
                    elif agent_num == 2:
                        priority = 3
                        task_type = "simulation"
                    elif agent_num == 3:
                        priority = 4
                        task_type = "simulation"
                    elif agent_num == 4:
                        priority = 3
                        task_type = "simulation"
                    elif agent_num == 5:
                        priority = 2
                        task_type = "simulation"
                    else:
                        priority = 5
                        task_type = "utility"
                    
                    # Add task
                    task_id = self.claude_manager.add_script_task(
                        script_path=script_path,
                        priority=priority,
                        task_type=task_type
                    )
                    
                    task_ids.append(task_id)
                    
                except (ValueError, IndexError):
                    logger.warning(f"Couldn't parse agent number from filename: {script_path}")
        
        self.status_bar.config(text=f"Started {len(task_ids)} example tasks")
    
    def _load_config(self):
        """Load configuration from file"""
        config_path = os.path.join(BASE_DIR, "claude_parallel_config.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update GUI variables
                self.max_tasks_var.set(config.get("max_parallel_tasks", 5))
                
                thresholds = config.get("resource_thresholds", {})
                self.cpu_threshold_var.set(thresholds.get("cpu_percent", 80))
                self.memory_threshold_var.set(thresholds.get("memory_percent", 85))
                
                self.fallback_mode_var.set(config.get("fallback_mode", "supplement"))
                
                # Update task type variables
                task_types = config.get("task_types", {})
                for task_type, vars in self.task_type_vars.items():
                    if task_type in task_types:
                        type_config = task_types[task_type]
                        vars["max"].set(type_config.get("max_instances", 1))
                        
                        resource_req = type_config.get("resource_requirements", {})
                        vars["cpu"].set(resource_req.get("cpu", 10))
                        vars["mem"].set(resource_req.get("memory", 10))
                
                self.status_bar.config(text="Configuration loaded")
                
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.status_bar.config(text=f"Error loading configuration: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        config_path = os.path.join(BASE_DIR, "claude_parallel_config.json")
        
        try:
            # Build configuration from GUI variables
            config = {}
            
            config["max_parallel_tasks"] = self.max_tasks_var.get()
            
            config["resource_thresholds"] = {
                "cpu_percent": self.cpu_threshold_var.get(),
                "memory_percent": self.memory_threshold_var.get(),
                "disk_percent": 90  # Default
            }
            
            config["fallback_mode"] = self.fallback_mode_var.get()
            
            # Task types configuration
            config["task_types"] = {}
            for task_type, vars in self.task_type_vars.items():
                config["task_types"][task_type] = {
                    "max_instances": vars["max"].get(),
                    "resource_requirements": {
                        "cpu": vars["cpu"].get(),
                        "memory": vars["mem"].get()
                    }
                }
            
            # Preserve existing advanced settings if available
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        existing_config = json.load(f)
                    
                    # Preserve settings not in the GUI
                    for key, value in existing_config.items():
                        if key not in ["max_parallel_tasks", "resource_thresholds", "fallback_mode", "task_types"]:
                            config[key] = value
                except Exception:
                    pass
            
            # Save configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.status_bar.config(text="Configuration saved")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            self.status_bar.config(text=f"Error saving configuration: {e}")
    
    def _apply_config(self):
        """Apply configuration changes to the running manager"""
        if not self.claude_manager:
            messagebox.showinfo("Information", "Claude Parallel Manager is not running. Changes will be applied when it starts.")
            return
        
        try:
            self._apply_config_to_manager()
            self.status_bar.config(text="Configuration applied")
            
        except Exception as e:
            logger.error(f"Error applying configuration: {e}")
            messagebox.showerror("Error", f"Failed to apply configuration: {e}")
            self.status_bar.config(text=f"Error applying configuration: {e}")
    
    def _apply_config_to_manager(self):
        """Apply configuration to the manager instance"""
        if not self.claude_manager:
            return
        
        # Update configuration
        self.claude_manager.config["max_parallel_tasks"] = self.max_tasks_var.get()
        
        self.claude_manager.config["resource_thresholds"] = {
            "cpu_percent": self.cpu_threshold_var.get(),
            "memory_percent": self.memory_threshold_var.get(),
            "disk_percent": 90  # Default
        }
        
        self.claude_manager.config["fallback_mode"] = self.fallback_mode_var.get()
        
        # Update task types configuration
        if "task_types" not in self.claude_manager.config:
            self.claude_manager.config["task_types"] = {}
            
        for task_type, vars in self.task_type_vars.items():
            self.claude_manager.config["task_types"][task_type] = {
                "max_instances": vars["max"].get(),
                "resource_requirements": {
                    "cpu": vars["cpu"].get(),
                    "memory": vars["mem"].get()
                }
            }
        
        # Save configuration
        self.claude_manager._save_config()
    
    def _on_close(self):
        """Handle window close event"""
        # Stop update thread
        self.update_thread_active = False
        
        # Stop Claude Parallel Manager if running
        if self.claude_manager:
            try:
                self.claude_manager.stop()
            except Exception as e:
                logger.error(f"Error stopping Claude Parallel Manager: {e}")
        
        # Destroy the window
        self.root.destroy()

# Integration with existing GUI function
def create_claude_parallel_tab(notebook):
    """
    Create a Claude Parallel tab in an existing notebook widget.
    
    This function is called by the main GUI to add the Claude Parallel
    functionality as a tab in the existing GlowingGoldenGlobe GUI.
    
    Args:
        notebook: The ttk.Notebook widget to add the tab to
    
    Returns:
        The created tab frame
    """
    # Create a frame for the tab
    tab_frame = ttk.Frame(notebook)
    
    # Initialize the Claude Parallel GUI inside this frame
    gui = ClaudeParallelGUI(tab_frame)
    
    # Return the frame to be added to the notebook
    return tab_frame

# If run as standalone application
if __name__ == "__main__":
    ClaudeParallelGUI()