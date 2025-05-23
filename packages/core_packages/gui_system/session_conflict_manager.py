"""
Session Conflict Manager for GUI
Prevents concurrent execution conflicts
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time
from datetime import datetime

class SessionConflictManager:
    """Manages session conflicts and prevents concurrent executions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_lock_file = 'session_locks.json'
        self.button_states = {}
        self.load_session_locks()
        
    def register_button(self, button_id, button_widget):
        """Register a button for conflict management"""
        self.button_states[button_id] = {
            'widget': button_widget,
            'original_state': button_widget['state'],
            'conflict_reason': None
        }
        
    def check_start_permission(self, session_type, source_button):
        """Check if a new session can be started"""
        conflicts = []
        
        # Check for active sessions
        for session_id, session in self.active_sessions.items():
            if session['status'] == 'active':
                conflicts.append({
                    'session_id': session_id,
                    'type': session['type'],
                    'started_by': session['started_by'],
                    'started_at': session['started_at']
                })
                
        if conflicts:
            # Show conflict dialog
            conflict_msg = "Cannot start new session. Active sessions:\\n\\n"
            for conflict in conflicts:
                conflict_msg += f"• {conflict['type']} session\\n"
                conflict_msg += f"  Started by: {conflict['started_by']}\\n"
                conflict_msg += f"  Started at: {conflict['started_at']}\\n\\n"
                
            conflict_msg += "Please wait for active sessions to complete or stop them first."
            
            messagebox.showwarning("Session Conflict", conflict_msg)
            return False
            
        return True
        
    def start_session(self, session_type, source_button, session_data=None):
        """Start a new session with conflict checking"""
        if not self.check_start_permission(session_type, source_button):
            return None
            
        # Generate session ID
        session_id = f"{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session record
        session = {
            'id': session_id,
            'type': session_type,
            'started_by': source_button,
            'started_at': datetime.now().isoformat(),
            'status': 'active',
            'data': session_data or {}
        }
        
        self.active_sessions[session_id] = session
        self.save_session_locks()
        
        # Update button states
        self.update_button_states()
        
        return session_id
        
    def end_session(self, session_id):
        """End an active session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['status'] = 'completed'
            self.active_sessions[session_id]['ended_at'] = datetime.now().isoformat()
            
            # Remove from active after logging
            self.log_session(self.active_sessions[session_id])
            del self.active_sessions[session_id]
            
            self.save_session_locks()
            self.update_button_states()
            
    def pause_session(self, session_id):
        """Pause an active session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['status'] = 'paused'
            self.active_sessions[session_id]['paused_at'] = datetime.now().isoformat()
            self.save_session_locks()
            self.update_button_states()
            
    def resume_session(self, session_id):
        """Resume a paused session"""
        if session_id in self.active_sessions:
            # Check for conflicts before resuming
            other_active = any(s['status'] == 'active' 
                             for sid, s in self.active_sessions.items() 
                             if sid != session_id)
            
            if other_active:
                messagebox.showwarning("Cannot Resume", 
                                     "Another session is currently active. "
                                     "Please wait or stop it first.")
                return False
                
            self.active_sessions[session_id]['status'] = 'active'
            self.active_sessions[session_id]['resumed_at'] = datetime.now().isoformat()
            self.save_session_locks()
            self.update_button_states()
            return True
            
        return False
        
    def update_button_states(self):
        """Update all registered button states based on active sessions"""
        has_active_session = any(s['status'] == 'active' 
                               for s in self.active_sessions.values())
        
        for button_id, button_info in self.button_states.items():
            widget = button_info['widget']
            
            # Determine if button should be disabled
            should_disable = False
            conflict_reason = None
            
            if has_active_session and button_id.startswith('start_'):
                # Disable other start buttons when session is active
                active_session = next(s for s in self.active_sessions.values() 
                                    if s['status'] == 'active')
                if active_session['started_by'] != button_id:
                    should_disable = True
                    conflict_reason = f"Active {active_session['type']} session"
                    
            # Update button state
            if should_disable:
                widget.configure(state='disabled')
                button_info['conflict_reason'] = conflict_reason
                
                # Add tooltip if possible
                if hasattr(widget, 'tooltip_text'):
                    widget.tooltip_text = conflict_reason
            else:
                # Restore original state
                widget.configure(state=button_info['original_state'])
                button_info['conflict_reason'] = None
                
    def get_active_session_info(self):
        """Get information about active sessions"""
        active_sessions = [s for s in self.active_sessions.values() 
                          if s['status'] == 'active']
        
        if not active_sessions:
            return None
            
        session = active_sessions[0]  # Should only be one active
        
        # Calculate elapsed time
        start_time = datetime.fromisoformat(session['started_at'])
        elapsed = datetime.now() - start_time
        
        return {
            'id': session['id'],
            'type': session['type'],
            'elapsed_time': elapsed,
            'started_by': session['started_by']
        }
        
    def save_session_locks(self):
        """Save session locks to file"""
        data = {
            'active_sessions': self.active_sessions,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.session_lock_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_session_locks(self):
        """Load session locks from file"""
        if os.path.exists(self.session_lock_file):
            try:
                with open(self.session_lock_file, 'r') as f:
                    data = json.load(f)
                    
                # Check if locks are stale (over 1 hour old)
                last_updated = datetime.fromisoformat(data['last_updated'])
                if (datetime.now() - last_updated).seconds > 3600:
                    # Clear stale locks
                    self.active_sessions = {}
                else:
                    self.active_sessions = data.get('active_sessions', {})
                    
            except Exception:
                self.active_sessions = {}
                
    def log_session(self, session):
        """Log completed session"""
        log_file = 'session_history.json'
        
        history = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
                
        history.append(session)
        
        # Keep only last 100 sessions
        if len(history) > 100:
            history = history[-100:]
            
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    def create_conflict_indicator(self, parent):
        """Create a visual conflict indicator widget"""
        indicator_frame = ttk.Frame(parent)
        
        # Session lock indicator
        self.lock_indicator = tk.Label(indicator_frame, 
                                      text="🔓", 
                                      font=('Arial', 16))
        self.lock_indicator.pack(side='left', padx=5)
        
        # Status text
        self.lock_status = tk.StringVar(value="No active sessions")
        ttk.Label(indicator_frame, 
                 textvariable=self.lock_status).pack(side='left')
                 
        # Update indicator
        self.update_conflict_indicator()
        
        return indicator_frame
        
    def update_conflict_indicator(self):
        """Update the conflict indicator display"""
        active = self.get_active_session_info()
        
        if active:
            self.lock_indicator.config(text="🔒", fg='red')
            elapsed = str(active['elapsed_time']).split('.')[0]
            self.lock_status.set(f"{active['type']} session active ({elapsed})")
        else:
            self.lock_indicator.config(text="🔓", fg='green')
            self.lock_status.set("No active sessions")
            
        # Schedule next update
        if hasattr(self, 'lock_indicator'):
            self.lock_indicator.after(1000, self.update_conflict_indicator)


# Global instance
conflict_manager = SessionConflictManager()


def with_session_check(session_type):
    """Decorator for functions that start sessions"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            button_id = f"start_{session_type}"
            
            # Check permission
            if conflict_manager.check_start_permission(session_type, button_id):
                # Start session
                session_id = conflict_manager.start_session(session_type, button_id)
                if session_id:
                    try:
                        # Store session ID for later use
                        self._current_session_id = session_id
                        result = func(self, *args, **kwargs)
                        return result
                    except Exception as e:
                        # End session on error
                        conflict_manager.end_session(session_id)
                        raise e
                        
        return wrapper
    return decorator