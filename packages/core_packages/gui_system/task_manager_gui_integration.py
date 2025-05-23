#!/usr/bin/env python
# Task Manager GUI Integration
# Connects Windows Task Manager directly to the GlowingGoldenGlobe GUI

import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import platform
import importlib.util

# Dynamic import of modules based on OS
def import_monitor_module():
    """Import the appropriate monitoring module based on the OS"""
    if platform.system() == "Windows" or ("microsoft" in platform.platform().lower()):
        # Check if win32 modules are available
        win32_available = importlib.util.find_spec("win32evtlog") is not None
        
        if win32_available:
            # Add parent directory to path
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            try:
                import task_manager_integration
                return task_manager_integration.TaskManagerIntegration
            except ImportError:
                pass
        
        # Fallback to WMI-based monitor
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            import windows_resource_monitor
            return windows_resource_monitor.WindowsResourceMonitor
        except ImportError:
            pass
    
    # Default fallback
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import hardware_monitor
        return hardware_monitor.HardwareMonitor
    except ImportError:
        # Create a minimal placeholder class
        class MinimalMonitor:
            def __init__(self, *args, **kwargs):
                pass
                
            def get_hardware_info(self):
                return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}
                
            def get_system_summary(self):
                return {"platform": platform.platform(), "processor": "Unknown"}
                
            def start_monitoring(self, interval=30):
                pass
                
            def stop_monitoring(self):
                pass
        
        return MinimalMonitor

class TaskManagerMonitorTab:
    """Task Manager integration tab for the GlowingGoldenGlobe GUI"""
    
    def __init__(self, parent_notebook):
        """
        Initialize the Task Manager monitor tab
        
        Args:
            parent_notebook: The parent ttk.Notebook widget
        """
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="System Monitor")
        
        # Import appropriate monitor module
        MonitorClass = import_monitor_module()
        self.monitor = MonitorClass()
        
        # Status variables
        self.status_var = tk.StringVar(value="Task Manager Integration Ready")
        self.direct_integration = tk.BooleanVar(value=False)
        
        # Alert log
        self.alerts = []
        
        # Set up tab content
        self._create_widgets()
        
        # Start monitoring if win32 modules are available
        win32_available = importlib.util.find_spec("win32evtlog") is not None
        if win32_available and (platform.system() == "Windows" or "microsoft" in platform.platform().lower()):
            self.direct_integration.set(True)
            self._setup_direct_monitoring()
    
    def _create_widgets(self):
        """Create widgets for the Task Manager monitor tab"""
        # Main layout frame with padding
        main_frame = ttk.Frame(self.tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        ttk.Label(main_frame, text="Windows Task Manager Integration", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 5))
        
        ttk.Label(main_frame, text="Monitor system resources directly from Windows Task Manager",
                 font=("Arial", 10)).pack(pady=(0, 20))
        
        # System info section
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        # Get system info
        system_info = self.monitor.get_system_summary()
        
        # Display system info
        ttk.Label(info_frame, text=f"Platform: {system_info.get('platform', 'Unknown')}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Processor: {system_info.get('processor', 'Unknown')}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Memory: {system_info.get('total_memory_gb', 'Unknown')} GB").pack(anchor=tk.W, pady=2)
        
        # Integration options
        options_frame = ttk.LabelFrame(main_frame, text="Integration Options", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Direct integration checkbox
        ttk.Checkbutton(options_frame, text="Use direct Task Manager integration", 
                       variable=self.direct_integration,
                       command=self._toggle_direct_integration).pack(anchor=tk.W, pady=5)
        
        ttk.Label(options_frame, text="Note: Direct integration requires administrator rights").pack(anchor=tk.W, pady=2)
        
        # Threshold settings
        threshold_frame = ttk.Frame(options_frame)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(threshold_frame, text="Alert Thresholds:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # CPU threshold
        ttk.Label(threshold_frame, text="CPU:").grid(row=1, column=0, sticky=tk.W, pady=2, padx=(20, 5))
        self.cpu_threshold = tk.StringVar(value=str(self.monitor.thresholds.get("cpu_percent", 80)))
        ttk.Spinbox(threshold_frame, from_=50, to=95, width=5, 
                   textvariable=self.cpu_threshold).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(threshold_frame, text="%").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Memory threshold
        ttk.Label(threshold_frame, text="Memory:").grid(row=2, column=0, sticky=tk.W, pady=2, padx=(20, 5))
        self.memory_threshold = tk.StringVar(value=str(self.monitor.thresholds.get("memory_percent", 85)))
        ttk.Spinbox(threshold_frame, from_=50, to=95, width=5, 
                   textvariable=self.memory_threshold).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(threshold_frame, text="%").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # Disk threshold
        ttk.Label(threshold_frame, text="Disk:").grid(row=3, column=0, sticky=tk.W, pady=2, padx=(20, 5))
        self.disk_threshold = tk.StringVar(value=str(self.monitor.thresholds.get("disk_percent", 90)))
        ttk.Spinbox(threshold_frame, from_=50, to=95, width=5, 
                   textvariable=self.disk_threshold).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Label(threshold_frame, text="%").grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # Apply button
        ttk.Button(options_frame, text="Apply Thresholds", 
                  command=self._apply_thresholds).pack(anchor=tk.E, pady=10)
        
        # Current readings section (matches Task Manager)
        readings_frame = ttk.LabelFrame(main_frame, text="Current Task Manager Readings", padding="10")
        readings_frame.pack(fill=tk.X, pady=10)
        
        # CPU reading
        cpu_frame = ttk.Frame(readings_frame)
        cpu_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cpu_frame, text="CPU Usage:").pack(side=tk.LEFT, padx=(0, 10))
        self.cpu_label = ttk.Label(cpu_frame, text="0%")
        self.cpu_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=200, mode='determinate')
        self.cpu_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.cpu_level = ttk.Label(cpu_frame, text="Normal", foreground="green")
        self.cpu_level.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Memory reading
        memory_frame = ttk.Frame(readings_frame)
        memory_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(memory_frame, text="Memory:").pack(side=tk.LEFT, padx=(0, 10))
        self.memory_label = ttk.Label(memory_frame, text="0%")
        self.memory_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=200, mode='determinate')
        self.memory_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.memory_level = ttk.Label(memory_frame, text="Normal", foreground="green")
        self.memory_level.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Disk reading
        disk_frame = ttk.Frame(readings_frame)
        disk_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(disk_frame, text="Disk Usage:").pack(side=tk.LEFT, padx=(0, 10))
        self.disk_label = ttk.Label(disk_frame, text="0%")
        self.disk_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=200, mode='determinate')
        self.disk_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.disk_level = ttk.Label(disk_frame, text="Normal", foreground="green")
        self.disk_level.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Refresh button
        refresh_frame = ttk.Frame(readings_frame)
        refresh_frame.pack(fill=tk.X, pady=5)
        
        self.auto_refresh = tk.BooleanVar(value=True)
        ttk.Checkbutton(refresh_frame, text="Auto-refresh", 
                       variable=self.auto_refresh).pack(side=tk.LEFT)
        
        ttk.Button(refresh_frame, text="Refresh Now", 
                  command=self._refresh_readings).pack(side=tk.RIGHT)
        
        # Alert log section
        alert_frame = ttk.LabelFrame(main_frame, text="Task Manager Alerts", padding="10")
        alert_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollable text for alerts
        self.alert_text = tk.Text(alert_frame, height=10, width=50, wrap=tk.WORD)
        alert_scrollbar = ttk.Scrollbar(alert_frame, command=self.alert_text.yview)
        self.alert_text.configure(yscrollcommand=alert_scrollbar.set)
        
        self.alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Start auto-refresh timer
        self._start_auto_refresh()
    
    def _toggle_direct_integration(self):
        """Toggle between direct Task Manager integration and custom monitoring"""
        if self.direct_integration.get():
            self._setup_direct_monitoring()
        else:
            self._setup_custom_monitoring()
    
    def _setup_direct_monitoring(self):
        """Set up direct Task Manager integration"""
        # Only available on Windows
        if platform.system() != "Windows" and not ("microsoft" in platform.platform().lower()):
            messagebox.showinfo("Not Available", "Direct Task Manager integration is only available on Windows")
            self.direct_integration.set(False)
            return
        
        # Check if we have win32 modules
        win32_available = importlib.util.find_spec("win32evtlog") is not None
        if not win32_available:
            messagebox.showinfo("Module Missing", 
                              "The win32evtlog module is required for direct integration.\n"
                              "Please install it with: pip install pywin32")
            self.direct_integration.set(False)
            return
        
        try:
            # Import the module
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import task_manager_integration
            
            # Replace the current monitor
            self.monitor = task_manager_integration.TaskManagerIntegration(callback=self._handle_alert)
            
            # Apply current thresholds
            self._apply_thresholds()
            
            # Start monitoring
            self.monitor.start_monitoring()
            
            self.status_var.set("Direct Task Manager integration active")
            self._add_alert("Direct Task Manager integration enabled", level="info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set up direct integration: {str(e)}")
            self.direct_integration.set(False)
    
    def _setup_custom_monitoring(self):
        """Set up custom resource monitoring"""
        try:
            # Import hardware monitor
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import hardware_monitor
            
            # Replace the current monitor
            self.monitor = hardware_monitor.HardwareMonitor()
            
            # Apply current thresholds
            self._apply_thresholds()
            
            # Start monitoring
            self.monitor.start_monitoring(interval=10)
            
            self.status_var.set("Custom hardware monitoring active")
            self._add_alert("Switched to custom hardware monitoring", level="info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set up custom monitoring: {str(e)}")
    
    def _apply_thresholds(self):
        """Apply threshold settings to the monitor"""
        try:
            # Get threshold values
            cpu_threshold = int(self.cpu_threshold.get())
            memory_threshold = int(self.memory_threshold.get())
            disk_threshold = int(self.disk_threshold.get())
            
            # Update monitor thresholds
            self.monitor.thresholds = {
                "cpu_percent": cpu_threshold,
                "memory_percent": memory_threshold,
                "disk_percent": disk_threshold
            }
            
            # Save configuration
            if hasattr(self.monitor, "save_config"):
                self.monitor.save_config()
            
            self.status_var.set("Thresholds applied")
            self._add_alert(f"Alert thresholds updated: CPU {cpu_threshold}%, Memory {memory_threshold}%, Disk {disk_threshold}%", 
                          level="info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply thresholds: {str(e)}")
    
    def _refresh_readings(self):
        """Refresh current resource readings"""
        try:
            # Get current info from monitor
            info = self.monitor.get_hardware_info()
            
            # Update CPU display
            cpu_percent = info.get("cpu_percent", 0)
            self.cpu_label.config(text=f"{cpu_percent:.1f}%")
            self.cpu_progress["value"] = cpu_percent
            
            # Update CPU level indicator
            if cpu_percent < 30:
                self.cpu_level.config(text="Very Low", foreground="green")
            elif cpu_percent < 60:
                self.cpu_level.config(text="Normal", foreground="green")
            elif cpu_percent < 80:
                self.cpu_level.config(text="Medium", foreground="orange")
            elif cpu_percent < 90:
                self.cpu_level.config(text="High", foreground="orange")
            else:
                self.cpu_level.config(text="Very High", foreground="red")
            
            # Update Memory display
            memory_percent = info.get("memory_percent", 0)
            memory_used_gb = info.get("memory_total", 0) / (1024**3) - info.get("memory_available", 0) / (1024**3)
            memory_total_gb = info.get("memory_total", 0) / (1024**3)
            
            if memory_total_gb > 0:
                self.memory_label.config(text=f"{memory_percent:.1f}% ({memory_used_gb:.1f}/{memory_total_gb:.1f} GB)")
            else:
                self.memory_label.config(text=f"{memory_percent:.1f}%")
                
            self.memory_progress["value"] = memory_percent
            
            # Update Memory level indicator
            if memory_percent < 50:
                self.memory_level.config(text="Low", foreground="green")
            elif memory_percent < 75:
                self.memory_level.config(text="Normal", foreground="green")
            elif memory_percent < 85:
                self.memory_level.config(text="Medium", foreground="orange")
            else:
                self.memory_level.config(text="High", foreground="red")
            
            # Update Disk display
            disk_percent = info.get("disk_percent", 0)
            disk_used_gb = (info.get("disk_total", 0) - info.get("disk_free", 0)) / (1024**3)
            disk_total_gb = info.get("disk_total", 0) / (1024**3)
            
            if disk_total_gb > 0:
                self.disk_label.config(text=f"{disk_percent:.1f}% ({disk_used_gb:.1f}/{disk_total_gb:.1f} GB)")
            else:
                self.disk_label.config(text=f"{disk_percent:.1f}%")
                
            self.disk_progress["value"] = disk_percent
            
            # Update Disk level indicator
            if disk_percent < 50:
                self.disk_level.config(text="Low", foreground="green")
            elif disk_percent < 75:
                self.disk_level.config(text="Normal", foreground="green")
            elif disk_percent < 90:
                self.disk_level.config(text="Medium", foreground="orange")
            else:
                self.disk_level.config(text="High", foreground="red")
            
            # Update status
            self.status_var.set(f"Last update: {time.strftime('%H:%M:%S')}")
            
            # Check for alerts
            self._check_for_alerts(info)
            
        except Exception as e:
            self.status_var.set(f"Error refreshing: {str(e)}")
    
    def _check_for_alerts(self, info):
        """Check for resource alerts based on thresholds"""
        cpu_percent = info.get("cpu_percent", 0)
        memory_percent = info.get("memory_percent", 0)
        disk_percent = info.get("disk_percent", 0)
        
        # Get thresholds
        cpu_threshold = int(self.cpu_threshold.get())
        memory_threshold = int(self.memory_threshold.get())
        disk_threshold = int(self.disk_threshold.get())
        
        # Check CPU
        if cpu_percent > cpu_threshold:
            self._add_alert(f"High CPU usage: {cpu_percent:.1f}% (threshold: {cpu_threshold}%)", 
                          level="warning")
        
        # Check Memory
        if memory_percent > memory_threshold:
            self._add_alert(f"High Memory usage: {memory_percent:.1f}% (threshold: {memory_threshold}%)", 
                          level="warning")
        
        # Check Disk
        if disk_percent > disk_threshold:
            self._add_alert(f"High Disk usage: {disk_percent:.1f}% (threshold: {disk_threshold}%)", 
                          level="warning")
    
    def _add_alert(self, message, level="info"):
        """Add an alert to the log"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Store alert
        self.alerts.append({
            "timestamp": timestamp,
            "message": message,
            "level": level
        })
        
        # Determine color
        if level == "error":
            color = "red"
        elif level == "warning":
            color = "orange"
        else:
            color = "green"
        
        # Update alert text
        self.alert_text.config(state=tk.NORMAL)
        
        # Insert with color tag
        tag_name = f"color_{len(self.alerts)}"
        self.alert_text.tag_configure(tag_name, foreground=color)
        
        self.alert_text.insert(tk.END, f"[{timestamp}] ", tag_name)
        self.alert_text.insert(tk.END, f"{message}\n", tag_name)
        
        # Scroll to end
        self.alert_text.see(tk.END)
        
        # Disable editing
        self.alert_text.config(state=tk.DISABLED)
    
    def _handle_alert(self, alert_info):
        """Handle an alert from the Task Manager integration"""
        message = alert_info.get("message", "Unknown alert")
        self._add_alert(message, level="warning")
    
    def _start_auto_refresh(self):
        """Start auto-refresh timer"""
        def refresh_loop():
            # Only update if auto-refresh is enabled
            if self.auto_refresh.get():
                self._refresh_readings()
            
            # Schedule next update
            self.tab.after(2000, refresh_loop)
        
        # Start first refresh
        self.tab.after(100, refresh_loop)

def integrate_with_gui(notebook):
    """
    Integrate Task Manager monitoring with the GUI
    
    Args:
        notebook: The main GUI notebook widget
    
    Returns:
        The created tab object
    """
    return TaskManagerMonitorTab(notebook)

# Example for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Task Manager Integration Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Test integration
    tab = integrate_with_gui(notebook)
    
    root.mainloop()