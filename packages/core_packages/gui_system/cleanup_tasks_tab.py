#!/usr/bin/env python
"""
Cleanup Tasks Tab for GlowingGoldenGlobe GUI
Integrates assessment-based cleanup scheduling and management
"""

import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class CleanupTasksTab:
    """Cleanup Tasks and Schedule Tab for the GlowingGoldenGlobe GUI"""
    
    def __init__(self, parent_notebook):
        """
        Initialize the Cleanup Tasks tab
        
        Args:
            parent_notebook: The parent ttk.Notebook widget
        """
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="Tasks & Schedule")
        
        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.utils_dir = self.base_dir / "utils"
        
        # Status variables
        self.status_var = tk.StringVar(value="Ready")
        self.last_assessment_var = tk.StringVar(value="Never")
        self.next_scheduled_var = tk.StringVar(value="Not scheduled")
        
        # Cleanup configuration
        self.cleanup_config = {
            "auto_cleanup_enabled": tk.BooleanVar(value=True),
            "schedule_interval_days": tk.IntVar(value=30),
            "dry_run_mode": tk.BooleanVar(value=False),
            "delete_threshold_days": tk.IntVar(value=60),
            "archive_threshold_days": tk.IntVar(value=30)
        }
        
        # Assessment results
        self.current_assessment = None
        
        self._create_widgets()
        self._load_config()
        self._update_schedule_info()
    
    def _create_widgets(self):
        """Create widgets for the Cleanup Tasks tab"""
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
        title_label = ttk.Label(main_frame, text="Cleanup Tasks & Schedule Manager", 
                               font=("Arial", 14, "bold"))\n        title_label.pack(pady=(0, 20))
        
        # Schedule Configuration Section
        schedule_frame = ttk.LabelFrame(main_frame, text="Schedule Configuration", padding="15")
        schedule_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Auto cleanup toggle
        ttk.Checkbutton(schedule_frame, text="Enable automatic scheduled cleanup", 
                       variable=self.cleanup_config["auto_cleanup_enabled"],
                       command=self._on_config_change).pack(anchor=tk.W, pady=5)
        
        # Schedule interval
        interval_frame = ttk.Frame(schedule_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="Schedule interval:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Spinbox(interval_frame, from_=7, to=90, width=5, 
                   textvariable=self.cleanup_config["schedule_interval_days"],
                   command=self._on_config_change).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(interval_frame, text="days").pack(side=tk.LEFT)
        
        # Dry run mode
        ttk.Checkbutton(schedule_frame, text="Dry run mode (show actions without executing)", 
                       variable=self.cleanup_config["dry_run_mode"],
                       command=self._on_config_change).pack(anchor=tk.W, pady=5)
        
        # Threshold settings
        threshold_frame = ttk.LabelFrame(schedule_frame, text="Cleanup Thresholds", padding="10")
        threshold_frame.pack(fill=tk.X, pady=10)
        
        # Archive threshold
        archive_frame = ttk.Frame(threshold_frame)
        archive_frame.pack(fill=tk.X, pady=2)
        ttk.Label(archive_frame, text="Archive files older than:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Spinbox(archive_frame, from_=7, to=365, width=5, 
                   textvariable=self.cleanup_config["archive_threshold_days"],
                   command=self._on_config_change).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(archive_frame, text="days").pack(side=tk.LEFT)
        
        # Delete threshold
        delete_frame = ttk.Frame(threshold_frame)
        delete_frame.pack(fill=tk.X, pady=2)
        ttk.Label(delete_frame, text="Delete files older than:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Spinbox(delete_frame, from_=30, to=365, width=5, 
                   textvariable=self.cleanup_config["delete_threshold_days"],
                   command=self._on_config_change).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(delete_frame, text="days").pack(side=tk.LEFT)
        
        # Schedule Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Schedule Status", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status information
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill=tk.X)
        
        ttk.Label(status_info_frame, text="Last assessment:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(status_info_frame, textvariable=self.last_assessment_var, 
                 foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(status_info_frame, text="Next scheduled:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(status_info_frame, textvariable=self.next_scheduled_var, 
                 foreground="green").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(status_info_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(status_info_frame, textvariable=self.status_var).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Manual Actions Section
        actions_frame = ttk.LabelFrame(main_frame, text="Manual Actions", padding="15")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Action buttons
        button_frame = ttk.Frame(actions_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Run Assessment Now", 
                  command=self._run_assessment_now).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="View Last Report", 
                  command=self._view_last_report).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Manual Cleanup", 
                  command=self._manual_cleanup).pack(side=tk.LEFT, padx=(0, 10))
        
        # Assessment Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Assessment Results", padding="15")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Results text area
        self.results_text = tk.Text(results_frame, height=15, width=80, wrap=tk.WORD)
        results_scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial results
        self._load_last_assessment()
    
    def _load_config(self):
        """Load configuration from file"""
        config_path = self.base_dir / "cleanup_tasks_config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update variables
                self.cleanup_config["auto_cleanup_enabled"].set(config.get("auto_cleanup_enabled", True))
                self.cleanup_config["schedule_interval_days"].set(config.get("schedule_interval_days", 30))
                self.cleanup_config["dry_run_mode"].set(config.get("dry_run_mode", False))
                self.cleanup_config["delete_threshold_days"].set(config.get("delete_threshold_days", 60))
                self.cleanup_config["archive_threshold_days"].set(config.get("archive_threshold_days", 30))
                
            except Exception as e:
                print(f"Error loading cleanup config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        config_path = self.base_dir / "cleanup_tasks_config.json"
        
        try:
            config = {
                "auto_cleanup_enabled": self.cleanup_config["auto_cleanup_enabled"].get(),
                "schedule_interval_days": self.cleanup_config["schedule_interval_days"].get(),
                "dry_run_mode": self.cleanup_config["dry_run_mode"].get(),
                "delete_threshold_days": self.cleanup_config["delete_threshold_days"].get(),
                "archive_threshold_days": self.cleanup_config["archive_threshold_days"].get(),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving cleanup config: {e}")
    
    def _on_config_change(self):
        """Handle configuration changes"""
        self._save_config()
        self._update_schedule_info()
    
    def _update_schedule_info(self):
        """Update schedule information display"""
        try:
            # Check for last assessment
            assessment_files = list(self.utils_dir.glob("cleanup_assessment_report_*.json"))
            if assessment_files:
                latest_file = max(assessment_files, key=lambda f: f.stat().st_mtime)
                last_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                self.last_assessment_var.set(last_time.strftime("%Y-%m-%d %H:%M"))
                
                # Calculate next scheduled time
                if self.cleanup_config["auto_cleanup_enabled"].get():
                    interval_days = self.cleanup_config["schedule_interval_days"].get()
                    next_time = last_time + timedelta(days=interval_days)
                    self.next_scheduled_var.set(next_time.strftime("%Y-%m-%d %H:%M"))
                else:
                    self.next_scheduled_var.set("Disabled")
            else:
                self.last_assessment_var.set("Never")
                self.next_scheduled_var.set("Not scheduled")
                
        except Exception as e:
            print(f"Error updating schedule info: {e}")
    
    def _run_assessment_now(self):
        """Run assessment immediately"""
        self.status_var.set("Running assessment...")
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=self._assessment_thread, daemon=True).start()
    
    def _assessment_thread(self):
        """Thread function for running assessment"""
        try:
            # Import assessment module
            sys.path.insert(0, str(self.utils_dir))
            
            try:
                import assessment_based_cleanup
                
                # Initialize cleanup system
                cleanup = assessment_based_cleanup.AssessmentBasedCleanup(str(self.utils_dir))
                
                # Run assessment
                results = cleanup.run_full_assessment()
                
                # Save report
                report_path = cleanup.save_assessment_report()
                
                # Update GUI
                self.tab.after(0, lambda: self._update_assessment_results(results, report_path))
                
            finally:
                if str(self.utils_dir) in sys.path:
                    sys.path.remove(str(self.utils_dir))
                    
        except Exception as e:
            self.tab.after(0, lambda: self._show_error(f"Assessment failed: {e}"))
    
    def _update_assessment_results(self, results, report_path):
        """Update assessment results in GUI"""
        try:
            # Clear previous results
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            
            # Add header
            self.results_text.insert(tk.END, "ASSESSMENT RESULTS\\n")
            self.results_text.insert(tk.END, "=" * 50 + "\\n\\n")
            
            # Add summary
            self.results_text.insert(tk.END, f"Assessment completed: {results['timestamp']}\\n")
            self.results_text.insert(tk.END, f"Total files assessed: {results['total_files']}\\n")
            self.results_text.insert(tk.END, f"Files to delete: {len(results['files_to_delete'])}\\n")
            self.results_text.insert(tk.END, f"Files to archive: {len(results['files_to_archive'])}\\n")
            self.results_text.insert(tk.END, f"Files to preserve: {len(results['files_to_preserve'])}\\n\\n")
            
            # Add recommendations
            if results['cleanup_recommendations']:
                self.results_text.insert(tk.END, "RECOMMENDATIONS:\\n")
                for rec in results['cleanup_recommendations']:
                    self.results_text.insert(tk.END, f"• {rec}\\n")
                self.results_text.insert(tk.END, "\\n")
            
            # Add detailed breakdown
            if results['files_to_delete']:
                self.results_text.insert(tk.END, "FILES TO DELETE:\\n")
                for file_info in results['files_to_delete']:
                    self.results_text.insert(tk.END, f"• {file_info['path']} - {file_info['reason']}\\n")
                self.results_text.insert(tk.END, "\\n")
            
            if results['files_to_archive']:
                self.results_text.insert(tk.END, "FILES TO ARCHIVE:\\n")
                for file_info in results['files_to_archive']:
                    self.results_text.insert(tk.END, f"• {file_info['path']} - {file_info['reason']}\\n")
                self.results_text.insert(tk.END, "\\n")
            
            # Add criteria details
            self.results_text.insert(tk.END, "ASSESSMENT CRITERIA DETAILS:\\n")
            criteria = results['assessment_criteria']
            
            self.results_text.insert(tk.END, f"Duplicates: {criteria['duplicates']['total_duplicate_sets']} sets found\\n")
            self.results_text.insert(tk.END, f"Obsolete files: {len(criteria['obsolete_files']['obsolete_files'])} found\\n")
            self.results_text.insert(tk.END, f"Corrupted files: {len(criteria['corruption']['corrupted_files'])} found\\n")
            self.results_text.insert(tk.END, f"Activity ratio: {criteria['session_activity']['activity_ratio']:.1%}\\n")
            self.results_text.insert(tk.END, f"Completion ratio: {criteria['workflow_completion']['completion_ratio']:.1%}\\n\\n")
            
            self.results_text.insert(tk.END, f"Full report saved to: {report_path}\\n")
            
            # Disable editing
            self.results_text.config(state=tk.DISABLED)
            
            # Update status
            self.status_var.set("Assessment completed")
            self.current_assessment = results
            self._update_schedule_info()
            
        except Exception as e:
            self._show_error(f"Failed to update results: {e}")
    
    def _view_last_report(self):
        """View the last assessment report"""
        try:
            assessment_files = list(self.utils_dir.glob("cleanup_assessment_report_*.json"))
            if not assessment_files:
                messagebox.showinfo("No Reports", "No assessment reports found.")
                return
            
            latest_file = max(assessment_files, key=lambda f: f.stat().st_mtime)
            
            # Try to open with default application
            import webbrowser
            webbrowser.open(str(latest_file))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open report: {e}")
    
    def _manual_cleanup(self):
        """Run manual cleanup with user confirmation"""
        if not self.current_assessment:
            messagebox.showinfo("No Assessment", "Please run an assessment first.")
            return
        
        # Show confirmation dialog
        files_to_clean = len(self.current_assessment['files_to_delete']) + len(self.current_assessment['files_to_archive'])
        
        if files_to_clean == 0:
            messagebox.showinfo("No Action Needed", "No files need cleanup based on the last assessment.")
            return
        
        dry_run = self.cleanup_config["dry_run_mode"].get()
        action_text = "simulate" if dry_run else "execute"
        
        result = messagebox.askyesno(
            "Confirm Cleanup",
            f"This will {action_text} cleanup of {files_to_clean} files.\\n\\n"
            f"Files to delete: {len(self.current_assessment['files_to_delete'])}\\n"
            f"Files to archive: {len(self.current_assessment['files_to_archive'])}\\n\\n"
            f"{'DRY RUN MODE - No files will be modified' if dry_run else 'Files will be permanently modified!'}\\n\\n"
            "Continue?"
        )
        
        if result:
            self._execute_cleanup_thread()
    
    def _execute_cleanup_thread(self):
        """Execute cleanup in separate thread"""
        self.status_var.set("Executing cleanup...")
        threading.Thread(target=self._cleanup_execution_thread, daemon=True).start()
    
    def _cleanup_execution_thread(self):
        """Thread function for executing cleanup"""
        try:
            # Import assessment module
            sys.path.insert(0, str(self.utils_dir))
            
            try:
                import assessment_based_cleanup
                
                # Initialize cleanup system
                cleanup = assessment_based_cleanup.AssessmentBasedCleanup(str(self.utils_dir))
                cleanup.assessment_results = self.current_assessment
                
                # Execute cleanup
                dry_run = self.cleanup_config["dry_run_mode"].get()
                execution_log = cleanup.execute_cleanup(dry_run=dry_run)
                
                # Update GUI
                self.tab.after(0, lambda: self._show_cleanup_results(execution_log))
                
            finally:
                if str(self.utils_dir) in sys.path:
                    sys.path.remove(str(self.utils_dir))
                    
        except Exception as e:
            self.tab.after(0, lambda: self._show_error(f"Cleanup failed: {e}"))
    
    def _show_cleanup_results(self, execution_log):
        """Show cleanup execution results"""
        try:
            # Clear and show results
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            
            # Add header
            mode_text = "DRY RUN" if execution_log['dry_run'] else "EXECUTION"
            self.results_text.insert(tk.END, f"CLEANUP {mode_text} RESULTS\\n")
            self.results_text.insert(tk.END, "=" * 50 + "\\n\\n")
            
            self.results_text.insert(tk.END, f"Execution time: {execution_log['timestamp']}\\n")
            self.results_text.insert(tk.END, f"Total actions: {len(execution_log['actions_taken'])}\\n")
            self.results_text.insert(tk.END, f"Errors: {len(execution_log['errors'])}\\n\\n")
            
            # Show actions
            if execution_log['actions_taken']:
                self.results_text.insert(tk.END, "ACTIONS TAKEN:\\n")
                for action in execution_log['actions_taken']:
                    self.results_text.insert(tk.END, f"• {action}\\n")
                self.results_text.insert(tk.END, "\\n")
            
            # Show errors
            if execution_log['errors']:
                self.results_text.insert(tk.END, "ERRORS:\\n")
                for error in execution_log['errors']:
                    self.results_text.insert(tk.END, f"• {error}\\n")
                self.results_text.insert(tk.END, "\\n")
            
            if not execution_log['dry_run'] and execution_log['actions_taken']:
                self.results_text.insert(tk.END, "Cleanup completed successfully!\\n")
            elif execution_log['dry_run']:
                self.results_text.insert(tk.END, "Dry run completed - no files were modified.\\n")
            
            self.results_text.config(state=tk.DISABLED)
            
            # Update status
            self.status_var.set("Cleanup completed")
            
            # Show message box
            if execution_log['errors']:
                messagebox.showwarning("Cleanup Completed with Errors", 
                                     f"Cleanup completed with {len(execution_log['errors'])} errors. Check the results for details.")
            else:
                messagebox.showinfo("Cleanup Completed", 
                                   f"Cleanup completed successfully! {len(execution_log['actions_taken'])} actions taken.")
                
        except Exception as e:
            self._show_error(f"Failed to show cleanup results: {e}")
    
    def _load_last_assessment(self):
        """Load and display the last assessment results"""
        try:
            assessment_files = list(self.utils_dir.glob("cleanup_assessment_report_*.json"))
            if not assessment_files:
                self.results_text.insert(tk.END, "No previous assessment reports found.\\n")
                self.results_text.insert(tk.END, "Click 'Run Assessment Now' to generate a report.")
                return
            
            latest_file = max(assessment_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                results = json.load(f)
            
            self.current_assessment = results
            self._update_assessment_results(results, str(latest_file))
            
        except Exception as e:
            self.results_text.insert(tk.END, f"Error loading last assessment: {e}")
    
    def _show_error(self, message):
        """Show error message"""
        self.status_var.set("Error")
        messagebox.showerror("Error", message)


def integrate_with_gui(notebook):
    """
    Integrate Cleanup Tasks with the GUI
    
    Args:
        notebook: The main GUI notebook widget
    
    Returns:
        The created tab object
    """
    return CleanupTasksTab(notebook)


# Example for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cleanup Tasks Integration Test")
    root.geometry("1000x700")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Test integration
    tab = integrate_with_gui(notebook)
    
    root.mainloop()