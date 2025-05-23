"""
Real-time Task Manager for GUI
Handles unique task ID generation and live updates
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import uuid
from datetime import datetime
import threading
import time

class RealtimeTaskManager:
    """Manages tasks with unique IDs and real-time updates"""
    
    def __init__(self, task_tree):
        self.task_tree = task_tree
        self.tasks = {}
        self.task_log_file = 'task_modifications_log.json'
        self.completed_log_file = 'completed_tasks_log.json'
        self.removed_log_file = 'removed_tasks_log.json'
        self.load_logs()
        self.start_monitoring()
        
    def generate_task_id(self, task_type='general'):
        """Generate unique task ID with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_part = str(uuid.uuid4())[:8]
        return f"{task_type}_{timestamp}_{unique_part}"
        
    def create_task(self, description, agent, priority='medium', folder=None):
        """Create a new task with all required attributes"""
        task_id = self.generate_task_id(description.split()[0].lower())
        
        task = {
            'id': task_id,
            'description': description,
            'agent': agent,  # Actual AI agent, not folder
            'folder': folder or self._get_agent_folder(agent),
            'status': 'pending',
            'priority': priority,
            'created': datetime.now().isoformat(),
            'mode': self._get_agent_mode(agent),
            'permanent_id': task_id,  # Permanent reference
            'modifications': []
        }
        
        self.tasks[task_id] = task
        self.add_task_to_tree(task)
        self.log_modification(task_id, 'created', task)
        return task_id
        
    def _get_agent_folder(self, agent):
        """Map agent to its working folder"""
        # Map actual agents to folders
        agent_folder_map = {
            'Claude-3-Opus': 'AI_Agent_1',
            'Claude-3-Sonnet': 'AI_Agent_2',
            'GPT-4': 'AI_Agent_3',
            'VSCode-Agent': 'AI_Agent_4',
            'Terminal-Agent': 'AI_Agent_5'
        }
        return agent_folder_map.get(agent, 'AI_Agent_1')
        
    def _get_agent_mode(self, agent):
        """Get the mode for the agent"""
        if 'Claude' in agent:
            return 'Claude API'
        elif 'GPT' in agent:
            return 'OpenAI API'
        elif 'VSCode' in agent:
            return 'VSCode Integration'
        else:
            return 'Terminal Mode'
            
    def update_task_status(self, task_id, new_status):
        """Update task status with logging"""
        if task_id in self.tasks:
            old_status = self.tasks[task_id]['status']
            self.tasks[task_id]['status'] = new_status
            self.tasks[task_id]['last_updated'] = datetime.now().isoformat()
            
            # Log the change
            self.log_modification(task_id, 'status_change', {
                'old_status': old_status,
                'new_status': new_status
            })
            
            # Update tree
            self.refresh_task_in_tree(task_id)
            
            # Handle completion
            if new_status == 'completed':
                self.handle_task_completion(task_id)
                
    def handle_task_completion(self, task_id):
        """Handle task completion with logging"""
        task = self.tasks.get(task_id)
        if task:
            # Log to completed tasks
            self.log_completed_task(task)
            
            # Don't remove immediately - mark for removal
            task['marked_for_removal'] = datetime.now().isoformat()
            
    def remove_completed_scheduled_tasks(self):
        """Auto-remove completed scheduled tasks after delay"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task.get('status') == 'completed' and 
                task.get('marked_for_removal')):
                marked_time = datetime.fromisoformat(task['marked_for_removal'])
                if (current_time - marked_time).seconds > 300:  # 5 minutes
                    tasks_to_remove.append(task_id)
                    
        for task_id in tasks_to_remove:
            self.remove_task(task_id)
            
    def remove_task(self, task_id):
        """Remove task with logging"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            self.log_removed_task(task)
            
            # Remove from tree
            for item in self.task_tree.get_children():
                values = self.task_tree.item(item)['values']
                if values and values[0] == task_id:
                    self.task_tree.delete(item)
                    break
                    
            # Remove from tasks
            del self.tasks[task_id]
            
    def add_task_to_tree(self, task):
        """Add task to the tree view"""
        self.task_tree.insert('', 'end', 
                             text=task['description'],
                             values=(
                                 task['id'],
                                 task['agent'],  # Show actual agent, not folder
                                 task['status'].title(),
                                 task['priority'].title(),
                                 datetime.fromisoformat(task['created']).strftime('%Y-%m-%d %H:%M')
                             ))
                             
    def refresh_task_in_tree(self, task_id):
        """Update task in tree view"""
        task = self.tasks.get(task_id)
        if not task:
            return
            
        for item in self.task_tree.get_children():
            values = self.task_tree.item(item)['values']
            if values and values[0] == task_id:
                self.task_tree.item(item, 
                                   text=task['description'],
                                   values=(
                                       task['id'],
                                       task['agent'],
                                       task['status'].title(),
                                       task['priority'].title(),
                                       datetime.fromisoformat(task['created']).strftime('%Y-%m-%d %H:%M')
                                   ))
                break
                
    def log_modification(self, task_id, action, details):
        """Log task modifications"""
        log_entry = {
            'task_id': task_id,
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Load existing log
        logs = []
        if os.path.exists(self.task_log_file):
            try:
                with open(self.task_log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
                
        logs.append(log_entry)
        
        # Save updated log
        with open(self.task_log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    def log_completed_task(self, task):
        """Log completed task"""
        self._append_to_log(self.completed_log_file, task)
        
    def log_removed_task(self, task):
        """Log removed task"""
        self._append_to_log(self.removed_log_file, task)
        
    def _append_to_log(self, log_file, entry):
        """Append entry to a log file"""
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
                
        logs.append({
            'entry': entry,
            'logged_at': datetime.now().isoformat()
        })
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    def load_logs(self):
        """Load existing logs"""
        # Implementation for loading previous state
        pass
        
    def restore_task(self, task_data):
        """Restore a task from log"""
        task_id = task_data.get('id', task_data.get('permanent_id'))
        if task_id and task_id not in self.tasks:
            self.tasks[task_id] = task_data
            self.add_task_to_tree(task_data)
            self.log_modification(task_id, 'restored', task_data)
            
    def start_monitoring(self):
        """Start monitoring for real-time updates"""
        def monitor():
            while True:
                try:
                    # Check for AI workflow updates
                    self.check_workflow_updates()
                    
                    # Auto-remove completed tasks
                    self.remove_completed_scheduled_tasks()
                    
                    time.sleep(2)  # Check every 2 seconds
                except Exception as e:
                    print(f"Task monitor error: {e}")
                    
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
    def check_workflow_updates(self):
        """Check for updates from AI workflow"""
        try:
            # Read active sessions
            session_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                       'ai_managers', 'active_sessions.json')
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    sessions = json.load(f)
                    
                # Update tasks based on active sessions
                for session_id, session_data in sessions.items():
                    agent = session_data.get('agent')
                    task_desc = session_data.get('task_description')
                    
                    # Find or create task
                    task_found = False
                    for task_id, task in self.tasks.items():
                        if (task['agent'] == agent and 
                            task['description'] == task_desc):
                            # Update existing task
                            self.update_task_status(task_id, 'in_progress')
                            task_found = True
                            break
                            
                    if not task_found and agent and task_desc:
                        # Create new task for active session
                        self.create_task(task_desc, agent, 'high')
                        
        except Exception as e:
            pass  # Silent fail for background updates