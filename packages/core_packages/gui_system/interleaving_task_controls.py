#!/usr/bin/env python3
"""
Revised interleaving controls that properly understand:
- AI_Agent folders are roles/capabilities, not instances
- Multiple tasks can run in parallel from the same folder
- Agent modes (Claude Code, API-Key, VSCode) are execution methods
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from interleaving_config_manager import get_config_manager
from ai_managers.interleaving_task_manager import get_interleaving_task_manager

class InterleavingTaskControls:
    """Interleaving controls that understand task instances and execution modes"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.config_manager = get_config_manager()
        self.task_manager = get_interleaving_task_manager()
        
        # Active task instances tracking
        self.active_tasks = {}  # {task_id: {agent_folder, mode, status, start_time}}
        
        # Control variables
        self.control_scope = tk.StringVar(value="new_tasks")  # new_tasks, active_task, all_tasks
        self.selected_folder = tk.StringVar(value="Div_AI_Agent_Focus_1")
        self.selected_mode = tk.StringVar(value="auto")  # auto, claude_code, api_key, vscode
        self.selected_task_id = tk.StringVar()
        
        # Interleaving settings
        self.interleaving_enabled = tk.BooleanVar(value=True)
        self.ai_can_override = tk.BooleanVar(value=True)
        self.apply_to_mode = tk.BooleanVar(value=False)  # Apply to all tasks using same mode
        
        # Initialize UI elements that might be referenced early
        self.status_label = None
        self.tasks_tree = None
        self._refresh_job = None
        
        # Initialize
        self._load_active_tasks()
        self._create_controls()
    
    def _load_active_tasks(self):
        """Load currently active task instances"""
        # In real implementation, this would query the task manager
        # For now, create some example tasks
        self.active_tasks = {
            "task_001": {
                "folder": "Div_AI_Agent_Focus_1",
                "mode": "claude_code",
                "description": "Build micro-robot arm component",
                "status": "running",
                "start_time": datetime.now().isoformat(),
                "interleaving": True
            },
            "task_002": {
                "folder": "Div_AI_Agent_Focus_1", 
                "mode": "api_key",
                "description": "Optimize joint mechanisms",
                "status": "running",
                "start_time": datetime.now().isoformat(),
                "interleaving": False
            }
        }
    
    def _create_controls(self):
        """Create the control interface"""
        # Main container
        container = ttk.Frame(self.parent_frame)
        container.pack(fill=tk.X, pady=(10, 0))
        
        # Separator
        ttk.Separator(container, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Main frame
        main_frame = ttk.LabelFrame(
            container,
            text="Claude Interleaving Task Control",
            padding=10
        )
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Description
        desc_text = ("Control interleaving for task instances. "
                    "Note: Agent folders define roles, multiple tasks can run in parallel.")
        ttk.Label(
            main_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray",
            wraplength=600
        ).pack(anchor="w", pady=(0, 10))
        
        # Control scope selection
        scope_frame = ttk.LabelFrame(main_frame, text="Control Scope", padding=5)
        scope_frame.pack(fill=tk.X, pady=5)
        
        scopes = [
            ("new_tasks", "New Tasks", "Apply to newly created tasks"),
            ("active_task", "Active Task", "Apply to a specific running task"),
            ("all_tasks", "All Tasks", "Apply to all tasks (current and future)")
        ]
        
        for value, text, tooltip in scopes:
            rb = ttk.Radiobutton(
                scope_frame,
                text=text,
                variable=self.control_scope,
                value=value,
                command=self._on_scope_change
            )
            rb.pack(side=tk.LEFT, padx=10)
            # Could add tooltip here
        
        # Scope-specific controls
        self.scope_panels = {}
        
        # New tasks panel
        self.scope_panels['new_tasks'] = self._create_new_tasks_panel(main_frame)
        
        # Active task panel
        self.scope_panels['active_task'] = self._create_active_task_panel(main_frame)
        
        # All tasks panel
        self.scope_panels['all_tasks'] = self._create_all_tasks_panel(main_frame)
        
        # Show initial panel
        self._on_scope_change()
        
        # Active tasks monitor
        monitor_frame = ttk.LabelFrame(main_frame, text="Active Task Instances", padding=5)
        monitor_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview for active tasks
        columns = ("folder", "mode", "description", "interleaving", "status")
        self.tasks_tree = ttk.Treeview(monitor_frame, columns=columns, height=6)
        
        # Column configuration
        self.tasks_tree.heading("#0", text="Task ID")
        self.tasks_tree.column("#0", width=100)
        
        col_widths = {"folder": 80, "mode": 80, "description": 200, "interleaving": 80, "status": 60}
        for col in columns:
            self.tasks_tree.heading(col, text=col.title())
            self.tasks_tree.column(col, width=col_widths.get(col, 100))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tasks
        self._refresh_task_list()
        
        # Bind selection
        self.tasks_tree.bind("<<TreeviewSelect>>", self._on_task_select)
        
        # Refresh controls
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.pack(fill=tk.X)
        
        ttk.Button(
            refresh_frame,
            text="Refresh Tasks",
            command=self._refresh_task_list
        ).pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            refresh_frame,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh,
            command=self._toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=20)
        
        # Status
        self.status_label = ttk.Label(refresh_frame, text="", font=("Arial", 9))
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Start auto-refresh
        self._toggle_auto_refresh()
    
    def _create_new_tasks_panel(self, parent):
        """Panel for controlling new task instances"""
        panel = ttk.Frame(parent)
        
        # Folder and mode selection
        select_frame = ttk.Frame(panel)
        select_frame.pack(fill=tk.X, pady=10)
        
        # Agent folder selection
        ttk.Label(select_frame, text="Agent Folder:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        folder_combo = ttk.Combobox(
            select_frame,
            textvariable=self.selected_folder,
            values=[f"AI_Agent_{i}" for i in range(1, 6)],
            state="readonly",
            width=15
        )
        folder_combo.grid(row=0, column=1, padx=5)
        
        # Folder role description
        self.folder_desc = ttk.Label(select_frame, text="", font=("Arial", 8), foreground="gray")
        self.folder_desc.grid(row=0, column=2, padx=10, sticky="w")
        folder_combo.bind("<<ComboboxSelected>>", self._update_folder_desc)
        
        # Execution mode selection
        ttk.Label(select_frame, text="Execution Mode:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        mode_combo = ttk.Combobox(
            select_frame,
            textvariable=self.selected_mode,
            values=["auto", "claude_code", "api_key", "vscode"],
            state="readonly",
            width=15
        )
        mode_combo.grid(row=1, column=1, padx=5, pady=(10, 0))
        
        # Interleaving settings
        settings_frame = ttk.Frame(panel)
        settings_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(
            settings_frame,
            text="Enable Interleaving for New Tasks",
            variable=self.interleaving_enabled,
            command=self._on_new_task_setting_change
        ).pack(anchor="w", pady=2)
        
        ttk.Checkbutton(
            settings_frame,
            text="Allow AI to Override (based on task analysis)",
            variable=self.ai_can_override,
            command=self._on_new_task_setting_change
        ).pack(anchor="w", padx=20, pady=2)
        
        ttk.Checkbutton(
            settings_frame,
            text="Apply to all tasks using selected execution mode",
            variable=self.apply_to_mode,
            command=self._on_new_task_setting_change
        ).pack(anchor="w", pady=2)
        
        # Initial update  
        self._update_folder_desc()
        
        return panel
    
    def _create_active_task_panel(self, parent):
        """Panel for controlling a specific active task"""
        panel = ttk.Frame(parent)
        
        info_frame = ttk.Frame(panel)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text="Selected Task:").pack(side=tk.LEFT, padx=(0, 10))
        self.task_info_label = ttk.Label(info_frame, text="None selected", font=("Arial", 9, "bold"))
        self.task_info_label.pack(side=tk.LEFT)
        
        # Task-specific controls
        control_frame = ttk.Frame(panel)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.task_interleaving = tk.BooleanVar()
        self.task_interleaving_check = ttk.Checkbutton(
            control_frame,
            text="Enable Interleaving for This Task",
            variable=self.task_interleaving,
            command=self._on_task_interleaving_change,
            state="disabled"
        )
        self.task_interleaving_check.pack(anchor="w")
        
        ttk.Label(
            control_frame,
            text="Note: Changes apply immediately to the running task",
            font=("Arial", 8),
            foreground="red"
        ).pack(anchor="w", pady=(5, 0))
        
        return panel
    
    def _create_all_tasks_panel(self, parent):
        """Panel for global task control"""
        panel = ttk.Frame(parent)
        
        ttk.Label(
            panel,
            text="⚠️ Warning: This affects all current and future tasks",
            font=("Arial", 10, "bold"),
            foreground="red"
        ).pack(pady=10)
        
        control_frame = ttk.Frame(panel)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.global_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame,
            text="Enable Interleaving Globally",
            variable=self.global_enabled
        ).pack(anchor="w")
        
        self.global_locked = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control_frame,
            text="🔒 Lock (Prevent all changes)",
            variable=self.global_locked
        ).pack(anchor="w", padx=20, pady=5)
        
        ttk.Button(
            panel,
            text="Apply Global Settings",
            command=self._apply_global_settings
        ).pack(pady=10)
        
        return panel
    
    def _on_scope_change(self):
        """Handle scope selection change"""
        # Hide all panels
        for panel in self.scope_panels.values():
            panel.pack_forget()
        
        # Show selected panel
        scope = self.control_scope.get()
        if scope in self.scope_panels:
            self.scope_panels[scope].pack(fill=tk.X, pady=10)
    
    def _update_folder_desc(self, event=None):
        """Update folder role description"""
        folder = self.selected_folder.get()
        
        roles = {
            "Div_AI_Agent_Focus_1": "3D modeling of micro-robot parts",
            "Div_AI_Agent_Focus_2": "Assembly and integration",
            "Div_AI_Agent_Focus_3": "Physics simulation and testing",
            "Div_AI_Agent_Focus_4": "Neural control systems",
            "Div_AI_Agent_Focus_5": "System optimization"
        }
        
        desc = roles.get(folder, "Unknown role")
        self.folder_desc.config(text=f"Role: {desc}")
    
    def _refresh_task_list(self):
        """Refresh the active tasks list"""
        # Ensure tree exists
        if not self.tasks_tree:
            return
            
        # Clear current items
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Add tasks
        for task_id, task_info in self.active_tasks.items():
            values = (
                task_info["folder"],
                task_info["mode"],
                task_info["description"],
                "Yes" if task_info.get("interleaving", False) else "No",
                task_info["status"]
            )
            self.tasks_tree.insert("", "end", text=task_id, values=values)
        
        # Update status if label exists
        if self.status_label:
            task_count = len(self.active_tasks)
            interleaving_count = sum(1 for t in self.active_tasks.values() if t.get("interleaving", False))
            self.status_label.config(text=f"Tasks: {task_count} | Interleaving: {interleaving_count}")
    
    def _on_task_select(self, event):
        """Handle task selection in treeview"""
        selection = self.tasks_tree.selection()
        if selection:
            task_id = self.tasks_tree.item(selection[0])["text"]
            self.selected_task_id.set(task_id)
            
            # Update active task panel if visible
            if self.control_scope.get() == "active_task":
                task_info = self.active_tasks.get(task_id, {})
                self.task_info_label.config(text=f"{task_id} ({task_info.get('mode', 'unknown')})")
                self.task_interleaving.set(task_info.get("interleaving", False))
                self.task_interleaving_check.config(state="normal")
    
    def _on_new_task_setting_change(self):
        """Handle new task setting changes"""
        folder = self.selected_folder.get()
        mode = self.selected_mode.get()
        enabled = self.interleaving_enabled.get()
        
        if self.apply_to_mode.get() and mode != "auto":
            # Apply to all tasks using this mode
            msg = f"Apply interleaving={'enabled' if enabled else 'disabled'} to all {mode} tasks?"
            if messagebox.askyesno("Confirm", msg):
                # Would update all matching tasks
                pass
        else:
            # Just save preference for new tasks
            self.config_manager.set_agent_setting(folder, enabled)
    
    def _on_task_interleaving_change(self):
        """Handle active task interleaving change"""
        task_id = self.selected_task_id.get()
        if task_id and task_id in self.active_tasks:
            enabled = self.task_interleaving.get()
            self.active_tasks[task_id]["interleaving"] = enabled
            
            # In real implementation, would notify the running task
            self._refresh_task_list()
            
            messagebox.showinfo("Updated", f"Interleaving {'enabled' if enabled else 'disabled'} for {task_id}")
    
    def _apply_global_settings(self):
        """Apply global settings to all tasks"""
        if messagebox.askyesno("Confirm", "Apply global settings to ALL tasks?"):
            enabled = self.global_enabled.get()
            locked = self.global_locked.get()
            
            self.config_manager.set_global_setting(enabled, locked)
            
            # Update all active tasks
            for task_id in self.active_tasks:
                self.active_tasks[task_id]["interleaving"] = enabled
            
            self._refresh_task_list()
            messagebox.showinfo("Applied", "Global settings applied to all tasks")
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if hasattr(self, '_refresh_job') and self._refresh_job:
            try:
                self.parent_frame.after_cancel(self._refresh_job)
            except Exception:
                pass  # Job might have already completed
            self._refresh_job = None
        
        if self.auto_refresh.get():
            self._schedule_refresh()
    
    def _schedule_refresh(self):
        """Schedule next refresh"""
        self._refresh_task_list()
        if self.auto_refresh.get():
            self._refresh_job = self.parent_frame.after(5000, self._schedule_refresh)


def add_interleaving_to_agent_config(agent_config_frame):
    """Add interleaving controls to Agent Configuration tab"""
    return InterleavingTaskControls(agent_config_frame)