#!/usr/bin/env python
"""
Simple launcher script for the GlowingGoldenGlobe GUI
This script:
1. Ensures desktop shortcuts are up to date
2. Cleans up temporary fix files when they're no longer needed
3. Provides automatic error handling with AI workflow integration
4. Logs maintenance operations for tracking

Usage: 
    python run_ggg_gui.py
"""

import os
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk
import traceback
import glob
import re
import shutil
import importlib.util
from datetime import datetime

# Add the current directory to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Define constants
GUI_CONFIG_FILE = "agent_mode_config.json"
BACKUP_DIR = os.path.join(script_dir, "backups")
MAX_BACKUPS = 5  # Maximum number of backup files to keep per file

def update_desktop_shortcut():
    """Update desktop shortcut using maintenance helper if available"""
    try:
        gui_file = "ggg_maintenance_helper.py"
        gui_path = os.path.join(script_dir, gui_file)
        spec = importlib.util.spec_from_file_location("GGGMaintenance", gui_path)
        if spec is None or spec.loader is None:
            print("Maintenance helper not available, skipping desktop shortcut update")
            return False
        GGGMaintenance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(GGGMaintenance)
        print("Checking if desktop shortcut needs updating...")
        GGGMaintenance.update_desktop_shortcut()
        print("Desktop shortcut check complete")
        return True
    except ImportError:
        print("Maintenance helper not available, skipping desktop shortcut update")
        return False
    except Exception as e:
        print(f"Error updating desktop shortcut: {str(e)}")
        return False

def choose_gui_version():
    """Select the best available GUI version"""
    print("Selecting optimal GUI version...")
    
    # Define parent directory
    parent_dir = os.path.dirname(script_dir)
    
    # List of available GUI versions (file_path, class_name, description)
    gui_versions = [
        (os.path.join(script_dir, "gui_main.py"), "MainGUI", "Primary GUI"),
        (os.path.join(script_dir, "agent_mode_gui_implementation.py"), "AgentModeGUI", "Agent Mode GUI"),
        # Add more GUI versions here if needed
    ]
    
    # Try each version in order
    for file_path, class_name, description in gui_versions:
        if os.path.exists(file_path):
            print(f"Using {description}: {os.path.basename(file_path)}")
            return file_path, class_name
    
    raise FileNotFoundError("No suitable GUI version found")

def patch_geometry_conflict():
    """Patch the TimeLimit class to fix geometry manager conflicts"""
    try:
        import agent_mode_gui_implementation
        
        # Define the fixed TimeLimit class
        class FixedTimeLimit:
            """Fixed helper class for time limit selection UI that uses consistent geometry manager"""
            
            @staticmethod
            def setup_time_limit_ui(options_frame, time_limit_hours, config):
                """Set up the time limit UI with both hours and minutes options using grid consistently"""
                import tkinter as tk
                from tkinter import ttk
                
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
        
        # Patch the TimeLimit class
        agent_mode_gui_implementation.TimeLimit = FixedTimeLimit
        print("Successfully patched TimeLimit class to fix geometry manager conflict")
        return True
    except Exception as e:
        print(f"Error patching geometry conflict: {str(e)}")
        return False

def log_error(error_msg, error_traceback=None):
    """Log error using managed logging with size limits and rotation"""
    try:
        # Import LogManager here to avoid circular imports
        sys.path.insert(0, os.path.dirname(script_dir))
        try:
            from ggg_log_manager import LogManager
            log_mgr = LogManager(os.path.dirname(script_dir))
        except ImportError:
            # Fallback to old method if LogManager not available
            return _log_error_fallback(error_msg, error_traceback)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare temp content (current error only)
        temp_content = f"Current Error ({timestamp}):\n{error_msg}\n"
        if error_traceback:
            # Only include essential traceback info for temp display
            lines = error_traceback.split('\n')
            key_lines = [line for line in lines if 'File "' in line or 'Error:' in line or 'Exception:' in line][:5]
            if key_lines:
                temp_content += "Key traceback lines:\n" + '\n'.join(key_lines) + "\n"
        temp_content += "\nFull error history: gui_launcher_error_log.txt"
        
        # Prepare historical content (complete error)
        historical_content = f"[{timestamp}] ERROR: {error_msg}\n"
        if error_traceback:
            historical_content += f"Traceback:\n{error_traceback}\n\n"
        else:
            historical_content += "\n"
        
        # Write using managed logging (with automatic rotation)
        temp_error_file = os.path.join(script_dir, "temp_error.txt")
        log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
        
        log_mgr.managed_write_log(temp_error_file, temp_content, is_temp=True)
        log_mgr.managed_write_log(log_file, historical_content, is_temp=False)
        
        try:
            # Also log to maintenance system if available
            sys.path.insert(0, os.path.dirname(script_dir))  # Add parent dir to path
            try:
                gui_file = "ggg_maintenance_helper.py"
                gui_path = os.path.join(script_dir, gui_file)
                spec = importlib.util.spec_from_file_location("GGGMaintenance", gui_path)
                if spec is None or spec.loader is None:
                    print("Maintenance helper not available, skipping desktop shortcut update")
                    return False
                GGGMaintenance = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(GGGMaintenance)
                GGGMaintenance.log_maintenance(f"GUI ERROR: {error_msg}", task_type="error", auto_run_ai=True)
            except ImportError:
                # GGGMaintenance not available in ggg_maintenance_helper
                pass
        except Exception:
            # Maintenance system not available, continue without it
            pass
            
        return True
    except:
        return False

def _log_error_fallback(error_msg, error_traceback=None):
    """Fallback logging method if LogManager not available"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write current error to temp file
        temp_error_file = os.path.join(script_dir, "temp_error.txt")
        with open(temp_error_file, "w") as f:
            f.write(f"Current Error ({timestamp}):\n{error_msg}\n")
            if error_traceback:
                lines = error_traceback.split('\n')
                key_lines = [line for line in lines if 'File "' in line or 'Error:' in line][:5]
                if key_lines:
                    f.write("Key traceback lines:\n" + '\n'.join(key_lines) + "\n")
            f.write("\nFull error history: gui_launcher_error_log.txt")
        
        # Append to historical log
        log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] ERROR: {error_msg}\n")
            if error_traceback:
                f.write(f"Traceback:\n{error_traceback}\n\n")
        
        return True
    except:
        return False

def read_error_log():
    """Read the current error using managed logging with reading limits"""
    try:
        # Try to use LogManager for safe reading
        sys.path.insert(0, os.path.dirname(script_dir))
        try:
            from ggg_log_manager import LogManager
            log_mgr = LogManager(os.path.dirname(script_dir))
            
            # Read current error from temp file first
            temp_error_file = os.path.join(script_dir, "temp_error.txt")
            result = log_mgr.safe_read_log(temp_error_file, read_type="display")
            
            if result["success"] and result["content"]:
                return result["content"]
            
            # Fallback to historical log with reading limits
            log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
            result = log_mgr.safe_read_log(log_file, max_lines=20, read_type="display")
            
            if result["success"]:
                return result["content"] if result["content"] else "No recent errors found."
            else:
                return f"Error reading log: {result.get('reason', 'unknown')}"
                
        except ImportError:
            # Fallback to direct reading if LogManager not available
            return _read_error_log_fallback()
            
    except Exception as e:
        return f"Error reading error information: {str(e)}"

def _read_error_log_fallback():
    """Fallback reading method with basic limits"""
    try:
        # Read current error from temp file first
        temp_error_file = os.path.join(script_dir, "temp_error.txt")
        if os.path.exists(temp_error_file):
            with open(temp_error_file, "r") as f:
                content = f.read(5000)  # Limit to 5000 characters
                return content
        
        # Fallback to reading last 50 lines from historical log
        log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
        if not os.path.exists(log_file):
            return "No error information available."
        
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Return last 50 lines maximum
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            content = ''.join(recent_lines)
            # Limit total characters
            return content[-5000:] if len(content) > 5000 else content
        
    except Exception as e:
        return f"Error reading error information: {str(e)}"

def read_full_error_log():
    """Read the complete historical error log (only when specifically needed)"""
    try:
        log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
        if not os.path.exists(log_file):
            return "No historical error log found."
        
        with open(log_file, "r") as f:
            content = f.read()
            
        # Return last 3000 characters if file is too large
        if len(content) > 3000:
            return "...\n" + content[-3000:]
        return content
    except Exception as e:
        return f"Error reading full log file: {str(e)}"

def verify_gui_launch(root, app):
    """Verify that the GUI has successfully launched by checking critical components"""
    try:
        # Check that the root window exists and is responsive
        if not root.winfo_exists():
            return False, "GUI window failed to initialize"
            
        # Check that the app object has been created properly
        if not hasattr(app, "main_tab"):
            return False, "GUI components failed to initialize"
            
        # Check that critical UI components are available
        if not hasattr(app, "notebook") or not app.notebook.winfo_exists():
            return False, "GUI tabs failed to initialize"

        # Successful verification
        return True, "GUI launched successfully"
    except Exception as e:
        return False, f"Error verifying GUI launch: {str(e)}"

def monitor_gui_status(root, app, check_interval=30):
    """Monitor GUI status continuously after launch
    
    Args:
        root: The Tkinter root window
        app: The main application instance
        check_interval: How often to check status (in seconds)
    """
    def check_status():
        try:
            # Skip checks if window doesn't exist anymore
            if not root.winfo_exists():
                return
                
            # Check critical components are still functioning
            if not hasattr(app, "notebook") or not app.notebook.winfo_exists():
                # Log error
                log_error("GUI monitoring detected failure: notebook widget no longer exists")
                messagebox.showerror(
                    "GUI Error",
                    "An error occurred with the GUI components.\nSee gui_launcher_error_log.txt for details."
                )
                return
                
            # Schedule next check
            root.after(check_interval * 1000, check_status)
            
        except Exception as e:
            # Something went wrong during the check itself
            try:
                log_error(f"GUI monitoring error: {str(e)}", traceback.format_exc())
            except:
                pass
    
    # Schedule first check
    root.after(check_interval * 1000, check_status)

def check_error_log(root, check_interval=60):
    """Periodically check the error log file for new errors
    
    Args:
        root: The Tkinter root window
        check_interval: How often to check the log file (in seconds)
    """
    try:
        log_file = os.path.join(script_dir, "gui_launcher_error_log.txt")
        
        # If file doesn't exist, create a timestamp to track future errors
        if not os.path.exists(log_file):
            # Nothing to check yet
            if root.winfo_exists():
                root.after(check_interval * 1000, lambda: check_error_log(root, check_interval))
            return
            
        # Check file modification time
        last_modified = os.path.getmtime(log_file)
        current_time = time.time()
        
        # Store the last check time as an attribute on the root window
        if not hasattr(root, '_last_error_check'):
            root._last_error_check = current_time
            root._last_log_modified = last_modified
            
        # If the log file has been modified since our last check
        if last_modified > root._last_error_check:
            # Read the new content
            with open(log_file, "r") as f:
                content = f.read()
                
            # Check for critical errors in the new content
            recent_errors = []
            for line in content.splitlines():
                if "] ERROR:" in line and "timestamp" in line:
                    error_time = datetime.strptime(line.split("]")[0].strip("["), "%Y-%m-%d %H:%M:%S")
                    error_age = (datetime.now() - error_time).total_seconds()
                    
                    # If error is recent (within the last minute)
                    if error_age < check_interval * 2:
                        recent_errors.append(line)
                        
            # If there are new errors, show a notification
            if recent_errors and root.winfo_exists():
                messagebox.showwarning(
                    "GUI Warning", 
                    f"Detected issues in the error log:\n\n{recent_errors[-1]}\n\nCheck the error log for details."
                )
        
        # Update the last check time
        root._last_error_check = current_time
        root._last_log_modified = last_modified
        
        # Schedule next check if root still exists
        if root.winfo_exists():
            root.after(check_interval * 1000, lambda: check_error_log(root, check_interval))
            
    except Exception as e:
        # Don't show any errors from the error checker itself
        print(f"Error checking log file: {str(e)}")
        # Still try to schedule the next check
        if root.winfo_exists():
            root.after(check_interval * 1000, lambda: check_error_log(root, check_interval))

def main():
    """Main entry point"""
    try:
        # 1. Update desktop shortcut
        update_desktop_shortcut()
        
        # 2. Apply geometry conflict patch
        patch_geometry_conflict()
        
        # 3. Choose best available GUI version
        gui_path, gui_version = choose_gui_version()
        spec = importlib.util.spec_from_file_location("gui_main", gui_path)
        if spec is None:
            raise ImportError(f"Could not create module spec for {gui_path}")

        gui_module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Module loader is None for {gui_path}")

        # 4. Load the module with error handling
        try:
            spec.loader.exec_module(gui_module)
        except ImportError as import_err:
            # Check if this is the apply_gui_enhancements error
            if "cannot import name 'apply_gui_enhancements'" in str(import_err):
                error_traceback = traceback.format_exc()
                log_error("Import error with apply_gui_enhancements, attempting to fix...", error_traceback)
                
                # Create a small fix script to correct the import in gui_enhanced.py
                try:
                    fix_path = os.path.join(script_dir, "gui_enhanced.py")
                    if os.path.exists(fix_path):
                        with open(fix_path, "r") as f:
                            content = f.read()
                            
                        if "implement_enhancements" in content and "apply_gui_enhancements = implement_enhancements" not in content:
                            # Add the alias if needed
                            with open(fix_path, "a") as f:
                                f.write("\n# Fix added by launcher\napply_gui_enhancements = implement_enhancements\n")
                            
                        # Try again with the fix
                        spec.loader.exec_module(gui_module)
                        print("Successfully fixed import issue.")
                    else:
                        raise import_err
                except Exception:
                    # If fix fails, raise the original error
                    raise import_err
            else:
                raise import_err

        # 5. Create and run the GUI with verification
        root = tk.Tk()
        
        # Use the selected GUI class name
        app = getattr(gui_module, gui_version)(root)
        
        # Verify that the GUI launched correctly
        success, message = verify_gui_launch(root, app)
        if not success:
            raise RuntimeError(f"GUI verification failed: {message}")
            
        # Log successful launch
        print(f"GUI successfully launched: {message}")
        
        # Monitor GUI status
        monitor_gui_status(root, app)
        
        # Check error log periodically
        check_error_log(root)
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Error starting GlowingGoldenGlobe GUI: {str(e)}"
        error_traceback = traceback.format_exc()
        log_error(error_msg, error_traceback)
          
        # Show enhanced error dialog with options to view log
        try:
            error_window = tk.Tk()
            error_window.title("GlowingGoldenGlobe Error")
            error_window.geometry("600x400")
            
            # Main frame
            main_frame = ttk.Frame(error_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Error message
            ttk.Label(
                main_frame, 
                text=f"Failed to start GlowingGoldenGlobe GUI", 
                font=("Arial", 12, "bold")
            ).pack(pady=(0, 10))
            
            ttk.Label(
                main_frame, 
                text=f"Error: {str(e)}",
                wraplength=550
            ).pack(pady=(0, 10))
            
            # Frame for error log
            log_frame = ttk.LabelFrame(main_frame, text="Error Log", padding=10)
            log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Error log text
            log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            log_text.insert(tk.END, read_error_log())
            log_text.config(state=tk.DISABLED)
            
            # Scrollbar for error log
            scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            log_text.config(yscrollcommand=scrollbar.set)
            
            # Buttons frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            # Retry button
            ttk.Button(
                button_frame, 
                text="Retry Launch", 
                command=lambda: [error_window.destroy(), main()]
            ).pack(side=tk.LEFT, padx=5)
            
            # Copy log button
            def copy_to_clipboard():
                error_window.clipboard_clear()
                error_window.clipboard_append(log_text.get("1.0", tk.END))
                ttk.Label(button_frame, text="Log copied to clipboard", foreground="green").pack(side=tk.LEFT, padx=5)
                
            ttk.Button(
                button_frame, 
                text="Copy Log", 
                command=copy_to_clipboard
            ).pack(side=tk.LEFT, padx=5)
            
            # Exit button
            ttk.Button(
                button_frame, 
                text="Exit", 
                command=error_window.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
            error_window.mainloop()
            
        except Exception:
            # Fallback to simple error message if the enhanced dialog fails
            try:
                messagebox.showerror(
                    "GlowingGoldenGlobe Error",
                    f"{error_msg}\n\nCheck gui_launcher_error_log.txt for details."
                )
            except:
                print(f"\nERROR: {error_msg}")
                print("\nSee gui_launcher_error_log.txt for details")

if __name__ == "__main__":
    main()