"""
ai_workflow_status.py - Central tracking system for AI Workflow status and active agents

This module maintains the status of all running AI workflows and provides functions to 
start, pause, and stop workflows. It tracks active agents and their states.
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

# Import the enhanced conflict handling system
try:
    from ai_managers.auto_conflict_handler import (
        initialize_conflict_handling, 
        get_task_guidelines, 
        should_read_guidelines,
        auto_provide_guidelines
    )
    ENHANCED_CONFLICT_HANDLING = True
except ImportError:
    ENHANCED_CONFLICT_HANDLING = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AIWorkflowStatus")

# Global constants
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_workflow_status.json")
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Workflow states
STATE_STOPPED = "stopped"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"

# Default status structure
DEFAULT_STATUS = {
    "workflow_state": STATE_STOPPED,
    "last_updated": "",
    "active_agents": {},
    "paused_agents": {},
    "terminated_agents": {},
    "statistics": {
        "start_time": "",
        "total_run_time": 0,
        "pause_count": 0,
        "completion_percentage": 0
    }
}

# Cached status to avoid excessive file operations
_cached_status = None
_last_load_time = 0
_status_lock = threading.Lock()

def _ensure_status_file():
    """Ensure the status file exists with default values if needed"""
    if not os.path.exists(STATUS_FILE):
        _save_status(DEFAULT_STATUS)
        return DEFAULT_STATUS
    return _load_status()

def _save_status(status):
    """Save the workflow status to the JSON file"""
    global _cached_status
    
    with _status_lock:
        # Update the last_updated timestamp
        status["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
        
        # Update cache
        _cached_status = status.copy()
        _last_load_time = time.time()
        
        logger.debug("Saved workflow status")

def _load_status():
    """Load the workflow status from the JSON file"""
    global _cached_status, _last_load_time
    
    with _status_lock:
        # Check if we have a recent cached status (within 2 seconds)
        if _cached_status and time.time() - _last_load_time < 2:
            return _cached_status.copy()
        
        # Load status from file
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    status = json.load(f)
                
                # Update cache
                _cached_status = status.copy()
                _last_load_time = time.time()
                return status
            else:
                return DEFAULT_STATUS.copy()
        except Exception as e:
            logger.error(f"Error loading workflow status: {e}")
            return DEFAULT_STATUS.copy()

def get_workflow_status():
    """Get the current workflow status
    
    Returns:
        dict: The current workflow status
    """
    return _ensure_status_file()

def get_workflow_state():
    """Get just the current workflow state (running, paused, stopped)
    
    Returns:
        str: The current workflow state
    """
    status = _ensure_status_file()
    return status.get("workflow_state", STATE_STOPPED)

def set_workflow_state(state):
    """Set the workflow state
    
    Args:
        state (str): The new workflow state (running, paused, stopped)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if state not in [STATE_RUNNING, STATE_PAUSED, STATE_STOPPED]:
        logger.error(f"Invalid workflow state: {state}")
        return False
    
    status = _ensure_status_file()
    previous_state = status.get("workflow_state", STATE_STOPPED)
    
    # Update state
    status["workflow_state"] = state
    
    # Update statistics based on state transition
    if previous_state != state:
        if state == STATE_RUNNING and previous_state == STATE_PAUSED:
            # Resuming from pause - don't update start time
            pass
        elif state == STATE_RUNNING:
            # Starting new workflow
            status["statistics"]["start_time"] = datetime.now().isoformat()
            status["statistics"]["total_run_time"] = 0
            status["statistics"]["pause_count"] = 0
            status["statistics"]["completion_percentage"] = 0
            # Clear agent lists if this is a fresh start
            if previous_state == STATE_STOPPED:
                status["active_agents"] = {}
                status["paused_agents"] = {}
                status["terminated_agents"] = {}
        elif state == STATE_PAUSED:
            # Pausing workflow
            status["statistics"]["pause_count"] += 1
            # Move active agents to paused list
            for agent_id, agent_info in status["active_agents"].items():
                status["paused_agents"][agent_id] = agent_info
            status["active_agents"] = {}
    
    # Save changes
    _save_status(status)
    
    # Notify all agents about the state change
    _notify_agents_of_state_change(state)
    
    logger.info(f"Workflow state changed from {previous_state} to {state}")
    return True

def _notify_agents_of_state_change(state):
    """Notify all AI agents about the state change by updating control files
    
    Args:
        state (str): The new workflow state
    """
    try:
        # Update the master terminate_status.json file
        terminate_file = os.path.join(AGENT_DIR, "terminate_status.json")
        if os.path.exists(terminate_file):
            terminate_data = {"terminate": state == STATE_STOPPED}
            with open(terminate_file, 'w') as f:
                json.dump(terminate_data, f)
        
        # Also update the boolean value in terminate_bool.py if it exists
        bool_file = os.path.join(AGENT_DIR, "terminate_bool.py")
        if os.path.exists(bool_file):
            with open(bool_file, 'w') as f:
                f.write(f"TERMINATE = {str(state == STATE_STOPPED)}  # Updated by workflow manager\n")
        
        # Create or update workflow_pause.json
        pause_file = os.path.join(AGENT_DIR, "workflow_pause.json")
        pause_data = {"paused": state == STATE_PAUSED, "timestamp": time.time()}
        with open(pause_file, 'w') as f:
            json.dump(pause_data, f)
        
        logger.info(f"Updated agent control files for state: {state}")
    except Exception as e:
        logger.error(f"Error notifying agents of state change: {e}")

def register_agent(agent_id, agent_info):
    """Register a new AI agent with the workflow
    
    Args:
        agent_id (str): Unique identifier for the agent
        agent_info (dict): Information about the agent
        
    Returns:
        bool: True if successful, False otherwise
    """
    status = _ensure_status_file()
    
    # Initialize enhanced conflict handling if available
    if ENHANCED_CONFLICT_HANDLING:
        try:
            initialize_conflict_handling()
            logger.info("Enhanced conflict handling initialized for agent registration")
        except Exception as e:
            logger.error(f"Error initializing enhanced conflict handling: {e}")
    
    # Check if agent should receive guidelines for its task
    task_description = agent_info.get("task_description", "")
    if ENHANCED_CONFLICT_HANDLING and task_description:
        if should_read_guidelines(task_description):
            guidelines = get_task_guidelines(task_description)
            agent_info["guidelines"] = guidelines
            agent_info["guidelines_provided"] = datetime.now().isoformat()
            logger.info(f"Provided guidelines to agent {agent_id} for task: {task_description[:50]}...")
    
    # Add agent to the appropriate list based on current workflow state
    if status["workflow_state"] == STATE_RUNNING:
        status["active_agents"][agent_id] = agent_info
    elif status["workflow_state"] == STATE_PAUSED:
        status["paused_agents"][agent_id] = agent_info
    else:  # STATE_STOPPED
        logger.warning(f"Attempting to register agent {agent_id} while workflow is stopped")
        return False
    
    # Save changes
    _save_status(status)
    logger.info(f"Registered agent: {agent_id}")
    return True

def unregister_agent(agent_id, reason="completed"):
    """Unregister an AI agent from the workflow
    
    Args:
        agent_id (str): Unique identifier for the agent
        reason (str): Reason for unregistering (completed, error, etc.)
        
    Returns:
        bool: True if successful, False otherwise
    """
    status = _ensure_status_file()
    
    # Check all agent lists
    agent_found = False
    agent_info = None
    
    if agent_id in status["active_agents"]:
        agent_info = status["active_agents"].pop(agent_id)
        agent_found = True
    elif agent_id in status["paused_agents"]:
        agent_info = status["paused_agents"].pop(agent_id)
        agent_found = True
    
    if agent_found and agent_info:
        # Add to terminated list with reason
        agent_info["termination_reason"] = reason
        agent_info["termination_time"] = datetime.now().isoformat()
        status["terminated_agents"][agent_id] = agent_info
        
        # Save changes
        _save_status(status)
        logger.info(f"Unregistered agent {agent_id}: {reason}")
        return True
    else:
        logger.warning(f"Agent not found for unregistering: {agent_id}")
        return False

def get_active_agents():
    """Get all currently active agents
    
    Returns:
        dict: Dictionary of active agents
    """
    status = _ensure_status_file()
    return status.get("active_agents", {}).copy()

def get_paused_agents():
    """Get all currently paused agents
    
    Returns:
        dict: Dictionary of paused agents
    """
    status = _ensure_status_file()
    return status.get("paused_agents", {}).copy()

def get_terminated_agents():
    """Get all terminated agents
    
    Returns:
        dict: Dictionary of terminated agents
    """
    status = _ensure_status_file()
    return status.get("terminated_agents", {}).copy()

def get_agent_count():
    """Get the count of agents in each state
    
    Returns:
        dict: Dictionary with counts for active, paused, and terminated agents
    """
    status = _ensure_status_file()
    return {
        "active": len(status.get("active_agents", {})),
        "paused": len(status.get("paused_agents", {})),
        "terminated": len(status.get("terminated_agents", {})),
        "total": len(status.get("active_agents", {})) + 
                 len(status.get("paused_agents", {})) + 
                 len(status.get("terminated_agents", {}))
    }

def update_agent_status(agent_id, status_update):
    """Update the status information for a specific agent
    
    Args:
        agent_id (str): Unique identifier for the agent
        status_update (dict): New status information to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    status = _ensure_status_file()
    
    # Find which list the agent is in
    if agent_id in status["active_agents"]:
        agent_list = status["active_agents"]
    elif agent_id in status["paused_agents"]:
        agent_list = status["paused_agents"]
    elif agent_id in status["terminated_agents"]:
        agent_list = status["terminated_agents"]
    else:
        logger.warning(f"Agent not found for status update: {agent_id}")
        return False
    
    # Update agent information
    agent_list[agent_id].update(status_update)
    
    # Save changes
    _save_status(status)
    logger.debug(f"Updated status for agent: {agent_id}")
    return True

def detect_active_agents():
    """Detect AI agents that are currently running in the system
    
    This function scans for AI agent processes using the presence of
    specific files and their timestamps.
    
    Returns:
        list: List of active agent IDs detected
    """
    # List of agent folders to check
    agent_folders = []
    for i in range(1, 6):  # Assuming Div_AI_Agent_Focus_1 through Div_AI_Agent_Focus_5
        folder = os.path.join(AGENT_DIR, f"AI_Agent_{i}")
        if os.path.exists(folder) and os.path.isdir(folder):
            agent_folders.append((f"AI_Agent_{i}", folder))
    
    active_agents = []
    
    # Check activity markers in each folder
    for agent_id, folder_path in agent_folders:
        # Check for running process indicators
        activity_markers = [
            os.path.join(folder_path, "agent_running.flag"),
            os.path.join(folder_path, "last_activity.log"),
            os.path.join(folder_path, "agent_outputs"),
        ]
        
        for marker in activity_markers:
            if os.path.exists(marker):
                # Check if the file or directory was modified in the last hour
                if os.path.isdir(marker):
                    # Check directory content's timestamps
                    contents = os.listdir(marker) if os.path.exists(marker) else []
                    if contents:
                        newest_file = max(
                            [os.path.join(marker, item) for item in contents],
                            key=os.path.getmtime
                        )
                        mod_time = os.path.getmtime(newest_file)
                    else:
                        mod_time = 0
                else:
                    # Check file timestamp
                    mod_time = os.path.getmtime(marker)
                
                # If modified in the last hour, consider active
                if time.time() - mod_time < 3600:  # 1 hour in seconds
                    active_agents.append(agent_id)
                    break
    
    logger.info(f"Detected {len(active_agents)} active agents: {active_agents}")
    return active_agents

def resume_paused_agents():
    """Attempt to resume all paused agents
    
    Returns:
        int: Number of agents successfully resumed
    """
    status = _ensure_status_file()
    
    if status["workflow_state"] != STATE_RUNNING:
        logger.warning("Cannot resume agents: workflow is not in running state")
        return 0
    
    paused = status.get("paused_agents", {})
    if not paused:
        logger.info("No paused agents to resume")
        return 0
    
    # Move all paused agents to active
    for agent_id, agent_info in paused.items():
        status["active_agents"][agent_id] = agent_info
    
    # Clear paused list
    resumed_count = len(paused)
    status["paused_agents"] = {}
    
    # Save changes
    _save_status(status)
    
    logger.info(f"Resumed {resumed_count} paused agents")
    return resumed_count

def start_ai_workflow(workflow_params=None):
    """Start the AI workflow with specified parameters
    
    Args:
        workflow_params (dict): Parameters for the workflow
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Current workflow state
    current_state = get_workflow_state()
    
    if current_state == STATE_RUNNING:
        logger.warning("AI Workflow is already running")
        return False
    
    # Update workflow state to running
    success = set_workflow_state(STATE_RUNNING)
    
    if success and workflow_params:
        # Store workflow parameters in the status
        status = _ensure_status_file()
        status["workflow_params"] = workflow_params
        _save_status(status)
    
    logger.info("AI Workflow started")
    return success

def pause_ai_workflow():
    """Pause the AI workflow
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Current workflow state
    current_state = get_workflow_state()
    
    if current_state != STATE_RUNNING:
        logger.warning(f"Cannot pause: AI Workflow is not running (current state: {current_state})")
        return False
    
    # Update workflow state to paused
    success = set_workflow_state(STATE_PAUSED)
    
    logger.info("AI Workflow paused")
    return success

def resume_ai_workflow():
    """Resume the AI workflow
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Current workflow state
    current_state = get_workflow_state()
    
    if current_state != STATE_PAUSED:
        logger.warning(f"Cannot resume: AI Workflow is not paused (current state: {current_state})")
        return False
    
    # Update workflow state to running
    success = set_workflow_state(STATE_RUNNING)
    
    if success:
        # Attempt to resume all paused agents
        resume_paused_agents()
    
    logger.info("AI Workflow resumed")
    return success

def stop_ai_workflow():
    """Stop the AI workflow
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Current workflow state
    current_state = get_workflow_state()
    
    if current_state == STATE_STOPPED:
        logger.warning("AI Workflow is already stopped")
        return False
    
    # Update workflow state to stopped
    success = set_workflow_state(STATE_STOPPED)
    
    logger.info("AI Workflow stopped")
    return success

def get_workflow_stats():
    """Get workflow statistics
    
    Returns:
        dict: Statistics about the workflow
    """
    status = _ensure_status_file()
    stats = status.get("statistics", {}).copy()
    
    # Calculate additional statistics
    if stats.get("start_time"):
        try:
            start_time = datetime.fromisoformat(stats["start_time"])
            elapsed = (datetime.now() - start_time).total_seconds()
            stats["elapsed_seconds"] = elapsed
            stats["elapsed_formatted"] = str(timedelta(seconds=int(elapsed)))
        except Exception as e:
            logger.error(f"Error calculating elapsed time: {e}")
    
    # Add agent counts
    counts = get_agent_count()
    stats.update(counts)
    
    return stats

def provide_guidelines_to_agent(agent_id: str, task_description: str) -> bool:
    """
    Provide guidelines to a specific agent for a task
    
    Args:
        agent_id (str): Unique identifier for the agent
        task_description (str): Description of the task the agent is working on
        
    Returns:
        bool: True if guidelines were provided, False otherwise
    """
    if not ENHANCED_CONFLICT_HANDLING:
        logger.warning("Enhanced conflict handling not available - cannot provide guidelines")
        return False
    
    status = _ensure_status_file()
    
    # Find the agent in active or paused agents
    agent_info = None
    agent_list = None
    
    if agent_id in status.get("active_agents", {}):
        agent_info = status["active_agents"][agent_id]
        agent_list = status["active_agents"]
    elif agent_id in status.get("paused_agents", {}):
        agent_info = status["paused_agents"][agent_id]
        agent_list = status["paused_agents"]
    
    if not agent_info:
        logger.warning(f"Agent {agent_id} not found in active or paused agents")
        return False
    
    # Check if guidelines should be provided
    if should_read_guidelines(task_description):
        guidelines = get_task_guidelines(task_description)
        agent_info["guidelines"] = guidelines
        agent_info["guidelines_provided"] = datetime.now().isoformat()
        agent_info["task_description"] = task_description
        
        # Update the agent info in the status
        agent_list[agent_id] = agent_info
        _save_status(status)
        
        logger.info(f"Provided guidelines to agent {agent_id} for task: {task_description[:50]}...")
        return True
    else:
        logger.info(f"No guidelines needed for agent {agent_id} task: {task_description[:50]}...")
        return False

def check_all_agents_for_guidelines():
    """
    Check all active agents to see if they need guidelines for their current tasks
    
    Returns:
        int: Number of agents that received guidelines
    """
    if not ENHANCED_CONFLICT_HANDLING:
        return 0
    
    status = _ensure_status_file()
    guidelines_provided = 0
    
    # Check active agents
    for agent_id, agent_info in status.get("active_agents", {}).items():
        task_description = agent_info.get("task_description", "")
        if task_description and not agent_info.get("guidelines"):
            if provide_guidelines_to_agent(agent_id, task_description):
                guidelines_provided += 1
    
    # Check paused agents
    for agent_id, agent_info in status.get("paused_agents", {}).items():
        task_description = agent_info.get("task_description", "")
        if task_description and not agent_info.get("guidelines"):
            if provide_guidelines_to_agent(agent_id, task_description):
                guidelines_provided += 1
    
    if guidelines_provided > 0:
        logger.info(f"Provided guidelines to {guidelines_provided} agents")
    
    return guidelines_provided

def get_agent_guidelines(agent_id: str) -> str:
    """
    Get the guidelines for a specific agent
    
    Args:
        agent_id (str): Unique identifier for the agent
        
    Returns:
        str: Guidelines for the agent, or empty string if none
    """
    status = _ensure_status_file()
    
    # Find the agent
    agent_info = None
    if agent_id in status.get("active_agents", {}):
        agent_info = status["active_agents"][agent_id]
    elif agent_id in status.get("paused_agents", {}):
        agent_info = status["paused_agents"][agent_id]
    
    if agent_info and "guidelines" in agent_info:
        return agent_info["guidelines"]
    
    return ""

# Ensure status file exists when the module is imported
_ensure_status_file()

# Initialize enhanced conflict handling if available
if ENHANCED_CONFLICT_HANDLING:
    try:
        initialize_conflict_handling()
        logger.info("Enhanced conflict handling initialized on module import")
    except Exception as e:
        logger.error(f"Error initializing enhanced conflict handling on import: {e}")