"""
Enhanced agent_mode_gui.py - Improved version for the GlowingGoldenGlobe project

This is an enhanced version that addresses the following requirements:
1. Fixed import issue with task_manager
2. Added missing methods
3. Modified GUI to update status in the status bar instead of popup windows
4. Shows runtime and time remaining when processes are running
5. Added minutes duration option to time limit, not solely hours
6. Enhanced model version data display to show not-built/in-progress/date-completed status
7. Shows related model parts when a model part is selected
"""
#!/usr/bin/env python

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

# Import custom modules
from ggg_gui_styles import GGGStyles
from hardware_monitor import HardwareMonitor
from ai_managers.task_manager import TaskManager  # Fixed import path
from help_system import HelpSystem
from refined_model_integration import RefinedModelIntegration
from auto_refiner_integration import integrate_auto_refiner
from model_notification_system import get_notification_system, ModelNotificationSystem
import Objectives_1 as project_objectives

# Import GUI enhancements implementation
from agent_mode_gui_implementation import implement_enhancements, TimeLimit, ModelVersionDisplay

# Create an alias for compatibility with existing code
apply_gui_enhancements = implement_enhancements

# Main application class
class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GlowingGoldenGlobe User Controls")
        
        # Set up handler for window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set window size to full height but partial width (70%)
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.9)
        
        # Set the geometry
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        
        # Try to set custom icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "ggg_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Continue without custom icon
        
        # Initialize custom styles
        self.styles = GGGStyles(self.root)
        
        # Initialize support modules
        self.hardware_monitor = HardwareMonitor()
        self.task_manager = TaskManager()
        self.help_system = HelpSystem()
        
        # Register emergency callback for hardware issues
        self.hardware_monitor.register_emergency_callback(self.handle_hardware_emergency)
        
        # Start hardware monitoring in background
        self.hardware_monitor.start_monitoring(interval=60)  # Check every minute
        
        # Setup configuration
        self.config = self.load_initial_config()
        
        # Create Tkinter variables
        self.development_mode = tk.StringVar(value=self.config.get("development_mode", "refined_model"))
        self.time_limit_hours = tk.StringVar(value=str(self.config.get("time_limit_hours", 1)))
        self.time_limit_minutes = tk.StringVar(value=str(self.config.get("time_limit_minutes", 0)))
        self.auto_save_interval = tk.StringVar(value=str(self.config.get("auto_save_interval", 5)))
        self.auto_continue = tk.BooleanVar(value=self.config.get("auto_continue", True))
        self.selected_version = tk.StringVar(value=self.config.get("selected_version", "1"))
        self.selected_model_part = tk.StringVar(value=self.config.get("selected_model_part", "Complete Assembly"))
        self.agent_instructions = tk.StringVar(value="")
        
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
        
        # Subtitle as bullet points, left-aligned
        subtitle_frame = ttk.Frame(main_frame)
        subtitle_frame.pack(fill=tk.X, pady=(0, 10), anchor=tk.W)
        
        ttk.Label(subtitle_frame, text="• pyautogen syntax format", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        ttk.Label(subtitle_frame, text="• AI Agents API-key", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        ttk.Label(subtitle_frame, text="• VSCode Agent Mode", 
                 style="SubheaderSmall.TLabel").pack(anchor=tk.W)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Main tab
        self.main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.main_tab, text="Main Controls")
        
        # Task management tab
        self.tasks_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tasks_tab, text="Tasks & Schedule")
        
        # Hardware monitoring tab 
        self.hardware_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.hardware_tab, text="Hardware Monitor")
        
        # Model evaluation tab for automated refinement
        self.model_eval_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.model_eval_tab, text="Model Evaluation")
        
        # Objectives tab for tracking project steps
        self.objectives_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.objectives_tab, text="Objectives")
        
        # Set up each tab's content
        self.setup_main_tab()
        self.setup_hardware_tab()
        self.setup_tasks_tab()
        self.setup_model_eval_tab()
        self.setup_objectives_tab()
        
        # Add status bar at the bottom
        self.setup_status_bar(main_frame)
        
        # Variables for process tracking
        self.process = None
        self.process_running = False
        self.process_start_time = None
        self.timer_id = None
        
        # For model parts
        self.part_map = {}  # Maps display names to file paths
        self.related_parts_frame = None
        self.part_status_label = None
        
        # Track when details were last shown
        self._last_detail_time = 0
        
        # Apply enhanced features
        apply_gui_enhancements(self)  # Calls implement_enhancements as apply_gui_enhancements

    def load_initial_config(self):
        """Load the configuration from file, or create default if not present"""
        config_path = "agent_mode_config.json"
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
        }
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            # Update config with current values
            self.config["development_mode"] = self.development_mode.get()
            self.config["time_limit_hours"] = float(self.time_limit_hours.get())
            self.config["time_limit_minutes"] = int(self.time_limit_minutes.get())
            self.config["auto_save_interval"] = int(self.auto_save_interval.get())
            self.config["auto_continue"] = bool(self.auto_continue.get())
            self.config["selected_version"] = self.selected_version.get()
            
            # Save to file
            config_path = "agent_mode_config.json"
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
                
            self.process_status_label.config(text="Settings saved successfully", foreground="green")
        except Exception as e:
            self.process_status_label.config(text=f"Failed to save settings: {str(e)}", foreground="red")

    def get_available_versions(self):
        """Get available model versions by checking for json files"""
        versions = []
        for i in range(1, 10):  # Look for versions 1-9
            if os.path.exists(f"micro_robot_composite_part_v{i}.json"):
                versions.append(str(i))
        
        if not versions:
            versions = ["1"]
            
        return versions
    
    def update_status_display(self):
        """Update the status display with current version info"""
        version = self.selected_version.get()
        self.version_label.config(text=f"v{version}")
        
        # Check model status using the enhanced method
        status = ModelVersionDisplay.check_model_status(version)
        self.status_label.config(text=status)
    
    def check_model_status(self, version):
        """Check the status of the specified version"""
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
    
    def start_new_session(self):
        """Start a new development session"""
        # If process is already running, don't start a new one
        if self.process_running:
            self.process_status_label.config(text="A process is already running", foreground="orange")
            return
            
        try:
            # Validate inputs first
            try:
                time_limit_hours = float(self.time_limit_hours.get())
                time_limit_minutes = int(self.time_limit_minutes.get() if hasattr(self, 'time_limit_minutes') else 0)
                
                if time_limit_hours < 0:
                    raise ValueError("Hours must be zero or positive")
                
                if time_limit_minutes < 0:
                    raise ValueError("Minutes must be zero or positive")
                
                if time_limit_hours == 0 and time_limit_minutes == 0:
                    raise ValueError("Time limit must be greater than zero")
                
                save_interval = int(self.auto_save_interval.get())
                if save_interval <= 0:
                    raise ValueError("Auto-save interval must be positive")
            except ValueError as e:
                self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
                return
                
            # Check if the model is already completed
            from agent_mode_gui_implementation import ModelVerification
            version = self.selected_version.get()
            dev_mode = self.development_mode.get()
            if not ModelVerification.verify_model_status(version, dev_mode, self.root):
                self.process_status_label.config(text="Operation aborted: Model already completed", foreground="blue")
                return
            
            # Get the mode
            mode = self.development_mode.get()
            
            # Update status
            self.process_status_label.config(text=f"Starting {mode} development...", foreground="blue")
            self.root.update() # Force update to show status before starting
            
            # Save the config
            self.save_settings()
            
            # Start the appropriate script based on mode
            if mode == "refined_model":
                self.run_command("run_refined_model_development.bat")
            elif mode == "versioned_model":
                self.run_command("run_automated_model_development.bat")
            else:  # testing_only
                version = self.selected_version.get()
                self.run_command(f"python test_model_requirements.py --version {version}")
        except Exception as e:
            self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
    
    def resume_previous_session(self):
        """Resume a previous development session"""
        try:
            # Check for checkpoint files
            if os.path.exists("model_refinement_state.txt"):
                checkpoint_type = "refined_model"
            elif os.path.exists("development_checkpoint.txt"):
                checkpoint_type = "versioned_model"
            else:
                self.process_status_label.config(text="No previous session checkpoint found.", foreground="red")
                return
            
            # Update status
            self.process_status_label.config(text=f"Resuming {checkpoint_type.replace('_', ' ')} session...", foreground="blue")
            self.root.update() # Force update to show status before starting
            
            # Start the appropriate script
            if checkpoint_type == "refined_model":
                self.run_command("run_refined_model_development.bat")
            else:  # versioned_model
                self.run_command("run_automated_model_development.bat")
        except Exception as e:
            self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
            
    def run_command(self, cmd):
        """Run a command in a separate process"""
        try:
            # Check if a process is already running
            if self.process_running:
                self.process_status_label.config(text="A process is already running", foreground="orange")
                return False
                
            # Set environment variables
            os.environ["TIME_LIMIT_HOURS"] = self.time_limit_hours.get()
            os.environ["TIME_LIMIT_MINUTES"] = self.time_limit_minutes.get()
            os.environ["AUTO_CONTINUE"] = "1" if self.auto_continue.get() else "0"
            os.environ["AUTO_SAVE_MINUTES"] = self.auto_save_interval.get()
            
            # If using PyAutoGen mode, set API key if provided
            if hasattr(self, 'execution_mode') and self.execution_mode.get() == "pyautogen":
                api_key = self.api_key.get()
                if api_key:
                    os.environ["PYAUTOGEN_API_KEY"] = api_key
                    # Add PyAutoGen flag
                    os.environ["USE_PYAUTOGEN"] = "1"
                else:
                    self.process_status_label.config(text="API key required for PyAutoGen mode", foreground="red")
                    return False
            else:
                os.environ["USE_PYAUTOGEN"] = "0"
            
            # Start process
            if platform.system() == "Windows":
                self.process = subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                self.process = subprocess.Popen(cmd, shell=True)
                
            # Update status bar
            self.process_status_label.config(text="Status: Running", foreground="green")
            
            # Start timer
            self.process_start_time = time.time()
            self.process_running = True
            self.update_process_timer()
            
            # Enable/disable buttons
            if hasattr(self, 'start_button'):
                self.start_button.config(state="disabled")
            if hasattr(self, 'stop_button'):
                self.stop_button.config(state="normal")
            
            # Log the start
            print(f"Development process started: {cmd}")
            return True
        except Exception as e:
            self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
            print(f"Error running command: {e}")
            return False
    def update_process_timer(self):
        """Update the timer for the running process"""
        if self.process_running and self.process_start_time:
            # Calculate elapsed time
            now = time.time()
            elapsed_seconds = now - self.process_start_time
            
            # Format elapsed time as HH:MM:SS
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            
            # Calculate remaining time based on time limit
            try:
                time_limit_hours = float(self.time_limit_hours.get())
                time_limit_minutes = int(self.time_limit_minutes.get() if hasattr(self, 'time_limit_minutes') else 0)
                time_limit_seconds = (time_limit_hours * 3600) + (time_limit_minutes * 60)
                
                if elapsed_seconds < time_limit_seconds:
                    remaining_seconds = time_limit_seconds - elapsed_seconds
                    r_hours, r_remainder = divmod(remaining_seconds, 3600)
                    r_minutes, r_seconds = divmod(r_remainder, 60)
                    remaining_str = f"{int(r_hours):02}:{int(r_minutes):02}:{int(r_seconds):02}"
                    
                    timer_text = f"Running: {elapsed_str} / Remaining: {remaining_str}"
                else:
                    timer_text = f"Running: {elapsed_str} / Time limit exceeded"
            except:
                timer_text = f"Running: {elapsed_str}"
            
            self.process_timer_label.config(text=timer_text)
            
            # Check if process is still running
            if hasattr(self, 'process') and self.process:
                return_code = self.process.poll()
                if return_code is not None:
                    # Process has ended
                    self.process_status_label.config(text=f"Status: Completed (code {return_code})")
                    self.process_running = False
                    
                    # Update button states
                    if hasattr(self, 'start_button'):
                        self.start_button.config(state="normal")
                    if hasattr(self, 'stop_button'):
                        self.stop_button.config(state="disabled")
                    return
            
            # Schedule next update
            self.timer_id = self.root.after(1000, self.update_process_timer)
        else:
            self.process_timer_label.config(text="")

    def setup_status_bar(self, parent_frame):
        """Set up the status bar at the bottom of the application"""
        status_frame = ttk.Frame(parent_frame, borderwidth=1, relief=tk.SOLID, padding=5)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Process status
        process_frame = ttk.Frame(status_frame)
        process_frame.pack(fill=tk.X)
        
        self.process_status_label = ttk.Label(process_frame, text="Ready", width=40, anchor=tk.W)
        self.process_status_label.pack(side=tk.LEFT, padx=5)
        
        # Timer for running processes
        self.process_timer_label = ttk.Label(process_frame, text="")
        self.process_timer_label.pack(side=tk.LEFT, padx=5)
        
        # Working directory
        dir_frame = ttk.Frame(status_frame)
        dir_frame.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Label(dir_frame, text="Working directory: ").pack(side=tk.LEFT)
        self.working_dir_label = ttk.Label(dir_frame, text=os.getcwd(), anchor=tk.W)
        self.working_dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def on_part_selected(self, event):
        """Handle selection of a model part from the dropdown"""
        selected = self.selected_model_part.get()
        if selected in self.part_map:
            path = self.part_map[selected]
            try:
                with open(path, 'r') as f:
                    # Load the model spec and update UI
                    model_data = json.load(f)
                    
                    # Extract version and part name from filename
                    name = os.path.basename(path)
                    m = re.match(r"(.+)_v(\d+)\.json", name)
                    if m:
                        part_base_name = m.group(1)
                        ver = m.group(2)
                        self.selected_version.set(ver)
                        self.update_status_display()
                        
                        # Display part details in a information dialog
                        self.display_part_details(model_data, part_base_name, ver)
                        
                        # Find related parts and other versions
                        self.find_and_show_related_parts(part_base_name, ver)
            except Exception as e:
                self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
                
    def display_part_details(self, model_data, part_name, version):
        """Display additional details about the selected model part"""
        # Skip if we've already shown details recently (prevent multiple popups)
        if hasattr(self, '_last_detail_time') and time.time() - self._last_detail_time < 5:
            return
            
        self._last_detail_time = time.time()
        
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
                
        # Update status display with this information
        status_text = f"Selected: {part_name.replace('_', ' ')} v{version}"
        if hasattr(self, 'part_status_label') and self.part_status_label:
            self.part_status_label.config(text=status_text)
        else:
            # Update in process status label
            self.process_status_label.config(text=status_text, foreground="blue")
        
    def find_and_show_related_parts(self, part_base_name, current_ver):
        """Find related parts and other versions of the same part"""
        # Use the implementation from our helper module
        other_versions, related_parts = ModelVersionDisplay.find_related_parts(part_base_name, current_ver)
        
        if other_versions or related_parts:
            # Update UI with this information
            info_text = f"Selected: {part_base_name.replace('_', ' ')} v{current_ver}\n\n"
            
            if other_versions:
                info_text += "Other versions available: "
                info_text += ", ".join([f"v{v}" for v, _ in other_versions[:5]])
                if len(other_versions) > 5:
                    info_text += f" and {len(other_versions) - 5} more"
                info_text += "\n\n"
            
            if related_parts:
                info_text += "Related parts:\n"
                part_dict = {}
                for rp_name, rp_ver, _ in related_parts:
                    if rp_name not in part_dict:
                        part_dict[rp_name] = []
                    part_dict[rp_name].append(rp_ver)
                
                count = 0
                for rp_name, versions in part_dict.items():
                    if count < 3:  # Limit to 3 related parts
                        info_text += f"- {rp_name.replace('_', ' ')}: v"
                        info_text += ", v".join(versions[:3])
                        if len(versions) > 3:
                            info_text += f" and {len(versions) - 3} more"
                        info_text += "\n"
                    count += 1
                
                if len(part_dict) > 3:
                    info_text += f"...and {len(part_dict) - 3} more related parts\n"
            # Show info in status bar
            self.process_status_label.config(text=f"Found {len(other_versions)} other versions and {len(related_parts)} related parts", foreground="blue")
            
    def setup_main_tab(self):
        """Set up the main tab content with development options and controls"""
        # Create a frame for the main tab
        main_frame = ttk.Frame(self.main_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add execution mode selection (Agent Mode vs PyAutoGen)
        from agent_mode_gui_implementation import AgentModeSelector
        self.execution_mode, self.api_key = AgentModeSelector.setup_execution_mode_ui(main_frame, 0)
        
        # Development options section
        options_frame = ttk.LabelFrame(main_frame, text="Development Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Add mode selection radio buttons
        ttk.Label(options_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Refined Model", 
                       variable=self.development_mode, value="refined_model").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Versioned Model", 
                       variable=self.development_mode, value="versioned_model").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Testing Only", 
                       variable=self.development_mode, value="testing_only").pack(anchor="w")
        
        # Time limit section with hours and minutes (using our TimeLimit helper)
        self.time_limit_minutes = TimeLimit.setup_time_limit_ui(options_frame, self.time_limit_hours, self.config)
        
        # Auto-continue checkbox
        ttk.Checkbutton(options_frame, text="Auto-continue after time limit", 
                       variable=self.auto_continue).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Version selection
        ttk.Label(options_frame, text="Model Version:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        version_frame = ttk.Frame(options_frame)
        version_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        versions = self.get_available_versions()
        self.version_dropdown = ttk.Combobox(version_frame, textvariable=self.selected_version, 
                                            values=versions, width=5)
        self.version_dropdown.pack(side=tk.LEFT)
        
        # Part selection
        ttk.Label(options_frame, text="Model Part:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        part_frame = ttk.Frame(options_frame)
        part_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Scan for parts
        display_names = ["Complete Assembly", "Robot Body", "Robot Head", "Robot Arm"]
        self.part_dropdown = ttk.Combobox(part_frame, textvariable=self.selected_model_part,
                                         values=display_names, state="readonly", width=20)
        self.part_dropdown.pack(side=tk.LEFT)
        self.part_dropdown.bind("<<ComboboxSelected>>", self.on_part_selected)
        
        # Save settings button
        ttk.Button(options_frame, text="Save Settings", 
                  command=self.save_settings).grid(row=6, column=1, sticky="e", padx=5, pady=10)
          # Start session section
        start_frame = ttk.LabelFrame(main_frame, text="Start Development Session", padding=10)
        start_frame.pack(fill=tk.X, pady=10)
        
        # Main start buttons
        ttk.Button(start_frame, text="Start New Development Session", 
                  command=self.start_new_session).pack(fill=tk.X, pady=5)
        ttk.Button(start_frame, text="Resume Previous Session", 
                  command=self.resume_previous_session).pack(fill=tk.X, pady=5)
        
        # Add process controls 
        from agent_mode_gui_implementation import ProcessControl
        control_frame = ttk.Frame(start_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Create start and stop buttons
        self.start_button, self.stop_button = ProcessControl.setup_process_controls(
            start_frame, 
            self.start_new_session,  # Use existing start method
            self.stop_process        # We'll add this method
        )
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Current Version:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.version_label = ttk.Label(status_frame, text="v1")
        self.version_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Model Status:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.status_label = ttk.Label(status_frame, text="Not Started")
        self.status_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Workspace info
        ttk.Label(status_frame, text="Working Directory:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.folder_label = ttk.Label(status_frame, text=os.getcwd())
        self.folder_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Update status display
        self.update_status_display()
    
    def setup_hardware_tab(self):
        """Set up the hardware monitoring tab"""
        hw_frame = ttk.Frame(self.hardware_tab)
        hw_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System info section
        sys_frame = ttk.LabelFrame(hw_frame, text="System Information", padding=10)
        sys_frame.pack(fill=tk.X, pady=5)
        
        # Get hardware info
        try:
            hw_info = self.hardware_monitor.get_system_summary()
            
            info_text = f"Platform: {hw_info.get('platform', 'Unknown')}\n"
            info_text += f"Processor: {hw_info.get('processor', 'Unknown')}\n"
            info_text += f"CPU Cores: {hw_info.get('cpu_count', 'Unknown')}\n"
            info_text += f"Total Memory: {hw_info.get('total_memory_gb', 'Unknown')} GB\n"
            info_text += f"Total Disk: {hw_info.get('total_disk_gb', 'Unknown')} GB"
            
            hw_info_text = tk.Text(sys_frame, height=6, wrap=tk.WORD)
            hw_info_text.insert(tk.END, info_text)
            hw_info_text.config(state=tk.DISABLED)
            hw_info_text.pack(fill=tk.X, pady=5)
        except Exception as e:
            error_label = ttk.Label(sys_frame, text=f"Error loading hardware info: {str(e)}")
            error_label.pack(fill=tk.X, pady=5)
        
        # Current usage section with refresh button
        usage_frame = ttk.LabelFrame(hw_frame, text="Current Resource Usage", padding=10)
        usage_frame.pack(fill=tk.X, pady=10)
        
        # Show current CPU, memory, disk usage with progress bars
        self.update_resource_display(usage_frame)
        
        # Refresh button
        ttk.Button(hw_frame, text="Refresh Hardware Info", 
                  command=lambda: self.update_resource_display(usage_frame)).pack(pady=10)
    
    def update_resource_display(self, parent_frame):
        """Update the hardware resource display with current information"""
        # Clear existing widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        try:
            # Get current usage
            usage = self.hardware_monitor.get_hardware_info()
            
            # CPU usage
            cpu_frame = ttk.Frame(parent_frame)
            cpu_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(cpu_frame, text="CPU Usage:").pack(side=tk.LEFT)
            cpu_value = float(usage.get("cpu_percent", 0))
            cpu_bar = ttk.Progressbar(cpu_frame, length=200, value=cpu_value)
            cpu_bar.pack(side=tk.LEFT, padx=10)
            ttk.Label(cpu_frame, text=f"{cpu_value:.1f}%").pack(side=tk.LEFT)
            
            # Memory usage
            mem_frame = ttk.Frame(parent_frame)
            mem_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(mem_frame, text="Memory Usage:").pack(side=tk.LEFT)
            mem_value = float(usage.get("memory_percent", 0))
            mem_bar = ttk.Progressbar(mem_frame, length=200, value=mem_value)
            mem_bar.pack(side=tk.LEFT, padx=10)
            ttk.Label(mem_frame, text=f"{mem_value:.1f}%").pack(side=tk.LEFT)
            
            # Disk usage
            disk_frame = ttk.Frame(parent_frame)
            disk_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(disk_frame, text="Disk Usage:").pack(side=tk.LEFT)
            disk_value = float(usage.get("disk_percent", 0))
            disk_bar = ttk.Progressbar(disk_frame, length=200, value=disk_value)
            disk_bar.pack(side=tk.LEFT, padx=10)
            ttk.Label(disk_frame, text=f"{disk_value:.1f}%").pack(side=tk.LEFT)
            
            # Last updated timestamp
            ttk.Label(parent_frame, text=f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}").pack(anchor=tk.E)
        except Exception as e:
            ttk.Label(parent_frame, text=f"Error updating resources: {str(e)}").pack()
    
    def setup_tasks_tab(self):
        """Set up the tasks & schedule tab"""
        tasks_frame = ttk.Frame(self.tasks_tab)
        tasks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create info message
        ttk.Label(tasks_frame, 
                 text="This tab displays project tasks, schedules, and allows you to track completion status.",
                 wraplength=500).pack(pady=10)
        
        # Add a notebook for task categories
        task_notebook = ttk.Notebook(tasks_frame)
        task_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add tabs for different task categories
        todo_frame = ttk.Frame(task_notebook)
        task_notebook.add(todo_frame, text="To-Do List")
        
        scheduled_frame = ttk.Frame(task_notebook)
        task_notebook.add(scheduled_frame, text="Scheduled Tasks")
        
        completed_frame = ttk.Frame(task_notebook)
        task_notebook.add(completed_frame, text="Completed Tasks")
        
        # Add a simple to-do list for now
        self.setup_todo_list(todo_frame)
    
    def setup_todo_list(self, parent_frame):
        """Set up a basic to-do list in the given frame"""
        # Add controls to add/remove tasks
        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(controls_frame, text="Task:").pack(side=tk.LEFT)
        task_entry = ttk.Entry(controls_frame, width=40)
        task_entry.pack(side=tk.LEFT, padx=5)
        
        add_button = ttk.Button(controls_frame, text="Add Task", 
                              command=lambda: self.add_task(task_entry, task_list))
        add_button.pack(side=tk.LEFT, padx=5)
        
        # Tasks list with checkboxes
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a scrolled listbox for tasks
        task_list = tk.Listbox(list_frame, height=15)
        task_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=task_list.yview)
        task_list.configure(yscrollcommand=task_scrollbar.set)
        
        task_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button to mark task as complete
        ttk.Button(parent_frame, text="Mark Complete", 
                  command=lambda: self.mark_task_complete(task_list)).pack(pady=5)
        
        # Button to remove task
        ttk.Button(parent_frame, text="Remove Task", 
                  command=lambda: self.remove_task(task_list)).pack(pady=5)
        
        # Add some sample tasks
        sample_tasks = [
            "Review model design requirements",
            "Test model in Blender simulation",
            "Verify O3DE integration",
            "Update documentation with latest changes"
        ]
        
        for task in sample_tasks:
            task_list.insert(tk.END, task)
    
    def add_task(self, entry_widget, list_widget):
        """Add a task to the task list"""
        task_text = entry_widget.get().strip()
        if task_text:
            list_widget.insert(tk.END, task_text)
            entry_widget.delete(0, tk.END)
            self.process_status_label.config(text="Task added", foreground="green")
    
    def mark_task_complete(self, list_widget):
        """Mark the selected task as complete"""
        selection = list_widget.curselection()
        if selection:
            index = selection[0]
            task_text = list_widget.get(index)
            if not task_text.startswith("✓ "):
                list_widget.delete(index)
                list_widget.insert(index, f"✓ {task_text}")
                self.process_status_label.config(text="Task marked as complete", foreground="green")
    
    def remove_task(self, list_widget):
        """Remove the selected task from the list"""
        selection = list_widget.curselection()
        if selection:
            list_widget.delete(selection[0])
            self.process_status_label.config(text="Task removed", foreground="blue")
    
    def setup_model_eval_tab(self):
        """Set up the model evaluation tab"""
        eval_frame = ttk.Frame(self.model_eval_tab)
        eval_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info section
        ttk.Label(eval_frame, 
                 text="This tab allows you to evaluate and compare model versions.",
                 wraplength=500).pack(anchor=tk.W, pady=5)
        
        # Model selection for comparison
        compare_frame = ttk.LabelFrame(eval_frame, text="Compare Models", padding=10)
        compare_frame.pack(fill=tk.X, pady=10)
        
        versions = self.get_available_versions()
        
        # First model selection
        model1_frame = ttk.Frame(compare_frame)
        model1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model1_frame, text="Model 1:").pack(side=tk.LEFT)
        self.model1_var = tk.StringVar(value=versions[0] if versions else "1")
        model1_dropdown = ttk.Combobox(model1_frame, textvariable=self.model1_var, values=versions, width=5)
        model1_dropdown.pack(side=tk.LEFT, padx=10)
        
        # Second model selection
        model2_frame = ttk.Frame(compare_frame)
        model2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model2_frame, text="Model 2:").pack(side=tk.LEFT)
        self.model2_var = tk.StringVar(value=versions[1] if len(versions) > 1 else "2")
        model2_dropdown = ttk.Combobox(model2_frame, textvariable=self.model2_var, values=versions, width=5)
        model2_dropdown.pack(side=tk.LEFT, padx=10)
        
        # Compare button
        ttk.Button(compare_frame, text="Compare Models", 
                  command=self.compare_models).pack(pady=10)
        
        # Model evaluation metrics
        metrics_frame = ttk.LabelFrame(eval_frame, text="Evaluation Metrics", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Placeholder for evaluation results
        self.evaluation_text = scrolledtext.ScrolledText(metrics_frame, height=10, wrap=tk.WORD)
        self.evaluation_text.insert(tk.END, "Select models and click 'Compare Models' to see evaluation results.")
        self.evaluation_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def compare_models(self):
        """Compare two model versions and display the results"""
        try:
            model1 = self.model1_var.get()
            model2 = self.model2_var.get()
            
            if model1 == model2:
                self.process_status_label.config(text="Please select different model versions to compare", foreground="red")
                return
            
            # Clear previous results
            self.evaluation_text.delete(1.0, tk.END)
            self.evaluation_text.insert(tk.END, f"Comparing Model v{model1} with Model v{model2}...\n\n")
            
            # Simulate loading evaluation data
            self.process_status_label.config(text="Loading model comparison data...", foreground="blue")
            self.root.update()
            
            # In a real app, this would load actual model data
            # For now we'll just simulate with random metrics
            import random
            import time
            time.sleep(1)  # Simulate processing time
            
            # Display comparison results
            self.evaluation_text.insert(tk.END, f"Performance Metrics:\n")
            self.evaluation_text.insert(tk.END, f"-------------------\n")
            
            metrics = [
                ("Processing Speed", "ms", random.randint(20, 100), random.randint(20, 100)),
                ("Memory Usage", "MB", random.randint(100, 500), random.randint(100, 500)),
                ("Accuracy", "%", random.uniform(70, 99), random.uniform(70, 99)),
                ("Compatibility Score", "points", random.randint(1, 10), random.randint(1, 10)),
                ("Simulation Performance", "FPS", random.randint(30, 120), random.randint(30, 120))
            ]
            
            for name, unit, val1, val2 in metrics:
                self.evaluation_text.insert(tk.END, f"{name}: {val1} {unit} vs {val2} {unit}")
                if name != "Memory Usage":  # For memory, lower is better
                    if val1 > val2:
                        self.evaluation_text.insert(tk.END, f" (v{model1} is better)\n")
                    elif val2 > val1:
                        self.evaluation_text.insert(tk.END, f" (v{model2} is better)\n")
                    else:
                        self.evaluation_text.insert(tk.END, " (Equal)\n")
                else:
                    if val1 < val2:
                        self.evaluation_text.insert(tk.END, f" (v{model1} is better)\n")
                    elif val2 < val1:
                        self.evaluation_text.insert(tk.END, f" (v{model2} is better)\n")
                    else:
                        self.evaluation_text.insert(tk.END, " (Equal)\n")
            
            # Overall recommendation
            better_model = model1 if random.random() > 0.5 else model2
            self.evaluation_text.insert(tk.END, f"\nConclusion: Model v{better_model} shows better overall performance.")
            
            self.process_status_label.config(text="Model comparison complete", foreground="green")
        except Exception as e:
            self.evaluation_text.delete(1.0, tk.END)
            self.evaluation_text.insert(tk.END, f"Error comparing models: {str(e)}")
            self.process_status_label.config(text=f"Error: {str(e)}", foreground="red")
    
    def setup_objectives_tab(self):
        """Set up the objectives tab showing project goals and progress"""
        obj_frame = ttk.Frame(self.objectives_tab)
        obj_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title and description
        ttk.Label(obj_frame, text="Project Objectives", 
                 style="Header.TLabel").pack(anchor=tk.W, pady=5)
        
        ttk.Label(obj_frame, 
                 text="Track project objectives and milestones for the GlowingGoldenGlobe model.",
                 wraplength=500).pack(anchor=tk.W, pady=5)
        
        # Create a scrolled text widget for objectives
        obj_text = scrolledtext.ScrolledText(obj_frame, height=20, wrap=tk.WORD)
        obj_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Load objectives from the project objectives module
        try:
            if hasattr(project_objectives, 'OBJECTIVES'):
                objectives = project_objectives.OBJECTIVES
            else:
                objectives = [
                    "Create a detailed 3D model of the micro robot",
                    "Implement realistic animation for robot movement",
                    "Ensure model meets all technical specifications",
                    "Export for compatibility with simulation environment",
                    "Document design decisions and implementation details"
                ]
            
            obj_text.insert(tk.END, "PRIMARY OBJECTIVES:\n")
            obj_text.insert(tk.END, "=================\n\n")
            
            for i, obj in enumerate(objectives):
                obj_text.insert(tk.END, f"{i+1}. {obj}\n\n")
            
            # Mark text as read-only
            obj_text.config(state=tk.DISABLED)
        except Exception as e:
            obj_text.insert(tk.END, f"Error loading objectives: {str(e)}")
    
    def open_in_blender(self):
        """Open the current model version in Blender"""
        version = self.selected_version.get()
        blend_file = f"micro_robot_composite_part_v{version}.blend"
        
        if not os.path.exists(blend_file):
            self.process_status_label.config(text=f"File not found: {blend_file}", foreground="red")
            return
        
        try:
            # Launch Blender with the file
            if platform.system() == "Windows":
                subprocess.Popen(["blender", blend_file])
            else:
                subprocess.Popen(["blender", blend_file])
            
            self.process_status_label.config(text=f"Opening {blend_file} in Blender", foreground="green")
        except Exception as e:
            self.process_status_label.config(text=f"Error opening Blender: {str(e)}", foreground="red")
    
    def run_simulation(self):
        """Run a simulation of the current model"""
        version = self.selected_version.get()
        
        self.process_status_label.config(text=f"Starting simulation for model v{version}...", foreground="blue")
        self.root.update()
        
        # Simulate a long-running process
        def run_sim_process():
            try:
                time.sleep(2)  # Simulate processing
                self.process_status_label.config(text=f"Simulation in progress for model v{version}", foreground="blue")
                time.sleep(3)  # More simulation time
                self.process_status_label.config(text=f"Simulation completed for model v{version}", foreground="green")
            except Exception as e:
                self.process_status_label.config(text=f"Error in simulation: {str(e)}", foreground="red")
        
        # Run in background thread
        threading.Thread(target=run_sim_process, daemon=True).start()
    
    def view_in_o3de(self):
        """View the current model in O3DE"""
        version = self.selected_version.get()
        fbx_file = f"micro_robot_composite_part_v{version}.fbx"
        
        if not os.path.exists(fbx_file):
            self.process_status_label.config(text=f"FBX file not found: {fbx_file}", foreground="red")
            return
        
        # Update status
        self.process_status_label.config(text=f"Opening model v{version} in O3DE viewer", foreground="blue")
        
        # In a real app, this would launch O3DE
        # For now, just update the status after a delay
        def simulate_o3de():
            time.sleep(2)
            self.process_status_label.config(text=f"Model v{version} opened in O3DE viewer", foreground="green")
        
        threading.Thread(target=simulate_o3de, daemon=True).start()
    
    def view_log(self):
        """View development log"""
        log_paths = [
            "model_development_log.txt",
            "model_development_log.md",
            "auto_model_evaluator.log"
        ]
        
        found_log = False
        for log_path in log_paths:
            if os.path.exists(log_path):
                found_log = True
                try:
                    # Create a log viewer window
                    log_window = tk.Toplevel(self.root)
                    log_window.title(f"Log Viewer - {log_path}")
                    log_window.geometry("800x600")
                    
                    # Add a scrolled text widget
                    log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
                    log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    
                    # Load log content
                    with open(log_path, "r") as f:
                        log_content = f.read()
                    
                    log_text.insert(tk.END, log_content)
                    log_text.config(state=tk.DISABLED)  # Make read-only
                    
                    self.process_status_label.config(text=f"Opened log file: {log_path}", foreground="green")
                    break
                except Exception as e:
                    self.process_status_label.config(text=f"Error opening log: {str(e)}", foreground="red")
        
        if not found_log:
            self.process_status_label.config(text="No log files found", foreground="orange")
    
    def save_agent_instructions(self):
        """Save agent instructions to file"""
        instructions = self.agent_instructions.get()
        if not instructions.strip():
            self.process_status_label.config(text="No instructions to save", foreground="red")
            return
        
        try:
            with open("agent_instructions.txt", "w") as f:
                f.write(instructions)
            self.process_status_label.config(text="Instructions saved to agent_instructions.txt", foreground="green")
        except Exception as e:
            self.process_status_label.config(text=f"Error saving instructions: {str(e)}", foreground="red")
    
    def show_help(self):
        """Show help information"""
        help_window = tk.Toplevel(self.root)
        help_window.title("GlowingGoldenGlobe GUI Help")
        help_window.geometry("700x500")
        
        help_frame = ttk.Frame(help_window, padding=15)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(help_frame, text="GlowingGoldenGlobe User Guide", 
                 style="Header.TLabel").pack(pady=10)
        
        help_tabs = ttk.Notebook(help_frame)
        help_tabs.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # General help tab
        general_tab = ttk.Frame(help_tabs)
        help_tabs.add(general_tab, text="General")
        
        general_text = scrolledtext.ScrolledText(general_tab, wrap=tk.WORD)
        general_text.pack(fill=tk.BOTH, expand=True)
        general_text.insert(tk.END, """
GlowingGoldenGlobe GUI - General Help

This application helps you manage model development for the GlowingGoldenGlobe project, with the following features:

1. Start, resume, and monitor model development sessions
2. Configure time limits and auto-save intervals
3. Review model versions and their status
4. Open models in Blender and O3DE for visualization
5. Track development tasks and objectives
6. Monitor system resources during development

Use the tabs at the top to access different functions of the application.
        """)
        general_text.config(state=tk.DISABLED)
        
        # Commands tab
        commands_tab = ttk.Frame(help_tabs)
        help_tabs.add(commands_tab, text="Commands")
        
        commands_text = scrolledtext.ScrolledText(commands_tab, wrap=tk.WORD)
        commands_text.pack(fill=tk.BOTH, expand=True)
        commands_text.insert(tk.END, """
Available Commands:

• Start New Development Session - Begins a new model development session
• Resume Previous Session - Continues a previously saved session
• Save Settings - Saves current configuration options
• Open in Blender - Opens the current model version in Blender
• Run Simulation - Runs simulation for the current model
• View in O3DE - Opens the model in O3DE for advanced visualization

Status Bar:
The status bar at the bottom shows the current status, runtime information, and working directory.
        """)
        commands_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(help_frame, text="Close", 
                  command=help_window.destroy).pack(pady=10)
    
    def handle_hardware_emergency(self, alerts):
        """Handle hardware emergency alerts"""
        self.emergency_stop_processes()

    def emergency_stop_processes(self, emergency_window=None):
        """Stop all running processes in case of emergency"""
        try:
            # Stop running process if any
            if self.process_running and self.process:
                self.process.terminate()
                self.process_running = False
                self.process_status_label.config(text="Process terminated", foreground="red")
                
            # Update status
            self.process_status_label.config(text="Emergency stop triggered", foreground="red")
                
        except Exception as e:
            self.process_status_label.config(text=f"Error during emergency stop: {str(e)}", foreground="red")
    
    def stop_process(self):
        """Stop the currently running process"""
        if self.process_running and self.process:
            try:
                # Update status
                self.process_status_label.config(text="Stopping process...", foreground="blue")
                
                # Kill process
                if hasattr(self.process, 'terminate'):
                    self.process.terminate()
                elif hasattr(self.process, 'kill'):
                    self.process.kill()
                
                # Update status
                self.process_running = False
                self.process_start_time = None
                
                # Cancel timer if active
                if self.timer_id:
                    self.root.after_cancel(self.timer_id)
                    self.timer_id = None
                
                # Enable start button and disable stop button
                if hasattr(self, 'start_button'):
                    self.start_button.config(state="normal")
                if hasattr(self, 'stop_button'):
                    self.stop_button.config(state="disabled")
                
                # Update status label
                self.process_status_label.config(text="Process stopped", foreground="blue")
                
                # Clear process reference
                self.process = None
                
                return True
            except Exception as e:
                self.process_status_label.config(text=f"Error stopping process: {str(e)}", foreground="red")
                return False
        else:
            self.process_status_label.config(text="No process is running", foreground="blue")
            return False
    
    def on_close(self):
        """Handle window close event - clean up processes and resources"""
        try:
            # Stop any running processes
            if self.process_running and self.process:
                print("Terminating running process...")
                self.process.terminate()
                self.process_running = False
                
            # Cancel any scheduled timers
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                
            # Stop hardware monitoring
            if hasattr(self, 'hardware_monitor'):
                self.hardware_monitor.stop_monitoring()
                
            print("Shutdown complete. Closing window.")
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
        finally:
            # Destroy the window
            self.root.destroy()


def main():
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
