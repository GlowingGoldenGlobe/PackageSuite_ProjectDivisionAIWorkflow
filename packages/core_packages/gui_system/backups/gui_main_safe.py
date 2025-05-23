#!/usr/bin/env python
"""
Safe version of GUI that handles missing imports gracefully
"""
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

# Fix path to find parent directory modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom modules with fallbacks
try:
    from ggg_gui_styles import GGGStyles
except ImportError:
    print("Warning: GGGStyles not available")
    GGGStyles = None

try:
    from hardware_monitor import HardwareMonitor
except ImportError:
    print("Warning: HardwareMonitor not available")
    HardwareMonitor = None

try:
    from ai_managers.task_manager import TaskManager
except ImportError:
    print("Warning: TaskManager not available")
    TaskManager = None

try:
    from help_system import HelpSystem
except ImportError:
    print("Warning: HelpSystem not available")
    HelpSystem = None

try:
    from refined_model_integration import RefinedModelIntegration
except ImportError:
    print("Warning: RefinedModelIntegration not available")
    RefinedModelIntegration = None

try:
    from auto_refiner_integration import integrate_auto_refiner
except ImportError:
    print("Warning: integrate_auto_refiner not available")
    integrate_auto_refiner = None

try:
    from model_notification_system import get_notification_system, ModelNotificationSystem
except ImportError:
    print("Warning: ModelNotificationSystem not available")
    ModelNotificationSystem = None
    get_notification_system = None

try:
    import Objectives_1 as project_objectives
except ImportError:
    print("Warning: Objectives_1 not available")
    project_objectives = None

try:
    from agent_mode_gui_implementation import implement_enhancements as apply_gui_enhancements
except ImportError:
    print("Warning: apply_gui_enhancements not available")
    apply_gui_enhancements = None

class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GlowingGoldenGlobe User Controls")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.9)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        
        # Initialize styles if available
        if GGGStyles:
            try:
                self.styles = GGGStyles(self.root)
            except Exception as e:
                print(f"Error initializing styles: {e}")
                self.styles = None
        else:
            self.styles = None
            
        # Initialize variables
        self.time_limit_hours = tk.StringVar(value="4")
        self.time_limit_minutes = tk.StringVar(value="0")
        self.current_version = tk.StringVar()
        self.resume_version = tk.StringVar()
        self.simulation_status = tk.StringVar(value="Not started")
        
        # Initialize hardware monitor if available
        if HardwareMonitor:
            try:
                self.hardware_monitor = HardwareMonitor()
            except Exception as e:
                print(f"Error initializing hardware monitor: {e}")
                self.hardware_monitor = None
        else:
            self.hardware_monitor = None
            
        # Initialize task manager if available
        if TaskManager:
            try:
                self.task_manager = TaskManager()
            except Exception as e:
                print(f"Error initializing task manager: {e}")
                self.task_manager = None
        else:
            self.task_manager = None
            
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main Control")
        
        # Apply GUI enhancements if available
        if apply_gui_enhancements:
            try:
                apply_gui_enhancements(self)
            except Exception as e:
                print(f"Error applying GUI enhancements: {e}")
        
        # Setup tabs
        self.setup_main_tab()
        
        # Add status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load settings
        self.load_initial_config()
        
    def setup_main_tab(self):
        """Set up the main control tab"""
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="GlowingGoldenGlobe Agent Control", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Session control frame
        session_frame = ttk.LabelFrame(main_frame, text="Session Control", padding="10")
        session_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time limit controls
        time_frame = ttk.Frame(session_frame)
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(time_frame, text="Time Limit:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(time_frame, textvariable=self.time_limit_hours, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="hours").pack(side=tk.LEFT, padx=(5, 10))
        ttk.Entry(time_frame, textvariable=self.time_limit_minutes, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="minutes").pack(side=tk.LEFT, padx=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(session_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Start New Session", 
                  command=self.start_new_session).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Resume Previous", 
                  command=self.resume_previous_session).pack(side=tk.LEFT)
        
        # Basic info frame
        info_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = tk.Text(info_frame, height=10, width=50)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Add basic system info
        self.update_system_info()
        
    def update_system_info(self):
        """Update system information display"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "GlowingGoldenGlobe System Status\n\n")
        self.info_text.insert(tk.END, f"Python Version: {sys.version.split()[0]}\n")
        self.info_text.insert(tk.END, f"Platform: {sys.platform}\n")
        self.info_text.insert(tk.END, f"Working Directory: {os.getcwd()}\n\n")
        
        # Module status
        self.info_text.insert(tk.END, "Module Status:\n")
        self.info_text.insert(tk.END, f"- GGGStyles: {'Available' if GGGStyles else 'Not Available'}\n")
        self.info_text.insert(tk.END, f"- HardwareMonitor: {'Available' if self.hardware_monitor else 'Not Available'}\n")
        self.info_text.insert(tk.END, f"- TaskManager: {'Available' if self.task_manager else 'Not Available'}\n")
        
        self.info_text.config(state=tk.DISABLED)
    
    def load_initial_config(self):
        """Load saved configuration"""
        config_file = os.path.join(os.path.dirname(__file__), "agent_mode_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.time_limit_hours.set(config.get("time_limit_hours", "4"))
                    self.time_limit_minutes.set(config.get("time_limit_minutes", "0"))
            except Exception as e:
                print(f"Could not load config: {str(e)}")
    
    def save_settings(self):
        """Save current settings"""
        config = {
            "time_limit_hours": self.time_limit_hours.get(),
            "time_limit_minutes": self.time_limit_minutes.get(),
            "last_session": datetime.datetime.now().isoformat()
        }
        
        config_file = os.path.join(os.path.dirname(__file__), "agent_mode_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Could not save config: {str(e)}")
    
    def start_new_session(self):
        """Start a new development session"""
        try:
            hours = float(self.time_limit_hours.get())
            minutes = int(self.time_limit_minutes.get())
            
            if hours < 0 or minutes < 0:
                messagebox.showerror("Invalid Input", "Time values must be positive")
                return
                
            total_seconds = int(hours * 3600 + minutes * 60)
            
            # Save settings
            self.save_settings()
            
            # Update status
            self.status_bar.config(text=f"Starting new session - Time limit: {hours}h {minutes}m")
            
            messagebox.showinfo("Session Started", 
                              f"New session started with time limit: {hours}h {minutes}m\n\n" +
                              "Note: Full agent integration is pending")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for time limit")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {str(e)}")
    
    def resume_previous_session(self):
        """Resume a previous development session"""
        messagebox.showinfo("Resume Session", 
                           "Resume functionality is not yet implemented.\n\n" +
                           "This will allow resuming incomplete sessions.")
        self.status_bar.config(text="Resume requested - Feature pending")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()