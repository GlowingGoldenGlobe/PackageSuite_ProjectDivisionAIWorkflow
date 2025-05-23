#!/usr/bin/env python
"""
Claude Resource Monitor for GlowingGoldenGlobe

This module provides enhanced resource monitoring and automatic resource allocation
for the Claude Parallel Execution System. It monitors system resources such as CPU,
memory, and disk usage, and adjusts the parallel execution workload accordingly.

The resource monitor runs as a background thread that periodically checks system
resources and provides recommendations for task scheduling and execution to the
Claude Parallel Manager.
"""

import os
import sys
import time
import json
import threading
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("claude_resource_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ClaudeResourceMonitor")

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to import psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    logger.warning("psutil not available, using fallback resource monitoring")
    PSUTIL_AVAILABLE = False

class ResourceUsage:
    """
    Represents a snapshot of system resource usage.
    """
    
    def __init__(self, cpu_percent: float = 0, memory_percent: float = 0, 
                 disk_percent: float = 0, network_bytes: int = 0):
        """
        Initialize resource usage snapshot.
        
        Args:
            cpu_percent: CPU usage as a percentage
            memory_percent: Memory usage as a percentage
            disk_percent: Disk usage as a percentage
            network_bytes: Network usage in bytes
        """
        self.timestamp = time.time()
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.disk_percent = disk_percent
        self.network_bytes = network_bytes
        self.process_details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert resource usage to a dictionary.
        
        Returns:
            Dictionary representation of resource usage
        """
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "network_bytes": self.network_bytes,
            "process_details": self.process_details
        }

class ResourceAllocationStrategy:
    """
    Represents a resource allocation strategy recommendation.
    """
    
    # Strategy types
    SCALE_UP = "scale_up"          # Increase task parallelism
    MAINTAIN = "maintain"          # Maintain current task parallelism
    SCALE_DOWN = "scale_down"      # Reduce task parallelism
    STOP_NEW_TASKS = "stop_new"    # Don't start new tasks, but allow current ones to finish
    EMERGENCY_STOP = "emergency"   # Stop all tasks due to critical resource shortage
    
    def __init__(self, strategy_type: str, max_tasks: int, resource_reason: str,
                 task_type_limits: Optional[Dict[str, int]] = None):
        """
        Initialize a resource allocation strategy.
        
        Args:
            strategy_type: Type of strategy (scale_up, maintain, scale_down, stop_new, emergency)
            max_tasks: Recommended maximum number of concurrent tasks
            resource_reason: Reason for the recommendation
            task_type_limits: Recommended limits for specific task types
        """
        self.timestamp = time.time()
        self.strategy_type = strategy_type
        self.max_tasks = max_tasks
        self.resource_reason = resource_reason
        self.task_type_limits = task_type_limits or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert strategy to a dictionary.
        
        Returns:
            Dictionary representation of the strategy
        """
        return {
            "timestamp": self.timestamp,
            "strategy_type": self.strategy_type,
            "max_tasks": self.max_tasks,
            "resource_reason": self.resource_reason,
            "task_type_limits": self.task_type_limits
        }

class ClaudeResourceMonitor:
    """
    Enhanced resource monitoring and automatic allocation for Claude Parallel Execution System.
    """
    
    def __init__(self, config_path: str = "claude_resource_config.json"):
        """
        Initialize the Resource Monitor.
        
        Args:
            config_path: Path to resource monitor configuration file
        """
        self.config_path = os.path.join(BASE_DIR, config_path)
        self.config = self._load_config()
        
        # Resource monitoring
        self.running = False
        self.monitor_thread = None
        self.allocation_thread = None
        self.current_usage = ResourceUsage()
        self.usage_history = []  # List of ResourceUsage objects
        self.max_history = self.config.get("max_history", 100)
        
        # Resource allocation
        self.current_strategy = None
        self.strategy_history = []
        self.strategy_callback = None
        
        # Load historic data if available
        self._load_history()
        
        logger.info("Resource Monitor initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        default_config = {
            "monitoring_interval": 5,  # Seconds between checks
            "allocation_interval": 15,  # Seconds between allocation decisions
            "max_history": 100,         # Maximum number of history entries to keep
            "resource_thresholds": {
                "cpu_percent": {
                    "low": 20,
                    "medium": 50,
                    "high": 80,
                    "critical": 90
                },
                "memory_percent": {
                    "low": 20,
                    "medium": 60,
                    "high": 80,
                    "critical": 90
                },
                "disk_percent": {
                    "low": 50,
                    "medium": 70,
                    "high": 85,
                    "critical": 95
                }
            },
            "task_type_weights": {
                "blender_task": {"cpu": 4.0, "memory": 3.0, "disk": 2.0},
                "simulation": {"cpu": 3.0, "memory": 2.0, "disk": 1.0},
                "analysis": {"cpu": 2.0, "memory": 1.5, "disk": 0.5},
                "utility": {"cpu": 1.0, "memory": 1.0, "disk": 0.5}
            },
            "save_history": True,
            "history_file": "resource_history.json",
            "adaptive_allocation": True,
            "log_level": "INFO"
        }
        
        # Save default configuration
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
        
        return default_config
    
    def _load_history(self):
        """Load resource usage and strategy history from file"""
        history_file = os.path.join(BASE_DIR, self.config.get("history_file", "resource_history.json"))
        
        if os.path.exists(history_file) and self.config.get("save_history", True):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                
                # Load usage history
                usage_data = data.get("usage_history", [])
                for usage_dict in usage_data:
                    usage = ResourceUsage(
                        cpu_percent=usage_dict.get("cpu_percent", 0),
                        memory_percent=usage_dict.get("memory_percent", 0),
                        disk_percent=usage_dict.get("disk_percent", 0),
                        network_bytes=usage_dict.get("network_bytes", 0)
                    )
                    usage.timestamp = usage_dict.get("timestamp", time.time())
                    usage.process_details = usage_dict.get("process_details", {})
                    self.usage_history.append(usage)
                
                # Load strategy history
                strategy_data = data.get("strategy_history", [])
                for strategy_dict in strategy_data:
                    strategy = ResourceAllocationStrategy(
                        strategy_type=strategy_dict.get("strategy_type", "maintain"),
                        max_tasks=strategy_dict.get("max_tasks", 5),
                        resource_reason=strategy_dict.get("resource_reason", ""),
                        task_type_limits=strategy_dict.get("task_type_limits", {})
                    )
                    strategy.timestamp = strategy_dict.get("timestamp", time.time())
                    self.strategy_history.append(strategy)
                
                # Limit history size
                self._trim_history()
                
                logger.info(f"Loaded {len(self.usage_history)} usage records and {len(self.strategy_history)} strategies from history")
                
            except Exception as e:
                logger.error(f"Error loading history: {e}")
    
    def _save_history(self):
        """Save resource usage and strategy history to file"""
        if not self.config.get("save_history", True):
            return
        
        history_file = os.path.join(BASE_DIR, self.config.get("history_file", "resource_history.json"))
        
        try:
            # Convert history to serializable format
            usage_history = [usage.to_dict() for usage in self.usage_history]
            strategy_history = [strategy.to_dict() for strategy in self.strategy_history]
            
            data = {
                "usage_history": usage_history,
                "strategy_history": strategy_history,
                "updated_at": time.time()
            }
            
            # Save to file
            with open(history_file, 'w') as f:
                json.dump(data, f)
            
            logger.debug(f"Saved resource history")
            
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def _trim_history(self):
        """Trim history to maximum size"""
        max_history = self.config.get("max_history", 100)
        
        if len(self.usage_history) > max_history:
            self.usage_history = self.usage_history[-max_history:]
        
        if len(self.strategy_history) > max_history:
            self.strategy_history = self.strategy_history[-max_history:]
    
    def start(self, strategy_callback=None):
        """
        Start the resource monitor.
        
        Args:
            strategy_callback: Callback function to call with new allocation strategies
        """
        if self.running:
            logger.warning("Resource Monitor is already running")
            return False
        
        # Store strategy callback
        self.strategy_callback = strategy_callback
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start allocation thread
        self.allocation_thread = threading.Thread(target=self._allocation_loop)
        self.allocation_thread.daemon = True
        self.allocation_thread.start()
        
        logger.info("Resource Monitor started")
        return True
    
    def stop(self):
        """Stop the resource monitor"""
        if not self.running:
            logger.warning("Resource Monitor is not running")
            return False
        
        # Signal threads to stop
        self.running = False
        
        # Wait for threads to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        if self.allocation_thread and self.allocation_thread.is_alive():
            self.allocation_thread.join(timeout=5.0)
        
        # Save history
        self._save_history()
        
        logger.info("Resource Monitor stopped")
        return True
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Monitoring loop started")
        
        interval = self.config.get("monitoring_interval", 5)
        
        while self.running:
            try:
                # Get current resource usage
                self.current_usage = self._get_resource_usage()
                
                # Add to history
                self.usage_history.append(self.current_usage)
                
                # Trim history if needed
                self._trim_history()
                
                # Log resource usage
                logger.debug(f"Resource usage: CPU {self.current_usage.cpu_percent:.1f}%, "
                           f"Memory {self.current_usage.memory_percent:.1f}%, "
                           f"Disk {self.current_usage.disk_percent:.1f}%")
                
                # Save history periodically (every 10 iterations)
                if len(self.usage_history) % 10 == 0:
                    self._save_history()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep for the monitoring interval
            time.sleep(interval)
    
    def _allocation_loop(self):
        """Main allocation loop"""
        logger.info("Allocation loop started")
        
        interval = self.config.get("allocation_interval", 15)
        
        while self.running:
            try:
                # Create a new allocation strategy
                strategy = self._create_allocation_strategy()
                
                # Update current strategy
                self.current_strategy = strategy
                
                # Add to history
                self.strategy_history.append(strategy)
                
                # Call the strategy callback if provided
                if self.strategy_callback:
                    try:
                        self.strategy_callback(strategy)
                    except Exception as e:
                        logger.error(f"Error in strategy callback: {e}")
                
                # Log the strategy
                logger.info(f"Resource allocation strategy: {strategy.strategy_type}, "
                          f"Max tasks: {strategy.max_tasks}, "
                          f"Reason: {strategy.resource_reason}")
                
            except Exception as e:
                logger.error(f"Error in allocation loop: {e}")
            
            # Sleep for the allocation interval
            time.sleep(interval)
    
    def _get_resource_usage(self) -> ResourceUsage:
        """
        Get current system resource usage.
        
        Returns:
            ResourceUsage object with current resource usage
        """
        cpu_percent = 0
        memory_percent = 0
        disk_percent = 0
        network_bytes = 0
        process_details = {}
        
        if PSUTIL_AVAILABLE:
            try:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Get network usage (simplified)
                network = psutil.net_io_counters()
                network_bytes = network.bytes_sent + network.bytes_recv
                
                # Get process details (top 5 CPU-consuming processes)
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    processes.append(proc.info)
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
                
                # Add top 5 processes to details
                for i, proc in enumerate(processes[:5]):
                    process_details[f"proc_{i+1}"] = {
                        "pid": proc.get('pid', 0),
                        "name": proc.get('name', 'unknown'),
                        "cpu_percent": proc.get('cpu_percent', 0),
                        "memory_percent": proc.get('memory_percent', 0)
                    }
                
            except Exception as e:
                logger.error(f"Error getting resource usage with psutil: {e}")
        else:
            # Fallback if psutil is not available
            cpu_percent = 50  # Assume 50% usage
            memory_percent = 50
            disk_percent = 50
        
        # Create and return resource usage
        usage = ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            network_bytes=network_bytes
        )
        usage.process_details = process_details
        
        return usage
    
    def _create_allocation_strategy(self) -> ResourceAllocationStrategy:
        """
        Create a resource allocation strategy based on current and historical usage.
        
        Returns:
            ResourceAllocationStrategy object with recommendations
        """
        # Get current resource usage
        cpu = self.current_usage.cpu_percent
        memory = self.current_usage.memory_percent
        disk = self.current_usage.disk_percent
        
        # Get resource thresholds
        thresholds = self.config.get("resource_thresholds", {})
        
        cpu_thresholds = thresholds.get("cpu_percent", {"low": 20, "medium": 50, "high": 80, "critical": 90})
        memory_thresholds = thresholds.get("memory_percent", {"low": 20, "medium": 60, "high": 80, "critical": 90})
        disk_thresholds = thresholds.get("disk_percent", {"low": 50, "medium": 70, "high": 85, "critical": 95})
        
        # Check for critical resource usage
        if (cpu >= cpu_thresholds.get("critical", 90) or 
            memory >= memory_thresholds.get("critical", 90) or 
            disk >= disk_thresholds.get("critical", 95)):
            
            # Critical resource usage - emergency strategy
            reason = f"Critical resource usage: CPU {cpu:.1f}%, Memory {memory:.1f}%, Disk {disk:.1f}%"
            return ResourceAllocationStrategy(
                strategy_type=ResourceAllocationStrategy.EMERGENCY_STOP,
                max_tasks=0,
                resource_reason=reason
            )
        
        # Check for high resource usage
        if (cpu >= cpu_thresholds.get("high", 80) or 
            memory >= memory_thresholds.get("high", 80) or 
            disk >= disk_thresholds.get("high", 85)):
            
            # High resource usage - scale down
            reason = f"High resource usage: CPU {cpu:.1f}%, Memory {memory:.1f}%, Disk {disk:.1f}%"
            
            # Calculate max tasks based on resource usage
            max_tasks = self._calculate_max_tasks_for_high_usage(cpu, memory, disk)
            
            # Calculate task type limits
            task_type_limits = self._calculate_task_type_limits(max_tasks)
            
            return ResourceAllocationStrategy(
                strategy_type=ResourceAllocationStrategy.SCALE_DOWN,
                max_tasks=max_tasks,
                resource_reason=reason,
                task_type_limits=task_type_limits
            )
        
        # Check for medium resource usage
        if (cpu >= cpu_thresholds.get("medium", 50) or 
            memory >= memory_thresholds.get("medium", 60) or 
            disk >= disk_thresholds.get("medium", 70)):
            
            # Medium resource usage - maintain current
            reason = f"Medium resource usage: CPU {cpu:.1f}%, Memory {memory:.1f}%, Disk {disk:.1f}%"
            
            # Calculate max tasks based on resource usage
            max_tasks = self._calculate_max_tasks_for_medium_usage(cpu, memory, disk)
            
            # Calculate task type limits
            task_type_limits = self._calculate_task_type_limits(max_tasks)
            
            return ResourceAllocationStrategy(
                strategy_type=ResourceAllocationStrategy.MAINTAIN,
                max_tasks=max_tasks,
                resource_reason=reason,
                task_type_limits=task_type_limits
            )
        
        # Low resource usage - scale up
        reason = f"Low resource usage: CPU {cpu:.1f}%, Memory {memory:.1f}%, Disk {disk:.1f}%"
        
        # Calculate max tasks based on resource usage
        max_tasks = self._calculate_max_tasks_for_low_usage(cpu, memory, disk)
        
        # Calculate task type limits
        task_type_limits = self._calculate_task_type_limits(max_tasks)
        
        return ResourceAllocationStrategy(
            strategy_type=ResourceAllocationStrategy.SCALE_UP,
            max_tasks=max_tasks,
            resource_reason=reason,
            task_type_limits=task_type_limits
        )
    
    def _calculate_max_tasks_for_high_usage(self, cpu: float, memory: float, disk: float) -> int:
        """
        Calculate maximum tasks for high resource usage.
        
        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            disk: Disk usage percentage
            
        Returns:
            Maximum number of tasks to run
        """
        # Base calculation - start with a low number
        max_tasks = 2
        
        # Adjust based on resource usage
        thresholds = self.config.get("resource_thresholds", {})
        cpu_high = thresholds.get("cpu_percent", {}).get("high", 80)
        memory_high = thresholds.get("memory_percent", {}).get("high", 80)
        
        # If resource usage is just above high threshold, allow more tasks
        if cpu < cpu_high + 5 and memory < memory_high + 5:
            max_tasks = 3
        
        # If using adaptive allocation, adjust based on running tasks
        if self.config.get("adaptive_allocation", True) and self.current_strategy:
            current_max = self.current_strategy.max_tasks
            
            # Don't reduce too drastically
            if current_max > 0:
                max_tasks = max(max_tasks, current_max - 1)
        
        return max_tasks
    
    def _calculate_max_tasks_for_medium_usage(self, cpu: float, memory: float, disk: float) -> int:
        """
        Calculate maximum tasks for medium resource usage.
        
        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            disk: Disk usage percentage
            
        Returns:
            Maximum number of tasks to run
        """
        # Base calculation - moderate number
        max_tasks = 5
        
        # Adjust based on resource usage
        thresholds = self.config.get("resource_thresholds", {})
        cpu_medium = thresholds.get("cpu_percent", {}).get("medium", 50)
        memory_medium = thresholds.get("memory_percent", {}).get("medium", 60)
        
        # If closer to high threshold, reduce tasks
        cpu_high = thresholds.get("cpu_percent", {}).get("high", 80)
        memory_high = thresholds.get("memory_percent", {}).get("high", 80)
        
        cpu_ratio = (cpu - cpu_medium) / (cpu_high - cpu_medium) if cpu_high > cpu_medium else 0
        memory_ratio = (memory - memory_medium) / (memory_high - memory_medium) if memory_high > memory_medium else 0
        
        # Use the most constrained resource
        constraint_ratio = max(cpu_ratio, memory_ratio)
        
        if constraint_ratio > 0.7:
            max_tasks = 4
        elif constraint_ratio > 0.3:
            max_tasks = 5
        else:
            max_tasks = 6
        
        # If using adaptive allocation, adjust based on running tasks
        if self.config.get("adaptive_allocation", True) and self.current_strategy:
            current_max = self.current_strategy.max_tasks
            
            # Don't change too drastically
            if current_max > 0:
                max_tasks = max(min(max_tasks, current_max + 1), current_max - 1)
        
        return max_tasks
    
    def _calculate_max_tasks_for_low_usage(self, cpu: float, memory: float, disk: float) -> int:
        """
        Calculate maximum tasks for low resource usage.
        
        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            disk: Disk usage percentage
            
        Returns:
            Maximum number of tasks to run
        """
        # Base calculation - higher number
        max_tasks = 8
        
        # Adjust based on resource usage
        thresholds = self.config.get("resource_thresholds", {})
        cpu_low = thresholds.get("cpu_percent", {}).get("low", 20)
        memory_low = thresholds.get("memory_percent", {}).get("low", 20)
        
        # If very low resource usage, allow more tasks
        if cpu < cpu_low / 2 and memory < memory_low / 2:
            max_tasks = 10
        
        # If using adaptive allocation, adjust based on running tasks
        if self.config.get("adaptive_allocation", True) and self.current_strategy:
            current_max = self.current_strategy.max_tasks
            
            # Don't increase too drastically
            if current_max > 0:
                max_tasks = min(max_tasks, current_max + 2)
        
        return max_tasks
    
    def _calculate_task_type_limits(self, max_tasks: int) -> Dict[str, int]:
        """
        Calculate limits for different task types based on their resource requirements.
        
        Args:
            max_tasks: Maximum total tasks
            
        Returns:
            Dictionary with limits for each task type
        """
        # Get task type weights
        task_weights = self.config.get("task_type_weights", {})
        
        # Default task types if not configured
        default_types = {
            "blender_task": {"cpu": 4.0, "memory": 3.0, "disk": 2.0},
            "simulation": {"cpu": 3.0, "memory": 2.0, "disk": 1.0},
            "analysis": {"cpu": 2.0, "memory": 1.5, "disk": 0.5},
            "utility": {"cpu": 1.0, "memory": 1.0, "disk": 0.5}
        }
        
        # Ensure all task types are in weights
        for task_type, default_weight in default_types.items():
            if task_type not in task_weights:
                task_weights[task_type] = default_weight
        
        # Calculate limits based on weights and max tasks
        limits = {}
        
        # Special handling for blender tasks due to high resource usage
        if "blender_task" in task_weights:
            blender_limit = max(1, round(max_tasks / 4))
            limits["blender_task"] = blender_limit
        
        # Calculate for other task types
        for task_type, weights in task_weights.items():
            if task_type == "blender_task":
                continue  # Already handled
            
            # Calculate relative weight
            cpu_weight = weights.get("cpu", 1.0)
            memory_weight = weights.get("memory", 1.0)
            
            # Average weight relative to a utility task
            relative_weight = (cpu_weight + memory_weight) / 2
            
            # Calculate limit based on weight and max tasks
            if relative_weight > 0:
                task_limit = max(1, round(max_tasks / relative_weight))
                
                # Don't exceed max tasks
                task_limit = min(task_limit, max_tasks)
                
                limits[task_type] = task_limit
        
        return limits
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.
        
        Returns:
            Dictionary with current resource usage
        """
        return self.current_usage.to_dict()
    
    def get_current_strategy(self) -> Dict[str, Any]:
        """
        Get current allocation strategy.
        
        Returns:
            Dictionary with current allocation strategy
        """
        if self.current_strategy:
            return self.current_strategy.to_dict()
        else:
            return {
                "strategy_type": "none",
                "max_tasks": 5,
                "resource_reason": "No strategy calculated yet",
                "task_type_limits": {}
            }
    
    def get_usage_history(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Get resource usage history.
        
        Args:
            limit: Maximum number of records to return (0 for all)
            
        Returns:
            List of resource usage dictionaries
        """
        if limit <= 0 or limit > len(self.usage_history):
            return [usage.to_dict() for usage in self.usage_history]
        else:
            return [usage.to_dict() for usage in self.usage_history[-limit:]]
    
    def get_strategy_history(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Get allocation strategy history.
        
        Args:
            limit: Maximum number of records to return (0 for all)
            
        Returns:
            List of allocation strategy dictionaries
        """
        if limit <= 0 or limit > len(self.strategy_history):
            return [strategy.to_dict() for strategy in self.strategy_history]
        else:
            return [strategy.to_dict() for strategy in self.strategy_history[-limit:]]
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get a summary of resource usage and allocation.
        
        Returns:
            Dictionary with resource summary
        """
        # Calculate usage statistics
        cpu_avg = 0
        memory_avg = 0
        disk_avg = 0
        
        if self.usage_history:
            # Calculate averages from last 10 records or all if fewer
            history_len = min(len(self.usage_history), 10)
            recent_history = self.usage_history[-history_len:]
            
            cpu_avg = sum(usage.cpu_percent for usage in recent_history) / history_len
            memory_avg = sum(usage.memory_percent for usage in recent_history) / history_len
            disk_avg = sum(usage.disk_percent for usage in recent_history) / history_len
        
        # Get current values
        current_cpu = self.current_usage.cpu_percent
        current_memory = self.current_usage.memory_percent
        current_disk = self.current_usage.disk_percent
        
        # Get current strategy
        strategy = "none"
        max_tasks = 5
        
        if self.current_strategy:
            strategy = self.current_strategy.strategy_type
            max_tasks = self.current_strategy.max_tasks
        
        # Create summary
        return {
            "current": {
                "cpu_percent": current_cpu,
                "memory_percent": current_memory,
                "disk_percent": current_disk
            },
            "average": {
                "cpu_percent": cpu_avg,
                "memory_percent": memory_avg,
                "disk_percent": disk_avg
            },
            "allocation": {
                "strategy": strategy,
                "max_tasks": max_tasks
            },
            "timestamp": time.time()
        }

# Example usage
if __name__ == "__main__":
    print("Claude Resource Monitor - Example Usage")
    print("=======================================")
    
    # Create resource monitor
    monitor = ClaudeResourceMonitor()
    
    # Define a callback function
    def strategy_callback(strategy):
        print(f"\nNew allocation strategy:")
        print(f"  Type: {strategy.strategy_type}")
        print(f"  Max tasks: {strategy.max_tasks}")
        print(f"  Reason: {strategy.resource_reason}")
        print(f"  Task type limits: {strategy.task_type_limits}")
    
    # Start the monitor with callback
    monitor.start(strategy_callback=strategy_callback)
    
    try:
        # Run for 60 seconds, printing resource usage every 10 seconds
        for i in range(6):
            time.sleep(10)
            
            # Get current resource usage
            usage = monitor.get_current_usage()
            
            print(f"\nResource usage update {i+1}/6:")
            print(f"  CPU: {usage['cpu_percent']:.1f}%")
            print(f"  Memory: {usage['memory_percent']:.1f}%")
            print(f"  Disk: {usage['disk_percent']:.1f}%")
            
            # Get resource summary
            summary = monitor.get_resource_summary()
            print(f"Resource summary:")
            print(f"  CPU average: {summary['average']['cpu_percent']:.1f}%")
            print(f"  Current strategy: {summary['allocation']['strategy']}")
            print(f"  Recommended max tasks: {summary['allocation']['max_tasks']}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Stop the monitor
        monitor.stop()