"""
Implementation of GUI enhancements for GlowingGoldenGlobe Agent Mode

IMPORTANT GUI DEVELOPMENT NOTES:
- Always check parent container's geometry manager before adding components
- Never mix pack() and grid() in the same container  
- See /docs/Procedure_for_Upgrading_the_GUI.md for safe practices
- For debugging, use /docs/Richard_Isaac_Craddock_Procedural_Problem_Solving_Method.md

This file contains the implementation of the following enhancements:
1. Adding minutes option to the time limit
2. Enhancing GUI model version data display
3. Agent Mode vs PyAutoGen selection for parallel execution
4. Start/Stop controls for running processes
5. Task completion marking without popups
6. Warning when starting a session with a finished model

IMPORTANT NOTES FOR AI ASSISTANTS:
- When modifying this file, always update the desktop shortcut using:
  from ggg_maintenance_helper import GGGMaintenance
  GGGMaintenance.update_desktop_shortcut()
  
- Clean up temporary files when you're done:
  from run_ggg_gui import clean_temporary_files
  clean_temporary_files()
  
- Avoid mixing pack and grid geometry managers in the same container
  Use either grid or pack consistently within each container

- For the TimeLimit class, always use grid geometry manager to avoid conflicts
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime
import re
import glob
import json
import time
import sys

class TimeLimit:
    """Helper class for time limit selection UI enhancements"""
    
    @staticmethod
    def setup_time_limit_ui(options_frame, time_limit_hours, config):
        """Set up the time limit UI with both hours and minutes options"""
        ttk.Label(options_frame, text="Time Limit:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        time_frame = ttk.Frame(options_frame)
        time_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Using grid for all children instead of pack
        # Add hours input
        hours_entry = ttk.Entry(time_frame, textvariable=time_limit_hours, width=5)
        hours_entry.grid(row=0, column=0, padx=(0, 2))
        
        hours_label = ttk.Label(time_frame, text=" hours")
        hours_label.grid(row=0, column=1, padx=(0, 5))
        
        # Add minutes input
        time_limit_minutes = tk.StringVar(value=str(config.get("time_limit_minutes", 0)))
        minutes_entry = ttk.Entry(time_frame, textvariable=time_limit_minutes, width=5)
        minutes_entry.grid(row=0, column=2, padx=(5, 2))
        
        minutes_label = ttk.Label(time_frame, text=" minutes")
        minutes_label.grid(row=0, column=3)
        
        return time_limit_minutes
    
    @staticmethod
    def validate_time_limit(time_limit_hours, time_limit_minutes):
        """Validate the time limit inputs"""
        try:
            hours = float(time_limit_hours.get())
            minutes = int(time_limit_minutes.get())
            
            if hours < 0:
                raise ValueError("Hours must be zero or positive")
            
            if minutes < 0:
                raise ValueError("Minutes must be zero or positive")
                
            if hours == 0 and minutes == 0:
                raise ValueError("Time limit must be greater than zero")
            
            return True
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return False
    
    @staticmethod
    def calculate_total_seconds(time_limit_hours, time_limit_minutes):
        """Calculate the total seconds from hours and minutes"""
        try:
            hours = float(time_limit_hours.get())
            minutes = int(time_limit_minutes.get())
            return (hours * 3600) + (minutes * 60)
        except (ValueError, TypeError):
            return 3600  # Default to 1 hour


class ModelVersionDisplay:
    """Helper class for model version display enhancements"""
    
    @staticmethod
    def check_model_status(version):
        """Enhanced check for model status with date information"""
        status = ""
        completion_date = ""
        
        # Check if JSON specification exists
        json_path = f"micro_robot_composite_part_v{version}.json"
        if not os.path.exists(json_path):
            return "Not built"
            
        # Get file modification time for completion date
        try:
            mtime = os.path.getmtime(json_path)
            completion_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except:
            completion_date = "Unknown"
        
        # Check if Blender file exists
        blend_path = f"micro_robot_composite_part_v{version}.blend"
        if not os.path.exists(blend_path):
            return f"Specification only (Created: {completion_date})"
        
        # Check if O3DE export exists
        fbx_path = f"micro_robot_composite_part_v{version}.fbx"
        if not os.path.exists(fbx_path):
            return f"3D model only (Created: {completion_date})"
        
        # Check if requirements met flag exists
        if os.path.exists(f"requirements_met_v{version}.flag"):
            return f"Requirements met (Completed: {completion_date})"
            
        # Check if simulation completed flag exists
        sim_flag = f"simulation_complete_v{version}.flag"
        if os.path.exists(sim_flag):
            try:
                sim_time = os.path.getmtime(sim_flag)
                sim_date = datetime.datetime.fromtimestamp(sim_time).strftime("%Y-%m-%d")
                return f"Simulation complete ({sim_date})"
            except:
                return f"Simulation complete (Date: {completion_date})"
        
        return f"In progress (Started: {completion_date})"
    
    @staticmethod
    def display_part_details(model_data, part_name, version, part_status_label=None):
        """Display additional details about the selected model part"""
        # Extract relevant information from model data
        creator = model_data.get("creator", "Unknown")
        creation_date = model_data.get("creation_date", "Unknown")
        dimensions = model_data.get("dimensions", {})
        materials = model_data.get("materials", [])
        
        # Format the details
        details = f"Part: {part_name.replace('_', ' ')}\n"
        details += f"Version: {version}\n"
        details += f"Creator: {creator}\n"
        details += f"Created: {creation_date}\n\n"
        
        if dimensions:
            details += f"Dimensions: {dimensions.get('width', 'N/A')}x{dimensions.get('height', 'N/A')}x{dimensions.get('depth', 'N/A')}\n\n"
            
        if materials:
            details += "Materials:\n"
            for material in materials[:3]:  # Show first 3 materials
                details += f"- {material}\n"
            if len(materials) > 3:
                details += f"...and {len(materials) - 3} more\n"
                
        # Update status display if label is provided
        if part_status_label:
            status_text = f"Selected: {part_name.replace('_', ' ')} v{version}"
            part_status_label.config(text=status_text)
            
        return details
    
    @staticmethod
    def find_related_parts(part_base_name, current_ver):
        """Find related parts and other versions of the same part"""
        related_parts = []
        other_versions = []
        
        # Search for related parts and other versions
        spec_pattern = os.path.join(os.getcwd(), "micro_robot_*.json")
        spec_files = glob.glob(spec_pattern)
        
        for path in spec_files:
            name = os.path.basename(path)
            m = re.match(r"(.+)_v(\d+)\.json", name)
            if m:
                file_part_name = m.group(1)
                file_ver = m.group(2)
                
                # Check if it's another version of the same part
                if file_part_name == part_base_name and file_ver != current_ver:
                    other_versions.append((file_ver, path))
                    
                # Check if it's a related part (shares part of the name)
                elif (file_part_name != part_base_name and 
                      (file_part_name in part_base_name or part_base_name in file_part_name)):
                    related_parts.append((file_part_name, file_ver, path))
        
        return other_versions, related_parts


class AgentModeSelector:
    """Helper class for Agent Mode vs PyAutoGen selection with execution style options"""
    
    @staticmethod
    def setup_execution_mode_ui(parent_frame, row_position=0):
        """Set up the execution mode selection UI (Agent Mode vs PyAutoGen) with parallel/sequential options"""
        # Create a StringVar to hold the selection
        execution_mode = tk.StringVar(value="agent_mode")
        execution_style = tk.StringVar(value="sequential")
        
        # Create a LabelFrame for the execution mode selection
        mode_frame = ttk.LabelFrame(parent_frame, text="Execution Mode", padding=5)
        mode_frame.grid(row=row_position, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
          # Add radio buttons for Agent Mode and PyAutoGen (using grid instead of pack)
        ttk.Radiobutton(mode_frame, text="Agent Mode", 
                       variable=execution_mode, value="agent_mode").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="PyAutoGen", 
                       variable=execution_mode, value="pyautogen").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Add execution style options (sequential vs parallel)
        style_frame = ttk.LabelFrame(mode_frame, text="Execution Style", padding=5)
        style_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Radiobutton(style_frame, text="Sequential execution", 
                       variable=execution_style, value="sequential").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(style_frame, text="Parallel execution", 
                       variable=execution_style, value="parallel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Add hardware usage controls
        hw_frame = ttk.Frame(style_frame)
        hw_frame.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(hw_frame, text="Max CPU %:").grid(row=0, column=0, padx=2)
        cpu_limit = tk.StringVar(value="80")
        ttk.Entry(hw_frame, textvariable=cpu_limit, width=3).grid(row=0, column=1, padx=2)
        
        ttk.Label(hw_frame, text="Max RAM %:").grid(row=0, column=2, padx=(10, 2))
        ram_limit = tk.StringVar(value="70")
        ttk.Entry(hw_frame, textvariable=ram_limit, width=3).grid(row=0, column=3, padx=2)
        
        # Add task confirmation options
        confirm_tasks = tk.BooleanVar(value=True)
        ttk.Checkbutton(style_frame, text="Confirm tasks before execution", 
                       variable=confirm_tasks).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
          # Add API key entry for PyAutoGen (only enabled when PyAutoGen is selected)
        api_frame = ttk.Frame(mode_frame)
        api_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        
        api_key = tk.StringVar()
        api_entry = ttk.Entry(api_frame, textvariable=api_key, width=30)
        api_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # Disable API key entry initially if Agent Mode is selected
        if execution_mode.get() == "agent_mode":
            api_entry.config(state="disabled")
        
        # Add trace to execution_mode to enable/disable API key entry
        def on_mode_change(*args):
            if execution_mode.get() == "agent_mode":
                api_entry.config(state="disabled")
            else:
                api_entry.config(state="normal")
        
        execution_mode.trace("w", on_mode_change)
        
        # Enable/disable hardware options based on execution style
        def on_style_change(*args):
            if execution_style.get() == "sequential":
                for widget in hw_frame.winfo_children():
                    widget.config(state="disabled")
            else:
                for widget in hw_frame.winfo_children():
                    widget.config(state="normal")
        
        execution_style.trace("w", on_style_change)
        # Initialize states based on default value
        on_style_change()
        
        return execution_mode, api_key, execution_style, cpu_limit, ram_limit, confirm_tasks
    
    @staticmethod
    def get_agent_execution_parameters(execution_mode, execution_style, cpu_limit, ram_limit, confirm_tasks):
        """Get execution parameters for the selected mode and style"""
        params = {
            "mode": execution_mode.get(),
            "style": execution_style.get(),
            "is_parallel": execution_style.get() == "parallel",
            "is_sequential": execution_style.get() == "sequential",
            "hardware_limits": {
                "cpu_limit": int(cpu_limit.get()) if cpu_limit.get().isdigit() else 80,
                "ram_limit": int(ram_limit.get()) if ram_limit.get().isdigit() else 70,
            },
            "confirm_tasks": confirm_tasks.get()
        }
        
        return params
    

class ProcessControl:
    """Helper class for process control (start/stop) with parallel execution support"""
    
    @staticmethod
    def setup_process_controls(parent_frame, start_callback, stop_callback):
        """Set up the process control UI with start and stop buttons"""
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Start button
        start_button = ttk.Button(control_frame, text="Start Process", command=start_callback)
        start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button (disabled by default)
        stop_button = ttk.Button(control_frame, text="Stop Process", command=stop_callback, state="disabled")
        stop_button.pack(side=tk.LEFT, padx=5)
        
        # Pause button for parallel processes
        pause_button = ttk.Button(control_frame, text="Pause Tasks", state="disabled")
        pause_button.pack(side=tk.LEFT, padx=5)
        
        # Task status indicator
        task_status = ttk.Label(control_frame, text="No active tasks")
        task_status.pack(side=tk.RIGHT, padx=5)
        
        return start_button, stop_button, pause_button, task_status
    
    @staticmethod
    def update_process_status(status_label, process_running, elapsed_time=None, remaining_time=None, foreground="black"):
        """Update the process status display with runtime information"""
        status_text = ""
        
        if process_running:
            status_text = "Process running"
            
            if elapsed_time is not None:
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                status_text += f" (Runtime: {int(hours)}h {int(minutes)}m {int(seconds)}s"
                
                if remaining_time is not None and remaining_time > 0:
                    r_hours, r_remainder = divmod(remaining_time, 3600)
                    r_minutes, r_seconds = divmod(r_remainder, 60)
                    status_text += f", Remaining: {int(r_hours)}h {int(r_minutes)}m {int(r_seconds)}s)"
                else:
                    status_text += ")"
        else:
            status_text = "Process not running"
        
        if status_label:
            try:
                status_label.config(text=status_text, foreground=foreground)
            except Exception:
                # Handle case where status_label might not have config method
                pass
                
        return status_text
    
    @staticmethod
    def setup_task_confirmation_dialog(parent, task_list, confirm_callback):
        """Create a dialog to confirm tasks before execution"""
        dialog = tk.Toplevel(parent)
        dialog.title("Confirm Tasks")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Calculate position to center the dialog
        window_width = 500
        window_height = 400
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create the main dialog content
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select tasks to execute in parallel:").pack(anchor="w", pady=(0, 10))
        
        # Create scrollable list of tasks with checkboxes
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        task_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=task_listbox.yview)
        
        # Insert tasks
        for task in task_list:
            task_listbox.insert(tk.END, task)
        
        # Hardware utilization frame
        hw_frame = ttk.LabelFrame(frame, text="Hardware Management", padding=5)
        hw_frame.pack(fill=tk.X, pady=10)
        
        # CPU usage display
        ttk.Label(hw_frame, text="Current CPU:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        cpu_bar = ttk.Progressbar(hw_frame, length=100)
        cpu_bar.grid(row=0, column=1, padx=5, pady=2)
        cpu_label = ttk.Label(hw_frame, text="0%")
        cpu_label.grid(row=0, column=2, padx=5, pady=2)
        
        # RAM usage display
        ttk.Label(hw_frame, text="Current RAM:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ram_bar = ttk.Progressbar(hw_frame, length=100)
        ram_bar.grid(row=1, column=1, padx=5, pady=2)
        ram_label = ttk.Label(hw_frame, text="0%")
        ram_label.grid(row=1, column=2, padx=5, pady=2)
        
        # Try to update hardware stats if psutil is available
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            ram_percent = psutil.virtual_memory().percent
            
            cpu_bar["value"] = cpu_percent
            cpu_label.config(text=f"{cpu_percent:.1f}%")
            
            ram_bar["value"] = ram_percent
            ram_label.config(text=f"{ram_percent:.1f}%")
        except ImportError:
            ttk.Label(hw_frame, text="Install psutil for hardware monitoring", 
                     foreground="red").grid(row=2, column=0, columnspan=3, pady=5)
        
        # Task management options
        options_frame = ttk.Frame(frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        auto_manage = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-manage resource allocation", 
                       variable=auto_manage).pack(anchor="w")
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Execute Selected", 
                  command=lambda: confirm_callback(
                      [task_listbox.get(idx) for idx in task_listbox.curselection()],
                      auto_manage.get()
                  )).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Select all button
        ttk.Button(button_frame, text="Select All", 
                  command=lambda: task_listbox.selection_set(0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        return dialog
        
    @staticmethod
    def stop_process(app):
        """Stop the currently running process"""
        if hasattr(app, 'process_running') and app.process_running and hasattr(app, 'process'):
            try:
                # Update status
                if hasattr(app, 'process_status_label'):
                    app.process_status_label.config(text="Stopping process...", foreground="blue")
                
                # Kill process
                if hasattr(app.process, 'terminate'):
                    app.process.terminate()
                elif hasattr(app.process, 'kill'):
                    app.process.kill()
                
                # Update status
                app.process_running = False
                app.process_start_time = None
                
                # Cancel timer if active
                if hasattr(app, 'timer_id') and app.timer_id:
                    app.root.after_cancel(app.timer_id)
                    app.timer_id = None
                    
                # Update status
                if hasattr(app, 'process_status_label'):
                    app.process_status_label.config(text="Process stopped", foreground="blue")
                    
                # Re-enable start button, disable stop button
                if hasattr(app, 'start_button'):
                    app.start_button.config(state="normal")
                if hasattr(app, 'stop_button'):
                    app.stop_button.config(state="disabled")
                    
            except Exception as e:
                if hasattr(app, 'process_status_label'):
                    app.process_status_label.config(text=f"Error stopping process: {str(e)}", foreground="red")
    
    @staticmethod
    def get_hardware_usage():
        """Get current hardware usage statistics"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram_percent = psutil.virtual_memory().percent
            
            # Get GPU usage if available
            gpu_percent = None
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_percent = gpus[0].load * 100
            except:
                pass
                
            return {
                "cpu": cpu_percent,
                "ram": ram_percent,
                "gpu": gpu_percent
            }
        except ImportError:
            return None


class TaskCompletion:
    """Helper class for task completion marking without popups"""
    
    @staticmethod
    def mark_task_completed(task_manager, task_id, task_list_widget, status_label):
        """Mark a task as completed and update the GUI without popups"""
        try:
            # Call task manager to mark the task as completed
            success = task_manager.mark_task_completed(task_id)
            
            if success:
                # Update the status label
                status_label.config(text=f"Task marked as completed", foreground="green")
                
                # Update the task list widget (if provided)
                if task_list_widget:
                    # Refresh the task list
                    TaskCompletion.refresh_task_list(task_manager, task_list_widget)
                
                return True
            else:
                # Update status with error
                status_label.config(text="Error: Failed to mark task as completed", foreground="red")
                return False
                
        except Exception as e:
            # Update status with exception
            status_label.config(text=f"Error: {str(e)}", foreground="red")
            return False
    
    @staticmethod
    def refresh_task_list(task_manager, task_list_widget):
        """Refresh the task list widget with updated task status"""
        # Clear current items
        task_list_widget.delete(0, tk.END)
        
        # Get updated task list
        tasks = task_manager.get_all_tasks()
        
        # Add tasks to the list with appropriate formatting
        for task in tasks:
            task_text = task.get("title", "Untitled Task")
            if task.get("completed", False):
                task_text = "✓ " + task_text
            else:
                task_text = "□ " + task_text
                
            task_list_widget.insert(tk.END, task_text)
            
            # Set tag for completed tasks (for styling)
            if task.get("completed", False):
                task_list_widget.itemconfig(tk.END, {'foreground': 'green'})


class ModelVerification:
    """Helper class for verifying model status before starting a session"""
    
    @staticmethod
    def is_model_completed(version):
        """Check if a model version is already completed"""
        # Check if requirements met flag exists
        if os.path.exists(f"requirements_met_v{version}.flag"):
            return True
            
        # Check if simulation completed flag exists
        if os.path.exists(f"simulation_complete_v{version}.flag"):
            return True
            
        return False
    
    @staticmethod
    def verify_model_status(version, development_mode, parent_window):
        """Verify model status and show warning if needed"""
        # Only check for completed models if in refined_model or versioned_model mode
        if development_mode in ["refined_model", "versioned_model"]:
            if ModelVerification.is_model_completed(version):
                # Show warning dialog
                response = messagebox.askyesno(
                    "Model Already Completed",
                    f"Model version {version} appears to be already completed.\n\n"
                    "Do you want to continue anyway?\n\n"
                    "- Click 'Yes' if you believe the model is not finished\n"
                    "- Click 'No' to abort",
                    parent=parent_window
                )
                return response
        
        # If model is not completed or in testing mode, allow to proceed
        return True


class ParallelTaskManager:
    """Manages parallel task execution in Agent Mode"""
    
    def __init__(self, parent_app):
        """Initialize the parallel task manager"""
        self.parent = parent_app
        self.tasks = []
        self.running_tasks = {}
        self.completed_tasks = []
        self.cpu_limit = 80
        self.ram_limit = 70
        self.confirm_tasks = True
        self.auto_manage = True
        
    def discover_tasks(self):
        """Discover available tasks based on project structure"""
        tasks = []
        
        # Check for agent folders with task files
        agent_folders = [d for d in os.listdir() if os.path.isdir(d) and d.startswith("agent")]
        for folder in agent_folders:
            task_files = [f for f in os.listdir(folder) if f.endswith(".py") and not f.startswith("__")]
            for task_file in task_files:
                tasks.append(f"{folder}/{task_file}")
        
        # Check for simulation scripts
        sim_scripts = [f for f in os.listdir() if f.endswith(".py") and "simulation" in f.lower()]
        tasks.extend(sim_scripts)
        
        # Check for blend scripts
        blend_scripts = [f for f in os.listdir() if f.endswith(".py") and "blend" in f.lower()]
        tasks.extend(blend_scripts)
        
        # Add specific project tasks
        if os.path.exists("agent1_part1.py"):
            tasks.append("agent1_part1.py")
        if os.path.exists("model_evaluation.py"):
            tasks.append("model_evaluation.py")
        
        return tasks
    
    def confirm_task_selection(self, all_tasks):
        """Show dialog to confirm which tasks to run in parallel"""
        if not self.confirm_tasks:
            # If confirmation is disabled, run all tasks
            return all_tasks
            
        selected_tasks = []
        
        # Create and show the confirmation dialog
        def handle_confirmation(tasks, auto):
            nonlocal selected_tasks
            self.auto_manage = auto
            selected_tasks = tasks
            dialog.destroy()
        
        dialog = ProcessControl.setup_task_confirmation_dialog(
            self.parent.root,
            all_tasks,
            handle_confirmation
        )
        
        # Wait for the dialog to be closed
        self.parent.root.wait_window(dialog)
        
        return selected_tasks
    
    def start_parallel_tasks(self, tasks):
        """Start the specified tasks in parallel"""
        if not tasks:
            self.parent.process_status_label.config(
                text="No tasks selected for execution",
                foreground="blue"
            )
            return False
        
        self.parent.process_status_label.config(
            text=f"Starting {len(tasks)} tasks in parallel...",
            foreground="blue"
        )
        
        # Initialize process tracking
        self.parent.process_running = True
        self.parent.process_start_time = datetime.datetime.now()
        self.running_tasks = {}
        
        # Start each task in a separate process
        import subprocess
        for task in tasks:
            try:
                # Create environment variables for the task
                env = os.environ.copy()
                env["VSCODE_AGENT_MODE"] = "true"
                env["TIME_LIMIT_HOURS"] = self.parent.time_limit_hours.get()
                env["TIME_LIMIT_MINUTES"] = self.parent.time_limit_minutes.get()
                env["AUTO_CONTINUE"] = "1" if self.parent.auto_continue.get() else "0"
                
                # Start the process
                process = subprocess.Popen(
                    [sys.executable, task],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                self.running_tasks[task] = {
                    "process": process,
                    "start_time": datetime.datetime.now(),
                    "status": "running"
                }
                
            except Exception as e:
                self.parent.process_status_label.config(
                    text=f"Error starting task {task}: {str(e)}",
                    foreground="red"
                )
        
        # Update UI
        self.parent.start_button.config(state="disabled")
        self.parent.stop_button.config(state="normal")
        
        # Start monitoring task progress
        self.start_task_monitoring()
        
        return True
    
    def start_task_monitoring(self):
        """Start monitoring task progress"""
        self.monitor_tasks()
    
    def monitor_tasks(self):
        """Monitor running tasks and update status"""
        if not self.parent.process_running:
            return
        
        # Check each running task
        completed = []
        for task, info in self.running_tasks.items():
            process = info["process"]
            return_code = process.poll()
            
            if return_code is not None:
                # Task has finished
                stdout, stderr = process.communicate()
                
                info["status"] = "completed" if return_code == 0 else "error"
                info["return_code"] = return_code
                info["stdout"] = stdout
                info["stderr"] = stderr
                info["end_time"] = datetime.datetime.now()
                
                completed.append(task)
                
                # Add to completed tasks
                self.completed_tasks.append(info)
        
        # Remove completed tasks from running
        for task in completed:
            del self.running_tasks[task]
        
        # Update status display
        if self.running_tasks:
            num_running = len(self.running_tasks)
            num_completed = len(self.completed_tasks)
            total = num_running + num_completed
            
            self.parent.process_status_label.config(
                text=f"Running: {num_running} tasks, Completed: {num_completed} of {total}",
                foreground="green"
            )
            
            # Schedule next update
            self.parent.root.after(1000, self.monitor_tasks)
        else:
            # All tasks completed
            self.parent.process_status_label.config(
                text=f"All {len(self.completed_tasks)} tasks completed",
                foreground="green"
            )
            
            # Calculate success rate
            successful = len([t for t in self.completed_tasks if t["status"] == "completed"])
            success_rate = (successful / len(self.completed_tasks)) * 100 if self.completed_tasks else 0
            
            self.parent.process_timer_label.config(
                text=f"Success rate: {success_rate:.1f}% ({successful}/{len(self.completed_tasks)})"
            )
            
            # Reset process state
            self.parent.process_running = False
            self.parent.start_button.config(state="normal")
            self.parent.stop_button.config(state="disabled")
    
    def stop_all_tasks(self):
        """Stop all running tasks"""
        for task, info in list(self.running_tasks.items()):
            try:
                process = info["process"]
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    # Add termination info
                    info["status"] = "terminated"
                    info["end_time"] = datetime.datetime.now()
                    # Move to completed tasks
                    self.completed_tasks.append(info)
            except Exception as e:
                print(f"Error stopping task {task}: {str(e)}")
        
        # Update status display
        if hasattr(self.parent, 'process_status_label'):
            self.parent.process_status_label.config(
                text=f"Stopped {len(self.running_tasks)} running tasks",
                foreground="blue"
            )
        
        # Clear running tasks
        self.running_tasks = {}
        
        # Reset UI state
        if hasattr(self.parent, 'process_running'):
            self.parent.process_running = False
        if hasattr(self.parent, 'start_button'):
            self.parent.start_button.config(state="normal")
        if hasattr(self.parent, 'stop_button'):
            self.parent.stop_button.config(state="disabled")
            
        return True


def implement_enhancements(main_app):
    """Implement the GUI enhancements in the main application"""
    # Set up execution mode UI if not already present
    if hasattr(main_app, 'main_tab'):
        # Add execution mode selector at the top of the main tab (Agent vs PyAutoGen)
        if not hasattr(main_app, 'execution_mode'):
            exec_mode_frame = ttk.Frame(main_app.main_tab)
            exec_mode_frame.pack(fill=tk.X, padx=5, pady=5, before=main_app.main_tab.winfo_children()[0])
            
            # Create mode selector
            execution_mode, api_key, execution_style, cpu_limit, ram_limit, confirm_tasks = \
                AgentModeSelector.setup_execution_mode_ui(exec_mode_frame)
            
            # Store variables in the main app
            main_app.execution_mode = execution_mode
            main_app.api_key = api_key 
            main_app.execution_style = execution_style
            main_app.cpu_limit = cpu_limit
            main_app.ram_limit = ram_limit
            main_app.confirm_tasks = confirm_tasks
            
            # Update start_new_session to check for execution mode
            original_start_session = getattr(main_app, 'start_new_session', None)
            
            def enhanced_start_session():
                """Enhanced start session that handles different execution modes"""
                # Get execution parameters
                params = AgentModeSelector.get_agent_execution_parameters(
                    execution_mode, execution_style, cpu_limit, ram_limit, confirm_tasks
                )
                
                # Handle parallel execution
                if params["is_parallel"]:
                    # Initialize parallel task manager if needed
                    if not hasattr(main_app, 'parallel_task_manager'):
                        main_app.parallel_task_manager = ParallelTaskManager(main_app)
                        main_app.parallel_task_manager.cpu_limit = params["hardware_limits"]["cpu_limit"]
                        main_app.parallel_task_manager.ram_limit = params["hardware_limits"]["ram_limit"]
                        main_app.parallel_task_manager.confirm_tasks = params["confirm_tasks"]
                    
                    # Discover tasks
                    tasks = main_app.parallel_task_manager.discover_tasks()
                    
                    # Show task confirmation dialog
                    selected_tasks = main_app.parallel_task_manager.confirm_task_selection(tasks)
                    
                    # Start tasks
                    if selected_tasks:
                        main_app.parallel_task_manager.start_parallel_tasks(selected_tasks)
                    
                # Regular sequential execution
                else:
                    # Call original start session method
                    if original_start_session:
                        original_start_session()
            
            # Replace the original method
            if original_start_session:
                main_app.start_new_session = enhanced_start_session
                
    # Enhance ProcessControl with parallel process handling
    if hasattr(main_app, 'process_frame'):
        # Set up enhanced process controls
        control_frame = ttk.Frame(main_app.process_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Set up callbacks
        def start_callback():
            main_app.start_new_session()
            
        def stop_callback():
            if hasattr(main_app, 'execution_style') and main_app.execution_style.get() == "parallel":
                # Stop parallel tasks
                if hasattr(main_app, 'parallel_task_manager'):
                    main_app.parallel_task_manager.stop_all_tasks()
            else:
                # Use existing stop process
                ProcessControl.stop_process(main_app)
        
        # Replace existing buttons if they exist
        if hasattr(main_app, 'start_button'):
            main_app.start_button.destroy()
        if hasattr(main_app, 'stop_button'):
            main_app.stop_button.destroy()
            
        # Set up enhanced process controls
        main_app.start_button, main_app.stop_button, main_app.pause_button, main_app.task_status = \
            ProcessControl.setup_process_controls(control_frame, start_callback, stop_callback)
    
    # Customize the process display behavior
    if hasattr(main_app, 'update_process_timer'):
        original_timer_update = main_app.update_process_timer
        
        def enhanced_timer_update():
            """Enhanced timer update that handles parallel execution"""
            if not main_app.process_running:
                if hasattr(main_app, 'process_status_label'):
                    main_app.process_status_label.config(text="Process not running", foreground="blue")
                return
                
            # Check if we're in parallel mode
            is_parallel = hasattr(main_app, 'execution_style') and main_app.execution_style.get() == "parallel"
            
            if is_parallel and hasattr(main_app, 'parallel_task_manager'):
                # Parallel task monitoring is handled by the task manager
                pass  # Monitor function is already scheduled by the task manager
            else:
                # Use original timer update for sequential execution
                original_timer_update()
        
        # Replace the timer update method
        main_app.update_process_timer = enhanced_timer_update
        
    return main_app
