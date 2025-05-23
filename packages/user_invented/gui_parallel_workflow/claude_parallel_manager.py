#!/usr/bin/env python
"""
Claude Parallel Manager for GlowingGoldenGlobe

This module enables Claude Code to execute multiple tasks simultaneously in parallel
as a standalone solution when other parallel agents (PyAutoGen, VSCode) are not available.
It integrates with the existing Parallel Execution Manager while adding Claude-specific
capabilities for AI-driven parallel task execution.

Responsibilities:
- Create and manage multiple Claude-driven task execution processes
- Intelligently distribute tasks based on available system resources
- Coordinate parallel execution of tasks that don't conflict with each other
- Provide progress tracking and execution metrics
- Fall back gracefully when other parallel agents become available
"""

import os
import sys
import json
import time
import queue
import logging
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set, Union
import datetime

# Try to import psutil for better system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "claude_parallel.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ClaudeParallelManager")

class ClaudeParallelManager:
    """
    Manager for Claude Code parallel task execution that allows Claude to run
    multiple tasks simultaneously when other parallel workflow options are not available.
    """
    
    def __init__(self, config_path: str = "claude_parallel_config.json"):
        """Initialize the Claude Parallel Manager"""
        self.config_path = os.path.join(BASE_DIR, config_path)
        self.config = self._load_config()
        
        # Task system
        self.task_queue = queue.PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = []
        self.task_history = []
        self.task_lock = threading.Lock()
        
        # Thread management
        self.main_thread = None
        self.running = False
        self.threads = []
        self.thread_stop_flags = {}
        
        # Monitoring
        self.monitor_thread = None
        self.monitoring = False
        
        # Resource tracking
        self.current_resources = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
        }
        
        logger.info("Claude Parallel Manager initialized")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Create default config
        default_config = {
            "max_parallel_tasks": 5,
            "resource_thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
            },
            "monitoring_interval": 5,
            "task_types": {
                "blender_task": {
                    "max_instances": 1,
                    "resource_requirements": {"cpu": 40, "memory": 30}
                },
                "simulation": {
                    "max_instances": 2,
                    "resource_requirements": {"cpu": 30, "memory": 25}
                },
                "analysis": {
                    "max_instances": 3,
                    "resource_requirements": {"cpu": 20, "memory": 15}
                },
                "utility": {
                    "max_instances": 5,
                    "resource_requirements": {"cpu": 10, "memory": 10}
                }
            },
            "agent_folders": [
                "AI_Agent_1",
                "AI_Agent_2",
                "AI_Agent_3",
                "AI_Agent_4",
                "AI_Agent_5"
            ],
            "default_task_type": "utility",
            "fallback_mode": "sequential",
            "task_timeout": 3600,  # 1 hour in seconds
            "check_other_agents": True
        }
        
        # Save default config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def add_task(self, task_data: Dict[str, Any], priority: int = 5):
        """
        Add a task to the queue with the given priority.
        Lower priority numbers are executed first.
        """
        
        # Add task metadata
        task_id = task_data.get("id", str(time.time()))
        task_data["id"] = task_id
        task_data["added_time"] = time.time()
        task_data["status"] = "queued"
        
        # Default task type if not specified
        if "task_type" not in task_data:
            task_data["task_type"] = self.config.get("default_task_type", "utility")
            
        logger.info(f"Adding task {task_id} to queue with priority {priority}")
        
        # Add to priority queue - (priority, time added, task data)
        # Time added is used as a secondary sort key to ensure FIFO within same priority
        self.task_queue.put((priority, time.time(), task_data))
        
        return task_id
    
    def start_monitoring(self):
        """Start the resource monitoring thread"""
        if self.monitoring:
            logger.warning("Resource monitoring is already active")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop the resource monitoring thread"""
        if not self.monitoring:
            logger.warning("Resource monitoring is not active")
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_resources(self):
        """Monitor system resources and adjust number of active tasks"""
        interval = self.config.get("monitoring_interval", 5)
        
        while self.monitoring:
            # Get current resource usage
            if PSUTIL_AVAILABLE:
                self.current_resources["cpu_percent"] = psutil.cpu_percent(interval=1)
                self.current_resources["memory_percent"] = psutil.virtual_memory().percent
                self.current_resources["disk_percent"] = psutil.disk_usage('/').percent
            else:
                # Fallback if psutil is not available
                self.current_resources["cpu_percent"] = 50  # Assume 50% usage
                self.current_resources["memory_percent"] = 50
                self.current_resources["disk_percent"] = 50
            
            # Log current resource usage
            logger.debug(f"CPU: {self.current_resources['cpu_percent']}%, "
                       f"Memory: {self.current_resources['memory_percent']}%, "
                       f"Disk: {self.current_resources['disk_percent']}%")
            
            # Sleep for the monitoring interval
            time.sleep(interval)
    
    def start(self):
        """Start the Claude Parallel Manager main thread"""
        if self.running:
            logger.warning("Claude Parallel Manager is already running")
            return False
        
        # Check if other agents are available and configured to be used
        if self.config.get("check_other_agents", True) and self._check_other_agents():
            logger.info("Other parallel agents are available, entering fallback mode")
            return self._start_fallback()
        
        self.running = True
        self.start_monitoring()
        
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        logger.info("Claude Parallel Manager started")
        return True
    
    def stop(self):
        """Stop the Claude Parallel Manager and all running tasks"""
        if not self.running:
            logger.warning("Claude Parallel Manager is not running")
            return False
        
        logger.info("Stopping Claude Parallel Manager")
        self.running = False
        
        # Stop all tasks
        self._stop_all_tasks()
        
        # Wait for main thread to complete
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5.0)
        
        # Stop monitoring
        self.stop_monitoring()
        
        logger.info("Claude Parallel Manager stopped")
        return True
    
    def _check_other_agents(self) -> bool:
        """
        Check if other parallel agents (PyAutoGen, VSCode) are available.
        Returns True if other agents are available, False otherwise.
        """
        # This would integrate with an agent detector module
        # For now, just return False to enable Claude parallel execution
        return False
    
    def _start_fallback(self) -> bool:
        """
        Start the manager in fallback mode when other agents are available.
        """
        fallback_mode = self.config.get("fallback_mode", "sequential")
        logger.info(f"Starting in fallback mode: {fallback_mode}")
        
        if fallback_mode == "sequential":
            # Start in sequential mode - only one task at a time
            self.config["max_parallel_tasks"] = 1
            self.running = True
            self.start_monitoring()
            
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()
            
            logger.info("Claude Parallel Manager started in sequential fallback mode")
            return True
        elif fallback_mode == "disabled":
            # Completely disable the manager when other agents are active
            logger.info("Claude Parallel Manager disabled due to other active agents")
            return False
        else:
            # Unknown fallback mode, default to sequential
            logger.warning(f"Unknown fallback mode: {fallback_mode}, defaulting to sequential")
            return self._start_fallback()
    
    def _main_loop(self):
        """Main task processing loop"""
        logger.info("Starting main processing loop")
        
        while self.running:
            try:
                # Check if we have capacity to run more tasks
                max_tasks = self.config.get("max_parallel_tasks", 5)
                current_tasks = len(self.active_tasks)
                
                if current_tasks < max_tasks:
                    # Check resource limits
                    if self._check_resources_available():
                        # Start a new task if one is available
                        self._start_next_task()
                
                # Check for completed tasks
                self._check_completed_tasks()
                
                # Sleep a short time to prevent CPU hogging
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(1.0)  # Sleep a bit longer on error
    
    def _check_resources_available(self) -> bool:
        """
        Check if there are enough system resources available to start a new task.
        Returns True if resources are available, False otherwise.
        """
        # Get resource thresholds
        thresholds = self.config.get("resource_thresholds", {})
        cpu_threshold = thresholds.get("cpu_percent", 80)
        memory_threshold = thresholds.get("memory_percent", 85)
        
        # Check current usage
        current_cpu = self.current_resources["cpu_percent"]
        current_memory = self.current_resources["memory_percent"]
        
        # Check if we're below thresholds
        cpu_available = current_cpu < cpu_threshold
        memory_available = current_memory < memory_threshold
        
        return cpu_available and memory_available
    
    def _start_next_task(self):
        """Get and start the next task from the queue if available"""
        try:
            # Try to get a task with a short timeout
            priority, _, task_data = self.task_queue.get(timeout=0.1)
            
            # Check if we're at the limit for this task type
            task_type = task_data.get("task_type", self.config.get("default_task_type", "utility"))
            type_limits = self.config.get("task_types", {}).get(task_type, {})
            max_instances = type_limits.get("max_instances", 5)
            
            # Count active tasks of this type
            active_count = sum(1 for t in self.active_tasks.values() 
                             if t.get("task_type") == task_type)
            
            if active_count >= max_instances:
                # We're at the limit for this task type, put it back in the queue
                self.task_queue.put((priority, time.time(), task_data))
                logger.debug(f"Reached limit for task type {task_type}, delaying task {task_data.get('id')}")
                return
            
            # Start the task
            task_id = task_data.get("id")
            logger.info(f"Starting task {task_id} with priority {priority}")
            
            # Update task status
            task_data["status"] = "running"
            task_data["start_time"] = time.time()
            
            # Start task in a separate thread
            thread_stop_flag = threading.Event()
            self.thread_stop_flags[task_id] = thread_stop_flag
            
            thread = threading.Thread(
                target=self._execute_task,
                args=(task_data, thread_stop_flag),
                daemon=True
            )
            thread.start()
            
            # Store thread and task data
            with self.task_lock:
                self.threads.append(thread)
                self.active_tasks[task_id] = task_data
            
            # Task is now being processed
            self.task_queue.task_done()
            
        except queue.Empty:
            # No tasks in queue
            pass
        except Exception as e:
            logger.error(f"Error starting next task: {e}")
    
    def _execute_task(self, task_data: Dict[str, Any], stop_flag: threading.Event):
        """Execute a task in a separate thread"""
        task_id = task_data.get("id")
        task_type = task_data.get("task_type")
        script_path = task_data.get("script_path")
        task_timeout = task_data.get("timeout", self.config.get("task_timeout", 3600))
        
        try:
            logger.info(f"Executing task {task_id} of type {task_type}")
            
            # Set start time for timeout checking
            start_time = time.time()
            result = None
            error = None
            
            # Check task type and execute accordingly
            if script_path and os.path.exists(script_path):
                # Execute a Python script
                result, error = self._run_script(script_path, stop_flag, task_timeout)
            elif "function" in task_data:
                # Execute a function if provided
                func_name = task_data["function"]
                func_args = task_data.get("args", [])
                func_kwargs = task_data.get("kwargs", {})
                
                try:
                    # Find and execute the function
                    result = self._execute_function(func_name, func_args, func_kwargs)
                except Exception as e:
                    error = str(e)
            else:
                error = "No valid script_path or function specified in task"
            
            # Check if task was stopped
            if stop_flag.is_set():
                task_data["status"] = "stopped"
                logger.info(f"Task {task_id} was stopped")
            else:
                # Task completed
                end_time = time.time()
                duration = end_time - start_time
                
                task_data["status"] = "completed" if error is None else "failed"
                task_data["end_time"] = end_time
                task_data["duration"] = duration
                task_data["result"] = result
                task_data["error"] = error
                
                logger.info(f"Task {task_id} completed with status {task_data['status']} in {duration:.2f} seconds")
            
            # Add to completed tasks
            with self.task_lock:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                self.completed_tasks.append(task_data)
                self.task_history.append(task_data)
                
                # Limit history size
                max_history = self.config.get("max_history", 100)
                if len(self.task_history) > max_history:
                    self.task_history = self.task_history[-max_history:]
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            # Mark task as failed
            task_data["status"] = "failed"
            task_data["error"] = str(e)
            task_data["end_time"] = time.time()
            
            # Update task lists
            with self.task_lock:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                self.completed_tasks.append(task_data)
                self.task_history.append(task_data)
    
    def _run_script(self, script_path: str, stop_flag: threading.Event, timeout: int) -> Tuple[Any, Optional[str]]:
        """Run a Python script with the given timeout"""
        logger.info(f"Running script: {script_path}")
        
        try:
            # Create a process to run the script
            process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the process to complete or timeout
            start_time = time.time()
            while process.poll() is None:
                # Check if we should stop
                if stop_flag.is_set():
                    process.terminate()
                    return None, "Task was stopped"
                
                # Check timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    return None, f"Task exceeded timeout of {timeout} seconds"
                
                # Sleep a bit to prevent CPU hogging
                time.sleep(0.1)
            
            # Get output and error
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return stdout, None
            else:
                return stdout, stderr
                
        except Exception as e:
            return None, str(e)
    
    def _execute_function(self, func_name: str, args: List[Any], kwargs: Dict[str, Any]) -> Any:
        """Execute a named function with the given arguments"""
        logger.info(f"Executing function: {func_name}")
        
        # This would require a more sophisticated implementation to dynamically
        # import and execute functions. For now, just return a placeholder result.
        return f"Function {func_name} would be executed with args={args}, kwargs={kwargs}"
    
    def _check_completed_tasks(self):
        """Check for completed tasks and perform any necessary cleanup"""
        # Clean up finished threads
        with self.task_lock:
            active_threads = []
            for thread in self.threads:
                if thread.is_alive():
                    active_threads.append(thread)
            self.threads = active_threads
    
    def _stop_all_tasks(self):
        """Stop all running tasks"""
        logger.info("Stopping all running tasks")
        
        # Set all stop flags
        for task_id, stop_flag in self.thread_stop_flags.items():
            stop_flag.set()
        
        # Wait for tasks to complete
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        # Clear active tasks
        with self.task_lock:
            for task_id, task_data in self.active_tasks.items():
                task_data["status"] = "stopped"
                self.completed_tasks.append(task_data)
            self.active_tasks.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the Claude Parallel Manager"""
        with self.task_lock:
            status = {
                "running": self.running,
                "resources": self.current_resources,
                "active_tasks": len(self.active_tasks),
                "queued_tasks": self.task_queue.qsize(),
                "completed_tasks": len(self.completed_tasks),
                "active_task_ids": list(self.active_tasks.keys()),
                "task_details": {
                    "active": list(self.active_tasks.values()),
                    "completed": self.completed_tasks[-10:] if self.completed_tasks else []
                },
                "config": {
                    "max_parallel_tasks": self.config.get("max_parallel_tasks", 5),
                    "resource_thresholds": self.config.get("resource_thresholds", {})
                }
            }
            return status
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.get("id") == task_id:
                return task
        
        # Check task history
        for task in self.task_history:
            if task.get("id") == task_id:
                return task
        
        return {"error": "Task not found"}
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or queued task"""
        logger.info(f"Attempting to cancel task {task_id}")
        
        # Check if task is active
        if task_id in self.active_tasks:
            # Set stop flag if available
            if task_id in self.thread_stop_flags:
                self.thread_stop_flags[task_id].set()
                logger.info(f"Stop flag set for task {task_id}")
                return True
        
        # Check if task is in queue
        new_queue = queue.PriorityQueue()
        found = False
        
        while not self.task_queue.empty():
            try:
                priority, time_added, task_data = self.task_queue.get()
                if task_data.get("id") == task_id:
                    # Found the task, mark it as cancelled
                    task_data["status"] = "cancelled"
                    self.completed_tasks.append(task_data)
                    found = True
                    logger.info(f"Cancelled queued task {task_id}")
                else:
                    # Put it back in the new queue
                    new_queue.put((priority, time_added, task_data))
            except queue.Empty:
                break
        
        # Replace queue with new_queue
        self.task_queue = new_queue
        
        return found
    
    def get_queue_status(self) -> List[Dict[str, Any]]:
        """Get a list of tasks in the queue"""
        items = []
        
        # Create a copy of the queue
        temp_queue = queue.PriorityQueue()
        queue_copy = []
        
        # Extract items from the original queue
        while not self.task_queue.empty():
            try:
                item = self.task_queue.get()
                queue_copy.append(item)
            except queue.Empty:
                break
        
        # Put items back into the original queue and create result list
        for priority, time_added, task_data in queue_copy:
            self.task_queue.put((priority, time_added, task_data))
            
            # Add task info to result
            items.append({
                "id": task_data.get("id"),
                "priority": priority,
                "task_type": task_data.get("task_type"),
                "added_time": datetime.datetime.fromtimestamp(time_added).isoformat(),
                "details": task_data
            })
        
        # Sort by priority
        return sorted(items, key=lambda x: x["priority"])
    
    # Utility methods for common task types
    
    def add_script_task(self, script_path: str, priority: int = 5, task_type: str = None) -> str:
        """Add a script execution task to the queue"""
        # Determine task type based on script path if not provided
        if task_type is None:
            if "blender" in script_path.lower():
                task_type = "blender_task"
            elif "simulation" in script_path.lower():
                task_type = "simulation"
            elif "analysis" in script_path.lower():
                task_type = "analysis"
            else:
                task_type = self.config.get("default_task_type", "utility")
        
        # Create task data
        task_data = {
            "script_path": script_path,
            "task_type": task_type,
            "name": os.path.basename(script_path)
        }
        
        # Add to queue
        return self.add_task(task_data, priority)
    
    def add_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Add multiple tasks to the queue in a batch"""
        task_ids = []
        
        for task in tasks:
            priority = task.pop("priority", 5)  # Extract priority if provided
            task_id = self.add_task(task, priority)
            task_ids.append(task_id)
        
        return task_ids


# Example usage
if __name__ == "__main__":
    print("Claude Parallel Manager - Example Usage")
    print("=======================================")
    
    # Create manager
    manager = ClaudeParallelManager()
    
    # Add some example tasks
    tasks = [
        {
            "script_path": os.path.join(BASE_DIR, "ai_managers", "test_script.py"),
            "task_type": "utility",
            "name": "Test Script 1",
            "priority": 1
        },
        {
            "script_path": os.path.join(BASE_DIR, "scripts", "test_script.py"), 
            "task_type": "analysis",
            "name": "Test Script 2",
            "priority": 2
        },
        {
            "function": "example_function",
            "args": ["arg1", "arg2"],
            "kwargs": {"param1": "value1"},
            "task_type": "utility",
            "name": "Test Function",
            "priority": 3
        }
    ]
    
    print("Adding example tasks...")
    task_ids = manager.add_batch_tasks(tasks)
    print(f"Added {len(task_ids)} tasks: {task_ids}")
    
    # Start the manager
    print("Starting manager...")
    manager.start()
    
    try:
        # Run for a while
        print("Running...")
        for i in range(6):
            time.sleep(5)
            
            # Get status
            status = manager.get_status()
            
            print(f"\nStatus Update {i+1}/6:")
            print(f"  Running: {status['running']}")
            print(f"  Active Tasks: {status['active_tasks']}")
            print(f"  Queued Tasks: {status['queued_tasks']}")
            print(f"  Completed Tasks: {status['completed_tasks']}")
            print(f"  CPU Usage: {status['resources']['cpu_percent']}%")
            print(f"  Memory Usage: {status['resources']['memory_percent']}%")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down...")
    finally:
        # Stop the manager
        print("Stopping manager...")
        manager.stop()
        print("Manager stopped.")