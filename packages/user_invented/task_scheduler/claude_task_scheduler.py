#!/usr/bin/env python
"""
Claude Task Scheduler for GlowingGoldenGlobe

This module provides scheduling capabilities for automated parallel execution in the
Claude Parallel Execution System. It allows tasks to be scheduled for regular execution
based on time intervals, specific times of day, or specific days of the week.

The scheduler runs as a background thread that monitors scheduled tasks and adds them
to the Claude Parallel Manager's queue when their scheduled time arrives.
"""

import os
import sys
import time
import json
import threading
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("claude_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ClaudeTaskScheduler")

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to import required modules
try:
    from claude_parallel_manager import ClaudeParallelManager
except ImportError:
    logger.error("Failed to import ClaudeParallelManager")
    ClaudeParallelManager = None

class ScheduledTask:
    """
    Represents a task scheduled for regular execution.
    """
    
    # Schedule types
    INTERVAL = "interval"  # Run every X minutes/hours
    DAILY = "daily"        # Run at specific time every day
    WEEKLY = "weekly"      # Run at specific time on specific day of week
    MONTHLY = "monthly"    # Run at specific time on specific day of month
    ONCE = "once"          # Run once at a specific time
    
    def __init__(self, task_id: str, task_data: Dict[str, Any], schedule_type: str, 
                 schedule_params: Dict[str, Any]):
        """
        Initialize a scheduled task.
        
        Args:
            task_id: Unique identifier for the task
            task_data: Task data for execution
            schedule_type: Type of schedule (interval, daily, weekly, monthly, once)
            schedule_params: Parameters for the schedule type
        """
        self.task_id = task_id
        self.task_data = task_data
        self.schedule_type = schedule_type
        self.schedule_params = schedule_params
        self.last_run = None
        self.next_run = self._calculate_next_run()
        self.enabled = True
    
    def _calculate_next_run(self) -> Optional[datetime.datetime]:
        """
        Calculate the next time this task should run.
        
        Returns:
            Next run time as datetime, or None if the task should not run again
        """
        now = datetime.datetime.now()
        
        if self.schedule_type == self.INTERVAL:
            # Run every X minutes/hours
            interval_minutes = self.schedule_params.get("minutes", 0)
            interval_hours = self.schedule_params.get("hours", 0)
            
            # Convert to total minutes
            total_minutes = interval_minutes + (interval_hours * 60)
            
            # Default to 60 minutes if not specified
            if total_minutes <= 0:
                total_minutes = 60
            
            if self.last_run:
                # Calculate next run based on last run
                return self.last_run + datetime.timedelta(minutes=total_minutes)
            else:
                # First run, start from now
                return now + datetime.timedelta(minutes=total_minutes)
            
        elif self.schedule_type == self.DAILY:
            # Run at specific time every day
            time_str = self.schedule_params.get("time", "00:00")
            try:
                hour, minute = map(int, time_str.split(":"))
            except (ValueError, TypeError):
                logger.error(f"Invalid time format for daily schedule: {time_str}")
                return now + datetime.timedelta(hours=24)  # Default to 24 hours from now
            
            # Create target time for today
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If target time is in the past, schedule for tomorrow
            if target <= now:
                target += datetime.timedelta(days=1)
            
            return target
            
        elif self.schedule_type == self.WEEKLY:
            # Run at specific time on specific day of week
            day_of_week = self.schedule_params.get("day", "monday").lower()
            time_str = self.schedule_params.get("time", "00:00")
            
            # Map day names to numbers (0=Monday, 6=Sunday)
            days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                   "friday": 4, "saturday": 5, "sunday": 6}
            
            target_day = days.get(day_of_week, 0)  # Default to Monday
            
            try:
                hour, minute = map(int, time_str.split(":"))
            except (ValueError, TypeError):
                logger.error(f"Invalid time format for weekly schedule: {time_str}")
                hour, minute = 0, 0  # Default to midnight
            
            # Calculate days until the target day
            current_day = now.weekday()
            days_ahead = target_day - current_day
            if days_ahead < 0:  # Target day already passed this week
                days_ahead += 7
            
            # If it's the target day and the time has passed, schedule for next week
            if days_ahead == 0 and now.hour > hour or (now.hour == hour and now.minute >= minute):
                days_ahead = 7
            
            # Create target datetime
            target = now + datetime.timedelta(days=days_ahead)
            target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return target
            
        elif self.schedule_type == self.MONTHLY:
            # Run at specific time on specific day of month
            day_of_month = self.schedule_params.get("day", 1)
            time_str = self.schedule_params.get("time", "00:00")
            
            try:
                day_of_month = int(day_of_month)
                if day_of_month < 1:
                    day_of_month = 1
                elif day_of_month > 28:
                    # To avoid issues with short months, limit to 28
                    day_of_month = 28
            except (ValueError, TypeError):
                logger.error(f"Invalid day of month: {self.schedule_params.get('day')}")
                day_of_month = 1  # Default to 1st of month
            
            try:
                hour, minute = map(int, time_str.split(":"))
            except (ValueError, TypeError):
                logger.error(f"Invalid time format for monthly schedule: {time_str}")
                hour, minute = 0, 0  # Default to midnight
            
            # Calculate next month's target date
            if now.day < day_of_month or (now.day == day_of_month and 
                                         (now.hour < hour or (now.hour == hour and now.minute < minute))):
                # Target day is later this month
                target = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Target day is next month
                if now.month == 12:
                    target = now.replace(year=now.year+1, month=1, day=day_of_month, 
                                        hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Try to create date for next month, handling month length issues
                    try:
                        target = now.replace(month=now.month+1, day=day_of_month, 
                                           hour=hour, minute=minute, second=0, microsecond=0)
                    except ValueError:
                        # Day doesn't exist in next month, use last day of next month
                        if now.month == 12:
                            next_month = 1
                            next_year = now.year + 1
                        else:
                            next_month = now.month + 1
                            next_year = now.year
                        
                        # Calculate last day of next month
                        if next_month in [4, 6, 9, 11]:
                            last_day = 30
                        elif next_month == 2:
                            # Check for leap year
                            if (next_year % 4 == 0 and next_year % 100 != 0) or next_year % 400 == 0:
                                last_day = 29
                            else:
                                last_day = 28
                        else:
                            last_day = 31
                        
                        target = datetime.datetime(next_year, next_month, last_day, hour, minute)
            
            return target
            
        elif self.schedule_type == self.ONCE:
            # Run once at a specific date and time
            date_str = self.schedule_params.get("date")
            time_str = self.schedule_params.get("time", "00:00")
            
            if not date_str:
                logger.error("No date specified for once schedule")
                return None
            
            try:
                # Parse date string (expected format: YYYY-MM-DD)
                year, month, day = map(int, date_str.split("-"))
                
                # Parse time string
                hour, minute = map(int, time_str.split(":"))
                
                # Create target datetime
                target = datetime.datetime(year, month, day, hour, minute)
                
                # If target is in the past, don't schedule
                if target <= now:
                    return None
                
                return target
                
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid date/time for once schedule: {e}")
                return None
        
        else:
            logger.error(f"Unknown schedule type: {self.schedule_type}")
            return None
    
    def is_due(self) -> bool:
        """
        Check if the task is due to run.
        
        Returns:
            True if the task should run now, False otherwise
        """
        if not self.enabled or not self.next_run:
            return False
        
        now = datetime.datetime.now()
        return now >= self.next_run
    
    def mark_executed(self):
        """Mark the task as executed and calculate the next run time"""
        self.last_run = datetime.datetime.now()
        
        # If this is a one-time task, disable it after execution
        if self.schedule_type == self.ONCE:
            self.enabled = False
            self.next_run = None
        else:
            self.next_run = self._calculate_next_run()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the scheduled task to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "task_id": self.task_id,
            "task_data": self.task_data,
            "schedule_type": self.schedule_type,
            "schedule_params": self.schedule_params,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """
        Create a ScheduledTask instance from a dictionary.
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            ScheduledTask instance
        """
        task = cls(
            task_id=data.get("task_id", "unknown"),
            task_data=data.get("task_data", {}),
            schedule_type=data.get("schedule_type", cls.INTERVAL),
            schedule_params=data.get("schedule_params", {})
        )
        
        # Restore state
        task.enabled = data.get("enabled", True)
        
        # Restore timestamps
        last_run_str = data.get("last_run")
        if last_run_str:
            try:
                task.last_run = datetime.datetime.fromisoformat(last_run_str)
            except (ValueError, TypeError):
                task.last_run = None
        
        # Calculate next run based on last run
        task.next_run = task._calculate_next_run()
        
        return task

class ClaudeTaskScheduler:
    """
    Task scheduler for Claude Parallel Execution System.
    """
    
    def __init__(self, config_path: str = "claude_scheduler_config.json"):
        """
        Initialize the Task Scheduler.
        
        Args:
            config_path: Path to scheduler configuration file
        """
        self.config_path = os.path.join(BASE_DIR, config_path)
        self.tasks = {}  # task_id -> ScheduledTask
        self.running = False
        self.scheduler_thread = None
        self.thread_lock = threading.Lock()
        self.claude_manager = None
        
        # Load tasks
        self._load_tasks()
        
        logger.info(f"Task Scheduler initialized with {len(self.tasks)} tasks")
    
    def _load_tasks(self):
        """Load scheduled tasks from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load task list
                task_list = data.get("tasks", [])
                
                # Create ScheduledTask instances
                for task_data in task_list:
                    try:
                        task = ScheduledTask.from_dict(task_data)
                        self.tasks[task.task_id] = task
                    except Exception as e:
                        logger.error(f"Error loading task: {e}")
                
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
                
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
    
    def _save_tasks(self):
        """Save scheduled tasks to file"""
        try:
            # Convert tasks to list of dictionaries
            task_list = [task.to_dict() for task in self.tasks.values()]
            
            # Create data structure
            data = {
                "tasks": task_list,
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(task_list)} scheduled tasks")
            
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def start(self, claude_manager: Optional[ClaudeParallelManager] = None):
        """
        Start the scheduler.
        
        Args:
            claude_manager: Claude Parallel Manager instance to use for task execution
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return False
        
        # Store Claude Parallel Manager reference
        self.claude_manager = claude_manager
        
        # Start the scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Task Scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return False
        
        # Signal thread to stop
        self.running = False
        
        # Wait for thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        # Save tasks
        self._save_tasks()
        
        logger.info("Task Scheduler stopped")
        return True
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        check_interval = 30  # Check every 30 seconds
        
        while self.running:
            try:
                # Get current time
                now = datetime.datetime.now()
                logger.debug(f"Scheduler check at {now.isoformat()}")
                
                # Check for tasks to execute
                due_tasks = []
                
                with self.thread_lock:
                    for task_id, task in list(self.tasks.items()):
                        if task.is_due():
                            due_tasks.append(task)
                
                # Execute due tasks
                for task in due_tasks:
                    logger.info(f"Task due for execution: {task.task_id}")
                    self._execute_task(task)
                
                # Save tasks periodically
                if due_tasks:
                    self._save_tasks()
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Sleep until next check
            for _ in range(check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _execute_task(self, task: ScheduledTask):
        """
        Execute a scheduled task.
        
        Args:
            task: The task to execute
        """
        logger.info(f"Executing scheduled task: {task.task_id}")
        
        try:
            # Check if Claude Manager is available
            if not self.claude_manager:
                logger.error("Cannot execute task: Claude Parallel Manager not available")
                return
            
            # Extract task data
            script_path = task.task_data.get("script_path")
            task_type = task.task_data.get("task_type", "utility")
            priority = task.task_data.get("priority", 5)
            
            # Add task to Claude Parallel Manager
            if script_path and os.path.exists(script_path):
                # Execute a script
                result_task_id = self.claude_manager.add_script_task(
                    script_path=script_path,
                    task_type=task_type,
                    priority=priority
                )
                logger.info(f"Scheduled task {task.task_id} added to queue with execution ID: {result_task_id}")
            else:
                logger.error(f"Cannot execute task {task.task_id}: Script not found or not specified")
            
            # Mark task as executed
            task.mark_executed()
            
        except Exception as e:
            logger.error(f"Error executing scheduled task {task.task_id}: {e}")
    
    def add_task(self, task_data: Dict[str, Any], schedule_type: str, 
                 schedule_params: Dict[str, Any]) -> str:
        """
        Add a new scheduled task.
        
        Args:
            task_data: Task data for execution
            schedule_type: Type of schedule (interval, daily, weekly, monthly, once)
            schedule_params: Parameters for the schedule type
            
        Returns:
            Task ID of the added task
        """
        # Generate a unique task ID
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        
        # Create the scheduled task
        task = ScheduledTask(
            task_id=task_id,
            task_data=task_data,
            schedule_type=schedule_type,
            schedule_params=schedule_params
        )
        
        # Add to tasks dictionary
        with self.thread_lock:
            self.tasks[task_id] = task
        
        # Save tasks
        self._save_tasks()
        
        logger.info(f"Added scheduled task: {task_id}")
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_id: ID of the task to remove
            
        Returns:
            True if the task was removed, False otherwise
        """
        with self.thread_lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                
                # Save tasks
                self._save_tasks()
                
                logger.info(f"Removed scheduled task: {task_id}")
                return True
            else:
                logger.warning(f"Task not found: {task_id}")
                return False
    
    def enable_task(self, task_id: str, enabled: bool = True) -> bool:
        """
        Enable or disable a scheduled task.
        
        Args:
            task_id: ID of the task to update
            enabled: Whether to enable or disable the task
            
        Returns:
            True if the task was updated, False otherwise
        """
        with self.thread_lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = enabled
                
                # Save tasks
                self._save_tasks()
                
                logger.info(f"{'Enabled' if enabled else 'Disabled'} scheduled task: {task_id}")
                return True
            else:
                logger.warning(f"Task not found: {task_id}")
                return False
    
    def update_task(self, task_id: str, task_data: Optional[Dict[str, Any]] = None,
                   schedule_type: Optional[str] = None, 
                   schedule_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a scheduled task.
        
        Args:
            task_id: ID of the task to update
            task_data: New task data (None to keep existing)
            schedule_type: New schedule type (None to keep existing)
            schedule_params: New schedule parameters (None to keep existing)
            
        Returns:
            True if the task was updated, False otherwise
        """
        with self.thread_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                
                # Update task data if provided
                if task_data is not None:
                    task.task_data = task_data
                
                # Update schedule if provided
                if schedule_type is not None:
                    task.schedule_type = schedule_type
                
                if schedule_params is not None:
                    task.schedule_params = schedule_params
                
                # Recalculate next run time
                task.next_run = task._calculate_next_run()
                
                # Save tasks
                self._save_tasks()
                
                logger.info(f"Updated scheduled task: {task_id}")
                return True
            else:
                logger.warning(f"Task not found: {task_id}")
                return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a scheduled task.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            Task details as a dictionary, or None if not found
        """
        with self.thread_lock:
            if task_id in self.tasks:
                return self.tasks[task_id].to_dict()
            else:
                return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled tasks.
        
        Returns:
            List of all scheduled tasks as dictionaries
        """
        with self.thread_lock:
            return [task.to_dict() for task in self.tasks.values()]
    
    def get_due_tasks(self) -> List[Dict[str, Any]]:
        """
        Get tasks that are due to run.
        
        Returns:
            List of due tasks as dictionaries
        """
        now = datetime.datetime.now()
        
        with self.thread_lock:
            return [task.to_dict() for task in self.tasks.values() 
                   if task.enabled and task.next_run and task.next_run <= now]
    
    def get_next_due_task(self) -> Optional[Dict[str, Any]]:
        """
        Get the next task that will be due.
        
        Returns:
            Next due task as a dictionary, or None if no tasks are scheduled
        """
        next_task = None
        next_run = None
        
        with self.thread_lock:
            for task in self.tasks.values():
                if not task.enabled or not task.next_run:
                    continue
                
                if next_run is None or task.next_run < next_run:
                    next_task = task
                    next_run = task.next_run
        
        return next_task.to_dict() if next_task else None
    
    def add_future_metrics_visualization_task(self) -> str:
        """
        Add a special task for metrics visualization scheduled 2 months in the future.
        
        Returns:
            Task ID of the added task
        """
        # Calculate date 2 months from now
        now = datetime.datetime.now()
        if now.month >= 11:
            future_month = (now.month + 2) % 12
            future_year = now.year + 1
        else:
            future_month = now.month + 2
            future_year = now.year
        
        future_date = now.replace(year=future_year, month=future_month, day=1)
        
        # Format date string
        date_str = future_date.strftime("%Y-%m-%d")
        
        # Create task data
        task_data = {
            "name": "Metrics Visualization Implementation",
            "description": "Implement visualization for parallel execution metrics",
            "script_path": os.path.join(BASE_DIR, "ai_managers", "examples_parallel_run", "future_metrics_visualization.py"),
            "task_type": "analysis",
            "priority": 3
        }
        
        # Schedule parameters
        schedule_params = {
            "date": date_str,
            "time": "10:00"
        }
        
        # Add the task
        task_id = self.add_task(
            task_data=task_data,
            schedule_type=ScheduledTask.ONCE,
            schedule_params=schedule_params
        )
        
        logger.info(f"Added future metrics visualization task: {task_id} scheduled for {date_str} 10:00")
        return task_id

# Example usage
if __name__ == "__main__":
    print("Claude Task Scheduler - Example Usage")
    print("=====================================")
    
    # Create scheduler
    scheduler = ClaudeTaskScheduler()
    
    # Add example tasks
    example_tasks = [
        {
            "name": "Hourly Task",
            "script_path": os.path.join(BASE_DIR, "ai_managers", "examples_parallel_run", "parallel_agent1_task.py"),
            "task_type": "utility",
            "priority": 5
        },
        {
            "name": "Daily Task",
            "script_path": os.path.join(BASE_DIR, "ai_managers", "examples_parallel_run", "parallel_agent2_task.py"),
            "task_type": "simulation",
            "priority": 3
        },
        {
            "name": "Weekly Task",
            "script_path": os.path.join(BASE_DIR, "ai_managers", "examples_parallel_run", "parallel_agent3_task.py"),
            "task_type": "analysis",
            "priority": 4
        }
    ]
    
    # Add tasks with different schedules
    task_ids = []
    
    # Hourly task
    task_ids.append(scheduler.add_task(
        task_data=example_tasks[0],
        schedule_type=ScheduledTask.INTERVAL,
        schedule_params={"hours": 1, "minutes": 0}
    ))
    
    # Daily task
    task_ids.append(scheduler.add_task(
        task_data=example_tasks[1],
        schedule_type=ScheduledTask.DAILY,
        schedule_params={"time": "12:00"}
    ))
    
    # Weekly task
    task_ids.append(scheduler.add_task(
        task_data=example_tasks[2],
        schedule_type=ScheduledTask.WEEKLY,
        schedule_params={"day": "monday", "time": "09:00"}
    ))
    
    # Future metrics visualization task
    metrics_task_id = scheduler.add_future_metrics_visualization_task()
    task_ids.append(metrics_task_id)
    
    # Print all tasks
    print(f"\nScheduled Tasks:")
    for task_id in task_ids:
        task = scheduler.get_task(task_id)
        next_run = task.get("next_run", "Not scheduled")
        
        if next_run and next_run != "Not scheduled":
            try:
                next_run_time = datetime.datetime.fromisoformat(next_run)
                next_run = next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
        
        print(f"  - {task.get('task_id')}: {task.get('task_data', {}).get('name', 'Unnamed')}")
        print(f"    Schedule: {task.get('schedule_type')} - Next run: {next_run}")
    
    # Don't start the scheduler when running as example
    print("\nExample completed. In a real application, you would:")
    print("1. Create a ClaudeParallelManager instance")
    print("2. Call scheduler.start(claude_manager) to start the scheduler")
    print("3. The scheduler would run tasks according to their schedules")