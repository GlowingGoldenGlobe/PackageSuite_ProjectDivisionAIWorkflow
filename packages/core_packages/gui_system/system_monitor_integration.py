#!/usr/bin/env python
# System Monitor Integration with Windows Built-in Services
# Uses Windows Task Manager, Performance Monitor, and WMI for maximum efficiency

import os
import sys
import time
import json
import datetime
import tkinter as tk
from tkinter import ttk
import platform
import subprocess
import threading
import importlib.util
import datetime

# Import resource manager components for alert handling if available
try:
    from resource_manager import get_resource_manager
    RESOURCE_MANAGER_AVAILABLE = True
except ImportError:
    RESOURCE_MANAGER_AVAILABLE = False
    
# Try to import system integration
try:
    from integrate_system_resource_manager import get_system_resource_integration
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    
# Try to import project resource manager
try:
    from ai_managers.project_resource_manager import ProjectResourceManager
    PROJECT_RESOURCE_MANAGER_AVAILABLE = True
except ImportError:
    PROJECT_RESOURCE_MANAGER_AVAILABLE = False

# Check for Windows platform and available modules
IS_WINDOWS = platform.system() == "Windows" or "microsoft" in platform.release().lower()
WMI_AVAILABLE = False
PYWIN32_AVAILABLE = False

if IS_WINDOWS:
    try:
        import wmi
        WMI_AVAILABLE = True
    except ImportError:
        pass
    
    try:
        import win32api
        import win32con
        import win32evtlog
        PYWIN32_AVAILABLE = True
    except ImportError:
        pass

class WindowsPerformanceMonitor:
    """Efficient Windows Performance Monitor using built-in services"""
    
    def __init__(self, update_callback=None, alert_callback=None):
        """
        Initialize performance monitor
        
        Args:
            update_callback: Function to call with new performance data
            alert_callback: Function to call when performance alerts occur
        """
        self.update_callback = update_callback
        self.alert_callback = alert_callback
        self.monitoring = False
        self.monitor_thread = None
        self.wmi_connection = None
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90
        }
        
        # Initialize WMI connection if available
        if IS_WINDOWS and WMI_AVAILABLE:
            try:
                import wmi
                self.wmi_connection = wmi.WMI()
            except Exception as e:
                print(f"Error initializing WMI: {str(e)}")
    
    # Cache for performance data to avoid spawning too many processes
    _performance_cache = {}
    _last_cache_time = 0
    _cache_validity = 2  # Cache validity in seconds
    _powershell_process = None
    
    def get_performance_data(self):
        """Get performance data from Windows built-in services - aligned directly with Task Manager"""
        # Use cached data if it's still valid
        current_time = time.time()
        if current_time - self._last_cache_time < self._cache_validity and self._performance_cache:
            return self._performance_cache.copy()
            
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "memory_total": 0,
            "memory_available": 0,
            "disk_total": 0,
            "disk_free": 0
        }
        
        if not IS_WINDOWS:
            return data
            
        try:
            # Use WMI for more stability (less process spawning)
            if WMI_AVAILABLE and self.wmi_connection:
                self._get_data_from_wmi(data)
                # Make small adjustments to match Task Manager display
                if "cpu_percent" in data:
                    data["cpu_percent"] = round(data["cpu_percent"], 1)
                if "memory_percent" in data:
                    data["memory_percent"] = round(data["memory_percent"], 1)
                if "disk_percent" in data:
                    data["disk_percent"] = round(data["disk_percent"], 1)
                    
                # Update cache
                self._performance_cache = data.copy()
                self._last_cache_time = current_time
                return data
                
            # Fallback to PowerShell if WMI not available - with optimizations to reduce process spawning
            ps_cmd = """
            # Get CPU usage exactly as Task Manager calculates it - with minimal sampling
            $cpu = (Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 1 | 
                   Select-Object -ExpandProperty CounterSamples | 
                   Select-Object -ExpandProperty CookedValue)
            
            # Get Memory usage exactly as Task Manager shows it
            $memoryPerformanceInfo = Get-Counter '\\Memory\\% Committed Bytes In Use' -SampleInterval 1 -MaxSamples 1 | 
                     Select-Object -ExpandProperty CounterSamples | 
                     Select-Object -ExpandProperty CookedValue
            
            # Get physical memory details for displaying GB values - use Get-WmiObject for better compatibility
            $memoryInfo = Get-WmiObject Win32_OperatingSystem
            $totalMemory = $memoryInfo.TotalVisibleMemorySize * 1KB
            $freeMemory = $memoryInfo.FreePhysicalMemory * 1KB
            
            # Get C: drive usage exactly as Task Manager shows it - use Get-WmiObject for better compatibility
            $diskInfo = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
            $diskTotal = $diskInfo.Size
            $diskFree = $diskInfo.FreeSpace
            $diskPercent = 100 - ($diskFree / $diskTotal * 100)
            
            Write-Output "$cpu"
            Write-Output "$memoryPerformanceInfo"
            Write-Output "$totalMemory"
            Write-Output "$freeMemory"
            Write-Output "$diskTotal"
            Write-Output "$diskFree"
            Write-Output "$diskPercent"
            """
            
            # Use subprocess with minimal window visibility
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
            result = subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], 
                                  capture_output=True, text=True, 
                                  startupinfo=startupinfo)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 7:
                    try:
                        # CPU - direct from Task Manager calculation
                        data["cpu_percent"] = round(float(lines[0]), 1)  # Round to match Task Manager display
                        
                        # Memory - direct from Task Manager calculation
                        data["memory_percent"] = round(float(lines[1]), 1)  # Round to match Task Manager display
                        
                        # Memory details
                        data["memory_total"] = float(lines[2])  # Already in bytes
                        data["memory_available"] = float(lines[3])  # Already in bytes
                        
                        # Disk details
                        data["disk_total"] = float(lines[4])
                        data["disk_free"] = float(lines[5])
                        data["disk_percent"] = round(float(lines[6]), 1)  # Direct from Task Manager calculation
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing performance data: {str(e)}")
                        
                        # Fallback to WMI if available
                        if WMI_AVAILABLE and self.wmi_connection:
                            self._get_data_from_wmi(data)
            else:
                # Fallback to WMI if PowerShell command failed
                if WMI_AVAILABLE and self.wmi_connection:
                    self._get_data_from_wmi(data)
        except Exception as e:
            print(f"Error getting performance data: {str(e)}")
            # Fallback to WMI if available
            if WMI_AVAILABLE and self.wmi_connection:
                self._get_data_from_wmi(data)
                
        return data
        
    def _get_data_from_wmi(self, data):
        """Fallback method to get data from WMI"""
        try:
            # CPU usage
            cpu_info = self.wmi_connection.Win32_Processor()
            if cpu_info:
                cpu_load_sum = sum(cpu.LoadPercentage for cpu in cpu_info if hasattr(cpu, 'LoadPercentage'))
                data["cpu_percent"] = cpu_load_sum / len(cpu_info) if len(cpu_info) > 0 else 0
            
            # Memory usage
            os_info = self.wmi_connection.Win32_OperatingSystem()
            if os_info and len(os_info) > 0:
                total_memory = float(os_info[0].TotalVisibleMemorySize) * 1024  # KB to bytes
                free_memory = float(os_info[0].FreePhysicalMemory) * 1024  # KB to bytes
                data["memory_total"] = total_memory
                data["memory_available"] = free_memory
                data["memory_percent"] = 100 * (1 - free_memory / total_memory) if total_memory > 0 else 0
            
            # Disk usage
            disk_info = self.wmi_connection.Win32_LogicalDisk(DeviceID="C:")
            if disk_info and len(disk_info) > 0:
                total_disk = float(disk_info[0].Size)
                free_disk = float(disk_info[0].FreeSpace)
                data["disk_total"] = total_disk
                data["disk_free"] = free_disk
                data["disk_percent"] = 100 * (1 - free_disk / total_disk) if total_disk > 0 else 0
        except Exception as e:
            print(f"Error in WMI fallback: {str(e)}")
            
            return data
            
        except Exception as e:
            print(f"Error getting performance data: {str(e)}")
            return data
    
    def check_alerts(self, data):
        """Check performance data against thresholds"""
        alerts = []
        
        # CPU alert
        if data["cpu_percent"] > self.thresholds["cpu_percent"]:
            alerts.append({
                "type": "cpu",
                "value": data["cpu_percent"],
                "threshold": self.thresholds["cpu_percent"],
                "message": f"CPU usage is high: {data['cpu_percent']:.1f}%"
            })
        
        # Memory alert
        if data["memory_percent"] > self.thresholds["memory_percent"]:
            alerts.append({
                "type": "memory",
                "value": data["memory_percent"],
                "threshold": self.thresholds["memory_percent"],
                "message": f"Memory usage is high: {data['memory_percent']:.1f}%"
            })
        
        # Disk alert
        if data["disk_percent"] > self.thresholds["disk_percent"]:
            alerts.append({
                "type": "disk",
                "value": data["disk_percent"],
                "threshold": self.thresholds["disk_percent"],
                "message": f"Disk usage is high: {data['disk_percent']:.1f}%"
            })
        
        return alerts
    
    def monitor_performance_thread(self):
        """Background thread for monitoring performance"""
        update_counter = 0
        alert_counter = 0
        
        while self.monitoring:
            try:
                # Get current performance data (uses cache when possible)
                data = self.get_performance_data()
                
                # Call update callback less frequently for UI updates
                # (Every 2 seconds is sufficient for UI, and reduces resource usage)
                update_counter += 1
                if update_counter >= 2:  # Update UI every ~2 seconds
                    if self.update_callback:
                        self.update_callback(data)
                    update_counter = 0
                
                # Check for alerts even less frequently
                # (Only needed every ~10 seconds and reduces PowerShell spawning)
                alert_counter += 1
                if alert_counter >= 10:  # Check alerts every ~10 seconds
                    alerts = self.check_alerts(data)
                    if alerts and self.alert_callback:
                        for alert in alerts:
                            self.alert_callback(alert)
                    alert_counter = 0
                
                # Wait before next update (slightly longer pause between checks)
                time.sleep(1)  # Base wait time between checks
                
            except Exception as e:
                print(f"Error in performance monitor thread: {str(e)}")
                time.sleep(5)  # Longer sleep on error
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_performance_thread, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
    
    def set_thresholds(self, cpu=None, memory=None, disk=None):
        """Set performance alert thresholds"""
        if cpu is not None:
            self.thresholds["cpu_percent"] = cpu
        if memory is not None:
            self.thresholds["memory_percent"] = memory
        if disk is not None:
            self.thresholds["disk_percent"] = disk

class SystemMonitorTab:
    """System Monitor tab using Windows built-in services"""
    
    # Class-level variable to track if an instance exists (to prevent multiple PowerShell processes)
    _instance_exists = False
    
    def __init__(self, parent_notebook):
        """
        Initialize the system monitor tab
        
        Args:
            parent_notebook: Parent ttk.Notebook widget
        """
        # Check if an instance already exists
        if SystemMonitorTab._instance_exists:
            print("Warning: Multiple SystemMonitorTab instances may cause performance issues")
            
        SystemMonitorTab._instance_exists = True
        
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="System Monitor")
        
        # Initialize monitor with reduced update frequency
        self.monitor = WindowsPerformanceMonitor(
            update_callback=self.update_performance_display,
            alert_callback=self.handle_alert
        )
        # Increase cache validity to reduce PowerShell processes
        self.monitor._cache_validity = 3  # Cache performance data for 3 seconds
        
        # Performance data
        self.performance_data = {}
        
        # Alert storage
        self.alerts = []
        
        # Last update time to prevent too-frequent updates
        self.last_update_time = 0
        self.update_interval = 3.0  # seconds
        
        # Create UI
        self._create_ui()
        
        # Start monitoring with a longer interval
        self.monitor.start_monitoring()
        
    def __del__(self):
        # Reset the class-level instance tracker when this instance is deleted
        SystemMonitorTab._instance_exists = False
    
    def _create_ui(self):
        """Create the user interface"""
        main_frame = ttk.Frame(self.tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="System Resource Monitor", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # System Info section
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid for system info
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_grid, text="Platform:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        self.platform_label = ttk.Label(info_grid, text=platform.platform())
        self.platform_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_grid, text="CPU:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        self.cpu_info_label = ttk.Label(info_grid, text="Querying system...")
        self.cpu_info_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_grid, text="Memory:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        self.memory_info_label = ttk.Label(info_grid, text="Querying system...")
        self.memory_info_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Update system info
        self._update_system_info()
        
        # Performance Monitor section
        monitor_frame = ttk.LabelFrame(main_frame, text="Performance Monitor", padding="10")
        monitor_frame.pack(fill=tk.X, pady=10)
        
        # CPU section
        cpu_frame = ttk.Frame(monitor_frame)
        cpu_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cpu_frame, text="CPU Usage:").pack(side=tk.LEFT, padx=(0, 5))
        self.cpu_value_label = ttk.Label(cpu_frame, text="0%", width=8)
        self.cpu_value_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=300, mode="determinate")
        self.cpu_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.cpu_status_label = ttk.Label(cpu_frame, text="Normal", foreground="green")
        self.cpu_status_label.pack(side=tk.RIGHT)
        
        # Memory section
        memory_frame = ttk.Frame(monitor_frame)
        memory_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(memory_frame, text="Memory:").pack(side=tk.LEFT, padx=(0, 5))
        self.memory_value_label = ttk.Label(memory_frame, text="0%", width=8)
        self.memory_value_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=300, mode="determinate")
        self.memory_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.memory_status_label = ttk.Label(memory_frame, text="Normal", foreground="green")
        self.memory_status_label.pack(side=tk.RIGHT)
        
        # Disk section
        disk_frame = ttk.Frame(monitor_frame)
        disk_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(disk_frame, text="Disk Usage:").pack(side=tk.LEFT, padx=(0, 5))
        self.disk_value_label = ttk.Label(disk_frame, text="0%", width=8)
        self.disk_value_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=300, mode="determinate")
        self.disk_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.disk_status_label = ttk.Label(disk_frame, text="Normal", foreground="green")
        self.disk_status_label.pack(side=tk.RIGHT)
        
        # Alert thresholds section
        threshold_frame = ttk.LabelFrame(main_frame, text="Alert Thresholds", padding="10")
        threshold_frame.pack(fill=tk.X, pady=10)
        
        # Create threshold grid
        t_grid = ttk.Frame(threshold_frame)
        t_grid.pack(fill=tk.X, pady=5)
        
        # CPU threshold
        ttk.Label(t_grid, text="CPU:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.cpu_threshold_var = tk.StringVar(value=str(self.monitor.thresholds["cpu_percent"]))
        cpu_spinbox = ttk.Spinbox(t_grid, from_=50, to=95, textvariable=self.cpu_threshold_var, width=5)
        cpu_spinbox.grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(t_grid, text="%").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # Memory threshold
        ttk.Label(t_grid, text="Memory:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.memory_threshold_var = tk.StringVar(value=str(self.monitor.thresholds["memory_percent"]))
        memory_spinbox = ttk.Spinbox(t_grid, from_=50, to=95, textvariable=self.memory_threshold_var, width=5)
        memory_spinbox.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(t_grid, text="%").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Disk threshold
        ttk.Label(t_grid, text="Disk:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.disk_threshold_var = tk.StringVar(value=str(self.monitor.thresholds["disk_percent"]))
        disk_spinbox = ttk.Spinbox(t_grid, from_=50, to=95, textvariable=self.disk_threshold_var, width=5)
        disk_spinbox.grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(t_grid, text="%").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # Apply button
        ttk.Button(threshold_frame, text="Apply Thresholds", 
                  command=self._apply_thresholds).pack(anchor=tk.E, pady=5)
        
        # Alert log section
        alert_frame = ttk.LabelFrame(main_frame, text="System Alerts", padding="10")
        alert_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Alert text with scrollbar
        alert_container = ttk.Frame(alert_frame)
        alert_container.pack(fill=tk.BOTH, expand=True)
        
        self.alert_text = tk.Text(alert_container, height=8, wrap=tk.WORD)
        alert_scrollbar = ttk.Scrollbar(alert_container, command=self.alert_text.yview)
        self.alert_text.configure(yscrollcommand=alert_scrollbar.set)
        
        self.alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear button
        ttk.Button(alert_frame, text="Clear Alerts", 
                  command=self._clear_alerts).pack(anchor=tk.E, pady=5)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Last updated label
        self.last_updated_label = ttk.Label(status_frame, text="")
        self.last_updated_label.pack(side=tk.RIGHT)
    
    def _update_system_info(self):
        """Update system information display"""
        try:
            # CPU Info
            cpu_info = "Unknown"
            if IS_WINDOWS:
                try:
                    if WMI_AVAILABLE and self.monitor.wmi_connection:
                        processors = self.monitor.wmi_connection.Win32_Processor()
                        if processors:
                            cpu_info = processors[0].Name
                    else:
                        # Try PowerShell
                        result = subprocess.run(
                            ["powershell", "-Command", "Get-WmiObject Win32_Processor | Select-Object -ExpandProperty Name"],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            cpu_info = result.stdout.strip()
                except Exception as e:
                    cpu_info = f"Error querying CPU: {str(e)}"
            else:
                # Fallback for non-Windows
                cpu_info = platform.processor() or "Unknown"
            
            self.cpu_info_label.config(text=cpu_info)
            
            # Memory Info
            memory_info = "Unknown"
            if IS_WINDOWS:
                try:
                    if WMI_AVAILABLE and self.monitor.wmi_connection:
                        os_info = self.monitor.wmi_connection.Win32_OperatingSystem()
                        if os_info and len(os_info) > 0:
                            total_memory_kb = float(os_info[0].TotalVisibleMemorySize)
                            memory_info = f"{total_memory_kb / (1024*1024):.2f} GB"
                    else:
                        # Try PowerShell
                        result = subprocess.run(
                            ["powershell", "-Command", "Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty TotalVisibleMemorySize"],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            total_memory_kb = float(result.stdout.strip())
                            memory_info = f"{total_memory_kb / (1024*1024):.2f} GB"
                except Exception as e:
                    memory_info = f"Error querying memory: {str(e)}"
            else:
                # Fallback for non-Windows
                memory_info = "Unknown"
            
            self.memory_info_label.config(text=memory_info)
            
        except Exception as e:
            print(f"Error updating system info: {str(e)}")
    
    def _apply_thresholds(self):
        """Apply threshold settings"""
        try:
            cpu_threshold = int(self.cpu_threshold_var.get())
            memory_threshold = int(self.memory_threshold_var.get())
            disk_threshold = int(self.disk_threshold_var.get())
            
            self.monitor.set_thresholds(
                cpu=cpu_threshold,
                memory=memory_threshold,
                disk=disk_threshold
            )
            
            self.status_label.config(text="Thresholds updated")
            self._add_alert(f"Alert thresholds updated: CPU {cpu_threshold}%, Memory {memory_threshold}%, Disk {disk_threshold}%", 
                          level="info")
        except Exception as e:
            self.status_label.config(text=f"Error updating thresholds: {str(e)}")
    
    def update_performance_display(self, data):
        """Update performance display with new data"""
        # Rate limiting to avoid too frequent updates
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
            
        self.last_update_time = current_time
        self.performance_data = data
        
        # Update CPU display
        cpu_percent = data.get("cpu_percent", 0)
        self.cpu_value_label.config(text=f"{cpu_percent:.1f}%")
        self.cpu_progress["value"] = cpu_percent
        
        # Update CPU status
        if cpu_percent < 30:
            self.cpu_status_label.config(text="Very Low", foreground="green")
        elif cpu_percent < 60:
            self.cpu_status_label.config(text="Normal", foreground="green")
        elif cpu_percent < 80:
            self.cpu_status_label.config(text="Medium", foreground="orange")
        elif cpu_percent < 90:
            self.cpu_status_label.config(text="High", foreground="orange")
        else:
            self.cpu_status_label.config(text="Very High", foreground="red")
        
        # Update Memory display
        memory_percent = data.get("memory_percent", 0)
        memory_total = data.get("memory_total", 0)
        memory_available = data.get("memory_available", 0)
        
        if memory_total > 0:
            memory_used = (memory_total - memory_available) / (1024**3)  # Convert to GB
            memory_total_gb = memory_total / (1024**3)  # Convert to GB
            self.memory_value_label.config(text=f"{memory_percent:.1f}%")
            self.memory_progress["value"] = memory_percent
        else:
            self.memory_value_label.config(text="N/A")
            self.memory_progress["value"] = 0
        
        # Update Memory status
        if memory_percent < 50:
            self.memory_status_label.config(text="Low", foreground="green")
        elif memory_percent < 75:
            self.memory_status_label.config(text="Normal", foreground="green")
        elif memory_percent < 85:
            self.memory_status_label.config(text="Medium", foreground="orange")
        else:
            self.memory_status_label.config(text="High", foreground="red")
        
        # Update Disk display
        disk_percent = data.get("disk_percent", 0)
        disk_total = data.get("disk_total", 0)
        disk_free = data.get("disk_free", 0)
        
        if disk_total > 0:
            disk_used = (disk_total - disk_free) / (1024**3)  # Convert to GB
            disk_total_gb = disk_total / (1024**3)  # Convert to GB
            self.disk_value_label.config(text=f"{disk_percent:.1f}%")
            self.disk_progress["value"] = disk_percent
        else:
            self.disk_value_label.config(text="N/A")
            self.disk_progress["value"] = 0
        
        # Update Disk status
        if disk_percent < 50:
            self.disk_status_label.config(text="Low", foreground="green")
        elif disk_percent < 75:
            self.disk_status_label.config(text="Normal", foreground="green")
        elif disk_percent < 90:
            self.disk_status_label.config(text="Medium", foreground="orange")
        else:
            self.disk_status_label.config(text="High", foreground="red")
        
        # Update last updated time
        self.last_updated_label.config(text=f"Last updated: {time.strftime('%H:%M:%S')}")
    
    def handle_alert(self, alert):
        """Handle a performance alert"""
        alert_type = alert.get("type", "unknown")
        alert_message = alert.get("message", "Unknown alert")
        
        # Add to alert log
        level = "warning"
        if alert_type == "cpu" and alert.get("value", 0) > 90:
            level = "error"
        elif alert_type == "memory" and alert.get("value", 0) > 90:
            level = "error"
        elif alert_type == "disk" and alert.get("value", 0) > 95:
            level = "error"
        
        self._add_alert(alert_message, level=level)
        
        # Forward alert to resource manager through integration system if available
        if INTEGRATION_AVAILABLE:
            try:
                # Use the integrated system for better coordination
                integration = get_system_resource_integration()
                integration._handle_system_alert(alert)
                
            except Exception as e:
                print(f"Error forwarding alert to integration system: {str(e)}")
        # Fallback to direct resource manager if integration is not available
        elif RESOURCE_MANAGER_AVAILABLE:
            try:
                resource_manager = get_resource_manager()
                result = resource_manager.handle_alert(alert)
                
                # If any action was taken, log it
                if result and result.get("actions_taken"):
                    for action in result.get("actions_taken", []):
                        self._add_alert(f"Resource manager action: {action}", level="info")
                        
            except Exception as e:
                print(f"Error forwarding alert to resource manager: {str(e)}")
                
        # Also forward to project resource manager if available
        if PROJECT_RESOURCE_MANAGER_AVAILABLE:
            try:
                project_resource_manager = ProjectResourceManager()
                
                # Convert to format expected by project resource manager
                resource_info = {
                    "hostname": "localhost",
                    "platform": "Windows",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Add the specific metric based on alert type
                if alert["type"] == "cpu":
                    resource_info["cpu_percent"] = alert["value"]
                elif alert["type"] == "memory":
                    resource_info["memory_percent"] = alert["value"]
                elif alert["type"] == "disk":
                    resource_info["disk_percent"] = alert["value"]
                
                # Let project resource manager handle the alert
                available, warnings = project_resource_manager.check_resource_availability(resource_info)
                
                # Log any warnings from project resource manager
                for warning in warnings:
                    self._add_alert(f"Project resource warning: {warning}", level="warning")
                
            except Exception as e:
                print(f"Error forwarding alert to project resource manager: {str(e)}")
    
    def _add_alert(self, message, level="info"):
        """Add an alert to the log"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine color
        if level == "error":
            color = "red"
        elif level == "warning":
            color = "orange"
        else:
            color = "green"
        
        # Store alert
        alert_id = len(self.alerts)
        self.alerts.append({
            "id": alert_id,
            "timestamp": timestamp,
            "message": message,
            "level": level
        })
        
        # Update alert text
        self.alert_text.config(state=tk.NORMAL)
        
        # Create tag for this alert
        tag_name = f"alert_{alert_id}"
        self.alert_text.tag_configure(tag_name, foreground=color)
        
        # Insert alert with the tag
        self.alert_text.insert(tk.END, f"[{timestamp}] ", tag_name)
        self.alert_text.insert(tk.END, f"{message}\n", tag_name)
        
        # Scroll to bottom
        self.alert_text.see(tk.END)
        
        # Make read-only again
        self.alert_text.config(state=tk.DISABLED)
    
    def _clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
        self.alert_text.config(state=tk.NORMAL)
        self.alert_text.delete("1.0", tk.END)
        self.alert_text.config(state=tk.DISABLED)
        self.status_label.config(text="Alerts cleared")

def integrate_with_gui(notebook):
    """
    Integrate the system monitor with the GUI
    
    Args:
        notebook: The ttk.Notebook widget to add the tab to
        
    Returns:
        The created tab object
    """
    tab = SystemMonitorTab(notebook)
    
    # Start the resource integration if available
    if INTEGRATION_AVAILABLE:
        try:
            integration = get_system_resource_integration()
            integration.start_monitoring()
            print("Resource integration monitoring started")
        except Exception as e:
            print(f"Error starting resource integration: {str(e)}")
    
    return tab

# Example for standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("System Monitor Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create system monitor tab
    tab = integrate_with_gui(notebook)
    
    root.mainloop()