"""
Agent Mode GUI Integration for Claude Code
Adds Claude Code awareness and usage tracking to existing GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

from mode_detector import detect_mode, get_mode_name, get_stop_command
from claude_usage_tracker import get_usage_display, record_session_end

def enhance_agent_mode_gui(gui_instance):
    """Enhance existing AgentModeStarter GUI with Claude Code support"""
    
    # Add mode detection status bar
    def create_mode_status_bar():
        """Create status bar showing current AI mode"""
        status_frame = ttk.Frame(gui_instance.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Mode indicator
        mode_label = ttk.Label(status_frame, text="AI Mode: ", font=('TkDefaultFont', 9))
        mode_label.pack(side=tk.LEFT, padx=5)
        
        gui_instance.mode_status = ttk.Label(status_frame, text="Detecting...", 
                                           font=('TkDefaultFont', 9, 'bold'))
        gui_instance.mode_status.pack(side=tk.LEFT)
        
        # Claude usage (shown only for Claude Code)
        gui_instance.claude_usage = ttk.Label(status_frame, text="", 
                                            font=('TkDefaultFont', 9))
        gui_instance.claude_usage.pack(side=tk.LEFT, padx=20)
        
        # Update mode periodically
        def update_mode_status():
            mode = detect_mode()
            mode_name = get_mode_name(mode)
            gui_instance.mode_status.config(text=mode_name)
            
            # Show Claude usage if in Claude Code mode
            if mode == "claude_code":
                usage = get_usage_display()
                gui_instance.claude_usage.config(text=f"Claude Usage: {usage}")
                gui_instance.claude_usage.pack(side=tk.LEFT, padx=20)
            else:
                gui_instance.claude_usage.pack_forget()
            
            # Schedule next update
            gui_instance.root.after(5000, update_mode_status)
        
        update_mode_status()
    
    # Override the control button methods
    original_start = gui_instance.start_new_session
    original_stop = gui_instance.stop_development if hasattr(gui_instance, 'stop_development') else None
    
    def enhanced_start_new_session():
        """Enhanced start that detects current mode"""
        mode = detect_mode()
        
        if mode == "claude_code":
            # If Claude Code is running, inform user
            response = messagebox.askyesno("Claude Code Active",
                "Claude Code is currently active.\n"
                "Starting a new session will switch to API mode.\n"
                "Continue?")
            if not response:
                return
            
            # Record Claude session end
            record_session_end()
        
        # Call original start method
        original_start()
    
    def enhanced_stop_development():
        """Enhanced stop that handles different modes"""
        mode = detect_mode()
        
        if mode == "claude_code":
            # For Claude Code, just record usage and inform user
            record_session_end()
            messagebox.showinfo("Claude Code",
                "Claude Code session recorded.\n"
                "Use Ctrl+C in terminal to stop Claude Code.")
            return
        elif mode == "none":
            messagebox.showinfo("Info", "No active AI mode to stop")
            return
        
        # For other modes, execute stop command
        cmd = get_stop_command(mode)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Success", f"Stopped {get_mode_name(mode)}")
            else:
                messagebox.showerror("Error", f"Failed to stop: {result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop mode: {str(e)}")
    
    # Add stop button if it doesn't exist
    if not hasattr(gui_instance, 'stop_button'):
        # Find the control button frame
        control_frame = None
        for child in gui_instance.root.winfo_children():
            if isinstance(child, ttk.Frame):
                # Look for frame with start button
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == 'Start New Session':
                        control_frame = child
                        break
        
        if control_frame:
            gui_instance.stop_button = ttk.Button(control_frame, text="Stop Current Mode",
                                                command=enhanced_stop_development,
                                                style="Danger.TButton")
            gui_instance.stop_button.pack(side=tk.LEFT, padx=10)
    else:
        # Replace existing stop command
        gui_instance.stop_button.config(command=enhanced_stop_development)
    
    # Replace start method
    gui_instance.start_new_session = enhanced_start_new_session
    
    # Add mode switcher in options
    def add_mode_switcher(parent_frame):
        """Add mode selection option"""
        mode_frame = ttk.Frame(parent_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="AI Mode:").pack(side=tk.LEFT, padx=5)
        
        mode_var = tk.StringVar(value="auto")
        modes = ["auto", "claude_code", "api_mode"]
        mode_menu = ttk.Combobox(mode_frame, textvariable=mode_var, 
                                values=modes, state="readonly", width=15)
        mode_menu.pack(side=tk.LEFT, padx=5)
        
        def on_mode_change(event=None):
            selected = mode_var.get()
            if selected == "claude_code":
                messagebox.showinfo("Claude Code Mode",
                    "To use Claude Code:\n"
                    "1. Save your work\n"
                    "2. Open terminal\n"
                    "3. Run: claude-code\n"
                    "4. Usage will be tracked automatically")
            elif selected == "api_mode":
                messagebox.showinfo("API Mode",
                    "API mode will use your Anthropic API key\n"
                    "for automated agent operations.")
        
        mode_menu.bind("<<ComboboxSelected>>", on_mode_change)
        
        ttk.Label(mode_frame, text="(auto detects current mode)").pack(side=tk.LEFT, padx=5)
    
    # Find development options frame and add mode switcher
    for child in gui_instance.root.winfo_children():
        if isinstance(child, ttk.LabelFrame) and "Development Options" in child.cget('text'):
            add_mode_switcher(child)
            break
    
    # Add the status bar
    create_mode_status_bar()
    
    return gui_instance

# Function to be called from existing agent_mode_gui.py
def integrate_claude_support(gui_app):
    """Main integration function to be called from agent_mode_gui.py"""
    return enhance_agent_mode_gui(gui_app)

if __name__ == "__main__":
    # Test integration
    import agent_mode_gui
    
    root = tk.Tk()
    app = agent_mode_gui.AgentModeStarter(root)
    enhanced_app = integrate_claude_support(app)
    root.mainloop()