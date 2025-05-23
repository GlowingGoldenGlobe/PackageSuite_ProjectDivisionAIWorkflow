"""
Claude Parallel Tab with Real-time Data
Replaces demo content with actual parallel execution data
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import threading
import time
from datetime import datetime

class ClaudeParallelRealtime:
    """Real-time Claude parallel execution display"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.active_tasks = {}
        self.create_widgets()
        self.start_monitoring()
        
    def create_widgets(self):
        """Create the Claude Parallel interface"""
        # Title
        ttk.Label(self.parent_frame, text="Claude Parallel Execution", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(self.parent_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        # Status indicators
        self.status_vars = {
            'status': tk.StringVar(value="Not Running"),
            'active_tasks': tk.StringVar(value="0"),
            'queued_tasks': tk.StringVar(value="0"),
            'completed_tasks': tk.StringVar(value="0"),
            'cpu_usage': tk.StringVar(value="0%"),
            'memory_usage': tk.StringVar(value="0%"),
            'available_agents': tk.StringVar(value="Detecting...")
        }
        
        labels = [
            ("Status:", 'status'),
            ("Active Tasks:", 'active_tasks'),
            ("Queued Tasks:", 'queued_tasks'),
            ("Completed Tasks:", 'completed_tasks'),
            ("CPU Usage:", 'cpu_usage'),
            ("Memory Usage:", 'memory_usage'),
            ("Available Agents:", 'available_agents')
        ]
        
        for i, (label, var_key) in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(status_grid, text=label).grid(row=row, column=col, sticky='w', padx=5, pady=2)
            ttk.Label(status_grid, textvariable=self.status_vars[var_key]).grid(row=row, column=col+1, sticky='w', padx=5, pady=2)
        
        # Active tasks section
        tasks_frame = ttk.LabelFrame(self.parent_frame, text="Active Tasks", padding=10)
        tasks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Task tree view
        columns = ('Type', 'Agent', 'Status', 'Progress', 'Duration', 'Started')
        self.task_tree = ttk.Treeview(tasks_frame, columns=columns, show='tree headings', height=10)
        
        self.task_tree.heading('#0', text='Task ID')
        self.task_tree.heading('Type', text='Type')
        self.task_tree.heading('Agent', text='Agent')
        self.task_tree.heading('Status', text='Status')
        self.task_tree.heading('Progress', text='Progress')
        self.task_tree.heading('Duration', text='Duration')
        self.task_tree.heading('Started', text='Started At')
        
        # Column widths
        self.task_tree.column('#0', width=150)
        self.task_tree.column('Type', width=100)
        self.task_tree.column('Agent', width=120)
        self.task_tree.column('Status', width=80)
        self.task_tree.column('Progress', width=80)
        self.task_tree.column('Duration', width=80)
        self.task_tree.column('Started', width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tasks_frame, orient='vertical', command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(self.parent_frame, text="Performance Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Metrics display
        self.metrics_text = tk.Text(metrics_frame, height=5, wrap='word')
        self.metrics_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Refresh", 
                  command=self.refresh_data).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Clear Completed", 
                  command=self.clear_completed).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export Report", 
                  command=self.export_report).pack(side='right', padx=5)
        
    def start_monitoring(self):
        """Start monitoring Claude parallel execution"""
        def monitor():
            while True:
                try:
                    self.update_from_parallel_data()
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Claude parallel monitor error: {e}")
                    
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def update_from_parallel_data(self):
        """Update display from actual parallel execution data"""
        try:
            # Read parallel execution status
            parallel_file = 'claude_parallel_execution.json'
            if os.path.exists(parallel_file):
                with open(parallel_file, 'r') as f:
                    data = json.load(f)
                    
                # Update status
                self.status_vars['status'].set(data.get('status', 'Not Running'))
                self.status_vars['active_tasks'].set(str(len(data.get('active_tasks', []))))
                self.status_vars['queued_tasks'].set(str(len(data.get('queued_tasks', []))))
                self.status_vars['completed_tasks'].set(str(data.get('completed_count', 0)))
                
                # Update resource usage
                resources = data.get('resources', {})
                self.status_vars['cpu_usage'].set(f"{resources.get('cpu', 0)}%")
                self.status_vars['memory_usage'].set(f"{resources.get('memory', 0)}%")
                
                # Update available agents
                agents = data.get('available_agents', [])
                if agents:
                    self.status_vars['available_agents'].set(f"{len(agents)} agents")
                else:
                    self.status_vars['available_agents'].set("None detected")
                    
                # Update active tasks
                self.update_task_tree(data.get('active_tasks', []))
                
                # Update metrics
                self.update_metrics(data.get('metrics', {}))
                
            else:
                # No parallel execution data - check for active sessions
                self.check_active_sessions()
                
        except Exception as e:
            print(f"Error updating Claude parallel data: {e}")
            
    def check_active_sessions(self):
        """Check for active AI sessions as fallback"""
        try:
            session_file = os.path.join('ai_managers', 'active_sessions.json')
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    sessions = json.load(f)
                    
                # Count Claude sessions
                claude_sessions = [s for s in sessions.values() 
                                 if 'claude' in s.get('agent', '').lower()]
                
                if claude_sessions:
                    self.status_vars['status'].set("Sessions Active")
                    self.status_vars['active_tasks'].set(str(len(claude_sessions)))
                    
                    # Convert sessions to tasks for display
                    tasks = []
                    for session in claude_sessions:
                        task = {
                            'id': session.get('id', 'unknown'),
                            'type': 'session',
                            'agent': session.get('agent', 'Claude'),
                            'status': 'running',
                            'progress': 'N/A',
                            'started_at': session.get('started_at', '')
                        }
                        tasks.append(task)
                        
                    self.update_task_tree(tasks)
                    
        except Exception as e:
            pass
            
    def update_task_tree(self, tasks):
        """Update the task tree with real data"""
        # Track existing items
        existing_ids = {}
        for item in self.task_tree.get_children():
            task_id = self.task_tree.item(item)['text']
            existing_ids[task_id] = item
            
        # Update or add tasks
        current_ids = set()
        for task in tasks:
            task_id = task.get('id', 'unknown')
            current_ids.add(task_id)
            
            # Calculate duration
            duration = "00:00:00"
            if task.get('started_at'):
                try:
                    start = datetime.fromisoformat(task['started_at'])
                    elapsed = datetime.now() - start
                    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                except:
                    pass
                    
            values = (
                task.get('type', 'general'),
                task.get('agent', 'Claude'),
                task.get('status', 'running'),
                task.get('progress', '0%'),
                duration,
                task.get('started_at', '')[:19]  # Trim to datetime
            )
            
            if task_id in existing_ids:
                # Update existing
                self.task_tree.item(existing_ids[task_id], values=values)
            else:
                # Add new
                self.task_tree.insert('', 'end', text=task_id, values=values)
                
        # Remove tasks no longer active
        for task_id, item in existing_ids.items():
            if task_id not in current_ids:
                self.task_tree.delete(item)
                
    def update_metrics(self, metrics):
        """Update performance metrics display"""
        self.metrics_text.delete(1.0, tk.END)
        
        if metrics:
            self.metrics_text.insert(tk.END, f"Average Task Duration: {metrics.get('avg_duration', 'N/A')}\\n")
            self.metrics_text.insert(tk.END, f"Success Rate: {metrics.get('success_rate', 'N/A')}\\n")
            self.metrics_text.insert(tk.END, f"Tasks per Hour: {metrics.get('tasks_per_hour', 'N/A')}\\n")
            self.metrics_text.insert(tk.END, f"Total Runtime: {metrics.get('total_runtime', 'N/A')}\\n")
        else:
            self.metrics_text.insert(tk.END, "No metrics available yet\\n")
            
    def refresh_data(self):
        """Manual refresh of data"""
        self.update_from_parallel_data()
        
    def clear_completed(self):
        """Clear completed tasks from display"""
        # This would communicate with the parallel execution system
        pass
        
    def export_report(self):
        """Export parallel execution report"""
        from tkinter import filedialog
        import json
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            report = {
                'timestamp': datetime.now().isoformat(),
                'status': self.status_vars['status'].get(),
                'active_tasks': [],
                'metrics': {}
            }
            
            # Collect active tasks
            for item in self.task_tree.get_children():
                task_data = {
                    'id': self.task_tree.item(item)['text'],
                    'values': self.task_tree.item(item)['values']
                }
                report['active_tasks'].append(task_data)
                
            # Save report
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            tk.messagebox.showinfo("Export Complete", f"Report saved to {filename}")


def create_claude_parallel_tab(parent):
    """Create and return Claude Parallel tab content"""
    parallel = ClaudeParallelRealtime(parent)
    return parallel