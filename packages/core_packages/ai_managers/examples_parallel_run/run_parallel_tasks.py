#!/usr/bin/env python
"""
Parallel Tasks Runner for Claude Parallel Execution System

This script demonstrates how to run multiple tasks in parallel using the
Claude Parallel Manager. It registers and launches tasks for different
AI agents and monitors their execution.

Usage:
  python run_parallel_tasks.py [--count=N] [--agent=N]

Options:
  --count=N    Number of tasks to run per agent (default: 1)
  --agent=N    Run tasks only for this agent number (1-5)
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parallel_tasks_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ParallelTasksRunner")

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Claude Parallel Manager
sys.path.append(BASE_DIR)
try:
    from claude_parallel_manager import ClaudeParallelManager
except ImportError:
    logger.error("Failed to import ClaudeParallelManager. Make sure it exists in the project root.")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run parallel tasks using Claude Parallel Manager")
    parser.add_argument("--count", type=int, default=1, help="Number of tasks to run per agent")
    parser.add_argument("--agent", type=int, help="Run tasks only for this agent number (1-5)")
    return parser.parse_args()

def get_task_scripts(agent_filter=None):
    """
    Get the list of task scripts to run.
    
    Args:
        agent_filter: Optional agent number to filter tasks (1-5)
        
    Returns:
        List of (agent_number, script_path) tuples
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tasks = []
    
    # Find all parallel agent task scripts
    for filename in os.listdir(current_dir):
        if filename.startswith("parallel_agent") and filename.endswith(".py"):
            try:
                # Extract agent number
                agent_num = int(filename.split("_agent")[1].split("_")[0])
                
                # Apply filter if specified
                if agent_filter is not None and agent_num != agent_filter:
                    continue
                
                script_path = os.path.join(current_dir, filename)
                tasks.append((agent_num, script_path))
            except (ValueError, IndexError):
                logger.warning(f"Couldn't parse agent number from filename: {filename}")
    
    # Sort by agent number
    return sorted(tasks, key=lambda x: x[0])

def run_parallel_tasks(task_count=1, agent_filter=None):
    """
    Run parallel tasks using the Claude Parallel Manager.
    
    Args:
        task_count: Number of tasks to run per agent
        agent_filter: Optional agent number to filter tasks (1-5)
    """
    logger.info(f"Starting parallel tasks runner with task_count={task_count}")
    
    # Initialize Claude Parallel Manager
    manager = ClaudeParallelManager()
    
    # Start the manager
    logger.info("Starting Claude Parallel Manager")
    manager.start()
    
    try:
        # Get task scripts
        tasks = get_task_scripts(agent_filter)
        logger.info(f"Found {len(tasks)} task scripts")
        
        if not tasks:
            logger.error("No task scripts found. Make sure parallel_agent*_task.py files exist.")
            manager.stop()
            return
        
        # Schedule tasks
        task_ids = []
        for i in range(task_count):
            for agent_num, script_path in tasks:
                # Determine priority and task type based on agent number
                if agent_num == 1:
                    priority = 2
                    task_type = "simulation"
                elif agent_num == 2:
                    priority = 3
                    task_type = "simulation"
                elif agent_num == 3:
                    priority = 4
                    task_type = "simulation"
                elif agent_num == 4:
                    priority = 3
                    task_type = "simulation"
                elif agent_num == 5:
                    priority = 2
                    task_type = "simulation"
                else:
                    priority = 5
                    task_type = "utility"
                
                # Add task to the manager
                task_id = manager.add_script_task(
                    script_path=script_path,
                    priority=priority,
                    task_type=task_type
                )
                
                task_ids.append((task_id, agent_num))
                logger.info(f"Added task {task_id} for Agent {agent_num} with priority {priority}")
        
        # Monitor task execution
        logger.info(f"Scheduled {len(task_ids)} tasks. Monitoring execution...")
        
        # Wait for tasks to complete or timeout
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        completed_tasks = set()
        
        while time.time() - start_time < timeout_seconds and len(completed_tasks) < len(task_ids):
            # Get status
            status = manager.get_status()
            
            # Check each task
            for task_id, agent_num in task_ids:
                if task_id in completed_tasks:
                    continue
                
                task_status = manager.get_task_status(task_id)
                if task_status.get("status") in ["completed", "failed", "stopped"]:
                    completed_tasks.add(task_id)
                    result = "✅ Completed" if task_status.get("status") == "completed" else f"❌ {task_status.get('status')}"
                    logger.info(f"Task {task_id} for Agent {agent_num}: {result}")
            
            # Print current status
            print(f"\rActive: {status.get('active_tasks', 0)}, "
                  f"Completed: {len(completed_tasks)}/{len(task_ids)}, "
                  f"CPU: {status.get('resources', {}).get('cpu_percent', 'N/A')}%, "
                  f"Memory: {status.get('resources', {}).get('memory_percent', 'N/A')}%", 
                  end="")
            
            # Sleep briefly
            time.sleep(2)
        
        print()  # New line after status updates
        
        # Final report
        elapsed_time = time.time() - start_time
        logger.info(f"Task execution completed in {elapsed_time:.1f} seconds")
        logger.info(f"Completed tasks: {len(completed_tasks)}/{len(task_ids)}")
        
        # Check for incomplete tasks
        if len(completed_tasks) < len(task_ids):
            logger.warning(f"{len(task_ids) - len(completed_tasks)} tasks did not complete within the timeout")
        
    finally:
        # Stop the manager
        logger.info("Stopping Claude Parallel Manager")
        manager.stop()

if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Run parallel tasks
    run_parallel_tasks(task_count=args.count, agent_filter=args.agent)
    
    print("\nParallel tasks execution completed")