#!/usr/bin/env python
# Windows Resource Monitor Integration
# Directly uses Windows Management Instrumentation (WMI) to get system metrics matching Task Manager

import os
import time
import json
import datetime
import subprocess
import threading
import platform

class WindowsResourceMonitor:
    """Monitors system resources directly from Windows Management Instrumentation"""
    
    def __init__(self, log_dir="logs", config_file="hardware_monitor_config.json"):
        self.log_dir = log_dir
        self.config_file = config_file
        self.monitoring = False
        self.monitor_thread = None
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
        }
        
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
            except Exception as e:
                print(f"Error loading monitor config: {str(e)}")
    
    def save_config(self):
        """Save monitoring configuration"""
        try:
            config = {
                "thresholds": self.thresholds,
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving monitor config: {str(e)}")
    
    def get_wmi_hardware_info(self):
        """Get hardware info directly from Windows WMI - matches Task Manager exactly"""
        info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "platform": platform.system(),
        }
        
        try:
            # Only run this on Windows
            if platform.system() != "Windows" and not ("microsoft" in platform.release().lower()):
                return info
            
            # CPU usage from WMI
            cpu_cmd = 'powershell "Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average"'
            result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    info["cpu_percent"] = float(result.stdout.strip())
                except ValueError:
                    info["cpu_percent"] = 0
            
            # Memory usage from WMI
            mem_cmd = 'powershell "(Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory, (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory"'
            result = subprocess.run(mem_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('\n')
                if len(parts) >= 2:
                    try:
                        # Convert from KB to bytes
                        free_memory = float(parts[0]) * 1024
                        # Note: TotalPhysicalMemory is already in bytes
                        total_memory = float(parts[1])
                        info["memory_total"] = total_memory
                        info["memory_available"] = free_memory
                        info["memory_percent"] = 100 * (1 - free_memory / total_memory)
                    except ValueError:
                        pass

            # Disk usage from WMI
            disk_cmd = 'powershell "Get-WmiObject Win32_LogicalDisk -Filter \'DeviceID=\"C:\"\' | Select-Object FreeSpace, Size"'
            result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if 'FreeSpace' in line and i+1 < len(lines):
                        try:
                            free_space = float(lines[i+1].split()[0])
                            size = float(lines[i+1].split()[1])
                            info["disk_total"] = size
                            info["disk_free"] = free_space
                            info["disk_percent"] = 100 * (1 - free_space / size)
                        except (ValueError, IndexError):
                            pass
                        break
            
            return info
        except Exception as e:
            print(f"Error getting WMI hardware info: {str(e)}")
            return info
    
    def check_thresholds(self, info):
        """Check if any resources exceed defined thresholds"""
        alerts = []
        critical_alerts = []
        critical_threshold = 95  # Critical threshold percentage
        
        # Check CPU usage
        if "cpu_percent" in info:
            cpu_percent = info["cpu_percent"]
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
            
        return alerts, critical_alerts
    
    def get_system_summary(self):
        """Get a summary of the system hardware"""
        summary = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        try:
            # Get processor info from WMI
            if platform.system() == "Windows" or ("microsoft" in platform.release().lower()):
                cpu_cmd = 'powershell "Get-WmiObject Win32_Processor | Select-Object Name | Format-List"'
                result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    processor_info = result.stdout.strip()
                    if "Name" in processor_info:
                        processor_name = processor_info.split(':', 1)[1].strip()
                        summary["processor"] = processor_name
                
                # Get memory info from WMI
                mem_cmd = 'powershell "Get-WmiObject Win32_ComputerSystem | Select-Object TotalPhysicalMemory"'
                result = subprocess.run(mem_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    mem_info = result.stdout.strip()
                    if "TotalPhysicalMemory" in mem_info:
                        try:
                            total_memory = float(mem_info.split(':', 1)[1].strip())
                            summary["total_memory_gb"] = round(total_memory / (1024**3), 2)
                        except (ValueError, IndexError):
                            pass
                
                # Get disk info from WMI
                disk_cmd = 'powershell "Get-WmiObject Win32_LogicalDisk -Filter \'DeviceID=\"C:\"\' | Select-Object Size"'
                result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    disk_info = result.stdout.strip()
                    if "Size" in disk_info:
                        try:
                            total_disk = float(disk_info.split(':', 1)[1].strip())
                            summary["total_disk_gb"] = round(total_disk / (1024**3), 2)
                        except (ValueError, IndexError):
                            pass
        except Exception as e:
            print(f"Error getting system summary: {str(e)}")
        
        return summary

    def setup_performance_alert(self, counter_path, threshold, alert_name):
        """
        Set up a Windows Performance Monitor alert
        
        Args:
            counter_path: Performance counter path (e.g. "\\Processor(_Total)\\% Processor Time")
            threshold: Threshold value to trigger alert
            alert_name: Name for the alert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a data collector set for alerts
            ps_script = f"""
            $dataCollectorSet = New-Object -COM Pla.DataCollectorSet
            $dataCollectorSet.DisplayName = "GGG Resource Monitor Alerts"
            $dataCollectorSet.Duration = 0
            
            # Create alert
            $alert = $dataCollectorSet.Alerts.CreateAlertNotification()
            $alert.Name = "{alert_name}"
            $alert.SampleInterval = 10
            $alert.ThresholdAction = 1  # Log to event log
            
            # Create threshold
            $threshold = $alert.AddThreshold("{counter_path}")
            $threshold.AboveOrBelow = 1  # Above
            $threshold.Threshold = {threshold}
            
            # Save and start
            $dataCollectorSet.Commit("GGG_Alerts", $null, 0x1003)  # 0x1003 = Create or modify
            $dataCollectorSet.Start($false)
            """
            
            # Write script to temp file
            temp_script = os.path.join(os.environ.get("TEMP", ""), "setup_alerts.ps1")
            with open(temp_script, "w") as f:
                f.write(ps_script)
            
            # Run PowerShell with admin rights
            result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Error setting up alert: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"Error setting up performance alert: {str(e)}")
            return False

# Simple usage example
if __name__ == "__main__":
    monitor = WindowsResourceMonitor()
    info = monitor.get_wmi_hardware_info()
    print(json.dumps(info, indent=2))
    
    summary = monitor.get_system_summary()
    print("\nSystem Summary:")
    print(json.dumps(summary, indent=2))
    
    # Setup alerts example
    if platform.system() == "Windows":
        print("\nSetting up performance alerts...")
        monitor.setup_performance_alert("\\Processor(_Total)\\% Processor Time", 80, "High CPU Alert")