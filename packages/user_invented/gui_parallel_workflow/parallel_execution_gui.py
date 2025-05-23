#!/usr/bin/env python
"""
Parallel Execution Manager GUI for GlowingGoldenGlobe

This module provides a graphical user interface for controlling and monitoring
the Parallel Execution Manager. It allows users to:

1. Start and stop parallel execution roles
2. View current resource usage
3. Send messages to the AI Manager
4. Configure execution parameters
5. Monitor task queues
"""

import os
import sys
import json
import time
import datetime
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
import queue
import subprocess

# Add the base directory to the path for imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Import GGG styles
try:
    from ggg_gui_styles import GGGStyles
except ImportError:
    print("Warning: GGGStyles not found. Using default styles.")
    class GGGStyles:
        @staticmethod
        def apply_styles(parent):
            pass

# Import the Parallel Execution Manager
try:
    from ai_managers.parallel_execution_manager import ParallelExecutionManager
except ImportError:
    try:
        # Try direct import if the package import fails
        sys.path.append(os.path.join(base_dir, 'ai_managers'))
        from parallel_execution_manager import ParallelExecutionManager
    except ImportError:
        print("Error: Could not import ParallelExecutionManager")
        print("This GUI requires the parallel_execution_manager.py module")
        sys.exit(1)

class ParallelExecutionGUI:
    """GUI for controlling the Parallel Execution Manager"""
    
    def __init__(self, root=None, manager=None, standalone=True):
        """Initialize the GUI
        
        Args:
            root (tk.Tk, optional): Tkinter root window. If None, a new window is created.
            manager (ParallelExecutionManager, optional): Instance of ParallelExecutionManager.
                If None, a new instance is created.
            standalone (bool): True if running as standalone app, False if embedded.
        """
        if standalone and root is None:
            self.root = tk.Tk()
            self.root.title("Parallel Execution Manager")
            self.root.geometry("900x700")
            self.standalone = True
        else:
            self.root = root
            self.standalone = False
            
        # Initialize or use provided manager
        self.manager = manager if manager is not None else ParallelExecutionManager()
        
        # Set up style
        try:
            GGGStyles.apply_styles(self.root)
        except Exception as e:
            print(f"Warning: Could not apply styles: {e}")
        
        # Load role descriptions
        self.role_descriptions = {
            self.manager.ROLE_AGENT_SIMULATIONS: "Runs AI agent simulations and evaluates results",
            self.manager.ROLE_PROJECT_MANAGEMENT: "Coordinates project activities and milestones",
            self.manager.ROLE_RESOURCE_MANAGEMENT: "Monitors and optimizes system resources",
            self.manager.ROLE_SCRIPT_ASSESSMENT: "Analyzes and improves Python scripts",
            self.manager.ROLE_GUI_TESTING: "Tests and validates GUI components",
            self.manager.ROLE_TASK_MANAGEMENT: "Schedules and prioritizes tasks",
        }
        
        # Set up variables
        self.role_vars = {}
        self.update_interval = tk.IntVar(value=2)  # seconds
        self.is_updating = False
        self.update_thread = None
        self.manual_control = tk.BooleanVar(value=True)
        self.user_message = tk.StringVar()
        
        # Create frames
        self.create_frames()
        self.create_widgets()
        
        # Message queue for updates from background thread
        self.message_queue = queue.Queue()
        
        # Status variables
        self.current_status = {}
        
        if self.standalone:
            # Start periodic updates
            self.toggle_updates()
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            self.root.mainloop()
    
    def create_frames(self):
        """Create the main frames for the UI"""
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame with title and buttons
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left frame for controls
        self.left_frame = ttk.LabelFrame(self.main_frame, text="Execution Controls")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Right frame for status
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.right_frame, text="System Status")
        self.status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Message frame
        self.message_frame = ttk.LabelFrame(self.right_frame, text="AI Manager Communication")
        self.message_frame.pack(fill=tk.BOTH, expand=True)
        
        # Queue status frame 
        self.queue_frame = ttk.LabelFrame(self.main_frame, text="Task Queues")
        self.queue_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def create_widgets(self):
        """Create and arrange widgets"""
        # Title and description
        ttk.Label(
            self.top_frame, 
            text="Parallel Execution Manager", 
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)
        
        # Control buttons
        control_frame = ttk.Frame(self.top_frame)
        control_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            control_frame, 
            text="Start All",
            command=self.start_all_roles
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Stop All",
            command=self.stop_all_roles
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Refresh",
            command=self.refresh_status
        ).pack(side=tk.LEFT, padx=5)
        
        # Manual control checkbox
        ttk.Checkbutton(
            control_frame,
            text="Manual Control",
            variable=self.manual_control,
            command=self.toggle_manual_control
        ).pack(side=tk.LEFT, padx=5)
        
        # Role controls
        self.create_role_controls()
        
        # Status display
        self.create_status_display()
        
        # Message area
        self.create_message_area()
        
        # Queue display
        self.create_queue_display()
    
    def create_role_controls(self):
        """Create controls for each execution role"""
        roles_frame = ttk.Frame(self.left_frame)
        roles_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        ttk.Label(roles_frame, text="Role", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(roles_frame, text="Status", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        ttk.Label(roles_frame, text="Control", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky=tk.W, pady=(0, 5))
        
        # Add controls for each role
        row = 1
        for role in self.role_descriptions:
            # Role name and description
            role_name = role.replace('_', ' ').title()
            description = self.role_descriptions.get(role, "")
            
            # Variable for role status
            var = tk.StringVar(value="Inactive")
            self.role_vars[role] = var
            
            # Role label with tooltip
            role_label = ttk.Label(roles_frame, text=role_name)
            role_label.grid(row=row, column=0, sticky=tk.W, pady=2)
            self.create_tooltip(role_label, description)
            
            # Status label
            status_label = ttk.Label(roles_frame, textvariable=var, width=10)
            status_label.grid(row=row, column=1, sticky=tk.W, pady=2)
            
            # Control buttons
            button_frame = ttk.Frame(roles_frame)
            button_frame.grid(row=row, column=2, sticky=tk.W, pady=2)
            
            ttk.Button(
                button_frame, 
                text="Start", 
                command=lambda r=role: self.start_role(r),
                width=8
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                button_frame, 
                text="Stop", 
                command=lambda r=role: self.stop_role(r),
                width=8
            ).pack(side=tk.LEFT, padx=2)
            
            row += 1
        
        # Separator
        ttk.Separator(self.left_frame).pack(fill=tk.X, padx=10, pady=10)
        
        # Update settings
        update_frame = ttk.Frame(self.left_frame)
        update_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(update_frame, text="Update interval (seconds):").pack(side=tk.LEFT)
        ttk.Spinbox(
            update_frame, 
            from_=1, 
            to=30, 
            width=3, 
            textvariable=self.update_interval
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            update_frame, 
            text="Apply", 
            command=self.apply_update_interval
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-update toggle
        update_toggle_frame = ttk.Frame(self.left_frame)
        update_toggle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.update_button = ttk.Button(
            update_toggle_frame, 
            text="Start Auto-Update", 
            command=self.toggle_updates
        )
        self.update_button.pack(side=tk.LEFT)
    
    def create_status_display(self):
        """Create the status display area"""
        # Main status frame with scrollbar
        status_inner_frame = ttk.Frame(self.status_frame)
        status_inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Resource bars
        resource_frame = ttk.LabelFrame(status_inner_frame, text="Resource Usage")
        resource_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # CPU usage
        ttk.Label(resource_frame, text="CPU:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.cpu_bar = ttk.Progressbar(resource_frame, length=200, mode='determinate', maximum=100)
        self.cpu_bar.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.cpu_label = ttk.Label(resource_frame, text="0%")
        self.cpu_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        
        # Memory usage
        ttk.Label(resource_frame, text="Memory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.mem_bar = ttk.Progressbar(resource_frame, length=200, mode='determinate', maximum=100)
        self.mem_bar.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.mem_label = ttk.Label(resource_frame, text="0%")
        self.mem_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        
        # Disk usage
        ttk.Label(resource_frame, text="Disk:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.disk_bar = ttk.Progressbar(resource_frame, length=200, mode='determinate', maximum=100)
        self.disk_bar.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.disk_label = ttk.Label(resource_frame, text="0%")
        self.disk_label.grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        
        # Active roles
        roles_frame = ttk.LabelFrame(status_inner_frame, text="Active Roles")
        roles_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable text area for active roles
        self.active_roles_text = scrolledtext.ScrolledText(
            roles_frame, 
            height=5, 
            width=40, 
            wrap=tk.WORD
        )
        self.active_roles_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.active_roles_text.config(state=tk.DISABLED)
        
        # Status log
        log_frame = ttk.LabelFrame(status_inner_frame, text="Status Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_log = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            width=40, 
            wrap=tk.WORD
        )
        self.status_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_log.config(state=tk.DISABLED)
    
    def create_message_area(self):
        """Create the message area for communicating with the AI Manager"""
        # Message input
        input_frame = ttk.Frame(self.message_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Message to AI Manager:").pack(anchor=tk.W)
        message_entry = ttk.Entry(input_frame, textvariable=self.user_message, width=50)
        message_entry.pack(fill=tk.X, expand=True, pady=5)
        message_entry.bind("<Return>", self.send_message)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="Send Message",
            command=self.send_message
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: self.user_message.set("")
        ).pack(side=tk.LEFT, padx=5)
        
        # Message history
        history_frame = ttk.Frame(self.message_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(history_frame, text="Message History:").pack(anchor=tk.W)
        self.message_history = scrolledtext.ScrolledText(
            history_frame,
            height=5,
            width=40,
            wrap=tk.WORD
        )
        self.message_history.pack(fill=tk.BOTH, expand=True, pady=5)
        self.message_history.config(state=tk.DISABLED)
    
    def create_queue_display(self):
        """Create the task queue display"""
        # Create a notebook with tabs for each queue
        self.queue_notebook = ttk.Notebook(self.queue_frame)
        self.queue_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a tab for each role queue
        self.queue_tabs = {}
        for role in self.role_descriptions:
            role_name = role.replace('_', ' ').title()
            
            # Create a frame for this role's queue
            tab_frame = ttk.Frame(self.queue_notebook)
            self.queue_notebook.add(tab_frame, text=role_name)
            
            # Add a text area for the queue items
            queue_text = scrolledtext.ScrolledText(
                tab_frame,
                height=5,
                width=40,
                wrap=tk.WORD
            )
            queue_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            queue_text.config(state=tk.DISABLED)
            
            self.queue_tabs[role] = queue_text
            
            # Add a frame for queue actions
            action_frame = ttk.Frame(tab_frame)
            action_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(
                action_frame,
                text="Add Task",
                command=lambda r=role: self.add_task_to_queue(r)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                action_frame,
                text="Clear Queue",
                command=lambda r=role: self.clear_queue(r)
            ).pack(side=tk.LEFT, padx=5)
    
    def toggle_updates(self):
        """Toggle automatic status updates"""
        if self.is_updating:
            self.is_updating = False
            self.update_button.config(text="Start Auto-Update")
        else:
            self.is_updating = True
            self.update_button.config(text="Stop Auto-Update")
            if self.update_thread is None or not self.update_thread.is_alive():
                self.update_thread = threading.Thread(target=self.update_status_thread, daemon=True)
                self.update_thread.start()
    
    def apply_update_interval(self):
        """Apply the new update interval"""
        try:
            interval = self.update_interval.get()
            if interval < 1:
                interval = 1
                self.update_interval.set(interval)
                
            self.log_message(f"Update interval set to {interval} seconds")
        except Exception as e:
            self.log_message(f"Error setting update interval: {e}")
    
    def update_status_thread(self):
        """Background thread for updating status"""
        while self.is_updating:
            # Get current status
            try:
                self.check_status()
            except Exception as e:
                self.message_queue.put(("error", f"Error updating status: {e}"))
            
            # Sleep for the specified interval
            try:
                interval = self.update_interval.get()
                time.sleep(interval)
            except:
                time.sleep(2)  # Default if there's an issue with the interval
        
        self.message_queue.put(("status", "Status updates stopped"))
    
    def check_status(self):
        """Check current status and push updates to the queue"""
        # Check resource usage
        if hasattr(self.manager, 'current_resources'):
            self.message_queue.put(("resources", self.manager.current_resources))
        
        # Check active roles
        if hasattr(self.manager, 'active_roles'):
            self.message_queue.put(("active_roles", self.manager.active_roles))
        
        # Check queue sizes
        if hasattr(self.manager, 'execution_queues'):
            queue_sizes = {}
            for role, queue_obj in self.manager.execution_queues.items():
                queue_sizes[role] = queue_obj.qsize()
            self.message_queue.put(("queue_sizes", queue_sizes))
    
    def process_messages(self):
        """Process messages from the update thread"""
        try:
            while True:
                message_type, message = self.message_queue.get_nowait()
                
                if message_type == "error":
                    self.log_message(f"ERROR: {message}")
                elif message_type == "status":
                    self.log_message(message)
                elif message_type == "resources":
                    self.update_resource_display(message)
                elif message_type == "active_roles":
                    self.update_active_roles_display(message)
                    self.update_role_status_display(message)
                elif message_type == "queue_sizes":
                    self.update_queue_display(message)
                
                self.message_queue.task_done()
        except queue.Empty:
            pass
        
        if self.is_updating:
            self.root.after(100, self.process_messages)
    
    def update_resource_display(self, resources):
        """Update the resource usage displays"""
        # Update CPU
        cpu = resources.get("cpu_percent", 0)
        self.cpu_bar["value"] = cpu
        self.cpu_label.config(text=f"{cpu:.1f}%")
        
        # Update Memory
        mem = resources.get("memory_percent", 0)
        self.mem_bar["value"] = mem
        self.mem_label.config(text=f"{mem:.1f}%")
        
        # Update Disk
        disk = resources.get("disk_percent", 0)
        self.disk_bar["value"] = disk
        self.disk_label.config(text=f"{disk:.1f}%")
    
    def update_active_roles_display(self, active_roles):
        """Update the active roles display"""
        self.active_roles_text.config(state=tk.NORMAL)
        self.active_roles_text.delete(1.0, tk.END)
        
        if active_roles:
            roles_list = list(active_roles)
            roles_list.sort()
            
            for role in roles_list:
                role_name = role.replace('_', ' ').title()
                self.active_roles_text.insert(tk.END, f"• {role_name}\n")
        else:
            self.active_roles_text.insert(tk.END, "No active roles")
        
        self.active_roles_text.config(state=tk.DISABLED)
    
    def update_role_status_display(self, active_roles):
        """Update the role status indicators"""
        for role, var in self.role_vars.items():
            if role in active_roles:
                var.set("Active")
            else:
                var.set("Inactive")
    
    def update_queue_display(self, queue_sizes):
        """Update the queue size displays"""
        for role, queue_text in self.queue_tabs.items():
            size = queue_sizes.get(role, 0)
            
            queue_text.config(state=tk.NORMAL)
            queue_text.delete(1.0, tk.END)
            
            if size > 0:
                queue_text.insert(tk.END, f"{size} task(s) in queue\n\n")
                
                # If we had actual task data, we could display it here
                queue_text.insert(tk.END, "Task details not available in this view.\n")
                queue_text.insert(tk.END, "Use the 'Add Task' button to create new tasks.")
            else:
                queue_text.insert(tk.END, "Queue is empty")
            
            queue_text.config(state=tk.DISABLED)
    
    def log_message(self, message):
        """Add a message to the status log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.status_log.config(state=tk.NORMAL)
        self.status_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_log.see(tk.END)  # Scroll to the end
        self.status_log.config(state=tk.DISABLED)
    
    def send_message(self, event=None):
        """Send a message to the AI Manager"""
        message = self.user_message.get().strip()
        if not message:
            return
        
        # Log the message
        self.message_history.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.message_history.insert(tk.END, f"[{timestamp}] User: {message}\n")
        self.message_history.see(tk.END)
        self.message_history.config(state=tk.DISABLED)
        
        # Process the message
        self.log_message(f"Message sent: {message}")
        
        # Clear the input
        self.user_message.set("")
        
        # TODO: Process the message with the AI Manager
        # This is a placeholder for actual message processing
        self.root.after(1000, lambda: self.receive_ai_response(message))
    
    def receive_ai_response(self, original_message):
        """Simulated AI response to user message"""
        responses = [
            "Processing your request.",
            f"Working on '{original_message}'.",
            "Task prioritized in the execution queue.",
            "I'll handle that right away.",
            "Your request has been queued."
        ]
        import random
        response = random.choice(responses)
        
        # Add to message history
        self.message_history.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.message_history.insert(tk.END, f"[{timestamp}] AI: {response}\n\n")
        self.message_history.see(tk.END)
        self.message_history.config(state=tk.DISABLED)
    
    def refresh_status(self):
        """Manually refresh the status display"""
        self.log_message("Manual refresh requested")
        try:
            self.check_status()
            self.process_messages()
        except Exception as e:
            self.log_message(f"Error refreshing status: {e}")
    
    def start_all_roles(self):
        """Start all roles"""
        self.log_message("Starting all roles...")
        try:
            self.manager.start_all_roles()
            self.log_message("All roles started")
        except Exception as e:
            self.log_message(f"Error starting roles: {e}")
    
    def stop_all_roles(self):
        """Stop all roles"""
        self.log_message("Stopping all roles...")
        try:
            self.manager.stop_all_roles()
            self.log_message("All roles stopped")
        except Exception as e:
            self.log_message(f"Error stopping roles: {e}")
    
    def start_role(self, role):
        """Start a specific role"""
        self.log_message(f"Starting role: {role}")
        try:
            if not hasattr(self.manager, '_start_role_thread'):
                self.log_message("Error: Manager does not support starting individual roles")
                return
                
            self.manager._start_role_thread(role)
            self.log_message(f"Role started: {role}")
        except Exception as e:
            self.log_message(f"Error starting role {role}: {e}")
    
    def stop_role(self, role):
        """Stop a specific role"""
        self.log_message(f"Stopping role: {role}")
        try:
            if role not in self.manager.active_roles:
                self.log_message(f"Role {role} is not active")
                return
                
            if role in self.manager.thread_stop_flags:
                self.manager.thread_stop_flags[role] = True
                
            self.log_message(f"Role stop requested: {role}")
        except Exception as e:
            self.log_message(f"Error stopping role {role}: {e}")
    
    def toggle_manual_control(self):
        """Toggle between manual and AI control"""
        if self.manual_control.get():
            self.log_message("Switched to manual control mode")
        else:
            self.log_message("Switched to AI control mode")
    
    def add_task_to_queue(self, role):
        """Add a task to a specific role queue"""
        # Create a dialog to enter task details
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add Task to {role.replace('_', ' ').title()}")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        task_name = tk.StringVar()
        task_priority = tk.StringVar(value="normal")
        task_desc = tk.StringVar()
        
        ttk.Label(dialog, text="Task Name:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        ttk.Entry(dialog, textvariable=task_name, width=40).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Priority:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        priority_frame = ttk.Frame(dialog)
        priority_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Radiobutton(priority_frame, text="Low", variable=task_priority, value="low").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(priority_frame, text="Normal", variable=task_priority, value="normal").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(priority_frame, text="High", variable=task_priority, value="high").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(dialog, text="Description:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        desc_entry = ttk.Entry(dialog, textvariable=task_desc, width=40)
        desc_entry.pack(fill=tk.X, padx=10, pady=5)
        
        def submit_task():
            name = task_name.get().strip()
            priority = task_priority.get()
            desc = task_desc.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Task name is required", parent=dialog)
                return
            
            # Create the task
            task = {
                "name": name,
                "priority": priority,
                "description": desc,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Add role-specific fields
            if role == self.manager.ROLE_AGENT_SIMULATIONS:
                # For agent simulations, we need agent_id and script
                task["agent_id"] = "AI_Agent_1"  # Default
                task["script"] = "simulation.py"  # Default
            elif role == self.manager.ROLE_SCRIPT_ASSESSMENT:
                # For script assessment, we need script_path
                task["script_path"] = ""  # Would be set by file picker
            
            try:
                if self.manager.queue_task(role, task):
                    self.log_message(f"Task '{name}' added to {role} queue")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", f"Failed to add task to {role} queue", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Error adding task: {str(e)}", parent=dialog)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Add Task", command=submit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def clear_queue(self, role):
        """Clear a specific role queue"""
        if messagebox.askyesno("Confirm", f"Clear the {role.replace('_', ' ').title()} queue?"):
            try:
                # Note: This is a limitation - Python's queue doesn't have a clear method
                # This is a workaround to empty the queue
                while not self.manager.execution_queues[role].empty():
                    try:
                        self.manager.execution_queues[role].get_nowait()
                        self.manager.execution_queues[role].task_done()
                    except queue.Empty:
                        break
                
                self.log_message(f"Queue cleared for {role}")
                self.refresh_status()
            except Exception as e:
                self.log_message(f"Error clearing queue: {e}")
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create tooltip window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                             background="#ffffff", relief=tk.SOLID, borderwidth=1,
                             font=("tahoma", "8", "normal"), padding=(5, 2))
            label.pack(ipadx=1)
        
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def on_close(self):
        """Handle window close event"""
        if hasattr(self, 'manager'):
            try:
                # Stop updates
                self.is_updating = False
                if self.update_thread and self.update_thread.is_alive():
                    self.update_thread.join(timeout=1.0)
                
                # Stop all roles if manager exists
                if hasattr(self.manager, 'stop_all_roles'):
                    self.manager.stop_all_roles()
            except:
                pass
        
        self.root.destroy()

if __name__ == "__main__":
    # Run as standalone application
    ParallelExecutionGUI()
