#!/usr/bin/env python
# Task Manager Integration - Get alerts directly from Windows Task Manager
# Uses Windows Events to listen for performance alerts

import os
import sys
import time
import json
import datetime
import subprocess
import threading
import platform
import signal
import win32evtlog
import win32con
import win32evtlogutil
import win32event

class TaskManagerIntegration:
    """
    Integrates with Windows Task Manager's performance monitoring
    and alert system through Event Log monitoring
    """
    
    def __init__(self, callback=None, config_file="task_manager_config.json"):
        self.config_file = config_file
        self.monitoring = False
        self.monitor_thread = None
        self.callback = callback  # Function to call when an alert is detected
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
        }
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load monitoring configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if "thresholds" in config:
                        self.thresholds.update(config["thresholds"])
            except Exception as e:
                print(f"Error loading config: {str(e)}")
    
    def save_config(self):
        """Save monitoring configuration"""
        try:
            config = {
                "thresholds": self.thresholds,
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    def setup_task_manager_alerts(self):
        """Configure Task Manager alerts through Performance Monitor"""
        try:
            # Check if running on Windows
            if platform.system() != "Windows" and not ("microsoft" in platform.release().lower()):
                print("This functionality is only available on Windows")
                return False
            
            # Create PowerShell script to set up alerts
            ps_script = f"""
            # Create Data Collector Set for alerts
            $dataCollectorSetName = "GlowingGoldenGlobe Alerts"
            
            # Remove existing data collector set if it exists
            try {{
                $existingSet = New-Object -ComObject Pla.DataCollectorSet
                $existingSet.Query($dataCollectorSetName, $null)
                $existingSet.Delete()
            }} catch {{
                # Doesn't exist, continue
            }}
            
            # Create new data collector set
            $dataCollectorSet = New-Object -ComObject Pla.DataCollectorSet
            $dataCollectorSet.DisplayName = $dataCollectorSetName
            $dataCollectorSet.Duration = 0  # Run until stopped
            
            # Set up CPU alert
            $cpuAlert = $dataCollectorSet.Alerts.CreateAlertNotification()
            $cpuAlert.Name = "CPU Alert"
            $cpuAlert.SampleInterval = 5  # Check every 5 seconds
            $cpuAlert.AlertThresholds.Add("\\Processor(_Total)\\% Processor Time", {self.thresholds["cpu_percent"]})
            
            # Set up Memory alert
            $memAlert = $dataCollectorSet.Alerts.CreateAlertNotification()
            $memAlert.Name = "Memory Alert"
            $memAlert.SampleInterval = 5
            $memAlert.AlertThresholds.Add("\\Memory\\% Committed Bytes In Use", {self.thresholds["memory_percent"]})
            
            # Set up Disk alert
            $diskAlert = $dataCollectorSet.Alerts.CreateAlertNotification()
            $diskAlert.Name = "Disk Alert"
            $diskAlert.SampleInterval = 10
            $diskAlert.AlertThresholds.Add("\\LogicalDisk(_Total)\\% Free Space", 100 - {self.thresholds["disk_percent"]})
            
            # Save and start
            $dataCollectorSet.Commit($dataCollectorSetName, $null, 0x0003)  # Create or modify
            $dataCollectorSet.Start($false)
            
            Write-Output "Task Manager alerts set up successfully."
            """
            
            # Write script to temp file
            temp_script = os.path.join(os.environ.get("TEMP", ""), "setup_tm_alerts.ps1")
            with open(temp_script, "w") as f:
                f.write(ps_script)
            
            # Run PowerShell as administrator
            result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Task Manager alerts configured successfully")
                return True
            else:
                print(f"Error setting up Task Manager alerts: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"Error setting up Task Manager alerts: {str(e)}")
            return False
    
    def monitor_performance_events(self):
        """Monitor Windows Event Log for performance alerts"""
        if platform.system() != "Windows" and not ("microsoft" in platform.release().lower()):
            print("Event monitoring is only available on Windows")
            return
        
        try:
            # Open the Application event log
            hand = win32evtlog.OpenEventLog(None, "Application")
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            # Get current position
            total_records = win32evtlog.GetNumberOfEventLogRecords(hand)
            last_read = datetime.datetime.now()
            
            while self.monitoring:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                
                for event in events:
                    # Check if this is a performance alert event
                    if event.EventID == 2031:  # Performance alert event ID
                        event_time = event.TimeGenerated
                        
                        # Only process recent events
                        if isinstance(event_time, datetime.datetime) and event_time > last_read:
                            source = event.SourceName
                            message = win32evtlogutil.SafeFormatMessage(event, "Application")
                            
                            if "GlowingGoldenGlobe" in message or "CPU Alert" in message or "Memory Alert" in message:
                                alert_info = {
                                    "timestamp": event_time.isoformat(),
                                    "source": source,
                                    "message": message,
                                    "id": event.EventID
                                }
                                
                                # Call callback if provided
                                if self.callback:
                                    self.callback(alert_info)
                                
                                print(f"Performance Alert: {message}")
                
                # Update last read time
                last_read = datetime.datetime.now()
                
                # Sleep to avoid high CPU usage
                time.sleep(5)
                
        except Exception as e:
            print(f"Error monitoring performance events: {str(e)}")
    
    def start_monitoring(self):
        """Start monitoring for Task Manager alerts"""
        if self.monitoring:
            return
        
        # Set up alerts first
        if not self.setup_task_manager_alerts():
            print("Failed to set up Task Manager alerts")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_performance_events, daemon=True)
        self.monitor_thread.start()
        print("Started monitoring for Task Manager alerts")
    
    def stop_monitoring(self):
        """Stop monitoring for Task Manager alerts"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
        print("Stopped monitoring for Task Manager alerts")
    
    def get_task_manager_values(self):
        """Get current values directly from Task Manager"""
        try:
            info = {
                "timestamp": datetime.datetime.now().isoformat(),
            }
            
            if platform.system() == "Windows" or ("microsoft" in platform.release().lower()):
                # Query performance counters directly
                ps_script = """
                $cpu = (Get-Counter "\\Processor(_Total)\\% Processor Time").CounterSamples.CookedValue
                $mem = (Get-Counter "\\Memory\\% Committed Bytes In Use").CounterSamples.CookedValue
                $disk = (Get-Counter "\\LogicalDisk(_Total)\\% Free Space").CounterSamples.CookedValue
                
                Write-Output "$cpu,$mem,$disk"
                """
                
                result = subprocess.run(["powershell", "-Command", ps_script], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    values = result.stdout.strip().split(',')
                    if len(values) == 3:
                        info["cpu_percent"] = float(values[0])
                        info["memory_percent"] = float(values[1])
                        info["disk_percent"] = 100 - float(values[2])  # Convert free space to used space
            
            return info
        
        except Exception as e:
            print(f"Error getting Task Manager values: {str(e)}")
            return {}

# Example usage
if __name__ == "__main__":
    def alert_handler(alert_info):
        print(f"ALERT: {alert_info['message']}")
    
    integration = TaskManagerIntegration(callback=alert_handler)
    
    print("Getting current Task Manager values...")
    values = integration.get_task_manager_values()
    print(json.dumps(values, indent=2))
    
    print("\nSetting up monitoring for Task Manager alerts...")
    integration.start_monitoring()
    
    try:
        print("Monitoring for alerts. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.stop_monitoring()
        print("Monitoring stopped.")