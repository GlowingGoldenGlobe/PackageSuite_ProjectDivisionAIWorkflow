#!/usr/bin/env python
# Hardware Resource Monitor for GlowingGoldenGlobe
# Tracks CPU, memory, and disk usage with scheduled checks

import os
import time
import json
import datetime
import platform
import threading
import subprocess
from pathlib import Path

# Try to import psutil for system monitoring
try:
    import psutil
except ImportError:
    print("psutil not installed. Limited functionality available.")
    psutil = None

class HardwareMonitor:
    """Monitors hardware resource usage and provides alerts"""
    def __init__(self, log_dir="logs", config_file="hardware_monitor_config.json"):
        self.log_dir = log_dir
        self.config_file = config_file
        self.monitoring = False
        self.monitor_thread = None
        self.history = []
        self.thresholds = {
            "cpu_percent": 80,  # Alert if CPU usage > 80%
            "memory_percent": 85,  # Alert if memory usage > 85%
            "disk_percent": 90,  # Alert if disk usage > 90%
        }
        
        # Critical resource monitoring
        self.critical_resource_issue = False
        self.critical_alerts = []
        self.emergency_callbacks = []
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Load configuration if exists
        self.load_config()
    
    def load_config(self):
        """Load monitoring configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if "thresholds" in config:
                        self.thresholds.update(config["thresholds"])
                    if "history" in config:
                        self.history = config["history"]
            except Exception as e:
                print(f"Error loading monitor config: {str(e)}")
    
    def save_config(self):
        """Save monitoring configuration"""
        try:
            config = {
                "thresholds": self.thresholds,
                "history": self.history[-50:],  # Keep last 50 entries
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving monitor config: {str(e)}")
    
    def get_hardware_info(self):
        """Get current hardware resource usage"""
        info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "platform": platform.system(),
        }
        
        if psutil:
            # CPU information - use average of multiple samples to match Task Manager
            cpu_samples = []
            for _ in range(3):  # Take 3 samples for more accuracy
                cpu_samples.append(psutil.cpu_percent(interval=0.25))
            info["cpu_percent"] = sum(cpu_samples) / len(cpu_samples)
            info["cpu_count"] = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            info["memory_total"] = memory.total
            info["memory_available"] = memory.available
            info["memory_percent"] = memory.percent
            
            # Disk information
            disk = psutil.disk_usage('/')
            info["disk_total"] = disk.total
            info["disk_free"] = disk.free
            info["disk_percent"] = disk.percent
            
            # For WSL, add special handling to get Windows Task Manager-like values
            if platform.system() == "Linux" and "microsoft" in platform.release().lower():
                try:
                    # For WSL, use additional methods to get Windows resource values
                    if hasattr(psutil, "cpu_times_percent"):
                        cpu_times = psutil.cpu_times_percent(interval=0.5)
                        # Calculate a better Windows-like CPU usage value
                        if hasattr(cpu_times, "idle"):
                            info["cpu_percent"] = 100.0 - cpu_times.idle
                except Exception as e:
                    # Fallback to default method if there's an error
                    print(f"Error getting WSL-specific metrics: {str(e)}")
        else:
            # Fallback to basic command-line tools
            if platform.system() == "Windows":
                # Windows - use wmic
                try:
                    info["cpu_percent"] = float(subprocess.check_output(
                        "wmic cpu get loadpercentage", shell=True
                    ).decode().split()[1])
                except:
                    info["cpu_percent"] = 0
            else:
                # Unix-like - use top
                try:
                    top_output = subprocess.check_output(["top", "-bn1"]).decode()
                    cpu_line = [l for l in top_output.split('\n') if 'Cpu(s)' in l][0]
                    info["cpu_percent"] = float(cpu_line.split()[1].replace('%', ''))
                except:
                    info["cpu_percent"] = 0
        
        return info
    
    def check_thresholds(self, info):
        """Check if any resources exceed defined thresholds"""
        alerts = []
        critical_alerts = []
        critical_threshold = 95  # Critical threshold percentage
        
        # Check CPU usage - calibrate to match Task Manager readings
        if "cpu_percent" in info:
            # Ensure the reading is accurate by rounding to nearest whole number
            # as Task Manager typically does
            cpu_percent = round(info["cpu_percent"])
            info["cpu_percent"] = cpu_percent  # Update the info dictionary with rounded value
            
            if cpu_percent > critical_threshold:
                critical_alerts.append(f"CRITICAL: CPU usage at {cpu_percent}%")
            elif cpu_percent > self.thresholds["cpu_percent"]:
                alerts.append(f"CPU usage is high: {cpu_percent}%")
        
        # Check memory usage
        if "memory_percent" in info:
            memory_percent = info["memory_percent"]
            if memory_percent > critical_threshold:
                critical_alerts.append(f"CRITICAL: Memory usage at {memory_percent}%")
            elif memory_percent > self.thresholds["memory_percent"]:
                alerts.append(f"Memory usage is high: {memory_percent}%")
        
        # Check disk usage
        if "disk_percent" in info:
            disk_percent = info["disk_percent"]
            if disk_percent > critical_threshold:
                critical_alerts.append(f"CRITICAL: Disk usage at {disk_percent}%")
            elif disk_percent > self.thresholds["disk_percent"]:
                alerts.append(f"Disk usage is high: {disk_percent}%")
        
        # Store critical alerts for emergency handling
        if critical_alerts:
            self.critical_resource_issue = True
            self.critical_alerts = critical_alerts
        else:
            self.critical_resource_issue = False
            self.critical_alerts = []
            
        return alerts, critical_alerts
    
    def record_usage(self, info):
        """Record hardware usage to log"""
        # Add to history
        record = {
            "timestamp": info["timestamp"],
            "cpu_percent": info.get("cpu_percent", 0),
            "memory_percent": info.get("memory_percent", 0),
            "disk_percent": info.get("disk_percent", 0)
        }
        
        self.history.append(record)
        
        # Save to log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"hardware_usage_{timestamp}.log")
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(info) + "\n")
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
    
    def get_recent_usage(self, count=10):
        """Get recent usage history"""
        return self.history[-count:]
    
    def register_emergency_callback(self, callback):
        """Register a callback function to be called during critical resource issues
        
        The callback should accept a list of alert messages as its argument.
        """
        if callable(callback) and callback not in self.emergency_callbacks:
            self.emergency_callbacks.append(callback)
            return True
        return False
            
    def handle_critical_resource_issue(self):
        """Handle critical resource issues by calling registered emergency callbacks"""
        if not self.critical_resource_issue or not self.critical_alerts:
            return
            
        # Log the critical issue
        timestamp = datetime.datetime.now().isoformat()
        log_file = os.path.join(self.log_dir, f"critical_resource_alert_{timestamp.replace(':', '-')}.log")
        try:
            with open(log_file, "w") as f:
                f.write(f"CRITICAL RESOURCE ALERT - {timestamp}\n")
                for alert in self.critical_alerts:
                    f.write(f"{alert}\n")
        except Exception as e:
            print(f"Error logging critical resource alert: {str(e)}")
            
        # Call all registered callbacks
        for callback in self.emergency_callbacks:
            try:
                callback(self.critical_alerts)
            except Exception as e:
                print(f"Error in emergency callback: {str(e)}")
                
        # Reset after handling
        self.critical_resource_issue = False
    
    def start_monitoring(self, interval=30):
        """Start background monitoring thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_task():
            while self.monitoring:
                try:
                    info = self.get_hardware_info()
                    alerts, critical_alerts = self.check_thresholds(info)
                    self.record_usage(info)
                    
                    # Handle any critical resource issues
                    if critical_alerts:
                        self.handle_critical_resource_issue()
                    
                    # Save config periodically
                    self.save_config()
                    
                    # Sleep for the specified interval
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring thread: {str(e)}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
    
    def get_system_summary(self):
        """Get a summary of the system hardware"""
        summary = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        if psutil:
            summary["cpu_count"] = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            summary["total_memory_gb"] = round(memory.total / (1024**3), 2)
            
            disk = psutil.disk_usage('/')
            summary["total_disk_gb"] = round(disk.total / (1024**3), 2)
        
        return summary

# Simple usage example
if __name__ == "__main__":
    monitor = HardwareMonitor()
    info = monitor.get_hardware_info()
    print(json.dumps(info, indent=2))
    
    summary = monitor.get_system_summary()
    print("\nSystem Summary:")
    print(json.dumps(summary, indent=2))
    
    print("\nStarting monitoring for 10 seconds...")
    monitor.start_monitoring(interval=2)
    time.sleep(10)
    monitor.stop_monitoring()
    
    print("\nRecent usage:")
    usage = monitor.get_recent_usage()
    for entry in usage:
        print(f"Time: {entry['timestamp']}, CPU: {entry['cpu_percent']}%, Memory: {entry['memory_percent']}%")
