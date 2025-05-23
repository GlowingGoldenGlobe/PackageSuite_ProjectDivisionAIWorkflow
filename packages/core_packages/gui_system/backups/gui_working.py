#!/usr/bin/env python
"""
Working GUI for GlowingGoldenGlobe - Clean Implementation
This version provides core functionality without complex dependencies
"""
import os
import sys
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import glob
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui_working.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GGGWorkingGUI")

# Fix import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Safe imports with error handling
try:
    from gui_styles import GGGStyles
    HAS_STYLES = True
except ImportError:
    HAS_STYLES = False
    logger.warning("Custom styles not available")

try:
    from hardware_monitor import HardwareMonitor
    HAS_MONITOR = True
except ImportError:
    HAS_MONITOR = False
    logger.warning("Hardware monitoring not available")

# Try to import Claude Parallel integration components
try:
    from gui_claude_integration import integrate_claude_parallel
    HAS_CLAUDE_INTEGRATION = True
except ImportError:
    logger.warning("Claude Parallel integration not available")
    HAS_CLAUDE_INTEGRATION = False

class WorkingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GlowingGoldenGlobe Agent Control")
        
        # Set window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.9)  # Increased to match the full GUI height
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Apply styles if available
        if HAS_STYLES:
            try:
                self.styles = GGGStyles(self.root)
            except Exception as e:
                logger.error(f"Style initialization error: {e}")
        
        # Initialize variables
        self.time_limit_hours = tk.StringVar(value="4")
        self.time_limit_minutes = tk.StringVar(value="0")
        self.model_version = tk.StringVar(value="1")
        
        # Initialize hardware monitor if available
        self.hardware_monitor = None
        if HAS_MONITOR:
            try:
                self.hardware_monitor = HardwareMonitor()
            except Exception as e:
                logger.error(f"Hardware monitor initialization error: {e}")
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create standard tabs
        self.setup_main_tab()
        self.setup_version_tab()
        self.setup_system_tab()
        
        # Add Claude Parallel tab if integration is available
        if HAS_CLAUDE_INTEGRATION:
            try:
                self.setup_claude_parallel_tab()
                logger.info("Claude Parallel tab added successfully")
            except Exception as e:
                logger.error(f"Error adding Claude Parallel tab: {e}")
        else:
            logger.info("Claude Parallel integration not available, skipping tab")
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load configuration
        self.load_config()
        
    def setup_main_tab(self):
        """Setup main control tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main Control")
        
        # Title
        title = ttk.Label(main_frame, text="GlowingGoldenGlobe Control Panel",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=20)
        
        # Session frame
        session_frame = ttk.LabelFrame(main_frame, text="Session Control", padding=20)
        session_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Time limit
        time_frame = ttk.Frame(session_frame)
        time_frame.pack(pady=10)
        
        ttk.Label(time_frame, text="Time Limit:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(time_frame, textvariable=self.time_limit_hours, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="hours").pack(side=tk.LEFT, padx=(5, 20))
        ttk.Entry(time_frame, textvariable=self.time_limit_minutes, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="minutes").pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(session_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Start New Session",
                  command=self.start_session, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Resume Previous",
                  command=self.resume_session, width=20).pack(side=tk.LEFT, padx=5)
        
        # Actions frame
        action_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding=20)
        action_frame.pack(fill=tk.X, padx=20, pady=10)
        
        action_buttons = [
            ("View Logs", self.view_logs),
            ("Open Model", self.open_model),
            ("Run Simulation", self.run_simulation),
            ("Show Status", self.show_status)
        ]
        
        for i, (text, command) in enumerate(action_buttons):
            ttk.Button(action_frame, text=text, command=command, width=15).grid(
                row=i//2, column=i%2, padx=10, pady=5)
    
    def setup_version_tab(self):
        """Setup version management tab"""
        version_frame = ttk.Frame(self.notebook)
        self.notebook.add(version_frame, text="Model Versions")
        
        # Version list
        list_frame = ttk.LabelFrame(version_frame, text="Available Versions", padding=20)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.version_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.version_listbox.yview)
        
        self.version_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate version list
        self.update_version_list()
        
        # Version controls
        control_frame = ttk.Frame(version_frame)
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(control_frame, text="Refresh List",
                  command=self.update_version_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="View Details",
                  command=self.view_version_details).pack(side=tk.LEFT, padx=5)
    
    def setup_system_tab(self):
        """Setup system information tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System Info")
        
        # System info
        info_frame = ttk.LabelFrame(system_frame, text="System Information", padding=20)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=15)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Update system info
        self.update_system_info()
        
        # Refresh button
        ttk.Button(system_frame, text="Refresh",
                  command=self.update_system_info).pack(pady=10)
    
    def start_session(self):
        """Start a new development session"""
        try:
            hours = float(self.time_limit_hours.get())
            minutes = int(self.time_limit_minutes.get())
            
            if hours < 0 or minutes < 0:
                messagebox.showerror("Invalid Input", "Time values must be positive")
                return
            
            total_time = f"{hours}h {minutes}m"
            
            self.status_bar.config(text=f"Starting session - Time limit: {total_time}")
            
            # Save config
            self.save_config()
            
            messagebox.showinfo("Session Started",
                              f"New session started\nTime limit: {total_time}\n\n" +
                              "Note: Full agent integration pending")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
    
    def resume_session(self):
        """Resume previous session"""
        self.status_bar.config(text="Resuming previous session...")
        messagebox.showinfo("Resume", "Resume functionality coming soon")
    
    def view_logs(self):
        """View development logs"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Development Logs")
        log_window.geometry("800x600")
        
        log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load logs
        log_files = glob.glob("**/*_log.txt", recursive=True) + \
                   glob.glob("**/*.log", recursive=True)
        
        if log_files:
            log_text.insert(1.0, f"Found {len(log_files)} log files:\n\n")
            for log_file in log_files[:5]:  # Show first 5
                log_text.insert(tk.END, f"- {log_file}\n")
        else:
            log_text.insert(1.0, "No log files found")
        
        log_text.config(state=tk.DISABLED)
        
        ttk.Button(log_window, text="Close",
                  command=log_window.destroy).pack(pady=10)
    
    def open_model(self):
        """Open model in default application"""
        self.status_bar.config(text="Opening model...")
        messagebox.showinfo("Open Model", "Model opening functionality coming soon")
    
    def run_simulation(self):
        """Run simulation"""
        self.status_bar.config(text="Running simulation...")
        messagebox.showinfo("Simulation", "Simulation functionality coming soon")
    
    def show_status(self):
        """Show current status"""
        status_info = [
            f"Time Limit: {self.time_limit_hours.get()}h {self.time_limit_minutes.get()}m",
            f"Current Version: {self.model_version.get()}",
            f"Working Directory: {os.getcwd()}",
            f"Python Version: {sys.version.split()[0]}"
        ]
        
        if self.hardware_monitor:
            try:
                usage = self.hardware_monitor.get_current_usage()
                status_info.append(f"CPU Usage: {usage.get('cpu_percent', 'N/A')}%")
                status_info.append(f"Memory Usage: {usage.get('memory_percent', 'N/A')}%")
            except:
                pass
        
        messagebox.showinfo("Status", "\n".join(status_info))
    
    def update_version_list(self):
        """Update the model version list"""
        self.version_listbox.delete(0, tk.END)
        
        # Find version files
        version_patterns = [
            "*_v*.json",
            "micro_robot_*_v*.blend",
            "AI_Agent_1/*_v*.json"
        ]
        
        versions = set()
        for pattern in version_patterns:
            for file in glob.glob(pattern, recursive=True):
                match = re.search(r'_v(\d+)', file)
                if match:
                    versions.add(int(match.group(1)))
        
        for version in sorted(versions):
            self.version_listbox.insert(tk.END, f"Version {version}")
        
        if not versions:
            self.version_listbox.insert(tk.END, "No versions found")
    
    def view_version_details(self):
        """View details of selected version"""
        selection = self.version_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a version")
            return
        
        version_text = self.version_listbox.get(selection[0])
        messagebox.showinfo("Version Details", f"Details for {version_text} coming soon")
    
    def update_system_info(self):
        """Update system information display"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info_lines = [
            f"Python Version: {sys.version}",
            f"Platform: {sys.platform}",
            f"Working Directory: {os.getcwd()}",
            f"Script Directory: {os.path.dirname(os.path.abspath(__file__))}",
            "",
            "Module Status:",
            f"- Custom Styles: {'Available' if HAS_STYLES else 'Not Available'}",
            f"- Hardware Monitor: {'Available' if HAS_MONITOR else 'Not Available'}",
            f"- Claude Parallel: {'Available' if HAS_CLAUDE_INTEGRATION else 'Not Available'}",
            ""
        ]
        
        if self.hardware_monitor:
            try:
                usage = self.hardware_monitor.get_current_usage()
                info_lines.extend([
                    "System Resources:",
                    f"- CPU Usage: {usage.get('cpu_percent', 'N/A')}%",
                    f"- Memory Usage: {usage.get('memory_percent', 'N/A')}%",
                    f"- Disk Usage: {usage.get('disk_percent', 'N/A')}%"
                ])
            except Exception as e:
                info_lines.append(f"Resource monitoring error: {e}")
        
        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)
        
    def setup_claude_parallel_tab(self):
        """Setup Claude Parallel tab"""
        # Create a frame for the Claude Parallel tab
        claude_frame = ttk.Frame(self.notebook)
        self.notebook.add(claude_frame, text="Claude Parallel")
        
        # Title
        title_label = ttk.Label(claude_frame, text="Claude Parallel Execution System", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # If the integration is available, use it to populate the tab
        try:
            integrate_claude_parallel(self.notebook)
            # The above function adds a tab, so we'll remove our placeholder
            self.notebook.forget(claude_frame)
            logger.info("Claude Parallel tab integrated successfully")
        except Exception as e:
            # If integration fails, create a fallback UI
            logger.error(f"Failed to integrate Claude Parallel: {e}")
            self._create_claude_fallback_ui(claude_frame)
    
    def _create_claude_fallback_ui(self, parent_frame):
        """Create a fallback UI for Claude Parallel tab if integration fails"""
        # Status section
        status_frame = ttk.LabelFrame(parent_frame, text="Claude Parallel Status", padding=10)
        status_frame.pack(fill=tk.X, padx=20, pady=10, anchor=tk.N)
        
        status_text = "Claude Parallel system is available but could not be fully integrated."
        ttk.Label(status_frame, text=status_text).pack(anchor=tk.W)
        
        # Available functions
        functions_frame = ttk.LabelFrame(parent_frame, text="Available Functions", padding=10)
        functions_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        functions_text = scrolledtext.ScrolledText(functions_frame, wrap=tk.WORD)
        functions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        functions_info = """
        # Claude Parallel System Functions
        
        1. **Parallel Task Execution**
           - Execute multiple AI tasks simultaneously
           - Coordinate between different AI agents
           - Manage resource allocation
        
        2. **AI Agent Detection**
           - Determine which AI agents are available
           - Select optimal execution strategy
           - Provide fallback mechanisms
        
        3. **Task Scheduling**
           - Schedule tasks for regular execution
           - Support interval, daily, weekly schedules
           - Track task execution history
        
        4. **Resource Monitoring**
           - Monitor system resource usage
           - Adjust resource allocation dynamically
           - Prevent system overload
        """
        
        functions_text.insert(1.0, functions_info)
        functions_text.config(state=tk.DISABLED)
        
        # Action buttons
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="View Documentation", 
                  command=lambda: self.show_info("Documentation", 
                                               "Please see CLAUDE_PARALLEL_README.md for full documentation.")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Check Integration", 
                  command=lambda: self.show_info("Integration Status", 
                                               "Claude Parallel integration is available but could not be initialized properly.")).pack(side=tk.LEFT, padx=5)
    
    def show_info(self, title, message):
        """Show an information dialog"""
        messagebox.showinfo(title, message)
    
    def load_config(self):
        """Load configuration from file"""
        config_file = os.path.join(os.path.dirname(__file__), "agent_mode_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.time_limit_hours.set(config.get("time_limit_hours", "4"))
                    self.time_limit_minutes.set(config.get("time_limit_minutes", "0"))
            except Exception as e:
                print(f"Config load error: {e}")
    
    def save_config(self):
        """Save configuration to file"""
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
            print(f"Config save error: {e}")

def main():
    """Main entry point"""
    root = tk.Tk()
    
    try:
        app = WorkingGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"GUI Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()