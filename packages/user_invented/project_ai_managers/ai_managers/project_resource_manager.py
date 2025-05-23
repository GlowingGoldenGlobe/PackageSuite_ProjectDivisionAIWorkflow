"""
Project Resource Manager

This specialized AI manager focuses on hardware resource coordination and optimization
across different machines. It works with the main project_ai_manager.py to:

1. Monitor and collect hardware usage information from multiple machines
2. Identify resource bottlenecks and optimally allocate computing tasks
3. Handle resource emergency events and implement recovery strategies
4. Connect to cloud computing resources when local resources are insufficient

This manager follows the specialized AI manager pattern described in project_ai_manager.py,
focusing specifically on computing resources to ensure project success.
"""

import os
import json
import time
import datetime
import platform
import threading
import subprocess
from pathlib import Path
import socket

# For network communications
try:
    import requests
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False
    print("Network communication features will be limited (requests module not available)")

# Try to import resource manager for coordination
try:
    from resource_manager import get_resource_manager
    RESOURCE_MANAGER_AVAILABLE = True
except ImportError:
    RESOURCE_MANAGER_AVAILABLE = False
    print("Resource manager integration will be limited (resource_manager module not available)")

# Try to import notification system
try:
    from model_notification_system import get_notification_system, ModelNotification
    NOTIFICATION_SYSTEM_AVAILABLE = True
except ImportError:
    NOTIFICATION_SYSTEM_AVAILABLE = False
    print("Notification features will be limited (model_notification_system module not available)")
    
# Lazy loading for Open3D capabilities - only check when requested
_open3d_checked = False
_open3d_available = None
_open3d_visualization = None

def check_open3d_capability():
    """Lazily check Open3D capabilities only when needed"""
    global _open3d_checked, _open3d_available, _open3d_visualization
    
    # Return cached results if already checked
    if _open3d_checked:
        return _open3d_available, _open3d_visualization
    
    # Mark as checked to avoid repeat attempts
    _open3d_checked = True
    
    # Only import and check when actually requested
    try:
        import check_open3d
        _open3d_available = check_open3d.is_open3d_available()
        _open3d_visualization = check_open3d.has_visualization_capability()
    except ImportError:
        _open3d_available = False
        _open3d_visualization = False
    
    return _open3d_available, _open3d_visualization

class ProjectResourceManager:
    """AI manager specialized for hardware resource coordination and optimization"""
    
    def __init__(self, config_file="resource_manager_config.json"):
        self.config_file = config_file
        self.resources = {}  # Dictionary of available compute resources
        self.resource_history = {}  # Resource usage history
        self.active_tasks = {}  # Currently running tasks and their resource requirements
        self.cloud_resources = {}  # Available cloud resources
        self.resource_alerts = []  # Recent resource alerts
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Load configuration
        self.config = self.load_config()
        
        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("resource_data", exist_ok=True)
    
    def load_config(self):
        """Load resource manager configuration"""
        default_config = {
            "resource_check_interval": 300,  # 5 minutes
            "alert_thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90
            },
            "emergency_thresholds": {
                "cpu_percent": 95,
                "memory_percent": 95,
                "disk_percent": 95
            },
            "known_resources": [],  # List of known compute resources
            "cloud_credentials": {},  # Credentials for cloud services
            "enable_cloud_fallback": False,  # Whether to use cloud when local resources are overwhelmed
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Update default config with loaded values
                    default_config.update(config)
            except Exception as e:
                self.log_event(f"Error loading configuration: {str(e)}")
                
        return default_config
    
    def save_config(self):
        """Save current configuration to disk"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.log_event(f"Error saving configuration: {str(e)}")
    
    def log_event(self, message, level="INFO"):
        """Log an event to the resource manager log file"""
        timestamp = datetime.datetime.now().isoformat()
        log_message = f"[{timestamp}] [{level}] {message}"
        
        try:
            with open(os.path.join("logs", "resource_manager.log"), "a") as f:
                f.write(log_message + "\n")
                
            # Add to alerts if warning or error
            if level in ["WARNING", "ERROR", "CRITICAL"]:
                self.resource_alerts.append({
                    "timestamp": timestamp,
                    "level": level,
                    "message": message
                })
                
                # Keep only recent alerts (max 100)
                if len(self.resource_alerts) > 100:
                    self.resource_alerts = self.resource_alerts[-100:]
        except Exception as e:
            print(f"Error logging to resource manager: {str(e)}")
            print(log_message)
    
    def get_local_resource_info(self):
        """Get information about local hardware resources"""
        info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "timestamp": datetime.datetime.now().isoformat(),
            "available": True  # Assume available by default
        }
        
        try:
            # Try to import psutil for detailed resource info
            import psutil
            
            # CPU information
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
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
            
            # Network information (simplified)
            try:
                network = psutil.net_io_counters()
                info["network_bytes_sent"] = network.bytes_sent
                info["network_bytes_recv"] = network.bytes_recv
            except:
                # Network info might not be available
                pass
                
        except ImportError:
            # Fall back to simpler methods if psutil is not available
            self.log_event("psutil not available, using limited resource information", "WARNING")
            
            # Use subprocess to get basic information
            if platform.system() == "Windows":
                # Try to get CPU info from Windows
                try:
                    output = subprocess.check_output("wmic cpu get LoadPercentage", shell=True).decode()
                    cpu_percent = float(output.strip().split("\n")[1])
                    info["cpu_percent"] = cpu_percent
                except:
                    info["cpu_percent"] = None
            else:
                # Unix-like systems
                try:
                    # Attempt to parse top output for CPU usage
                    top_output = subprocess.check_output(["top", "-bn1"]).decode()
                    cpu_line = [l for l in top_output.split('\n') if 'Cpu(s)' in l][0]
                    cpu_percent = float(cpu_line.split()[1].replace('%', ''))
                    info["cpu_percent"] = cpu_percent
                except:
                    info["cpu_percent"] = None
        
        except Exception as e:
            self.log_event(f"Error getting resource information: {str(e)}", "ERROR")
            info["error"] = str(e)
        
        return info
    
    def check_resource_availability(self, resource_info):
        """
        Check if a resource is available for new tasks based on usage thresholds
        
        Returns a tuple: (available, warning_message)
        """
        available = True
        warnings = []
        
        # Track alerts to forward to the resource manager
        alerts = []
        
        # Check CPU usage
        if "cpu_percent" in resource_info and resource_info["cpu_percent"] is not None:
            cpu_percent = resource_info["cpu_percent"]
            cpu_threshold = self.config["alert_thresholds"]["cpu_percent"]
            
            if cpu_percent > cpu_threshold:
                available = False
                warning_msg = f"CPU usage is high: {cpu_percent}% (threshold: {cpu_threshold}%)"
                warnings.append(warning_msg)
                
                # Create alert for resource manager
                alerts.append({
                    "type": "cpu",
                    "value": cpu_percent,
                    "threshold": cpu_threshold,
                    "message": warning_msg
                })
        
        # Check memory usage
        if "memory_percent" in resource_info and resource_info["memory_percent"] is not None:
            memory_percent = resource_info["memory_percent"]
            memory_threshold = self.config["alert_thresholds"]["memory_percent"]
            
            if memory_percent > memory_threshold:
                available = False
                warning_msg = f"Memory usage is high: {memory_percent}% (threshold: {memory_threshold}%)"
                warnings.append(warning_msg)
                
                # Create alert for resource manager
                alerts.append({
                    "type": "memory",
                    "value": memory_percent,
                    "threshold": memory_threshold,
                    "message": warning_msg
                })
        
        # Check disk usage
        if "disk_percent" in resource_info and resource_info["disk_percent"] is not None:
            disk_percent = resource_info["disk_percent"]
            disk_threshold = self.config["alert_thresholds"]["disk_percent"]
            
            if disk_percent > disk_threshold:
                available = False
                warning_msg = f"Disk usage is high: {disk_percent}% (threshold: {disk_threshold}%)"
                warnings.append(warning_msg)
                
                # Create alert for resource manager
                alerts.append({
                    "type": "disk",
                    "value": disk_percent,
                    "threshold": disk_threshold,
                    "message": warning_msg
                })
        
        # Forward alerts to resource manager if available
        if alerts and RESOURCE_MANAGER_AVAILABLE:
            try:
                resource_manager = get_resource_manager()
                for alert in alerts:
                    resource_manager.handle_alert(alert)
            except Exception as e:
                self.log_event(f"Error forwarding alerts to resource manager: {str(e)}", "ERROR")
        
        # Send notification for serious issues
        if not available and NOTIFICATION_SYSTEM_AVAILABLE:
            # Only notify for serious issues (multiple warnings or critical thresholds)
            if len(warnings) > 1 or any("critical" in w.lower() for w in warnings):
                try:
                    notification_system = get_notification_system()
                    notification = ModelNotification(
                        model_version="system",
                        message=f"Resource availability warning on {resource_info.get('hostname', 'unknown')}",
                        notification_type="warning",
                        source="project_resource_manager",
                        details={
                            "warnings": warnings,
                            "resource": resource_info.get('hostname', 'unknown'),
                            "timestamp": resource_info.get('timestamp')
                        }
                    )
                    notification_system.add_notification(notification)
                except Exception as e:
                    self.log_event(f"Error sending notification: {str(e)}", "ERROR")
        
        return available, warnings
    
    def start_resource_monitoring(self):
        """Start monitoring resources periodically"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        def monitoring_task():
            while self.is_monitoring:
                try:
                    # Get local resource information
                    local_info = self.get_local_resource_info()
                    
                    # Check availability
                    available, warnings = self.check_resource_availability(local_info)
                    local_info["available"] = available
                    
                    # Log warnings
                    for warning in warnings:
                        self.log_event(warning, "WARNING")
                    
                    # Update local resource information
                    hostname = local_info["hostname"]
                    self.resources[hostname] = local_info
                    
                    # Save history
                    if hostname not in self.resource_history:
                        self.resource_history[hostname] = []
                    
                    # Keep only recent history (max 100 entries)
                    history_entry = {
                        "timestamp": local_info["timestamp"],
                        "cpu_percent": local_info.get("cpu_percent"),
                        "memory_percent": local_info.get("memory_percent"),
                        "disk_percent": local_info.get("disk_percent"),
                        "available": available
                    }
                    
                    self.resource_history[hostname].append(history_entry)
                    if len(self.resource_history[hostname]) > 100:
                        self.resource_history[hostname] = self.resource_history[hostname][-100:]
                    
                    # Check other network resources if available
                    if NETWORK_AVAILABLE:
                        self.check_network_resources()
                    
                    # Check cloud resources if enabled
                    if self.config.get("enable_cloud_fallback", False):
                        self.check_cloud_resources()
                    
                    # Save resource data periodically
                    self.save_resource_data()
                    
                except Exception as e:
                    self.log_event(f"Error in resource monitoring: {str(e)}", "ERROR")
                
                # Sleep until next check
                time.sleep(self.config.get("resource_check_interval", 300))
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=monitoring_task, daemon=True)
        self.monitoring_thread.start()
        
        self.log_event("Resource monitoring started")
    
    def stop_resource_monitoring(self):
        """Stop the resource monitoring thread"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
            self.monitoring_thread = None
        
        self.log_event("Resource monitoring stopped")
    
    def check_network_resources(self):
        """Check the status of other compute resources on the network"""
        # This is a placeholder implementation
        # In a real implementation, this would communicate with other machines
        # running the resource manager to collect their status
        pass
    
    def check_cloud_resources(self):
        """Check availability and pricing of cloud computing resources"""
        # This is a placeholder implementation
        # In a real implementation, this would check the status of configured
        # cloud resources like AWS, GCP, or Azure
        pass
    
    def save_resource_data(self):
        """Save current resource data to disk"""
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "resources": self.resources,
            "active_tasks": self.active_tasks
        }
        
        try:
            # Save to timestamped file
            filename = f"resource_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join("resource_data", filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Also save to latest file
            latest_path = os.path.join("resource_data", "latest_resource_data.json")
            with open(latest_path, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            self.log_event(f"Error saving resource data: {str(e)}", "ERROR")
    
    def handle_resource_emergency(self, resource_name, emergency_info):
        """
        Handle a resource emergency (critical hardware issue)
        
        This method is called when a resource reports a critical issue that
        requires immediate attention.
        """
        self.log_event(f"EMERGENCY: Critical resource issue on {resource_name}", "CRITICAL")
        
        # Log detailed information
        if isinstance(emergency_info, dict):
            for key, value in emergency_info.items():
                self.log_event(f"  {key}: {value}", "CRITICAL")
        else:
            self.log_event(f"  Details: {emergency_info}", "CRITICAL")
        
        # Take emergency actions
        self.emergency_task_reallocation(resource_name)
        
        # Notify using the notification system if available
        if NOTIFICATION_SYSTEM_AVAILABLE:
            try:
                notification_system = get_notification_system()
                notification = ModelNotification(
                    model_version="system",
                    message=f"CRITICAL RESOURCE EMERGENCY on {resource_name}",
                    notification_type="error",
                    source="project_resource_manager",
                    details=emergency_info if isinstance(emergency_info, dict) else {"details": str(emergency_info)}
                )
                notification_system.add_notification(notification)
            except Exception as e:
                self.log_event(f"Error sending notification: {str(e)}", "ERROR")
        
        # Forward to system resource manager if available
        if RESOURCE_MANAGER_AVAILABLE:
            try:
                system_resource_manager = get_resource_manager()
                alert = {
                    "type": "emergency",
                    "resource": resource_name,
                    "details": emergency_info
                }
                system_resource_manager.handle_emergency([f"Emergency on {resource_name}: {emergency_info}"])
            except Exception as e:
                self.log_event(f"Error forwarding emergency to resource manager: {str(e)}", "ERROR")
        
        return True
    
    def emergency_task_reallocation(self, problematic_resource):
        """
        Attempt to reallocate tasks from a problematic resource to other available resources
        """
        self.log_event(f"Attempting emergency task reallocation from {problematic_resource}", "WARNING")
        
        # Find tasks running on the problematic resource
        tasks_to_move = []
        for task_id, task_info in self.active_tasks.items():
            if task_info.get("resource") == problematic_resource:
                tasks_to_move.append((task_id, task_info))
        
        if not tasks_to_move:
            self.log_event(f"No active tasks found on {problematic_resource}", "INFO")
            return
        
        self.log_event(f"Found {len(tasks_to_move)} tasks to reallocate", "INFO")
        
        # Find available alternative resources
        available_resources = []
        for resource_name, resource_info in self.resources.items():
            if resource_name != problematic_resource and resource_info.get("available", False):
                available_resources.append((resource_name, resource_info))
        
        if not available_resources:
            # Check if cloud fallback is enabled
            if self.config.get("enable_cloud_fallback", False) and self.cloud_resources:
                self.log_event("No local resources available, attempting cloud fallback", "WARNING")
                # This would allocate tasks to cloud resources
                pass
            else:
                self.log_event("No alternative resources available for task reallocation", "ERROR")
                return
        
        # Reallocate tasks
        for task_id, task_info in tasks_to_move:
            # This is a placeholder for actual task reallocation logic
            # In a real implementation, this would:
            # 1. Stop the task on the problematic resource
            # 2. Transfer necessary data to the new resource
            # 3. Start the task on the new resource
            # 4. Update the task status
            
            if available_resources:
                new_resource, _ = available_resources[0]  # Simply take the first available resource
                self.log_event(f"Reallocating task {task_id} from {problematic_resource} to {new_resource}", "INFO")
                
                # Update task information
                task_info["resource"] = new_resource
                task_info["reallocated"] = True
                task_info["reallocated_time"] = datetime.datetime.now().isoformat()
                self.active_tasks[task_id] = task_info
            else:
                self.log_event(f"Could not reallocate task {task_id}, no resources available", "ERROR")
    
    def find_optimal_resource(self, task_requirements):
        """
        Find the optimal resource for a task based on its requirements
        
        Args:
            task_requirements: Dict with CPU, memory, disk, etc. requirements
            
        Returns:
            Tuple of (resource_name, score) or (None, 0) if no suitable resource found
        """
        best_resource = None
        best_score = 0
        
        for resource_name, resource_info in self.resources.items():
            # Skip unavailable resources
            if not resource_info.get("available", False):
                continue
            
            # Calculate a score based on how well the resource meets requirements
            score = self._calculate_resource_score(resource_info, task_requirements)
            
            if score > best_score:
                best_resource = resource_name
                best_score = score
        
        # If no suitable resource found locally, check cloud if enabled
        if best_resource is None and self.config.get("enable_cloud_fallback", False):
            # Check cloud resources
            for cloud_name, cloud_info in self.cloud_resources.items():
                score = self._calculate_resource_score(cloud_info, task_requirements)
                
                if score > best_score:
                    best_resource = cloud_name
                    best_score = score
        
        return best_resource, best_score
    
    def _calculate_resource_score(self, resource_info, requirements):
        """Calculate a score for how well a resource meets requirements"""
        score = 100  # Start with perfect score
        
        # CPU availability score
        if "cpu_percent" in resource_info and "cpu_required" in requirements:
            cpu_available = 100 - resource_info["cpu_percent"]
            cpu_required = requirements["cpu_required"]
            
            if cpu_available < cpu_required:
                # Not enough CPU
                score -= 50
            else:
                # Enough CPU but don't want too much excess
                efficiency = cpu_required / cpu_available if cpu_available > 0 else 0
                score -= (1 - efficiency) * 20
        
        # Memory availability score
        if "memory_percent" in resource_info and "memory_required" in requirements:
            memory_available = 100 - resource_info["memory_percent"]
            memory_required = requirements["memory_required"]
            
            if memory_available < memory_required:
                # Not enough memory
                score -= 50
            else:
                # Enough memory but don't want too much excess
                efficiency = memory_required / memory_available if memory_available > 0 else 0
                score -= (1 - efficiency) * 20
        
        # Disk availability score
        if "disk_percent" in resource_info and "disk_required" in requirements:
            disk_available = 100 - resource_info["disk_percent"]
            disk_required = requirements["disk_required"]
            
            if disk_available < disk_required:
                # Not enough disk
                score -= 30
            else:
                # Enough disk but don't want too much excess
                efficiency = disk_required / disk_available if disk_available > 0 else 0
                score -= (1 - efficiency) * 10
        
        # Additional factors
        
        # Prefer non-cloud resources unless explicitly specified
        if resource_info.get("is_cloud", False) and not requirements.get("prefer_cloud", False):
            score -= 20
        
        # Prefer designated GPU machines for GPU tasks
        if requirements.get("gpu_required", False) and not resource_info.get("has_gpu", False):
            score -= 70
        
        # Normalize score to 0-100 range
        score = max(0, min(100, score))
        
        return score
    
    def register_task(self, task_id, task_info):
        """Register a new task with resource requirements"""
        if task_id in self.active_tasks:
            self.log_event(f"Task {task_id} is already registered", "WARNING")
            return False
        
        # Find optimal resource
        resource_name, score = self.find_optimal_resource(task_info.get("requirements", {}))
        
        if resource_name is None or score <= 0:
            self.log_event(f"No suitable resource found for task {task_id}", "ERROR")
            return False
        
        # Assign resource
        task_info["resource"] = resource_name
        task_info["score"] = score
        task_info["registered_time"] = datetime.datetime.now().isoformat()
        task_info["status"] = "registered"
        
        # Store task information
        self.active_tasks[task_id] = task_info
        
        self.log_event(f"Task {task_id} registered on resource {resource_name} with score {score}", "INFO")
        return True
    
    def start_task(self, task_id):
        """Mark a task as started and update resource usage"""
        if task_id not in self.active_tasks:
            self.log_event(f"Task {task_id} is not registered", "ERROR")
            return False
        
        # Update task status
        task_info = self.active_tasks[task_id]
        task_info["status"] = "running"
        task_info["start_time"] = datetime.datetime.now().isoformat()
        
        self.active_tasks[task_id] = task_info
        
        self.log_event(f"Task {task_id} started on resource {task_info.get('resource')}", "INFO")
        return True
    
    def complete_task(self, task_id, success=True):
        """Mark a task as completed and free up resources"""
        if task_id not in self.active_tasks:
            self.log_event(f"Task {task_id} is not registered", "ERROR")
            return False
        
        # Update task status
        task_info = self.active_tasks[task_id]
        task_info["status"] = "completed" if success else "failed"
        task_info["end_time"] = datetime.datetime.now().isoformat()
        
        # Calculate duration
        if "start_time" in task_info:
            try:
                start_time = datetime.datetime.fromisoformat(task_info["start_time"])
                end_time = datetime.datetime.fromisoformat(task_info["end_time"])
                duration = (end_time - start_time).total_seconds()
                task_info["duration_seconds"] = duration
            except:
                pass
        
        # Store completed task
        completed_tasks_file = os.path.join("resource_data", "completed_tasks.json")
        try:
            completed_tasks = []
            if os.path.exists(completed_tasks_file):
                with open(completed_tasks_file, 'r') as f:
                    completed_tasks = json.load(f)
            
            completed_tasks.append(task_info)
            
            with open(completed_tasks_file, 'w') as f:
                json.dump(completed_tasks, f, indent=4)
        except Exception as e:
            self.log_event(f"Error saving completed task: {str(e)}", "ERROR")
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        self.log_event(f"Task {task_id} {'completed successfully' if success else 'failed'}", "INFO")
        return True

    def get_resource_status_report(self, include_capabilities=False):
        """Generate a comprehensive report on resource status
        
        Args:
            include_capabilities: Whether to check and include additional capabilities
                                 like Open3D (only performed when requested)
        """
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "resources": {},
            "active_tasks": len(self.active_tasks),
            "alerts": self.resource_alerts[-10:] if self.resource_alerts else [],  # Last 10 alerts
        }
        
        # Only include capabilities if specifically requested
        if include_capabilities:
            # Network is always checked since it's used for core functionality
            capabilities = {"network": NETWORK_AVAILABLE}
            
            # Only check Open3D when needed
            open3d_available, open3d_visualization = check_open3d_capability()
            capabilities.update({
                "open3d": open3d_available,
                "visualization": open3d_visualization
            })
            
            report["capabilities"] = capabilities
        
        # Summarize resource status
        for resource_name, resource_info in self.resources.items():
            # Create a simplified summary
            summary = {
                "available": resource_info.get("available", False),
                "cpu_percent": resource_info.get("cpu_percent"),
                "memory_percent": resource_info.get("memory_percent"),
                "disk_percent": resource_info.get("disk_percent"),
                "is_cloud": resource_info.get("is_cloud", False),
                "active_tasks": 0  # Will count below
            }
            
            # Count tasks on this resource
            for task_info in self.active_tasks.values():
                if task_info.get("resource") == resource_name:
                    summary["active_tasks"] += 1
            
            report["resources"][resource_name] = summary
        
        return report

# Simple test code
if __name__ == "__main__":
    print("Testing Project Resource Manager...")
    
    manager = ProjectResourceManager()
    print("Initial configuration:", manager.config)
    
    print("\nGetting local resource information...")
    local_info = manager.get_local_resource_info()
    print(json.dumps(local_info, indent=2))
    
    print("\nStarting resource monitoring...")
    manager.start_resource_monitoring()
    
    print("\nPress Ctrl+C to stop...")
    try:
        # Let the monitoring run for a while
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_resource_monitoring()
        
    print("\nResource status report:")
    report = manager.get_resource_status_report()
    print(json.dumps(report, indent=2))
