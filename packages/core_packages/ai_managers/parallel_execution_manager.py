#!/usr/bin/env python
"""
Parallel Execution Manager for GlowingGoldenGlobe

This specialized AI manager coordinates parallel execution of different project roles
while ensuring optimal hardware resource allocation. It intelligently schedules and 
manages concurrent processes without overloading the system.

Responsibilities:
- Coordinate simultaneous execution of multiple AI Managers
- Monitor system resources and dynamically adjust workloads
- Schedule and prioritize tasks based on resource availability
- Implement adaptive load balancing across different roles
- Prevent system overload and resource contention
- Provide progress reporting and execution metrics

NOTE: This manager follows the Automation Guidelines in README.md to ensure automation works within
established project guidelines without deviating irrationally from conventions.
"""

import os
import time
import json
import threading
import logging
import queue
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set, Union

# Try to import psutil for better system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
# Import file usage tracker
try:
    from file_usage_tracker import get_file_usage_tracker
    FILE_TRACKER_AVAILABLE = True
except ImportError:
    FILE_TRACKER_AVAILABLE = False
    print("File usage tracking will be disabled (file_usage_tracker module not available)")

class ParallelExecutionManager:
    """
    Specialized AI Manager that coordinates parallel execution of project roles
    while ensuring optimal hardware resource utilization.
    """
    
    # Define project role categories for execution
    ROLE_AGENT_SIMULATIONS = "agent_simulations"
    ROLE_PROJECT_MANAGEMENT = "project_management"
    ROLE_RESOURCE_MANAGEMENT = "resource_management"
    ROLE_SCRIPT_ASSESSMENT = "script_assessment"
    ROLE_GUI_TESTING = "gui_testing"
    ROLE_TASK_MANAGEMENT = "task_management"
    
    def __init__(self, config_path: str = "parallel_execution_config.json", build_contexts: bool = True):
        """Initialize the Parallel Execution Manager"""
        self.config_path = config_path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.build_contexts = build_contexts
        self.context_builder = None
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.base_dir, "parallel_execution.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ParallelExecutionManager")
        self.logger.info("Initializing Parallel Execution Manager")
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize execution queues for different roles
        self.execution_queues = {
            self.ROLE_AGENT_SIMULATIONS: queue.Queue(),
            self.ROLE_PROJECT_MANAGEMENT: queue.Queue(),
            self.ROLE_RESOURCE_MANAGEMENT: queue.Queue(),
            self.ROLE_SCRIPT_ASSESSMENT: queue.Queue(),
            self.ROLE_GUI_TESTING: queue.Queue(),
            self.ROLE_TASK_MANAGEMENT: queue.Queue(),
        }
        
        # Initialize threads for each role
        self.role_threads = {}
        self.active_roles = set()
        self.thread_stop_flags = {}
        
        # Resource monitoring thread
        self.monitor_thread = None
        self.monitoring = False
        
        # Resource thresholds - will be overridden by config
        self.resource_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
        }
        
        # Current resource usage
        self.current_resources = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
        }
        
        # Initialize file usage tracker if available
        self.file_tracker = None
        if FILE_TRACKER_AVAILABLE:
            try:
                self.file_tracker = get_file_usage_tracker()
                self.logger.info("File usage tracking enabled")
            except Exception as e:
                self.logger.error(f"Error initializing file usage tracker: {str(e)}")
        else:
            self.logger.warning("File usage tracking not available")
        
        # Role priority and resource requirements
        self.role_priorities = {
            self.ROLE_RESOURCE_MANAGEMENT: 10,  # Highest priority
            self.ROLE_PROJECT_MANAGEMENT: 9,
            self.ROLE_TASK_MANAGEMENT: 8,
            self.ROLE_AGENT_SIMULATIONS: 7,
            self.ROLE_SCRIPT_ASSESSMENT: 6,
            self.ROLE_GUI_TESTING: 5,
        }
        
        # Resource requirements per role (percentage of total)
        self.role_resource_requirements = {
            self.ROLE_AGENT_SIMULATIONS: {"cpu": 60, "memory": 40},
            self.ROLE_PROJECT_MANAGEMENT: {"cpu": 10, "memory": 15},
            self.ROLE_RESOURCE_MANAGEMENT: {"cpu": 5, "memory": 10},
            self.ROLE_SCRIPT_ASSESSMENT: {"cpu": 20, "memory": 20},
            self.ROLE_GUI_TESTING: {"cpu": 15, "memory": 25},
            self.ROLE_TASK_MANAGEMENT: {"cpu": 5, "memory": 10},
        }
        
        # Agent folder mapping
        self.agent_folders = {}
        for i in range(1, 13):
            self.agent_folders[f"AI_Agent_{i}"] = os.path.join(self.base_dir, f"AI_Agent_{i}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        config_path = os.path.join(self.base_dir, self.config_path)
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {config_path}")
                return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Create default config
        default_config = {
            "resource_thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
            },
            "role_priorities": {
                self.ROLE_RESOURCE_MANAGEMENT: 10,
                self.ROLE_PROJECT_MANAGEMENT: 9,
                self.ROLE_TASK_MANAGEMENT: 8,
                self.ROLE_AGENT_SIMULATIONS: 7,
                self.ROLE_SCRIPT_ASSESSMENT: 6,
                self.ROLE_GUI_TESTING: 5,
            },
            "role_resource_requirements": {
                self.ROLE_AGENT_SIMULATIONS: {"cpu": 60, "memory": 40},
                self.ROLE_PROJECT_MANAGEMENT: {"cpu": 10, "memory": 15},
                self.ROLE_RESOURCE_MANAGEMENT: {"cpu": 5, "memory": 10},
                self.ROLE_SCRIPT_ASSESSMENT: {"cpu": 20, "memory": 20},
                self.ROLE_GUI_TESTING: {"cpu": 15, "memory": 25},
                self.ROLE_TASK_MANAGEMENT: {"cpu": 5, "memory": 10},
            },
            "monitoring_interval": 5,  # seconds
        }
        
        # Save default config
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info(f"Created default configuration at {config_path}")
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file"""
        config_path = os.path.join(self.base_dir, self.config_path)
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved configuration to {config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def start_monitoring(self):
        """Start the resource monitoring thread"""
        if self.monitoring:
            self.logger.warning("Resource monitoring is already active")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop the resource monitoring thread"""
        if not self.monitoring:
            self.logger.warning("Resource monitoring is not active")
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Resource monitoring stopped")
    
    def _monitor_resources(self):
        """Monitor system resources and adjust active roles"""
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
            
            # Check if any thresholds are exceeded
            cpu_threshold = self.resource_thresholds.get("cpu_percent", 80)
            mem_threshold = self.resource_thresholds.get("memory_percent", 85)
            disk_threshold = self.resource_thresholds.get("disk_percent", 90)
            
            # Log current resource usage
            self.logger.debug(f"CPU: {self.current_resources['cpu_percent']}%, "
                           f"Memory: {self.current_resources['memory_percent']}%, "
                           f"Disk: {self.current_resources['disk_percent']}%")
            
            # Check if we need to scale back some roles
            if (self.current_resources["cpu_percent"] > cpu_threshold or
                self.current_resources["memory_percent"] > mem_threshold):
                self._scale_back_roles()
            else:
                # If resources are available, consider starting new roles
                self._scale_up_roles()
            
            # Sleep for the monitoring interval
            time.sleep(interval)
    
    def _scale_back_roles(self):
        """Scale back roles when resource usage is too high"""
        self.logger.warning("Resource usage too high, scaling back roles")
        
        # Get roles sorted by priority (lowest first)
        sorted_roles = sorted(
            self.active_roles, 
            key=lambda x: self.role_priorities.get(x, 0)
        )
        
        # Start shutting down the lowest priority roles
        if sorted_roles:
            role_to_stop = sorted_roles[0]
            self.logger.info(f"Stopping role: {role_to_stop}")
            
            # Signal the thread to stop
            if role_to_stop in self.thread_stop_flags:
                self.thread_stop_flags[role_to_stop] = True
                
                # Wait for thread to finish current task
                thread = self.role_threads.get(role_to_stop)
                if thread and thread.is_alive():
                    thread.join(timeout=5.0)
                
                # Remove from active roles
                if role_to_stop in self.active_roles:
                    self.active_roles.remove(role_to_stop)
    
    def _scale_up_roles(self):
        """Start additional roles when resources are available"""
        # Check which roles are not active yet
        inactive_roles = set(self.role_priorities.keys()) - self.active_roles
        
        if not inactive_roles:
            return  # All roles are active
        
        # Get inactive roles sorted by priority (highest first)
        sorted_roles = sorted(
            inactive_roles, 
            key=lambda x: self.role_priorities.get(x, 0),
            reverse=True
        )
        
        # Check if we have enough resources for the highest priority inactive role
        for role in sorted_roles:
            cpu_req = self.role_resource_requirements.get(role, {}).get("cpu", 0)
            mem_req = self.role_resource_requirements.get(role, {}).get("memory", 0)
            
            # Check if there are enough resources available
            if (self.current_resources["cpu_percent"] + cpu_req < self.resource_thresholds["cpu_percent"] and
                self.current_resources["memory_percent"] + mem_req < self.resource_thresholds["memory_percent"]):
                
                # Start this role
                self.logger.info(f"Starting role: {role}")
                self._start_role_thread(role)
                break  # Start only one role at a time
    
    def _start_role_thread(self, role: str):
        """Start a thread for the given role"""
        if role in self.active_roles:
            self.logger.warning(f"Role {role} is already active")
            return
        
        # Reset stop flag
        self.thread_stop_flags[role] = False
        
        # Create and start thread
        if role == self.ROLE_AGENT_SIMULATIONS:
            thread = threading.Thread(target=self._run_agent_simulations, daemon=True)
        elif role == self.ROLE_PROJECT_MANAGEMENT:
            thread = threading.Thread(target=self._run_project_management, daemon=True)
        elif role == self.ROLE_RESOURCE_MANAGEMENT:
            thread = threading.Thread(target=self._run_resource_management, daemon=True)
        elif role == self.ROLE_SCRIPT_ASSESSMENT:
            thread = threading.Thread(target=self._run_script_assessment, daemon=True)
        elif role == self.ROLE_GUI_TESTING:
            thread = threading.Thread(target=self._run_gui_testing, daemon=True)
        elif role == self.ROLE_TASK_MANAGEMENT:
            thread = threading.Thread(target=self._run_task_management, daemon=True)
        else:
            self.logger.error(f"Unknown role: {role}")
            return
        
        # Start thread and mark role as active
        thread.start()
        self.role_threads[role] = thread
        self.active_roles.add(role)
        self.logger.info(f"Started thread for role: {role}")
    
    def queue_task(self, role: str, task: Dict[str, Any]):
        """Queue a task for the specified role"""
        if role not in self.execution_queues:
            self.logger.error(f"Unknown role: {role}")
            return False
        
        # Generate a workflow ID for file tracking if not provided
        if self.file_tracker and 'workflow_id' not in task:
            task['workflow_id'] = f"{role}_{int(time.time())}_{task.get('name', 'task').replace(' ', '_')}"
            
            # Register anticipated files if specified
            if 'files' in task:
                self.file_tracker.register_workflow(
                    task['workflow_id'],
                    role,
                    task['files'],
                    priority=self.role_priorities.get(role, 5)
                )
                self.logger.info(f"Registered workflow {task['workflow_id']} for file tracking with {len(task['files'])} files")
        
        self.execution_queues[role].put(task)
        self.logger.info(f"Queued task for role {role}: {task.get('name', 'unnamed')}")
        return True
    
    def start_all_roles(self):
        """Start all roles with appropriate resource allocation"""
        self.logger.info("Starting all roles with resource limitations")
        
        # Build context summaries for all roles if enabled
        if self.build_contexts:
            self._build_role_contexts()
        
        # Start resource monitoring first
        self.start_monitoring()
        
        # Start with highest priority roles first
        sorted_roles = sorted(
            self.role_priorities.keys(),
            key=lambda x: self.role_priorities.get(x, 0),
            reverse=True
        )
        
        for role in sorted_roles:
            # Start role if it's not already active
            if role not in self.active_roles:
                self._start_role_thread(role)
                
                # Wait a bit to allow resource monitoring to adjust
                time.sleep(2.0)
    
    def stop_all_roles(self):
        """Stop all active roles"""
        self.logger.info("Stopping all active roles")
        
        # Signal all threads to stop
        for role in self.active_roles:
            if role in self.thread_stop_flags:
                self.thread_stop_flags[role] = True
        
        # Wait for all threads to finish
        for role, thread in self.role_threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=5.0)
        
        # Clear active roles
        self.active_roles.clear()
        
        # Stop resource monitoring
        self.stop_monitoring()
    
    def _should_stop(self, role: str) -> bool:
        """Check if the thread for this role should stop"""
        return role in self.thread_stop_flags and self.thread_stop_flags[role]
    
    def _build_role_contexts(self):
        """Build context summaries for all roles"""
        self.logger.info("Building context summaries for all roles")
        
        try:
            # Import the context builder
            from ai_roles_context_builder import AIManagerContextBuilder
            
            self.context_builder = AIManagerContextBuilder(self.base_dir)
            
            # Build general context
            general_context = self.context_builder.build_context()
            self.context_builder.save_context(general_context)
            
            # Map our roles to context builder roles
            role_mapping = {
                self.ROLE_PROJECT_MANAGEMENT: "project_ai_manager",
                self.ROLE_RESOURCE_MANAGEMENT: "resource_manager",
                self.ROLE_TASK_MANAGEMENT: "task_manager",
                self.ROLE_SCRIPT_ASSESSMENT: "script_assessment",
                self.ROLE_GUI_TESTING: "gui_testing",
                self.ROLE_AGENT_SIMULATIONS: "agent_simulations"
            }
            
            # Build role-specific contexts
            for parallel_role, context_role in role_mapping.items():
                try:
                    context = self.context_builder.build_context(context_role)
                    summary = self.context_builder.create_role_specific_summary(context_role)
                    
                    # Save the summary to a role-specific file
                    summary_path = os.path.join(self.base_dir, "ai_managers", f"{context_role}_context.md")
                    with open(summary_path, 'w') as f:
                        f.write(summary)
                    
                    self.logger.info(f"Built context for role: {context_role}")
                except Exception as e:
                    self.logger.error(f"Error building context for {context_role}: {e}")
            
            # Update the startup summary with parallel execution info
            self.context_builder.update_startup_summary({
                "Parallel Execution": "Active",
                "Active Roles": len(self.role_priorities),
                "Context Building": "Enabled"
            })
            
            self.logger.info("Context building completed successfully")
            
        except ImportError:
            self.logger.warning("Context builder not available - continuing without context summaries")
        except Exception as e:
            self.logger.error(f"Error during context building: {e}")
            # Continue execution even if context building fails
    
    def get_role_context(self, role: str) -> str:
        """Get the context summary for a specific role"""
        role_mapping = {
            self.ROLE_PROJECT_MANAGEMENT: "project_ai_manager",
            self.ROLE_RESOURCE_MANAGEMENT: "resource_manager",
            self.ROLE_TASK_MANAGEMENT: "task_manager",
            self.ROLE_SCRIPT_ASSESSMENT: "script_assessment",
            self.ROLE_GUI_TESTING: "gui_testing",
            self.ROLE_AGENT_SIMULATIONS: "agent_simulations"
        }
        
        context_role = role_mapping.get(role)
        if not context_role:
            return f"No context mapping for role: {role}"
        
        context_path = os.path.join(self.base_dir, "ai_managers", f"{context_role}_context.md")
        
        if os.path.exists(context_path):
            with open(context_path, 'r') as f:
                return f.read()
        else:
            return f"No context file found for role: {context_role}"
    
    def get_available_roles(self):
        """Return a list of all available roles."""
        return [
            self.ROLE_AGENT_SIMULATIONS,
            self.ROLE_PROJECT_MANAGEMENT,
            self.ROLE_RESOURCE_MANAGEMENT,
            self.ROLE_SCRIPT_ASSESSMENT, 
            self.ROLE_GUI_TESTING,
            self.ROLE_TASK_MANAGEMENT
        ]
    
    #
    # Role-specific execution methods
    #
    
    def _run_agent_simulations(self):
        """Run Agent Folder Simulations"""
        role = self.ROLE_AGENT_SIMULATIONS
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Extract task details
                    agent_id = task.get("agent_id")
                    script = task.get("script")
                    workflow_id = task.get("workflow_id")
                    
                    # Update workflow status if tracking enabled
                    if self.file_tracker and workflow_id:
                        self.file_tracker.update_workflow_status(workflow_id, "in_progress")
                    
                    if agent_id and script:
                        agent_folder = self.agent_folders.get(agent_id)
                        if agent_folder and os.path.exists(agent_folder):
                            script_path = os.path.join(agent_folder, script)
                            if os.path.exists(script_path):
                                # Run the simulation script with workflow ID for file tracking
                                self._run_script(script_path, workflow_id)
                            else:
                                self.logger.error(f"Script not found: {script_path}")
                        else:
                            self.logger.error(f"Agent folder not found: {agent_folder}")
                    
                    # Complete workflow if tracking enabled
                    if self.file_tracker and workflow_id:
                        self.file_tracker.complete_workflow(workflow_id)
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, check for automatic work
                    self._run_automatic_agent_simulations()
            
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Small delay to prevent CPU hogging
            time.sleep(0.1)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _run_automatic_agent_simulations(self):
        """Run automatic simulations in AI Agent folders"""
        # This is an example of what this method might do
        for agent_id, folder_path in self.agent_folders.items():
            if not os.path.exists(folder_path):
                continue
                
            # Check if there are any simulation scripts
            sim_scripts = [f for f in os.listdir(folder_path) 
                          if f.endswith(".py") and "simulation" in f.lower()]
            
            for script in sim_scripts:
                # Check if this simulation should be run (e.g., not recently run)
                # This is a simplified check - you would want more sophisticated logic
                log_file = os.path.join(folder_path, f"{script}.log")
                should_run = True
                
                if os.path.exists(log_file):
                    # Check when it was last run
                    mod_time = os.path.getmtime(log_file)
                    now = time.time()
                    hours_since_run = (now - mod_time) / 3600
                    
                    # Only run if it hasn't been run in the last 12 hours
                    should_run = hours_since_run > 12
                
                if should_run:
                    # Create a task and queue it
                    task = {
                        "name": f"Auto-simulation {script}",
                        "agent_id": agent_id,
                        "script": script,
                        "priority": "normal"
                    }
                    self.queue_task(self.ROLE_AGENT_SIMULATIONS, task)
                    
                    # Only schedule one simulation at a time
                    break
    
    def _run_project_management(self):
        """Run Project Management tasks"""
        role = self.ROLE_PROJECT_MANAGEMENT
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Implement project management logic here
                    # (e.g., call project_ai_manager functions)
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, perform routine checks
                    pass
                    
                # Call the project AI manager to coordinate project activities
                self._coordinate_project_activities()
                
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Sleep a bit longer for project management tasks
            time.sleep(5.0)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _coordinate_project_activities(self):
        """Coordinate project activities using the Project AI Manager"""
        try:
            # This would integrate with project_ai_manager.py
            pass
        except Exception as e:
            self.logger.error(f"Error coordinating project activities: {str(e)}")
    
    def _run_resource_management(self):
        """Run Resource Management tasks"""
        role = self.ROLE_RESOURCE_MANAGEMENT
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Implement resource management logic here
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, perform routine resource checks
                    pass
                
                # Check and optimize resource allocation
                self._optimize_resource_allocation()
                
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Sleep for resource management checks
            time.sleep(10.0)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _optimize_resource_allocation(self):
        """Optimize resource allocation for all running processes"""
        try:
            # Integration with project_resource_manager.py would go here
            pass
        except Exception as e:
            self.logger.error(f"Error optimizing resource allocation: {str(e)}")
    
    def _run_script_assessment(self):
        """Run Script Assessment tasks"""
        role = self.ROLE_SCRIPT_ASSESSMENT
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Implement script assessment logic
                    script_path = task.get("script_path")
                    if script_path and os.path.exists(script_path):
                        self._assess_script(script_path)
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, perform routine assessments
                    self._run_automated_script_assessments()
                
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Sleep between script assessments
            time.sleep(15.0)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _assess_script(self, script_path):
        """Assess a script for quality and improvements"""
        try:
            # Basic script assessment logic
            self.logger.info(f"Assessing script: {script_path}")
            
            # Check if file exists
            if not os.path.exists(script_path):
                self.logger.error(f"Script not found: {script_path}")
                return
            
            # Check file size
            file_size = os.path.getsize(script_path)
            self.logger.info(f"Script size: {file_size} bytes")
            
            # Check Python syntax
            result = subprocess.run(
                ["python", "-m", "py_compile", script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Script has syntax errors: {result.stderr}")
            else:
                self.logger.info(f"Script syntax is valid")
            
            # TODO: More advanced assessment would go here
            
        except Exception as e:
            self.logger.error(f"Error assessing script {script_path}: {str(e)}")
    
    def _run_automated_script_assessments(self):
        """Run automated assessments on project scripts"""
        # Find scripts that might need assessment
        scripts_to_check = []
        
        # Look for recently modified Python files
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    
                    # Skip files in certain directories
                    if any(skip_dir in full_path for skip_dir in ['__pycache__', '.git', 'Lib', 'Scripts']):
                        continue
                    
                    # Check if modified in last 24 hours
                    mod_time = os.path.getmtime(full_path)
                    if (time.time() - mod_time) < 86400:  # 24 hours in seconds
                        scripts_to_check.append(full_path)
        
        # Queue up to 3 scripts for assessment
        for script in scripts_to_check[:3]:
            task = {
                "name": f"Auto-assess {os.path.basename(script)}",
                "script_path": script,
                "priority": "low"
            }
            self.queue_task(self.ROLE_SCRIPT_ASSESSMENT, task)
    
    def _run_gui_testing(self):
        """Run GUI Testing tasks"""
        role = self.ROLE_GUI_TESTING
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Implement GUI testing logic
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, perform routine GUI tests
                    self._run_automated_gui_tests()
                
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Sleep between GUI tests to avoid overwhelming the system
            time.sleep(30.0)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _run_automated_gui_tests(self):
        """Run automated GUI tests"""
        # This would integrate with GUI testing frameworks
        # For demonstration, we'll just log a message
        self.logger.info("Running automated GUI tests")
        
        # Find GUI-related files
        gui_files = [f for f in os.listdir(self.base_dir) 
                    if f.endswith('.py') and 'gui' in f.lower()]
        
        if gui_files:
            self.logger.info(f"Found {len(gui_files)} GUI files to potentially test")
    
    def _run_task_management(self):
        """Run Task Management activities"""
        role = self.ROLE_TASK_MANAGEMENT
        self.logger.info(f"Starting {role} execution")
        
        while not self._should_stop(role):
            try:
                # Check if there are tasks in the queue
                try:
                    task = self.execution_queues[role].get(block=True, timeout=1.0)
                    self.logger.info(f"Processing {role} task: {task.get('name', 'unnamed')}")
                    
                    # Implement task management logic
                    
                    # Mark task as done
                    self.execution_queues[role].task_done()
                except queue.Empty:
                    # No tasks available, perform routine task management
                    self._manage_project_tasks()
                
            except Exception as e:
                self.logger.error(f"Error in {role} thread: {str(e)}")
            
            # Sleep between task management runs
            time.sleep(20.0)
        
        self.logger.info(f"Stopped {role} execution")
    
    def _manage_project_tasks(self):
        """Manage project tasks using the Task Manager"""
        # This would integrate with task_manager.py
        self.logger.info("Managing project tasks")
    
    def _run_script(self, script_path: str, workflow_id: Optional[str] = None) -> bool:
        """Run a Python script and return success/failure"""
        self.logger.info(f"Running script: {script_path}")
        
        # Try to acquire file lock if file tracking is enabled
        if self.file_tracker and workflow_id:
            role = self._get_role_from_workflow_id(workflow_id)
            if not self.file_tracker.request_file_lock(script_path, role or "unknown", "read", workflow_id=workflow_id):
                self.logger.warning(f"Could not acquire file lock for {script_path}, it may be in use by another role")
                # We'll continue anyway but log the warning
        
        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True
            )
            
            # Release file lock if we acquired one
            if self.file_tracker and workflow_id:
                role = self._get_role_from_workflow_id(workflow_id)
                self.file_tracker.release_file_lock(script_path, role or "unknown")
            
            if result.returncode == 0:
                self.logger.info(f"Script executed successfully: {script_path}")
                return True
            else:
                self.logger.error(f"Script execution failed: {script_path}")
                self.logger.error(f"Error output: {result.stderr}")
                return False
                
        except Exception as e:
            # Release file lock in case of exception
            if self.file_tracker and workflow_id:
                role = self._get_role_from_workflow_id(workflow_id)
                self.file_tracker.release_file_lock(script_path, role or "unknown")
                
            self.logger.error(f"Error running script {script_path}: {str(e)}")
            return False
            
    def _get_role_from_workflow_id(self, workflow_id: str) -> Optional[str]:
        """Extract role from workflow ID if possible"""
        if not workflow_id:
            return None
            
        # Workflow IDs are formatted as role_timestamp_name
        parts = workflow_id.split('_', 1)
        if parts and len(parts) > 0:
            role_name = parts[0]
            # Verify it's a valid role
            for role in [self.ROLE_AGENT_SIMULATIONS, self.ROLE_PROJECT_MANAGEMENT, 
                        self.ROLE_RESOURCE_MANAGEMENT, self.ROLE_SCRIPT_ASSESSMENT,
                        self.ROLE_GUI_TESTING, self.ROLE_TASK_MANAGEMENT]:
                if role_name == role:
                    return role
        return None


if __name__ == "__main__":
    # Example usage
    manager = ParallelExecutionManager()
    
    # Start all roles with resource management
    manager.start_all_roles()
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        manager.stop_all_roles()
    except Exception as e:
        print(f"Error: {e}")
        manager.stop_all_roles()
