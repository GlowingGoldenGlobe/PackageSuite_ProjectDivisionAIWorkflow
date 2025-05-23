"""
AI Workflow Status Indicators for Main Controls Tab
Restores the original metrics levels indicators with enhanced functionality
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime

class AIWorkflowStatusIndicator:
    """Enhanced status indicator showing AI Workflow metrics levels"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.create_widgets()
        self.update_status()
        
    def create_widgets(self):
        """Create the status indicator widgets"""
        # Main container frame
        self.container = ttk.LabelFrame(self.parent_frame, text="AI Workflow Status", padding=5)
        
        # Status metrics section
        metrics_frame = ttk.Frame(self.container)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Create metric level indicators
        self.metrics = {
            'automation_level': {
                'label': 'Automation Level:',
                'value': tk.StringVar(value='Not Started'),
                'color': tk.StringVar(value='gray')
            },
            'active_sessions': {
                'label': 'Active Sessions:',
                'value': tk.StringVar(value='0'),
                'color': tk.StringVar(value='gray')
            },
            'task_completion': {
                'label': 'Task Completion:',
                'value': tk.StringVar(value='0%'),
                'color': tk.StringVar(value='gray')
            },
            'system_health': {
                'label': 'System Health:',
                'value': tk.StringVar(value='Unknown'),
                'color': tk.StringVar(value='gray')
            }
        }
        
        # Create metric displays
        row = 0
        for metric_key, metric_data in self.metrics.items():
            # Label
            label = ttk.Label(metrics_frame, text=metric_data['label'])
            label.grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
            
            # Value with color
            value_label = ttk.Label(metrics_frame, 
                                   textvariable=metric_data['value'],
                                   font=('Arial', 9, 'bold'))
            value_label.grid(row=row, column=1, sticky='w', pady=2)
            
            # Status indicator dot
            indicator = tk.Label(metrics_frame, text='●', font=('Arial', 12))
            indicator.grid(row=row, column=2, padx=(10, 0))
            
            # Store reference for color updates
            metric_data['indicator'] = indicator
            
            row += 1
            
        # Session elapsed time
        self.elapsed_frame = ttk.Frame(self.container)
        self.elapsed_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(self.elapsed_frame, text="Session Time:").pack(side=tk.LEFT, padx=(0, 5))
        self.elapsed_time = tk.StringVar(value="00:00:00")
        self.elapsed_label = ttk.Label(self.elapsed_frame, 
                                      textvariable=self.elapsed_time,
                                      font=('Courier', 10, 'bold'))
        self.elapsed_label.pack(side=tk.LEFT)
        
        # Session start time storage
        self.session_start_time = None
        
    def update_status(self):
        """Update status from AI workflow status file"""
        try:
            # Read workflow status
            status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai_workflow_status.json')
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    
                # Update automation level
                if status.get('state') == 'running':
                    self.metrics['automation_level']['value'].set('Active')
                    self.metrics['automation_level']['indicator'].config(fg='green')
                    
                    # Track session start
                    if not self.session_start_time:
                        self.session_start_time = datetime.now()
                        
                elif status.get('state') == 'paused':
                    self.metrics['automation_level']['value'].set('Paused')
                    self.metrics['automation_level']['indicator'].config(fg='orange')
                else:
                    self.metrics['automation_level']['value'].set('Not Started')
                    self.metrics['automation_level']['indicator'].config(fg='gray')
                    self.session_start_time = None
                    
                # Update active sessions
                active_count = len(status.get('active_agents', []))
                self.metrics['active_sessions']['value'].set(str(active_count))
                if active_count > 0:
                    self.metrics['active_sessions']['indicator'].config(fg='green')
                else:
                    self.metrics['active_sessions']['indicator'].config(fg='gray')
                    
                # Update task completion
                stats = status.get('statistics', {})
                total_tasks = stats.get('total_tasks_started', 0)
                completed_tasks = stats.get('total_tasks_completed', 0)
                if total_tasks > 0:
                    completion_pct = int((completed_tasks / total_tasks) * 100)
                    self.metrics['task_completion']['value'].set(f'{completion_pct}%')
                    if completion_pct >= 80:
                        self.metrics['task_completion']['indicator'].config(fg='green')
                    elif completion_pct >= 50:
                        self.metrics['task_completion']['indicator'].config(fg='orange')
                    else:
                        self.metrics['task_completion']['indicator'].config(fg='red')
                        
                # Update system health
                error_count = stats.get('total_errors', 0)
                if error_count == 0:
                    self.metrics['system_health']['value'].set('Good')
                    self.metrics['system_health']['indicator'].config(fg='green')
                elif error_count < 5:
                    self.metrics['system_health']['value'].set('Warning')
                    self.metrics['system_health']['indicator'].config(fg='orange')
                else:
                    self.metrics['system_health']['value'].set('Critical')
                    self.metrics['system_health']['indicator'].config(fg='red')
                    
        except Exception as e:
            print(f"Error updating workflow status: {e}")
            
        # Update elapsed time
        if self.session_start_time:
            elapsed = datetime.now() - self.session_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed_time.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
        # Schedule next update
        self.parent_frame.after(1000, self.update_status)
        
    def get_frame(self):
        """Return the container frame"""
        return self.container


def create_ai_workflow_indicators(parent, row=0, column=0, columnspan=2):
    """Create and return AI Workflow status indicators using grid geometry"""
    indicator = AIWorkflowStatusIndicator(parent)
    indicator.get_frame().grid(row=row, column=column, columnspan=columnspan, 
                              sticky='ew', padx=5, pady=5)
    return indicator