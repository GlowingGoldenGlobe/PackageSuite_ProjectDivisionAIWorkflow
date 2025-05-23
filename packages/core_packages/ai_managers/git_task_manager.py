#!/usr/bin/env python3
"""
Git Task Manager - Integrates Git Operations with AI Task Management System

This module handles Git-related tasks and interfaces with the project's
AI task management system. It ensures Git operations are fully automated
and any issues that require attention are properly tracked.

Usage:
    from ai_managers.git_task_manager import register_git_task, check_credentials
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("git_task_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
TASK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_tasks.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "git_credentials.json")

def load_tasks():
    """Load existing tasks from file"""
    if os.path.exists(TASK_FILE):
        try:
            with open(TASK_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks: {str(e)}")
    
    # Return empty tasks structure if file doesn't exist or error
    return {
        "tasks": [],
        "last_updated": datetime.now().isoformat()
    }

def save_tasks(tasks_data):
    """Save tasks to file"""
    try:
        # Update last updated timestamp
        tasks_data["last_updated"] = datetime.now().isoformat()
        
        with open(TASK_FILE, 'w') as f:
            json.dump(tasks_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving tasks: {str(e)}")
        return False

def register_git_task(task_type, description, details=None, priority="medium", auto_solve=True):
    """
    Register a Git-related task in the AI task management system
    
    Args:
        task_type: Type of task (e.g., "git_conflict", "credential_needed")
        description: Brief description of the task
        details: Additional details about the task (dict)
        priority: Priority level ("low", "medium", "high", "critical")
        auto_solve: Whether the AI system should attempt to solve this automatically
    
    Returns:
        task_id: ID of the registered task
    """
    tasks_data = load_tasks()
    
    # Generate task ID
    task_id = f"git_{len(tasks_data['tasks']) + 1}_{int(datetime.now().timestamp())}"
    
    # Create task structure
    task = {
        "id": task_id,
        "type": task_type,
        "description": description,
        "details": details or {},
        "priority": priority,
        "auto_solve": auto_solve,
        "status": "pending",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat(),
        "attempts": 0,
        "last_attempt": None,
        "resolution": None
    }
    
    # Add task to list
    tasks_data["tasks"].append(task)
    
    # Save updated tasks
    save_tasks(tasks_data)
    
    logger.info(f"Registered new Git task: {task_id} - {description}")
    
    # Try to update GUI notification system if it exists
    try:
        update_gui_notification(task)
    except Exception as e:
        logger.warning(f"Could not update GUI notification: {str(e)}")
    
    return task_id

def update_gui_notification(task):
    """Update GUI notification system with new task"""
    # Import dynamically to prevent circular imports
    try:
        # Try different potential module paths for the notification system
        notification_modules = [
            "gui_notification_system",
            "notification_system",
            "ggg_notification_system",
            "agent_mode_notification"
        ]
        
        notification_module = None
        for module_name in notification_modules:
            try:
                notification_module = __import__(module_name)
                break
            except ImportError:
                continue
        
        if notification_module:
            # Add notification to the GUI system
            if hasattr(notification_module, 'add_notification'):
                notification_module.add_notification(
                    title=f"Git {task['type']}",
                    message=task['description'],
                    notification_type="task",
                    priority=task['priority'],
                    data=task
                )
                logger.info("Added notification to GUI system")
            else:
                logger.warning("Notification module found but no add_notification function")
        else:
            # Fallback to writing to a notifications file that the GUI can check
            with open("git_notifications.json", "a") as f:
                f.write(json.dumps(task) + "\n")
            logger.info("Added notification to git_notifications.json file")
    
    except Exception as e:
        logger.error(f"Error updating GUI notification: {str(e)}")

def check_credentials():
    """
    Check if Git credentials are available and prompt for them if needed
    
    Returns:
        dict: Credentials information or None if not available
    """
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
    
    # Check if credentials are stored in Git config
    username, _ = run_command("git config --get user.name")
    email, _ = run_command("git config --get user.email")
    
    if username and email:
        # Save to credentials file for future use
        credentials = {
            "username": username,
            "email": email,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(CREDENTIALS_FILE, 'w') as f:
                json.dump(credentials, f, indent=2)
            return credentials
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
    
    # Register a task to get credentials
    register_git_task(
        task_type="credential_needed",
        description="Git credentials required for repository operations",
        priority="high",
        auto_solve=False  # This requires user input
    )
    
    return None

def run_command(command, cwd=None):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {result.stderr}")
            return None, result.stderr
        return result.stdout.strip(), None
    except Exception as e:
        logger.error(f"Error running command '{command}': {str(e)}")
        return None, str(e)

def is_authentication_error(error_message):
    """Check if an error is related to authentication"""
    auth_patterns = [
        r"authentication failed",
        r"could not read username",
        r"could not read password",
        r"permission denied",
        r"403 forbidden",
        r"authentication required",
        r"could not authenticate"
    ]
    
    if error_message:
        for pattern in auth_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                return True
    
    return False

def process_git_error(error_message, command=None):
    """
    Process a Git error and register appropriate tasks
    
    Args:
        error_message: Error message from Git
        command: The command that caused the error (optional)
    
    Returns:
        task_id: ID of registered task if applicable
    """
    if is_authentication_error(error_message):
        # Handle authentication errors
        return register_git_task(
            task_type="authentication_error",
            description="Git authentication failed. Credentials may be incorrect or missing.",
            details={"error": error_message, "command": command},
            priority="high",
            auto_solve=False  # Requires user input
        )
    
    # Handle merge conflicts
    if "CONFLICT" in error_message:
        conflict_files = []
        if command:
            # Try to extract conflicted files
            output, _ = run_command("git diff --name-only --diff-filter=U")
            if output:
                conflict_files = [f for f in output.split('\n') if f.strip()]
        
        return register_git_task(
            task_type="merge_conflict",
            description=f"Git merge conflict in {len(conflict_files)} files" if conflict_files else "Git merge conflict",
            details={"error": error_message, "command": command, "conflict_files": conflict_files},
            priority="high",
            auto_solve=True  # AI can attempt to solve this
        )
    
    # General error
    return register_git_task(
        task_type="git_error",
        description="Git operation failed",
        details={"error": error_message, "command": command},
        priority="medium",
        auto_solve=True  # AI can attempt to diagnose
    )

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Git Task Manager')
    parser.add_argument('--check-creds', action='store_true', help='Check Git credentials')
    parser.add_argument('--test-task', action='store_true', help='Create a test Git task')
    
    args = parser.parse_args()
    
    if args.check_creds:
        credentials = check_credentials()
        if credentials:
            print(f"Found credentials for {credentials['username']} ({credentials['email']})")
        else:
            print("No credentials found")
    elif args.test_task:
        task_id = register_git_task(
            task_type="test",
            description="Test Git task for demonstration",
            priority="low"
        )
        print(f"Created test task with ID: {task_id}")
    else:
        parser.print_help()
