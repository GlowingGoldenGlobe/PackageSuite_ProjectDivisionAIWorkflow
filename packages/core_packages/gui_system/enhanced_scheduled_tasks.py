"""
Enhanced Scheduled Tasks Component
With description column and message-alert attribute
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, time
import uuid

class EnhancedScheduledTasks:
    """Enhanced scheduled tasks with description and alert attributes"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.scheduled_tasks = []
        self.load_scheduled_tasks()
        self.create_widgets()
        self.check_scheduled_tasks()
        
    def create_widgets(self):
        """Create the scheduled tasks interface"""
        # Main frame
        self.main_frame = ttk.LabelFrame(self.parent_frame, 
                                        text="Scheduled Tasks", 
                                        padding=10)
        
        # Tree view with new columns
        columns = ('TaskID', 'Time', 'Description', 'MessageAlert', 'Automation', 'Status')
        self.schedule_tree = ttk.Treeview(self.main_frame, 
                                         columns=columns,
                                         show='tree headings',
                                         height=8)
        
        # Configure columns
        self.schedule_tree.heading('#0', text='Name')
        self.schedule_tree.heading('TaskID', text='Task ID')
        self.schedule_tree.heading('Time', text='Schedule')
        self.schedule_tree.heading('Description', text='Description')
        self.schedule_tree.heading('MessageAlert', text='Alert')
        self.schedule_tree.heading('Automation', text='Auto')
        self.schedule_tree.heading('Status', text='Status')
        
        # Set column widths
        self.schedule_tree.column('#0', width=150)
        self.schedule_tree.column('TaskID', width=120)
        self.schedule_tree.column('Time', width=100)
        self.schedule_tree.column('Description', width=250)
        self.schedule_tree.column('MessageAlert', width=50)
        self.schedule_tree.column('Automation', width=50)
        self.schedule_tree.column('Status', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, 
                                 orient='vertical',
                                 command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.schedule_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Control buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Task", 
                  command=self.add_scheduled_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Task", 
                  command=self.edit_scheduled_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Remove Task", 
                  command=self.remove_scheduled_task).pack(side='left', padx=5)
        
        # Log buttons
        ttk.Button(button_frame, text="Completed Log", 
                  command=self.show_completed_log).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Removed Log", 
                  command=self.show_removed_log).pack(side='right', padx=5)
        
        # Populate initial data
        self.refresh_schedule_tree()
        
    def generate_task_id(self, task_name):
        """Generate unique task ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique = str(uuid.uuid4())[:6]
        safe_name = task_name.lower().replace(' ', '_')[:10]
        return f"sched_{safe_name}_{timestamp}_{unique}"
        
    def add_scheduled_task(self):
        """Add a new scheduled task"""
        dialog = ScheduledTaskDialog(self.parent_frame, "Add Scheduled Task")
        
        if dialog.result:
            task_id = self.generate_task_id(dialog.result['name'])
            task = {
                'id': task_id,
                'name': dialog.result['name'],
                'time': dialog.result['time'],
                'description': dialog.result['description'],
                'message_alert': dialog.result['message_alert'],
                'automation': dialog.result['automation'],
                'status': 'scheduled',
                'created': datetime.now().isoformat()
            }
            
            self.scheduled_tasks.append(task)
            self.save_scheduled_tasks()
            self.refresh_schedule_tree()
            
    def edit_scheduled_task(self):
        """Edit selected scheduled task"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a task to edit")
            return
            
        item = self.schedule_tree.item(selection[0])
        task_id = item['values'][0]
        
        # Find task
        task = None
        for t in self.scheduled_tasks:
            if t['id'] == task_id:
                task = t
                break
                
        if task:
            dialog = ScheduledTaskDialog(self.parent_frame, 
                                       "Edit Scheduled Task", 
                                       task)
            if dialog.result:
                # Update task
                task.update(dialog.result)
                self.save_scheduled_tasks()
                self.refresh_schedule_tree()
                
    def remove_scheduled_task(self):
        """Remove selected scheduled task"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a task to remove")
            return
            
        if messagebox.askyesno("Confirm", "Remove selected task?"):
            item = self.schedule_tree.item(selection[0])
            task_id = item['values'][0]
            
            # Find and log task before removal
            for i, task in enumerate(self.scheduled_tasks):
                if task['id'] == task_id:
                    self.log_removed_task(task)
                    self.scheduled_tasks.pop(i)
                    break
                    
            self.save_scheduled_tasks()
            self.refresh_schedule_tree()
            
    def refresh_schedule_tree(self):
        """Refresh the schedule tree view"""
        # Clear existing items
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
            
        # Add tasks
        for task in self.scheduled_tasks:
            # Skip completed tasks (auto-remove)
            if task.get('status') == 'completed':
                continue
                
            alert_text = "Yes" if task.get('message_alert') else "No"
            auto_text = "Yes" if task.get('automation') else "No"
            
            self.schedule_tree.insert('', 'end',
                                     text=task['name'],
                                     values=(
                                         task['id'],
                                         task['time'],
                                         task['description'],
                                         alert_text,
                                         auto_text,
                                         task['status'].title()
                                     ))
                                     
    def check_scheduled_tasks(self):
        """Check and execute scheduled tasks"""
        current_time = datetime.now().strftime('%H:%M')
        
        for task in self.scheduled_tasks:
            if (task['status'] == 'scheduled' and 
                task['time'] == current_time):
                
                if task.get('message_alert'):
                    # Show alert to user
                    messagebox.showinfo("Scheduled Task Alert", 
                                      f"Task: {task['name']}\\n"
                                      f"Description: {task['description']}")
                    task['status'] = 'alerted'
                    
                elif task.get('automation'):
                    # Queue for automation
                    self.queue_for_automation(task)
                    task['status'] = 'queued'
                else:
                    # Just mark as ready
                    task['status'] = 'ready'
                    
                self.save_scheduled_tasks()
                self.refresh_schedule_tree()
                
        # Auto-remove completed tasks
        self.auto_remove_completed()
        
        # Schedule next check
        self.parent_frame.after(30000, self.check_scheduled_tasks)  # Check every 30 seconds
        
    def auto_remove_completed(self):
        """Auto-remove completed scheduled tasks"""
        tasks_to_remove = []
        
        for task in self.scheduled_tasks:
            if task.get('status') == 'completed':
                # Log before removal
                self.log_completed_task(task)
                tasks_to_remove.append(task)
                
        for task in tasks_to_remove:
            self.scheduled_tasks.remove(task)
            
        if tasks_to_remove:
            self.save_scheduled_tasks()
            self.refresh_schedule_tree()
            
    def queue_for_automation(self, task):
        """Queue task for AI automation"""
        # Create automation request
        automation_request = {
            'task_id': task['id'],
            'task_name': task['name'],
            'description': task['description'],
            'requested_at': datetime.now().isoformat(),
            'priority': 'scheduled'
        }
        
        # Write to automation queue
        queue_file = 'automation_queue.json'
        queue = []
        if os.path.exists(queue_file):
            try:
                with open(queue_file, 'r') as f:
                    queue = json.load(f)
            except:
                queue = []
                
        queue.append(automation_request)
        
        with open(queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
            
    def save_scheduled_tasks(self):
        """Save scheduled tasks to file"""
        with open('scheduled_tasks.json', 'w') as f:
            json.dump(self.scheduled_tasks, f, indent=2)
            
    def load_scheduled_tasks(self):
        """Load scheduled tasks from file"""
        if os.path.exists('scheduled_tasks.json'):
            try:
                with open('scheduled_tasks.json', 'r') as f:
                    self.scheduled_tasks = json.load(f)
            except:
                self.scheduled_tasks = []
        else:
            # Default tasks for demo
            self.scheduled_tasks = [
                {
                    'id': self.generate_task_id('Daily Backup'),
                    'name': 'Daily Backup',
                    'time': '23:00',
                    'description': 'Backup all project files and databases',
                    'message_alert': False,
                    'automation': True,
                    'status': 'scheduled',
                    'created': datetime.now().isoformat()
                }
            ]
            
    def log_completed_task(self, task):
        """Log completed task"""
        self._append_to_log('scheduled_completed_log.json', task)
        
    def log_removed_task(self, task):
        """Log removed task"""
        self._append_to_log('scheduled_removed_log.json', task)
        
    def _append_to_log(self, log_file, entry):
        """Append entry to log file"""
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
            
    def show_completed_log(self):
        """Show completed tasks log"""
        self._show_log_window('scheduled_completed_log.json', 'Completed Tasks Log')
        
    def show_removed_log(self):
        """Show removed tasks log"""
        self._show_log_window('scheduled_removed_log.json', 'Removed Tasks Log')
        
    def _show_log_window(self, log_file, title):
        """Show log in a window"""
        if not os.path.exists(log_file):
            messagebox.showinfo(title, "No log entries found")
            return
            
        # Create log window
        log_window = tk.Toplevel(self.parent_frame)
        log_window.title(title)
        log_window.geometry("800x600")
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word')
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Load and display log
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
                
            for log in reversed(logs):  # Show newest first
                entry = log['entry']
                logged_at = log['logged_at']
                
                text_widget.insert('end', f"=== Logged: {logged_at} ===\\n")
                text_widget.insert('end', f"Task: {entry.get('name')}\\n")
                text_widget.insert('end', f"ID: {entry.get('id')}\\n")
                text_widget.insert('end', f"Description: {entry.get('description')}\\n")
                text_widget.insert('end', f"Status: {entry.get('status')}\\n")
                text_widget.insert('end', "\\n")
                
        except Exception as e:
            text_widget.insert('end', f"Error loading log: {e}")
            
        text_widget.configure(state='disabled')
        
        # Restore button
        def restore_selected():
            # Get selected text range
            try:
                sel_start = text_widget.index('sel.first')
                sel_end = text_widget.index('sel.last')
                selected_text = text_widget.get(sel_start, sel_end)
                
                # Extract task ID from selection
                import re
                id_match = re.search(r'ID: (\\S+)', selected_text)
                if id_match:
                    task_id = id_match.group(1)
                    
                    # Find and restore task
                    for log in logs:
                        if log['entry'].get('id') == task_id:
                            self.scheduled_tasks.append(log['entry'])
                            self.save_scheduled_tasks()
                            self.refresh_schedule_tree()
                            messagebox.showinfo("Restored", f"Task {task_id} restored")
                            log_window.destroy()
                            return
                            
            except tk.TclError:
                pass
                
            messagebox.showinfo("No Selection", "Please select a task entry to restore")
            
        ttk.Button(log_window, text="Restore Selected", 
                  command=restore_selected).pack(pady=10)
                  

class ScheduledTaskDialog:
    """Dialog for adding/editing scheduled tasks"""
    
    def __init__(self, parent, title, task=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.name_var = tk.StringVar(value=task.get('name', '') if task else '')
        self.time_var = tk.StringVar(value=task.get('time', '09:00') if task else '09:00')
        self.desc_var = tk.StringVar(value=task.get('description', '') if task else '')
        self.alert_var = tk.BooleanVar(value=task.get('message_alert', False) if task else False)
        self.auto_var = tk.BooleanVar(value=task.get('automation', True) if task else True)
        
        # Create form
        form_frame = ttk.Frame(self.dialog, padding=20)
        form_frame.pack(fill='both', expand=True)
        
        # Name
        ttk.Label(form_frame, text="Task Name:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)
        
        # Time
        ttk.Label(form_frame, text="Schedule Time:").grid(row=1, column=0, sticky='w', pady=5)
        time_frame = ttk.Frame(form_frame)
        time_frame.grid(row=1, column=1, sticky='w', pady=5)
        
        # Time spinboxes
        hours = ttk.Spinbox(time_frame, from_=0, to=23, width=3, 
                           format="%02.0f")
        hours.grid(row=0, column=0)
        ttk.Label(time_frame, text=":").grid(row=0, column=1)
        minutes = ttk.Spinbox(time_frame, from_=0, to=59, width=3,
                             format="%02.0f")
        minutes.grid(row=0, column=2)
        
        # Set initial time
        if task and task.get('time'):
            h, m = task['time'].split(':')
            hours.set(int(h))
            minutes.set(int(m))
            
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='nw', pady=5)
        desc_text = tk.Text(form_frame, width=40, height=5)
        desc_text.grid(row=2, column=1, pady=5)
        if task and task.get('description'):
            desc_text.insert('1.0', task['description'])
            
        # Options
        ttk.Label(form_frame, text="Options:").grid(row=3, column=0, sticky='w', pady=5)
        options_frame = ttk.Frame(form_frame)
        options_frame.grid(row=3, column=1, sticky='w', pady=5)
        
        ttk.Checkbutton(options_frame, text="Show message alert", 
                       variable=self.alert_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Enable automation", 
                       variable=self.auto_var).pack(anchor='w')
                       
        # Note about options
        note_label = ttk.Label(options_frame, 
                              text="Note: Message alerts notify the user\\n"
                                   "Automation queues the task for AI execution",
                              font=('Arial', 9, 'italic'))
        note_label.pack(anchor='w', pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="OK", command=lambda: self.ok_clicked(hours, minutes, desc_text)).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Wait for dialog
        self.dialog.wait_window()
        
    def ok_clicked(self, hours, minutes, desc_text):
        """Handle OK button"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a task name")
            return
            
        self.result = {
            'name': name,
            'time': f"{int(hours.get()):02d}:{int(minutes.get()):02d}",
            'description': desc_text.get('1.0', 'end-1c').strip(),
            'message_alert': self.alert_var.get(),
            'automation': self.auto_var.get()
        }
        
        self.dialog.destroy()


def create_enhanced_scheduled_tasks(parent):
    """Create and return enhanced scheduled tasks component"""
    tasks = EnhancedScheduledTasks(parent)
    return tasks.main_frame