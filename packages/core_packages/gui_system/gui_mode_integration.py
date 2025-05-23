"""
GUI Mode Integration Module
Integrates mode detection, Claude usage tracking, and control buttons
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
from mode_detector import detect_mode, get_mode_name, get_stop_command, get_start_command
from claude_usage_tracker import get_usage_display, record_session_end

class ModeControlPanel:
    """Control panel for different AI modes with usage tracking"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_mode = tk.StringVar(value="Detecting...")
        self.usage_display = tk.StringVar(value="Initializing...")
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="AI Mode Control & Usage", padding=10)
        self.frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Mode detection display
        mode_frame = ttk.Frame(self.frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Current Mode:").pack(side=tk.LEFT, padx=5)
        self.mode_label = ttk.Label(mode_frame, textvariable=self.current_mode, 
                                   font=('TkDefaultFont', 10, 'bold'))
        self.mode_label.pack(side=tk.LEFT, padx=5)
        
        # Claude usage display (only shown for Claude Code mode)
        self.usage_frame = ttk.Frame(self.frame)
        self.usage_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.usage_frame, text="Claude Usage:").pack(side=tk.LEFT, padx=5)
        self.usage_label = ttk.Label(self.usage_frame, textvariable=self.usage_display)
        self.usage_label.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Stop button - adapts to current mode
        self.stop_button = ttk.Button(button_frame, text="Stop Current Mode", 
                                     command=self.stop_current_mode)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Mode selection and start
        ttk.Label(button_frame, text="Start Mode:").pack(side=tk.LEFT, padx=10)
        
        self.mode_select = ttk.Combobox(button_frame, 
                                       values=["claude_code", "vscode_agent", "pyautogen"],
                                       state="readonly", width=15)
        self.mode_select.set("claude_code")
        self.mode_select.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Selected Mode",
                                      command=self.start_selected_mode)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        self.refresh_button = ttk.Button(button_frame, text="Refresh",
                                        command=self.update_display)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Time limit settings for Claude Code
        self.time_limit_frame = ttk.Frame(self.frame)
        self.time_limit_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.time_limit_frame, text="Session Time Limit (hours):").pack(side=tk.LEFT, padx=5)
        self.time_limit_var = tk.StringVar(value="2")
        self.time_limit_entry = ttk.Entry(self.time_limit_frame, textvariable=self.time_limit_var, width=5)
        self.time_limit_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.time_limit_frame, text="(Claude Code auto-reminder)").pack(side=tk.LEFT, padx=5)
        
        # Start periodic updates
        self.update_display()
        self.schedule_updates()
    
    def update_display(self):
        """Update mode and usage display"""
        try:
            # Detect current mode
            mode = detect_mode()
            mode_name = get_mode_name(mode)
            self.current_mode.set(mode_name)
            
            # Update usage display for Claude Code
            if mode == "claude_code":
                self.usage_frame.pack(fill=tk.X, pady=5)
                self.time_limit_frame.pack(fill=tk.X, pady=5)
                self.usage_display.set(get_usage_display())
            else:
                self.usage_frame.pack_forget()
                self.time_limit_frame.pack_forget()
            
            # Update button states
            self.stop_button.config(state="normal" if mode != "none" else "disabled")
            
        except Exception as e:
            self.current_mode.set(f"Error: {str(e)}")
    
    def schedule_updates(self):
        """Schedule periodic display updates"""
        self.update_display()
        self.parent.after(5000, self.schedule_updates)  # Update every 5 seconds
    
    def stop_current_mode(self):
        """Stop the currently running mode"""
        try:
            mode = detect_mode()
            if mode == "none":
                messagebox.showinfo("Info", "No active mode to stop")
                return
            
            # Special handling for Claude Code
            if mode == "claude_code":
                # Record session end before stopping
                record_session_end()
                messagebox.showinfo("Claude Code", 
                    "Claude Code session ended. Token usage recorded.\n"
                    "Use Ctrl+C in the terminal to stop Claude Code.")
                return
            
            # Stop other modes
            cmd = get_stop_command(mode)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", f"Stopped {get_mode_name(mode)}")
            else:
                messagebox.showerror("Error", f"Failed to stop: {result.stderr}")
            
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop mode: {str(e)}")
    
    def start_selected_mode(self):
        """Start the selected mode"""
        try:
            selected = self.mode_select.get()
            if not selected:
                messagebox.showwarning("Warning", "Please select a mode to start")
                return
            
            # Check if mode is already running
            current = detect_mode()
            if current == selected:
                messagebox.showinfo("Info", f"{get_mode_name(selected)} is already running")
                return
            
            # Special instructions for Claude Code
            if selected == "claude_code":
                messagebox.showinfo("Claude Code", 
                    "To start Claude Code:\n"
                    "1. Open a terminal\n"
                    "2. Navigate to your project directory\n"
                    "3. Run: claude-code\n\n"
                    f"Time limit reminder set for {self.time_limit_var.get()} hours")
                # Set up time limit reminder
                self.setup_time_limit_reminder()
                return
            
            # Start other modes
            cmd = get_start_command(selected)
            
            # Run in background thread
            def run_command():
                subprocess.Popen(cmd)
            
            thread = threading.Thread(target=run_command)
            thread.daemon = True
            thread.start()
            
            messagebox.showinfo("Success", f"Starting {get_mode_name(selected)}...")
            
            # Update display after a short delay
            self.parent.after(2000, self.update_display)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start mode: {str(e)}")
    
    def setup_time_limit_reminder(self):
        """Set up time limit reminder for Claude Code"""
        try:
            hours = float(self.time_limit_var.get())
            milliseconds = int(hours * 60 * 60 * 1000)
            
            def show_reminder():
                record_session_end()  # Record usage
                messagebox.showwarning("Time Limit Reminder",
                    f"Claude Code has been running for {hours} hours.\n"
                    f"Current usage: {get_usage_display()}\n\n"
                    "Consider taking a break or switching to API mode.")
            
            self.parent.after(milliseconds, show_reminder)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid time limit value")

def integrate_with_gui(parent_window):
    """Integrate mode control panel with existing GUI"""
    panel = ModeControlPanel(parent_window)
    return panel

if __name__ == "__main__":
    # Test standalone
    root = tk.Tk()
    root.title("Mode Control Test")
    panel = ModeControlPanel(root)
    root.mainloop()