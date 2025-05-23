"""
workflow_pause.py - Mechanism for pausing and resuming AI workflow execution

This module provides functions for AI agents to check if they should pause their
execution, and handle pausing and resuming gracefully.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WorkflowPause")

# Global constants
PAUSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_pause.json")
PAUSE_CHECK_INTERVAL = 2  # seconds

# Global pause state cache to avoid excessive file operations
_pause_state = {"paused": False, "timestamp": 0}
_pause_lock = threading.Lock()
_last_check_time = 0

def _load_pause_state():
    """Load the pause state from the JSON file
    
    Returns:
        dict: The pause state (paused: bool, timestamp: float)
    """
    global _pause_state, _last_check_time
    
    # Check if we need to reload (after PAUSE_CHECK_INTERVAL)
    current_time = time.time()
    if current_time - _last_check_time < PAUSE_CHECK_INTERVAL:
        return _pause_state
    
    with _pause_lock:
        try:
            if os.path.exists(PAUSE_FILE):
                with open(PAUSE_FILE, 'r') as f:
                    state = json.load(f)
                
                # Update cache
                _pause_state = state
                _last_check_time = current_time
                return state
            else:
                # Default to not paused if file doesn't exist
                return {"paused": False, "timestamp": 0}
        except Exception as e:
            logger.error(f"Error loading pause state: {e}")
            return {"paused": False, "timestamp": 0}

def is_paused():
    """Check if the workflow is currently paused
    
    Returns:
        bool: True if paused, False otherwise
    """
    state = _load_pause_state()
    return state.get("paused", False)

def should_pause():
    """Alias for is_paused() for more intuitive usage
    
    Returns:
        bool: True if the workflow should pause, False otherwise
    """
    return is_paused()

def handle_pause(agent_id=None, max_pause_seconds=None):
    """Handle pausing the execution if pause is requested
    
    This function will block until the pause is lifted or the maximum
    pause time is reached.
    
    Args:
        agent_id (str): Optional ID of the agent for logging
        max_pause_seconds (int): Maximum time to stay paused before resuming anyway
        
    Returns:
        bool: True if execution was paused at some point, False otherwise
    """
    if not is_paused():
        return False
    
    agent_str = f"Agent {agent_id}" if agent_id else "Agent"
    logger.info(f"{agent_str} entering pause state")
    
    start_pause_time = time.time()
    was_paused = False
    
    # Enter pause loop
    while is_paused():
        was_paused = True
        
        # Check if max pause time has been exceeded
        if max_pause_seconds and time.time() - start_pause_time > max_pause_seconds:
            logger.warning(f"{agent_str} resuming after maximum pause time ({max_pause_seconds}s)")
            break
        
        # Wait a bit before checking again to avoid tight loop
        time.sleep(PAUSE_CHECK_INTERVAL)
    
    if was_paused:
        pause_duration = time.time() - start_pause_time
        logger.info(f"{agent_str} resuming after being paused for {pause_duration:.1f} seconds")
    
    return was_paused

def check_and_handle_pause(agent_id=None, max_pause_seconds=None):
    """Check if pause is requested and handle it if it is
    
    Convenience function that combines is_paused() and handle_pause()
    
    Args:
        agent_id (str): Optional ID of the agent for logging
        max_pause_seconds (int): Maximum time to stay paused before resuming anyway
        
    Returns:
        bool: True if execution was paused at some point, False otherwise
    """
    if is_paused():
        return handle_pause(agent_id, max_pause_seconds)
    return False

def set_pause_state(paused):
    """Set the pause state
    
    This function is primarily used internally by the workflow management system.
    
    Args:
        paused (bool): Whether to pause (True) or resume (False)
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _pause_state, _last_check_time
    
    with _pause_lock:
        try:
            state = {"paused": paused, "timestamp": time.time()}
            
            # Save to file
            with open(PAUSE_FILE, 'w') as f:
                json.dump(state, f)
            
            # Update cache
            _pause_state = state
            _last_check_time = time.time()
            
            logger.info(f"Set pause state to: {'paused' if paused else 'resumed'}")
            return True
        except Exception as e:
            logger.error(f"Error setting pause state: {e}")
            return False

# Example decorator for making functions pause-aware
def pause_aware(func):
    """Decorator to make a function pause-aware
    
    This decorator will check for pause before executing the function, 
    and will handle the pause if requested.
    
    Example usage:
    
    @pause_aware
    def my_function(arg1, arg2):
        # Function body
    """
    def wrapper(*args, **kwargs):
        check_and_handle_pause()
        return func(*args, **kwargs)
    return wrapper