#!/usr/bin/env python
"""
Auto Conflict Handler - Startup Integration

This script automatically initializes the session detection and conflict handling system
when any AI agent or workflow starts. It should be imported by all major entry points.
"""

import sys
import os
import atexit
import logging
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Add the parent directory to the path so we can import ai_managers modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoConflictHandler")

# Global instances
_session_detector = None
_file_tracker = None
_guidelines_system = None
_override_emailer = None
_automation_schema = None

def _load_automation_schema() -> Optional[Dict]:
    """Load the restricted automation schema"""
    global _automation_schema
    
    if _automation_schema is not None:
        return _automation_schema
    
    try:
        schema_path = os.path.join(os.path.dirname(__file__), "restricted_automation_schema.json")
        with open(schema_path, 'r') as f:
            _automation_schema = json.load(f)
        return _automation_schema
    except Exception as e:
        logger.error(f"Failed to load automation schema: {e}")
        return None

def initialize_conflict_handling(force_reinit: bool = False) -> bool:
    """
    Initialize the automatic conflict handling system
    
    Args:
        force_reinit: Force reinitialization even if already initialized
        
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global _session_detector, _file_tracker, _guidelines_system, _override_emailer
    
    if not force_reinit and _session_detector is not None and _file_tracker is not None and _guidelines_system is not None and _override_emailer is not None:
        logger.debug("Conflict handling already initialized")
        return True
    
    try:
        # Import and initialize session detector
        from ai_managers.session_detector import get_session_detector
        _session_detector = get_session_detector()
        
        # Import and initialize file usage tracker
        from ai_managers.file_usage_tracker import get_file_usage_tracker
        _file_tracker = get_file_usage_tracker()
        
        # Import and initialize context-aware guidelines system
        from ai_managers.context_aware_guidelines import get_guidelines_system
        _guidelines_system = get_guidelines_system()
        
        # Import and initialize manual override emailer
        from ai_managers.manual_override_emailer import get_override_emailer
        _override_emailer = get_override_emailer()
        
        # Register cleanup function
        atexit.register(cleanup_on_exit)
        
        logger.info("Auto conflict handling, guidelines system, and restricted automation initialized successfully")
        
        # Log current session info
        session_type = _session_detector.get_current_session_type()
        session_id = _session_detector.get_current_session_id()
        logger.info(f"Current session: {session_type} (ID: {session_id})")
        
        # Check for immediate conflicts
        if _session_detector.has_conflicting_sessions():
            logger.warning("Conflicts detected immediately on startup")
            conflicts = _session_detector.get_conflicting_sessions()
            logger.warning(f"Found {len(conflicts)} conflicting sessions")
            
            # Let the file tracker handle the conflicts
            # It will do this automatically when it tries to access files
        
        return True
        
    except ImportError as e:
        logger.error(f"Could not import required modules: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initializing conflict handling: {e}")
        return False

def get_session_info() -> Optional[dict]:
    """Get information about the current session"""
    if _session_detector is None:
        return None
    
    return {
        "session_type": _session_detector.get_current_session_type(),
        "session_id": _session_detector.get_current_session_id(),
        "has_conflicts": _session_detector.has_conflicting_sessions(),
        "active_sessions": len(_session_detector.get_active_sessions())
    }

def check_for_conflicts() -> bool:
    """Manual check for conflicts"""
    if _session_detector is None:
        logger.warning("Session detector not initialized")
        return False
    
    return _session_detector.has_conflicting_sessions()

def get_conflicting_sessions() -> list:
    """Get list of conflicting sessions"""
    if _session_detector is None:
        return []
    
    return _session_detector.get_conflicting_sessions()

def request_file_access(file_path: str, operation: str = "write", role: str = "auto") -> bool:
    """
    Request access to a file with automatic conflict handling
    
    Args:
        file_path: Path to the file
        operation: Type of operation ("read" or "write")
        role: Role requesting access (auto-detected if "auto")
        
    Returns:
        bool: True if access granted, False if denied
    """
    if _file_tracker is None:
        logger.warning("File tracker not initialized")
        return True  # Allow access if tracker is not available
    
    if role == "auto":
        role = _session_detector.get_current_session_type() if _session_detector else "unknown"
    
    return _file_tracker.request_file_lock(file_path, role, operation)

def release_file_access(file_path: str, role: str = "auto") -> bool:
    """
    Release access to a file
    
    Args:
        file_path: Path to the file
        role: Role releasing access (auto-detected if "auto")
        
    Returns:
        bool: True if release successful, False otherwise
    """
    if _file_tracker is None:
        return True  # Nothing to release if tracker is not available
    
    if role == "auto":
        role = _session_detector.get_current_session_type() if _session_detector else "unknown"
    
    return _file_tracker.release_file_lock(file_path, role)

def get_task_guidelines(task_description: str) -> str:
    """
    Get guidelines relevant to the current task
    
    Args:
        task_description: Description of what the agent is working on
        
    Returns:
        str: Formatted guidelines relevant to the task
    """
    if _guidelines_system is None:
        logger.warning("Guidelines system not initialized")
        return "Guidelines system not available"
    
    return _guidelines_system.get_quick_guidelines(task_description)

def should_read_guidelines(task_description: str) -> bool:
    """
    Check if the agent should read guidelines for the current task
    
    Args:
        task_description: Description of what the agent is working on
        
    Returns:
        bool: True if guidelines should be read, False otherwise
    """
    if _guidelines_system is None:
        return False
    
    return _guidelines_system.should_agent_read_guidelines(task_description)

def get_contextual_guidelines(task_description: str, include_session_context: bool = True) -> Dict[str, Any]:
    """
    Get detailed contextual guidelines for the current task
    
    Args:
        task_description: Description of what the agent is working on
        include_session_context: Whether to include session context in guidelines
        
    Returns:
        Dict: Detailed guidelines data including relevant sections
    """
    if _guidelines_system is None:
        return {"error": "Guidelines system not initialized"}
    
    session_context = None
    if include_session_context and _session_detector:
        session_context = {
            "session_type": _session_detector.get_current_session_type(),
            "session_id": _session_detector.get_current_session_id(),
            "has_conflicts": _session_detector.has_conflicting_sessions(),
        }
    
    return _guidelines_system.get_relevant_guidelines(task_description, session_context)

def auto_provide_guidelines(task_description: str) -> Optional[str]:
    """
    Automatically provide guidelines if the task warrants them
    
    Args:
        task_description: Description of what the agent is working on
        
    Returns:
        str: Guidelines if they should be provided, None otherwise
    """
    if should_read_guidelines(task_description):
        return get_task_guidelines(task_description)
    return None

def check_operation_allowed(operation: str, target: str) -> bool:
    """
    Check if an operation is allowed under restricted automation mode
    
    Args:
        operation: Type of operation (read, write, delete, etc.)
        target: Target file or folder path
        
    Returns:
        bool: True if operation is allowed, False if restricted
    """
    if _override_emailer is None:
        logger.warning("Override emailer not initialized - allowing operation")
        return True
    
    restriction_info = _override_emailer.check_operation_restrictions(operation, target)
    return not restriction_info["restricted"] or restriction_info["auto_approved"]

def request_manual_override(operation: str, target: str, reason: str) -> str:
    """
    Request manual override for a restricted operation
    
    Args:
        operation: Type of operation requiring approval
        target: Target file or folder
        reason: Reason for the operation
        
    Returns:
        str: Request ID for tracking, or "auto_approved" if allowed
    """
    if _override_emailer is None:
        logger.warning("Override emailer not initialized - auto-approving operation")
        return "auto_approved"
    
    session_id = _session_detector.get_current_session_id() if _session_detector else None
    return _override_emailer.request_manual_override(operation, target, reason, session_id)

def safe_file_operation(file_path: str, operation: str = "read", task_context: str = "", user_request: bool = False) -> Dict[str, Any]:
    """
    Comprehensive file operation safety check with token optimization
    
    Args:
        file_path: Path to the file
        operation: Operation type (read, write, delete, modify, etc.)
        task_context: Current task description for contingency checking
        user_request: True if user explicitly requested this file
        
    Returns:
        Dict with 'allowed': bool, 'reason': str, 'token_saved': bool
    """
    result = {
        "allowed": True,
        "reason": "Operation allowed",
        "token_saved": False,
        "requires_override": False
    }
    
    # Load schema
    schema = _load_automation_schema()
    if not schema:
        logger.warning("No automation schema available - defaulting to allow")
        return result
    
    # Get the automation mode section
    automation_mode = schema.get("restricted_automation_mode", {})
    file_name = os.path.basename(file_path)
    
    # Check contingent files first (token optimization)
    contingent_files = automation_mode.get("contingent_files", {})
    
    # Check exact filename match
    if file_name in contingent_files:
        file_config = contingent_files[file_name]
        if not _check_contingency(file_config, task_context, user_request):
            result.update({
                "allowed": False,
                "reason": f"Contingency not met: {file_config.get('reason', 'Unknown')}",
                "token_saved": True
            })
            logger.info(f"Token saved: Skipping {file_name} - contingency not met")
            return result
    
    # Check pattern matching for contingent files
    for pattern, file_config in contingent_files.items():
        if _matches_pattern(file_name, pattern):
            if not _check_contingency(file_config, task_context, user_request):
                result.update({
                    "allowed": False,
                    "reason": f"Contingency not met: {file_config.get('reason', 'Unknown')}",
                    "token_saved": True
                })
                logger.info(f"Token saved: Skipping {file_name} - pattern {pattern} contingency not met")
                return result
    
    # Check fully restricted files
    file_restrictions = automation_mode.get("file_restrictions", {})
    
    for pattern, restriction in file_restrictions.items():
        if _matches_pattern(file_name, pattern):
            if restriction.get("automation") == False:
                allowed_ops = restriction.get("allowed_operations", [])
                if operation not in allowed_ops:
                    result.update({
                        "allowed": False,
                        "reason": f"Restricted operation: {restriction.get('reason', 'Unknown')}",
                        "requires_override": restriction.get("override_required", True)
                    })
                    return result
    
    # Check folder restrictions
    folder_restrictions = automation_mode.get("folder_restrictions", {})
    
    for folder_pattern, restriction in folder_restrictions.items():
        if folder_pattern in file_path or file_path.startswith(folder_pattern):
            if restriction.get("automation") == False:
                allowed_ops = restriction.get("allowed_operations", [])
                if operation not in allowed_ops:
                    result.update({
                        "allowed": False,
                        "reason": f"Folder restricted: {restriction.get('reason', 'Unknown')}",
                        "requires_override": restriction.get("override_required", True)
                    })
                    return result
    
    return result

def _check_contingency(file_config: Dict, task_context: str, user_request: bool) -> bool:
    """Check if contingency conditions are met"""
    if user_request:
        return True  # User explicitly requested this file
    
    contingency = file_config.get("contingency", "")
    if not contingency:
        return True  # No contingency specified
    
    # Load schema for keyword matching
    schema = _load_automation_schema()
    if not schema:
        return True
    
    contingency_keywords = schema.get("restricted_automation_mode", {}).get("contingency_keywords", {})
    
    # Parse contingency (supports OR logic)
    contingency_parts = [part.strip() for part in contingency.split(" OR ")]
    
    for part in contingency_parts:
        if part == "user_request" and user_request:
            return True
        
        # Check if task context matches contingency keywords
        if part in contingency_keywords:
            keywords = contingency_keywords[part]
            task_lower = task_context.lower()
            
            if any(keyword.lower() in task_lower for keyword in keywords):
                return True
    
    return False

def _matches_pattern(filename: str, pattern: str) -> bool:
    """Check if filename matches pattern (supports wildcards)"""
    if pattern == filename:
        return True
    
    # Convert simple wildcards to regex
    regex_pattern = pattern.replace("*", ".*").replace("?", ".")
    
    try:
        return bool(re.match(f"^{regex_pattern}$", filename))
    except re.error:
        # Fallback to simple string matching
        return pattern in filename

def safe_file_operation_legacy(operation: str, target: str, reason: str = "") -> bool:
    """
    Legacy function for backward compatibility - perform a file operation with automatic restriction checking
    
    Args:
        operation: Type of operation (read, write, delete, etc.)
        target: Target file or folder path
        reason: Reason for the operation
        
    Returns:
        bool: True if operation completed or approved, False if blocked
    """
    # Use the new safe_file_operation function
    result = safe_file_operation(target, operation, reason, user_request=True)
    
    if result["allowed"]:
        logger.info(f"Operation {operation} on {target} is allowed")
        return True
    
    if result["requires_override"]:
        # Operation is restricted - request override
        logger.warning(f"Operation {operation} on {target} is restricted - requesting override")
        request_id = request_manual_override(operation, target, reason)
        
        if request_id == "auto_approved":
            logger.info(f"Operation {operation} on {target} was auto-approved")
            return True
        
        # Operation blocked - email sent for approval
        logger.info(f"Manual override requested for {operation} on {target} - Request ID: {request_id}")
        logger.info(f"Email notification sent to yerbro@gmail.com")
    
    return False

def cleanup_on_exit():
    """Cleanup function called when the program exits"""
    global _session_detector, _file_tracker, _guidelines_system
    
    logger.info("Cleaning up conflict handling system")
    
    try:
        if _session_detector:
            _session_detector.unregister_current_session()
            _session_detector.stop_monitoring()
        
        if _file_tracker:
            # Release any remaining locks held by this session
            current_session_id = _session_detector.get_current_session_id() if _session_detector else None
            if current_session_id:
                _file_tracker.complete_workflow(current_session_id)
    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def print_session_status():
    """Print current session status (for debugging)"""
    info = get_session_info()
    if info:
        print(f"\n=== Session Status ===")
        print(f"Type: {info['session_type']}")
        print(f"ID: {info['session_id']}")
        print(f"Has conflicts: {info['has_conflicts']}")
        print(f"Active sessions: {info['active_sessions']}")
        
        if info['has_conflicts']:
            conflicts = get_conflicting_sessions()
            print(f"\nConflicting sessions:")
            for conflict in conflicts:
                print(f"  - {conflict['session_info']['type']} (ID: {conflict['session_id']})")
        
        print(f"\nGuidelines System: {'Available' if _guidelines_system else 'Not Available'}")
        print("===================\n")
    else:
        print("Session info not available")

def print_guidelines_for_task(task_description: str):
    """Print guidelines for a specific task (for debugging)"""
    print(f"\n=== Guidelines for Task ===")
    print(f"Task: {task_description}")
    print(f"Should read guidelines: {should_read_guidelines(task_description)}")
    
    if should_read_guidelines(task_description):
        guidelines = get_task_guidelines(task_description)
        print("\nRelevant Guidelines:")
        print(guidelines)
    else:
        print("No specific guidelines needed for this task.")
    print("========================\n")

# Auto-initialize when this module is imported (unless it's the main module)
if __name__ != "__main__":
    initialize_conflict_handling()

# Example usage and test
if __name__ == "__main__":
    print("Testing Auto Conflict Handler")
    
    # Initialize
    success = initialize_conflict_handling()
    print(f"Initialization successful: {success}")
    
    if success:
        # Print session info
        print_session_status()
        
        # Test file access
        test_file = "test_file.txt"
        print(f"Requesting access to {test_file}")
        access_granted = request_file_access(test_file, "write")
        print(f"Access granted: {access_granted}")
        
        if access_granted:
            print(f"Releasing access to {test_file}")
            release_successful = release_file_access(test_file)
            print(f"Release successful: {release_successful}")
        
        # Check for conflicts
        has_conflicts = check_for_conflicts()
        print(f"Has conflicts: {has_conflicts}")
        
        if has_conflicts:
            conflicts = get_conflicting_sessions()
            print(f"Conflicts: {len(conflicts)}")
            for conflict in conflicts:
                print(f"  - {conflict['session_info']['type']}")