#!/usr/bin/env python3
"""
Task ID Display Manager for Interleaving Controls
Provides visibility into active and planned task IDs
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
from pathlib import Path

class TaskIDDisplayManager:
    """Manages display of task IDs for interleaving control"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.task_data = self._load_task_data()
        self._create_display()
    
    def _load_task_data(self):
        """Load active and planned tasks from various sources"""
        task_data = {
            "active_tasks": {},
            "planned_tasks": {},
            "completed_tasks": {}
        }
        
        # Load from project_tasks.json if available
        try:
            task_file = Path(__file__).parent.parent / "project_tasks.json"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    data = json.load(f)
                    # Extract task IDs and info
                    if "active_tasks" in data:
                        for task in data["active_tasks"]:
                            task_id = task.get("id", f"task_{datetime.now().timestamp()}")
                            task_data["active_tasks"][task_id] = {
                                "agent": task.get("agent", "unassigned"),
                                "description": task.get("description", ""),
                                "status": task.get("status", "running")
                            }
        except Exception as e:
            print(f"Error loading task data: {e}")
        
        # Check AI workflow status
        try:
            workflow_file = Path(__file__).parent.parent / "ai_workflow_status.json"
            if workflow_file.exists():
                with open(workflow_file, 'r') as f:
                    workflow_data = json.load(f)
                    # Extract active agent tasks
                    for agent_id, agent_info in workflow_data.get("active_agents", {}).items():
                        task_id = agent_info.get("task_id", f"{agent_id}_task")
                        task_data["active_tasks"][task_id] = {
                            "agent": agent_id,
                            "description": agent_info.get("task_description", ""),
                            "status": "active"
                        }
        except Exception as e:
            print(f"Error loading workflow status: {e}")
        
        # Add some example planned tasks
        task_data["planned_tasks"] = {
            "enhance_3d_model": {
                "agent": "AI_Agent_1",
                "description": "Enhance 3D model with retractable components",
                "priority": "high"
            },
            "optimize_physics": {
                "agent": "AI_Agent_2", 
                "description": "Optimize physics simulation parameters",
                "priority": "medium"
            },
            "generate_docs": {
                "agent": "AI_Agent_3",
                "description": "Generate technical documentation",
                "priority": "low"
            }
        }
        
        return task_data
    
    def _create_display(self):
        """Create the task ID display interface"""
        # Main container
        container = ttk.LabelFrame(self.parent_frame, text="Task ID Reference", padding=10)
        container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create notebook for different task views
        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Active tasks tab
        active_frame = ttk.Frame(notebook)
        notebook.add(active_frame, text="Active Tasks")
        self._create_active_tasks_view(active_frame)
        
        # Planned tasks tab
        planned_frame = ttk.Frame(notebook)
        notebook.add(planned_frame, text="Planned Tasks")
        self._create_planned_tasks_view(planned_frame)
        
        # Task ID generator
        generator_frame = ttk.Frame(notebook)
        notebook.add(generator_frame, text="Generate Task ID")
        self._create_task_id_generator(generator_frame)
        
        # Refresh button
        ttk.Button(container, text="Refresh Task List", 
                  command=self._refresh_tasks).pack(pady=5)
    
    def _create_active_tasks_view(self, parent):
        """Create view for active tasks"""
        # Create treeview
        columns = ("Agent", "Description", "Status", "Actions")
        self.active_tree = ttk.Treeview(parent, columns=columns, show='tree headings')
        
        # Configure columns
        self.active_tree.heading('#0', text='Task ID')
        self.active_tree.heading('Agent', text='Agent')
        self.active_tree.heading('Description', text='Description')
        self.active_tree.heading('Status', text='Status')
        self.active_tree.heading('Actions', text='Actions')
        
        self.active_tree.column('#0', width=150)
        self.active_tree.column('Agent', width=100)
        self.active_tree.column('Description', width=300)
        self.active_tree.column('Status', width=100)
        self.active_tree.column('Actions', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.active_tree.yview)
        self.active_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.active_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate with data
        self._populate_active_tasks()
        
        # Bind double-click to copy task ID
        self.active_tree.bind('<Double-Button-1>', self._copy_task_id)
    
    def _create_planned_tasks_view(self, parent):
        """Create view for planned tasks"""
        # Create treeview
        columns = ("Agent", "Description", "Priority")
        self.planned_tree = ttk.Treeview(parent, columns=columns, show='tree headings')
        
        # Configure columns
        self.planned_tree.heading('#0', text='Task ID')
        self.planned_tree.heading('Agent', text='Assigned Agent')
        self.planned_tree.heading('Description', text='Description')
        self.planned_tree.heading('Priority', text='Priority')
        
        self.planned_tree.column('#0', width=150)
        self.planned_tree.column('Agent', width=100)
        self.planned_tree.column('Description', width=300)
        self.planned_tree.column('Priority', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.planned_tree.yview)
        self.planned_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.planned_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate with data
        self._populate_planned_tasks()
        
        # Bind double-click
        self.planned_tree.bind('<Double-Button-1>', self._copy_task_id)
    
    def _create_task_id_generator(self, parent):
        """Create task ID generator interface"""
        # Instructions
        ttk.Label(parent, text="Generate a new task ID for manual task creation:",
                 font=("Arial", 10)).pack(pady=10)
        
        # Input frame
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(input_frame, text="Task Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.task_type_var = tk.StringVar()
        task_type_combo = ttk.Combobox(input_frame, textvariable=self.task_type_var,
                                       values=["model", "simulation", "analysis", "utility", "custom"],
                                       width=20)
        task_type_combo.grid(row=0, column=1, pady=5)
        task_type_combo.current(0)
        
        ttk.Label(input_frame, text="Short Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.task_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.task_name_var, width=25).grid(row=1, column=1, pady=5)
        
        # Generate button
        ttk.Button(input_frame, text="Generate ID", 
                  command=self._generate_task_id).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Generated ID display
        self.generated_id_var = tk.StringVar()
        id_frame = ttk.LabelFrame(parent, text="Generated Task ID", padding=10)
        id_frame.pack(fill=tk.X, padx=20, pady=10)
        
        id_label = ttk.Label(id_frame, textvariable=self.generated_id_var, 
                            font=("Courier", 12, "bold"))
        id_label.pack()
        
        ttk.Button(id_frame, text="Copy to Clipboard", 
                  command=self._copy_generated_id).pack(pady=5)
    
    def _populate_active_tasks(self):
        """Populate active tasks tree"""
        # Clear existing
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)
        
        # Add tasks
        for task_id, task_info in self.task_data["active_tasks"].items():
            self.active_tree.insert('', 'end', text=task_id,
                                   values=(task_info["agent"],
                                          task_info["description"],
                                          task_info["status"],
                                          "Click to copy ID"))
    
    def _populate_planned_tasks(self):
        """Populate planned tasks tree"""
        # Clear existing
        for item in self.planned_tree.get_children():
            self.planned_tree.delete(item)
        
        # Add tasks
        for task_id, task_info in self.task_data["planned_tasks"].items():
            self.planned_tree.insert('', 'end', text=task_id,
                                    values=(task_info["agent"],
                                           task_info["description"],
                                           task_info["priority"]))
    
    def _copy_task_id(self, event):
        """Copy task ID to clipboard on double-click"""
        tree = event.widget
        selection = tree.selection()
        if selection:
            item = selection[0]
            task_id = tree.item(item, 'text')
            self.parent_frame.clipboard_clear()
            self.parent_frame.clipboard_append(task_id)
            # Show feedback
            from tkinter import messagebox
            messagebox.showinfo("Copied", f"Task ID '{task_id}' copied to clipboard!")
    
    def _generate_task_id(self):
        """Generate a new task ID"""
        task_type = self.task_type_var.get()
        task_name = self.task_name_var.get().strip()
        
        if not task_name:
            task_name = "task"
        
        # Clean the name
        task_name = task_name.lower().replace(" ", "_")
        
        # Generate timestamp component
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create ID
        task_id = f"{task_type}_{task_name}_{timestamp}"
        
        self.generated_id_var.set(task_id)
    
    def _copy_generated_id(self):
        """Copy generated ID to clipboard"""
        task_id = self.generated_id_var.get()
        if task_id:
            self.parent_frame.clipboard_clear()
            self.parent_frame.clipboard_append(task_id)
            from tkinter import messagebox
            messagebox.showinfo("Copied", f"Task ID '{task_id}' copied to clipboard!")
    
    def _refresh_tasks(self):
        """Refresh task lists"""
        self.task_data = self._load_task_data()
        self._populate_active_tasks()
        self._populate_planned_tasks()
        print("[INFO] Task lists refreshed")


def add_task_id_display(parent_frame):
    """Add task ID display to the interleaving controls"""
    return TaskIDDisplayManager(parent_frame)