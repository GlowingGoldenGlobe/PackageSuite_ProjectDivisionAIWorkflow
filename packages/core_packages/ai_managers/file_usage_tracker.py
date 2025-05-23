#!/usr/bin/env python
"""
File Usage Tracker

This module implements a system for tracking file usage across parallel execution roles.
It prevents conflicts when multiple AI Manager roles try to access the same files
simultaneously by maintaining a centralized record of file locks and workflows.

The system allows:
- Registering workflows with anticipated file usage
- Requesting and releasing file locks
- Handling conflicts based on role priorities
- Tracking lock status and ownership
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set, Union

# Import session detector for automatic conflict handling
try:
    from session_detector import get_session_detector, get_current_session_type
    SESSION_DETECTOR_AVAILABLE = True
except ImportError:
    SESSION_DETECTOR_AVAILABLE = False
    print("Session detector not available - conflict detection will be limited")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/file_usage_tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FileUsageTracker")

class FileUsageTracker:
    """
    Tracks file usage across parallel execution roles to prevent conflicts
    """
    
    def __init__(self, tracker_path="ai_managers/file_usage_tracker.json"):
        """Initialize the file usage tracker"""
        self.tracker_path = tracker_path
        self.lock = threading.Lock()  # Thread safety for JSON operations
        self._load_tracker()
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Initialize session detector if available
        self.session_detector = None
        if SESSION_DETECTOR_AVAILABLE:
            try:
                self.session_detector = get_session_detector()
                self.current_session_type = get_current_session_type()
                self.current_session_id = self.session_detector.get_current_session_id()
                logger.info(f"Session detector initialized - current session: {self.current_session_type}")
                
                # Check for conflicts on startup
                if self.session_detector.has_conflicting_sessions():
                    conflicts = self.session_detector.get_conflicting_sessions()
                    logger.warning(f"Detected {len(conflicts)} conflicting sessions on startup")
                    self._handle_session_conflicts(conflicts)
            except Exception as e:
                logger.error(f"Error initializing session detector: {e}")
                self.session_detector = None
        
        logger.info("File Usage Tracker initialized")
    
    def _load_tracker(self):
        """Load tracker data from JSON file"""
        try:
            if os.path.exists(self.tracker_path):
                with open(self.tracker_path, 'r') as f:
                    self.tracker_data = json.load(f)
                logger.debug(f"Loaded tracker data from {self.tracker_path}")
            else:
                self.tracker_data = {
                    "file_locks": {},
                    "workflows": {},
                    "last_updated": datetime.now().isoformat()
                }
                logger.warning(f"Tracker file not found at {self.tracker_path}, created new tracker data")
                self._save_tracker()
        except Exception as e:
            logger.error(f"Error loading tracker data: {str(e)}")
            self.tracker_data = {
                "file_locks": {},
                "workflows": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_tracker(self):
        """Save tracker data to JSON file"""
        try:
            self.tracker_data["last_updated"] = datetime.now().isoformat()
            with open(self.tracker_path, 'w') as f:
                json.dump(self.tracker_data, f, indent=2)
            logger.debug(f"Saved tracker data to {self.tracker_path}")
        except Exception as e:
            logger.error(f"Error saving tracker data: {str(e)}")
    
    def _handle_session_conflicts(self, conflicts: List[Dict[str, Any]]):
        """Handle conflicts between different session types"""
        logger.info("Handling session conflicts automatically")
        
        # Priority order: GUI > Terminal > VSCode > Manual
        session_priorities = {
            "gui_workflow": 10,
            "terminal": 8,
            "vscode_agent": 6,
            "manual_script": 4,
            "unknown": 2
        }
        
        current_priority = session_priorities.get(self.current_session_type, 0)
        
        for conflict in conflicts:
            conflict_session = conflict["session_info"]
            conflict_type = conflict_session.get("type", "unknown")
            conflict_priority = session_priorities.get(conflict_type, 0)
            
            if current_priority > conflict_priority:
                logger.info(f"Current session ({self.current_session_type}) has higher priority than {conflict_type}")
                # Current session continues, conflicting session should yield
                self._notify_session_to_yield(conflict["session_id"])
            elif current_priority < conflict_priority:
                logger.warning(f"Conflicting session ({conflict_type}) has higher priority than current session ({self.current_session_type})")
                # Current session should yield or ask user
                self._handle_yield_request(conflict["session_id"], conflict_type)
            else:
                logger.info(f"Equal priority conflict between {self.current_session_type} and {conflict_type} - asking user")
                self._ask_user_for_conflict_resolution(conflict["session_id"], conflict_type)
    
    def _notify_session_to_yield(self, session_id: str):
        """Notify another session to yield priority"""
        try:
            # Create a yield notification file
            yield_file = f"session_yield_{session_id}.json"
            yield_data = {
                "yielding_to": self.current_session_id,
                "yield_reason": "priority_conflict",
                "timestamp": datetime.now().isoformat(),
                "message": f"Please yield to higher priority session: {self.current_session_type}"
            }
            
            with open(yield_file, 'w') as f:
                json.dump(yield_data, f, indent=2)
            
            logger.info(f"Created yield notification for session {session_id}")
        except Exception as e:
            logger.error(f"Error creating yield notification: {e}")
    
    def _handle_yield_request(self, higher_priority_session_id: str, higher_priority_type: str):
        """Handle when current session should yield to higher priority"""
        logger.warning(f"Session conflict: {higher_priority_type} session has higher priority")
        
        # Check if user wants to continue anyway
        yield_response = self._check_user_yield_preference()
        
        if yield_response == "yield":
            logger.info("Current session yielding to higher priority session")
            self._pause_current_operations()
        elif yield_response == "continue":
            logger.info("User chose to continue despite lower priority")
        else:
            # Default: ask user
            print(f"\n⚠️  CONFLICT DETECTED ⚠️")
            print(f"Another {higher_priority_type} session is active with higher priority.")
            print(f"Current session: {self.current_session_type}")
            print("Options:")
            print("1. Continue anyway (may cause conflicts)")
            print("2. Pause current session")
            print("3. Stop current session")
            
            try:
                choice = input("Enter choice (1-3): ").strip()
                if choice == "2":
                    self._pause_current_operations()
                elif choice == "3":
                    self._stop_current_session()
                else:
                    logger.warning("User chose to continue despite conflict risk")
            except:
                logger.warning("Could not get user input - continuing with conflict risk")
    
    def _ask_user_for_conflict_resolution(self, conflict_session_id: str, conflict_type: str):
        """Ask user how to resolve equal priority conflict"""
        print(f"\n⚠️  SESSION CONFLICT ⚠️")
        print(f"Equal priority conflict detected:")
        print(f"Current session: {self.current_session_type}")
        print(f"Conflicting session: {conflict_type}")
        print("Both sessions may try to access the same files.")
        print("Options:")
        print("1. Continue (risk of conflicts)")
        print("2. Coordinate with other session")
        print("3. Stop current session")
        
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "2":
                print("Please coordinate manually with the other session.")
            elif choice == "3":
                self._stop_current_session()
            else:
                logger.warning("User chose to continue with conflict risk")
        except:
            logger.warning("Could not get user input - continuing with conflict risk")
    
    def _check_user_yield_preference(self) -> str:
        """Check if user has a preference for yielding"""
        # Check for user preference file
        pref_file = "user_conflict_preferences.json"
        if os.path.exists(pref_file):
            try:
                with open(pref_file, 'r') as f:
                    prefs = json.load(f)
                return prefs.get("yield_preference", "ask")
            except:
                pass
        
        return "ask"  # Default to asking user
    
    def _pause_current_operations(self):
        """Pause current session operations"""
        logger.info("Pausing current session operations")
        
        # Create pause marker
        pause_file = f"session_paused_{self.current_session_id}.json"
        pause_data = {
            "paused_at": datetime.now().isoformat(),
            "reason": "conflict_resolution",
            "session_id": self.current_session_id,
            "session_type": self.current_session_type
        }
        
        with open(pause_file, 'w') as f:
            json.dump(pause_data, f, indent=2)
    
    def _stop_current_session(self):
        """Stop current session"""
        logger.info("Stopping current session due to conflict")
        
        if self.session_detector:
            self.session_detector.unregister_current_session()
        
        # Create stop marker
        stop_file = f"session_stopped_{self.current_session_id}.json"
        stop_data = {
            "stopped_at": datetime.now().isoformat(),
            "reason": "user_requested_due_to_conflict",
            "session_id": self.current_session_id,
            "session_type": self.current_session_type
        }
        
        with open(stop_file, 'w') as f:
            json.dump(stop_data, f, indent=2)
        
        exit(0)
    
    def register_workflow(self, workflow_id: str, role: str, anticipated_files: List[str], 
                          priority: int = 5) -> bool:
        """
        Register a new workflow with anticipated file usage
        
        Args:
            workflow_id: Unique identifier for the workflow
            role: The role executing the workflow
            anticipated_files: List of files the workflow expects to use
            priority: Priority level of the workflow (higher number = higher priority)
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        with self.lock:
            try:
                if workflow_id in self.tracker_data["workflows"]:
                    logger.warning(f"Workflow ID {workflow_id} already exists")
                    return False
                
                self.tracker_data["workflows"][workflow_id] = {
                    "role": role,
                    "status": "registered",
                    "start_time": datetime.now().isoformat(),
                    "anticipated_files": anticipated_files,
                    "priority": priority
                }
                self._save_tracker()
                logger.info(f"Registered workflow {workflow_id} with {len(anticipated_files)} anticipated files")
                return True
            except Exception as e:
                logger.error(f"Error registering workflow: {str(e)}")
                return False
    
    def check_file_lock(self, file_path: str) -> Dict[str, Any]:
        """
        Check if a file is currently locked
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Dict: Lock information if locked, empty dict if not
        """
        with self.lock:
            self._cleanup_stale_locks()
            return self.tracker_data["file_locks"].get(file_path, {})
    
    def request_file_lock(self, file_path: str, role: str, operation: str = "write", 
                          expected_duration: int = 60, workflow_id: Optional[str] = None) -> bool:
        """
        Request a lock on a file for a specific operation
        
        Args:
            file_path: Path to the file to lock
            role: Role requesting the lock
            operation: Type of operation ("read" or "write")
            expected_duration: Expected duration in seconds
            workflow_id: ID of the associated workflow
            
        Returns:
            bool: True if lock granted, False if denied
        """
        with self.lock:
            try:
                # Auto-check for session conflicts if session detector is available
                if self.session_detector and self.session_detector.has_conflicting_sessions():
                    conflicts = self.session_detector.get_conflicting_sessions()
                    logger.warning(f"Session conflicts detected while requesting file lock for {file_path}")
                    self._handle_session_conflicts(conflicts)
                
                # Clean up any stale locks first
                self._cleanup_stale_locks()
                
                # Check if file is already locked
                if file_path in self.tracker_data["file_locks"]:
                    current_lock = self.tracker_data["file_locks"][file_path]
                    
                    # Allow multiple read operations
                    if operation == "read" and current_lock["operation"] == "read":
                        # Update readers list if not already there
                        readers = current_lock.get("readers", [])
                        if role not in readers:
                            readers.append(role)
                            current_lock["readers"] = readers
                            self.tracker_data["file_locks"][file_path] = current_lock
                            self._save_tracker()
                        logger.debug(f"Granted shared read lock on {file_path} to {role}")
                        return True
                    
                    # Check if this role already has the lock (reentrant lock)
                    if current_lock["locked_by"] == role:
                        # Update the expected duration and timestamp
                        current_lock["expected_duration"] = max(current_lock["expected_duration"], expected_duration)
                        current_lock["timestamp"] = datetime.now().isoformat()
                        self.tracker_data["file_locks"][file_path] = current_lock
                        self._save_tracker()
                        logger.debug(f"Updated existing lock on {file_path} for {role}")
                        return True
                    
                    # It's a conflict - check priority if we have workflow information
                    if workflow_id and current_lock.get("workflow_id"):
                        requestor_priority = self._get_workflow_priority(workflow_id)
                        current_priority = self._get_workflow_priority(current_lock["workflow_id"])
                        
                        # Higher priority can preempt lower priority
                        if requestor_priority > current_priority + 2:  # Significant priority difference
                            logger.warning(f"Priority preemption: {role} ({requestor_priority}) preempting " 
                                          f"{current_lock['locked_by']} ({current_priority}) for {file_path}")
                            # Override the lock
                            self._create_new_lock(file_path, role, operation, expected_duration, workflow_id)
                            return True
                    
                    # Lock denied
                    logger.warning(f"Lock denied for {file_path}: already locked by {current_lock['locked_by']}")
                    return False
                
                # If not locked, create a new lock
                self._create_new_lock(file_path, role, operation, expected_duration, workflow_id)
                logger.info(f"Granted new lock on {file_path} to {role} for {operation}")
                return True
                
            except Exception as e:
                logger.error(f"Error requesting file lock: {str(e)}")
                return False
    
    def _create_new_lock(self, file_path: str, role: str, operation: str,
                         expected_duration: int, workflow_id: Optional[str]):
        """Create a new lock entry"""
        lock_entry = {
            "locked_by": role,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "process_id": os.getpid(),
            "expected_duration": expected_duration,
            "workflow_id": workflow_id
        }
        
        # Add readers list for read operations
        if operation == "read":
            lock_entry["readers"] = [role]
            
        self.tracker_data["file_locks"][file_path] = lock_entry
        self._save_tracker()
    
    def _get_workflow_priority(self, workflow_id: str) -> int:
        """Get the priority of a workflow"""
        if workflow_id in self.tracker_data["workflows"]:
            return self.tracker_data["workflows"][workflow_id].get("priority", 0)
        return 0
    
    def release_file_lock(self, file_path: str, role: str) -> bool:
        """
        Release a lock on a file
        
        Args:
            file_path: Path to the file to unlock
            role: Role releasing the lock
            
        Returns:
            bool: True if lock released, False otherwise
        """
        with self.lock:
            try:
                if file_path in self.tracker_data["file_locks"]:
                    current_lock = self.tracker_data["file_locks"][file_path]
                    
                    # Handle read locks (multiple readers)
                    if current_lock["operation"] == "read" and "readers" in current_lock:
                        if role in current_lock["readers"]:
                            current_lock["readers"].remove(role)
                            
                            # If no more readers, remove the lock
                            if not current_lock["readers"]:
                                del self.tracker_data["file_locks"][file_path]
                            else:
                                self.tracker_data["file_locks"][file_path] = current_lock
                                
                            self._save_tracker()
                            logger.debug(f"Released read lock on {file_path} for {role}")
                            return True
                    
                    # Handle write locks (single owner)
                    elif current_lock["locked_by"] == role:
                        del self.tracker_data["file_locks"][file_path]
                        self._save_tracker()
                        logger.info(f"Released lock on {file_path} for {role}")
                        return True
                    
                    logger.warning(f"Cannot release lock on {file_path}: not owned by {role}")
                else:
                    logger.warning(f"Cannot release lock on {file_path}: not locked")
                
                return False
                
            except Exception as e:
                logger.error(f"Error releasing file lock: {str(e)}")
                return False
    
    def _cleanup_stale_locks(self):
        """Remove locks that have exceeded their expected duration"""
        now = datetime.now()
        stale_locks = []
        
        for file_path, lock_info in self.tracker_data["file_locks"].items():
            try:
                lock_time = datetime.fromisoformat(lock_info["timestamp"])
                expected_duration = lock_info.get("expected_duration", 60)  # Default 60 seconds
                
                # Check if lock has expired
                if (now - lock_time).total_seconds() > expected_duration + 30:  # Add 30s buffer
                    stale_locks.append((file_path, lock_info["locked_by"]))
            except Exception as e:
                logger.error(f"Error checking lock expiration: {str(e)}")
        
        # Remove stale locks
        for file_path, owner in stale_locks:
            logger.warning(f"Removing stale lock on {file_path} from {owner}")
            del self.tracker_data["file_locks"][file_path]
        
        # Save if we removed any locks
        if stale_locks:
            self._save_tracker()
    
    def complete_workflow(self, workflow_id: str) -> bool:
        """
        Mark a workflow as completed and release all associated locks
        
        Args:
            workflow_id: ID of the workflow to complete
            
        Returns:
            bool: True if workflow completed, False otherwise
        """
        with self.lock:
            try:
                if workflow_id in self.tracker_data["workflows"]:
                    # Update workflow status
                    self.tracker_data["workflows"][workflow_id]["status"] = "completed"
                    self.tracker_data["workflows"][workflow_id]["end_time"] = datetime.now().isoformat()
                    
                    # Release all associated locks
                    associated_locks = []
                    for file_path, lock_info in list(self.tracker_data["file_locks"].items()):
                        if lock_info.get("workflow_id") == workflow_id:
                            associated_locks.append(file_path)
                            del self.tracker_data["file_locks"][file_path]
                    
                    self._save_tracker()
                    logger.info(f"Completed workflow {workflow_id} and released {len(associated_locks)} locks")
                    return True
                
                logger.warning(f"Cannot complete workflow {workflow_id}: not registered")
                return False
                
            except Exception as e:
                logger.error(f"Error completing workflow: {str(e)}")
                return False
    
    def get_active_workflows(self) -> Dict[str, Any]:
        """Get all active workflows"""
        active_workflows = {}
        
        for workflow_id, workflow_info in self.tracker_data["workflows"].items():
            if workflow_info.get("status") == "registered" or workflow_info.get("status") == "in_progress":
                active_workflows[workflow_id] = workflow_info
        
        return active_workflows
    
    def get_file_locks(self) -> Dict[str, Any]:
        """Get all current file locks"""
        return self.tracker_data["file_locks"]
    
    def update_workflow_status(self, workflow_id: str, status: str) -> bool:
        """
        Update the status of a workflow
        
        Args:
            workflow_id: ID of the workflow to update
            status: New status ('registered', 'in_progress', 'completed', 'failed')
            
        Returns:
            bool: True if status updated, False otherwise
        """
        with self.lock:
            try:
                if workflow_id in self.tracker_data["workflows"]:
                    self.tracker_data["workflows"][workflow_id]["status"] = status
                    self.tracker_data["workflows"][workflow_id]["updated_time"] = datetime.now().isoformat()
                    self._save_tracker()
                    logger.info(f"Updated workflow {workflow_id} status to {status}")
                    return True
                
                logger.warning(f"Cannot update workflow {workflow_id}: not registered")
                return False
                
            except Exception as e:
                logger.error(f"Error updating workflow status: {str(e)}")
                return False


# Singleton instance
_tracker_instance = None

def get_file_usage_tracker() -> FileUsageTracker:
    """Get the singleton instance of the FileUsageTracker"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = FileUsageTracker()
    return _tracker_instance


# Example usage
if __name__ == "__main__":
    print("Testing File Usage Tracker")
    
    # Get tracker instance
    tracker = get_file_usage_tracker()
    
    # Register a workflow
    workflow_id = f"test_workflow_{int(time.time())}"
    tracker.register_workflow(
        workflow_id,
        "agent_simulations",
        ["/path/to/file1.py", "/path/to/file2.json"],
        priority=7
    )
    
    # Request locks
    print("\nRequesting locks:")
    print(f"Lock 1: {tracker.request_file_lock('/path/to/file1.py', 'agent_simulations', workflow_id=workflow_id)}")
    print(f"Lock 2: {tracker.request_file_lock('/path/to/file2.json', 'agent_simulations', workflow_id=workflow_id)}")
    
    # Check locks
    print("\nCurrent locks:")
    for file_path, lock_info in tracker.get_file_locks().items():
        print(f"- {file_path}: locked by {lock_info['locked_by']}")
    
    # Release locks
    print("\nReleasing locks:")
    print(f"Release 1: {tracker.release_file_lock('/path/to/file1.py', 'agent_simulations')}")
    
    # Complete workflow
    print("\nCompleting workflow:")
    print(f"Complete: {tracker.complete_workflow(workflow_id)}")
    
    # Check locks again
    print("\nRemaining locks:")
    for file_path, lock_info in tracker.get_file_locks().items():
        print(f"- {file_path}: locked by {lock_info['locked_by']}")