#!/usr/bin/env python
"""
GUI Tab Template
Template for creating new GUI tabs in the GlowingGoldenGlobe system
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for AI workflow integration
sys.path.append(str(Path(__file__).parent.parent))

# Required AI workflow integration import
from ai_workflow_integration import check_file_access, can_read_file

class TemplateTab:
    """Template Tab for the GlowingGoldenGlobe GUI"""
    
    def __init__(self, parent_notebook):
        """
        Initialize the Template tab
        
        Args:
            parent_notebook: The parent ttk.Notebook widget
        """
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="Template")
        
        # Paths
        self.base_dir = Path(__file__).parent.parent
        
        # Status variables
        self.status_var = tk.StringVar(value="Ready")
        
        # Configuration
        self.config = {
            "setting1": tk.BooleanVar(value=True),
            "setting2": tk.StringVar(value="default"),
            "setting3": tk.IntVar(value=30)
        }
        
        self._create_widgets()
        self._load_config()
    
    def _create_widgets(self):
        """Create widgets for the Template tab"""
        # Main scrollable frame
        main_canvas = tk.Canvas(self.tab)
        scrollbar = ttk.Scrollbar(self.tab, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main layout with padding
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Template Tab", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="15")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Settings controls
        ttk.Checkbutton(config_frame, text="Enable setting 1", 
                       variable=self.config["setting1"],
                       command=self._on_config_change).pack(anchor=tk.W, pady=5)
        
        # Actions Section
        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding="15")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Action buttons
        button_frame = ttk.Frame(actions_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Action 1", 
                  command=self._action_1).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Action 2", 
                  command=self._action_2).pack(side=tk.LEFT, padx=(0, 10))
        
        # Status Section
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="15")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results text area
        self.results_text = tk.Text(results_frame, height=10, width=80, wrap=tk.WORD)
        results_scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_config(self):
        """Load configuration from file with AI workflow integration"""
        config_path = self.base_dir / "template_config.json"
        
        # Check file access with AI workflow integration
        access_result = check_file_access(str(config_path), "read", "loading template configuration")
        if not access_result['allowed']:
            if access_result.get('token_saved'):
                self.status_var.set("Config load skipped - token optimization")
                return
            else:
                self.status_var.set(f"Config access denied: {access_result['reason']}")
                return
        
        if config_path.exists():
            try:
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update variables
                self.config["setting1"].set(config.get("setting1", True))
                self.config["setting2"].set(config.get("setting2", "default"))
                self.config["setting3"].set(config.get("setting3", 30))
                
                self.status_var.set("Configuration loaded")
                
            except Exception as e:
                self.status_var.set(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save configuration to file with AI workflow integration"""
        config_path = self.base_dir / "template_config.json"
        
        # Check file access
        access_result = check_file_access(str(config_path), "write", "saving template configuration")
        if not access_result['allowed']:
            if access_result.get('requires_override'):
                messagebox.showerror("Access Denied", f"Cannot save config: {access_result['reason']}")
                return
        
        try:
            import json
            config = {
                "setting1": self.config["setting1"].get(),
                "setting2": self.config["setting2"].get(),
                "setting3": self.config["setting3"].get(),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.status_var.set("Configuration saved")
                
        except Exception as e:
            self.status_var.set(f"Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def _on_config_change(self):
        """Handle configuration changes"""
        self._save_config()
    
    def _action_1(self):
        """Perform action 1 with thread safety"""
        self.status_var.set("Performing action 1...")
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=self._action_1_thread, daemon=True).start()
    
    def _action_1_thread(self):
        """Thread function for action 1"""
        try:
            # Simulate work
            import time
            time.sleep(2)
            
            result = "Action 1 completed successfully"
            
            # Schedule GUI update on main thread
            self.tab.after(0, lambda: self._update_results(result))
            
        except Exception as e:
            self.tab.after(0, lambda: self._show_error(f"Action 1 failed: {e}"))
    
    def _action_2(self):
        """Perform action 2"""
        try:
            result = "Action 2 completed"
            self._update_results(result)
            self.status_var.set("Action 2 completed")
            
        except Exception as e:
            self._show_error(f"Action 2 failed: {e}")
    
    def _update_results(self, result_text: str):
        """Update results display (thread-safe)"""
        try:
            # Clear and update results
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            
            # Add timestamp and result
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.results_text.insert(tk.END, f"[{timestamp}] {result_text}\n")
            
            self.results_text.config(state=tk.DISABLED)
            self.status_var.set("Ready")
            
        except Exception as e:
            self._show_error(f"Failed to update results: {e}")
    
    def _show_error(self, message: str):
        """Show error message (thread-safe)"""
        self.status_var.set("Error")
        messagebox.showerror("Error", message)


def integrate_with_gui(notebook):
    """
    Integrate Template Tab with the GUI - REQUIRED FUNCTION
    
    Args:
        notebook: The main GUI notebook widget
    
    Returns:
        The created tab object
    """
    return TemplateTab(notebook)


# Example for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Template Tab Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Test integration
    tab = integrate_with_gui(notebook)
    
    root.mainloop()