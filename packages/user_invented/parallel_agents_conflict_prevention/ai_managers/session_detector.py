#!/usr/bin/env python
"""
Session Detector for GlowingGoldenGlobe AI System

Automatically detects different types of AI agent sessions:
- Terminal sessions (Claude, ChatGPT CLI, etc.)
- GUI workflow sessions (started from the project GUI)
- VSCode agent mode sessions
- Manual script executions

This enables automatic conflict handling between different session types.
"""

import os
import sys
import json
import time
import psutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class SessionDetector:
    """Detects and tracks different types of AI agent sessions"""
    
    SESSION_TERMINAL = "terminal"
    SESSION_GUI = "gui_workflow"
    SESSION_VSCODE = "vscode_agent"
    SESSION_MANUAL = "manual_script"
    SESSION_UNKNOWN = "unknown"
    
    def __init__(self, session_file="ai_managers/active_sessions.json"):
        self.session_file = session_file
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.session_data = {}
        self.current_session_id = None
        self.detection_thread = None
        self.monitoring = False
        
        # Load existing sessions
        self._load_sessions()
        
        # Detect current session type
        self._detect_current_session()
        
        # Start monitoring
        self.start_monitoring()
    
    def _load_sessions(self):
        """Load existing session data"""
        session_path = os.path.join(self.base_dir, self.session_file)
        
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r') as f:
                    self.session_data = json.load(f)
            except:
                self.session_data = {
                    "active_sessions": {},
                    "last_updated": datetime.now().isoformat()
                }
        else:
            self.session_data = {
                "active_sessions": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_sessions(self):
        """Save session data to file"""
        session_path = os.path.join(self.base_dir, self.session_file)
        
        self.session_data["last_updated"] = datetime.now().isoformat()
        
        try:
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            with open(session_path, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving session data: {e}")
    
    def _detect_current_session(self) -> str:
        """Detect the type of current session"""
        session_type = self.SESSION_UNKNOWN
        session_info = {
            "type": session_type,
            "start_time": datetime.now().isoformat(),
            "process_id": os.getpid(),
            "parent_process": None,
            "command_line": None,
            "working_directory": os.getcwd(),
            "environment_hints": []
        }
        
        try:
            current_process = psutil.Process(os.getpid())
            
            # Get command line
            try:
                session_info["command_line"] = ' '.join(current_process.cmdline())
            except:
                session_info["command_line"] = "Unknown"
            
            # Check parent process
            try:
                parent = current_process.parent()
                if parent:
                    session_info["parent_process"] = {
                        "name": parent.name(),
                        "pid": parent.pid,
                        "cmdline": ' '.join(parent.cmdline()) if hasattr(parent, 'cmdline') else "Unknown"
                    }
                    
                    # Detect session type based on parent process
                    parent_name = parent.name().lower()
                    parent_cmd = session_info["parent_process"]["cmdline"].lower()
                    
                    # Terminal sessions
                    if any(term in parent_name for term in ['cmd', 'powershell', 'bash', 'zsh', 'fish', 'terminal', 'wt']):
                        session_type = self.SESSION_TERMINAL
                        session_info["environment_hints"].append("terminal_parent")
                    
                    # VSCode sessions
                    elif 'code' in parent_name or 'vscode' in parent_name:
                        session_type = self.SESSION_VSCODE
                        session_info["environment_hints"].append("vscode_parent")
                    
                    # GUI workflow (usually started by python GUI process)
                    elif 'python' in parent_name and 'gui' in parent_cmd:
                        session_type = self.SESSION_GUI
                        session_info["environment_hints"].append("gui_workflow_parent")
            except:
                pass
            
            # Additional detection based on environment variables
            env_vars = os.environ
            
            # Check for Claude CLI indicators
            if 'ANTHROPIC_API_KEY' in env_vars:
                session_info["environment_hints"].append("anthropic_api_key")
                if session_type == self.SESSION_UNKNOWN:
                    session_type = self.SESSION_TERMINAL
            
            # Check for VSCode indicators
            if any(var.startswith('VSCODE_') for var in env_vars):
                session_info["environment_hints"].append("vscode_env")
                if session_type == self.SESSION_UNKNOWN:
                    session_type = self.SESSION_VSCODE
            
            # Check for terminal indicators
            if 'TERM' in env_vars or 'SHELL' in env_vars:
                session_info["environment_hints"].append("terminal_env")
                if session_type == self.SESSION_UNKNOWN:
                    session_type = self.SESSION_TERMINAL
            
            # Check working directory for GUI workflow
            if 'gui' in os.getcwd().lower():
                session_info["environment_hints"].append("gui_working_dir")
                if session_type == self.SESSION_UNKNOWN:
                    session_type = self.SESSION_GUI
            
            # Check for manual script execution
            if len(sys.argv) > 0 and sys.argv[0].endswith('.py'):
                session_info["environment_hints"].append("python_script")
                if session_type == self.SESSION_UNKNOWN:
                    session_type = self.SESSION_MANUAL
        
        except Exception as e:
            print(f"Error detecting session: {e}")
        
        # Update session info
        session_info["type"] = session_type
        
        # Generate session ID
        self.current_session_id = f"{session_type}_{int(time.time())}_{os.getpid()}"
        
        # Register session
        self.session_data["active_sessions"][self.current_session_id] = session_info
        self._save_sessions()
        
        return session_type
    
    def get_current_session_type(self) -> str:
        """Get the current session type"""
        if self.current_session_id and self.current_session_id in self.session_data["active_sessions"]:
            return self.session_data["active_sessions"][self.current_session_id]["type"]
        return self.SESSION_UNKNOWN
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID"""
        return self.current_session_id
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions"""
        return self.session_data.get("active_sessions", {})
    
    def get_sessions_by_type(self, session_type: str) -> Dict[str, Any]:
        """Get all sessions of a specific type"""
        sessions = {}
        for session_id, session_info in self.session_data.get("active_sessions", {}).items():
            if session_info.get("type") == session_type:
                sessions[session_id] = session_info
        return sessions
    
    def start_monitoring(self):
        """Start monitoring for session changes"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.detection_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
        self.detection_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
    
    def _monitor_sessions(self):
        """Monitor for session changes and cleanup stale sessions"""
        while self.monitoring:
            try:
                # Cleanup stale sessions
                current_time = time.time()
                stale_sessions = []
                
                for session_id, session_info in self.session_data.get("active_sessions", {}).items():
                    try:
                        # Check if process still exists
                        pid = session_info.get("process_id")
                        if pid and not psutil.pid_exists(pid):
                            stale_sessions.append(session_id)
                        
                        # Check if session is too old (older than 24 hours)
                        try:
                            start_time = datetime.fromisoformat(session_info.get("start_time", ""))
                            if (datetime.now() - start_time).total_seconds() > 86400:  # 24 hours
                                stale_sessions.append(session_id)
                        except:
                            pass
                    except:
                        stale_sessions.append(session_id)
                
                # Remove stale sessions
                for session_id in stale_sessions:
                    if session_id in self.session_data["active_sessions"]:
                        del self.session_data["active_sessions"][session_id]
                
                if stale_sessions:
                    self._save_sessions()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in session monitoring: {e}")
                time.sleep(30)
    
    def unregister_current_session(self):
        """Unregister the current session when it ends"""
        if self.current_session_id and self.current_session_id in self.session_data["active_sessions"]:
            # Mark session as ended
            self.session_data["active_sessions"][self.current_session_id]["end_time"] = datetime.now().isoformat()
            
            # Move to completed sessions (keep for history)
            if "completed_sessions" not in self.session_data:
                self.session_data["completed_sessions"] = {}
            
            self.session_data["completed_sessions"][self.current_session_id] = self.session_data["active_sessions"][self.current_session_id]
            del self.session_data["active_sessions"][self.current_session_id]
            
            self._save_sessions()
    
    def has_conflicting_sessions(self, session_type: Optional[str] = None) -> bool:
        """Check if there are conflicting sessions"""
        if not session_type:
            session_type = self.get_current_session_type()
        
        active_sessions = self.get_active_sessions()
        
        # Different session types that may conflict
        conflicting_types = []
        if session_type == self.SESSION_TERMINAL:
            conflicting_types = [self.SESSION_GUI, self.SESSION_VSCODE]
        elif session_type == self.SESSION_GUI:
            conflicting_types = [self.SESSION_TERMINAL, self.SESSION_VSCODE]
        elif session_type == self.SESSION_VSCODE:
            conflicting_types = [self.SESSION_TERMINAL, self.SESSION_GUI]
        
        # Check for conflicting sessions
        for session_id, session_info in active_sessions.items():
            if session_id != self.current_session_id and session_info.get("type") in conflicting_types:
                return True
        
        return False
    
    def get_conflicting_sessions(self, session_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of conflicting sessions"""
        if not session_type:
            session_type = self.get_current_session_type()
        
        active_sessions = self.get_active_sessions()
        
        # Different session types that may conflict
        conflicting_types = []
        if session_type == self.SESSION_TERMINAL:
            conflicting_types = [self.SESSION_GUI, self.SESSION_VSCODE]
        elif session_type == self.SESSION_GUI:
            conflicting_types = [self.SESSION_TERMINAL, self.SESSION_VSCODE]
        elif session_type == self.SESSION_VSCODE:
            conflicting_types = [self.SESSION_TERMINAL, self.SESSION_GUI]
        
        conflicts = []
        for session_id, session_info in active_sessions.items():
            if session_id != self.current_session_id and session_info.get("type") in conflicting_types:
                conflicts.append({
                    "session_id": session_id,
                    "session_info": session_info
                })
        
        return conflicts


# Global instance
_session_detector = None

def get_session_detector() -> SessionDetector:
    """Get the global session detector instance"""
    global _session_detector
    if _session_detector is None:
        _session_detector = SessionDetector()
    return _session_detector

def get_current_session_type() -> str:
    """Quick function to get current session type"""
    detector = get_session_detector()
    return detector.get_current_session_type()

def has_conflicting_sessions() -> bool:
    """Quick function to check for conflicting sessions"""
    detector = get_session_detector()
    return detector.has_conflicting_sessions()

# Auto-initialize when module is imported
if __name__ != "__main__":
    get_session_detector()

# Example usage
if __name__ == "__main__":
    print("Session Detector Test")
    detector = SessionDetector()
    
    print(f"Current session type: {detector.get_current_session_type()}")
    print(f"Current session ID: {detector.get_current_session_id()}")
    print(f"Has conflicts: {detector.has_conflicting_sessions()}")
    
    print("\nActive sessions:")
    for session_id, session_info in detector.get_active_sessions().items():
        print(f"- {session_id}: {session_info['type']}")
    
    if detector.has_conflicting_sessions():
        print("\nConflicting sessions:")
        for conflict in detector.get_conflicting_sessions():
            print(f"- {conflict['session_id']}: {conflict['session_info']['type']}")