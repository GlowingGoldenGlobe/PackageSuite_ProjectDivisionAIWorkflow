#!/usr/bin/env python3
"""
Real-time Interleaving Status Indicator for Main Controls tab
Shows current interleaving status and active task monitoring
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
from pathlib import Path
import threading
import time

class InterleavingStatusIndicator:
    """Visual indicator for interleaving status in Main Controls"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.status_vars = {}
        self.update_thread = None
        self.running = False
        self._create_indicator()
        self.start_monitoring()
    
    def _create_indicator(self):
        """Create the status indicator UI"""
        # Compact frame that fits in Main Controls
        indicator_frame = ttk.LabelFrame(self.parent_frame, text="Interleaving Status", padding=5)
        indicator_frame.pack(fill=tk.X, pady=5)
        
        # Overall status
        status_line = ttk.Frame(indicator_frame)
        status_line.pack(fill=tk.X)
        
        ttk.Label(status_line, text="Global Status:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.global_status = tk.StringVar(value="⚪ Unknown")
        self.global_label = ttk.Label(status_line, textvariable=self.global_status, font=("Arial", 9))
        self.global_label.pack(side=tk.LEFT)
        
        # Active agents with interleaving
        active_frame = ttk.Frame(indicator_frame)
        active_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(active_frame, text="Active:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Create status indicators for each agent
        for i in range(1, 6):
            agent = f"AI_Agent_{i}"
            self.status_vars[agent] = tk.StringVar(value="⚫")
            label = ttk.Label(active_frame, textvariable=self.status_vars[agent], font=("Arial", 10))
            label.pack(side=tk.LEFT, padx=2)
            
            # Tooltip
            self._create_tooltip(label, f"{agent}")
    
    def _create_tooltip(self, widget, text):
        """Create hover tooltip"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.update_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                self._update_status()
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in status monitor: {e}")
                time.sleep(5)
    
    def _update_status(self):
        """Update status indicators"""
        # Check interleaving config
        config_file = Path(__file__).parent.parent / "interleaving_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Update global status
                global_enabled = config.get("global_settings", {}).get("use_interleaving", False)
                if global_enabled:
                    self.global_status.set("🟢 Enabled")
                    self.global_label.config(foreground="green")
                else:
                    self.global_status.set("🔴 Disabled")
                    self.global_label.config(foreground="red")
                
                # Check agent-specific settings
                for agent in self.status_vars:
                    agent_config = config.get("agent_settings", {}).get(agent, {})
                    if agent_config.get("use_interleaving", global_enabled):
                        # Check if agent is active
                        if self._is_agent_active(agent):
                            self.status_vars[agent].set("🟢")  # Active with interleaving
                        else:
                            self.status_vars[agent].set("🔵")  # Enabled but idle
                    else:
                        self.status_vars[agent].set("⚫")  # Disabled
                        
            except Exception as e:
                print(f"Error reading config: {e}")
        else:
            self.global_status.set("⚪ Not Configured")
            self.global_label.config(foreground="gray")
    
    def _is_agent_active(self, agent):
        """Check if agent has active tasks"""
        # Check workflow status
        workflow_file = Path(__file__).parent.parent / "ai_workflow_status.json"
        if workflow_file.exists():
            try:
                with open(workflow_file, 'r') as f:
                    status = json.load(f)
                    return agent in status.get("active_agents", {})
            except:
                pass
        return False


class ResourceMonitorWidget:
    """Real-time resource monitoring widget"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.monitors = {}
        self._create_monitor()
        self.start_monitoring()
    
    def _create_monitor(self):
        """Create resource monitor UI"""
        # Compact monitor frame
        monitor_frame = ttk.LabelFrame(self.parent_frame, text="AI Resource Usage", padding=5)
        monitor_frame.pack(fill=tk.X, pady=5)
        
        # Resource bars
        resources = [
            ("CPU", "blue"),
            ("Memory", "green"),
            ("Tasks", "orange")
        ]
        
        for resource, color in resources:
            row = ttk.Frame(monitor_frame)
            row.pack(fill=tk.X, pady=2)
            
            ttk.Label(row, text=f"{resource}:", width=8, font=("Arial", 9)).pack(side=tk.LEFT)
            
            # Progress bar
            progress = ttk.Progressbar(row, length=150, mode='determinate')
            progress.pack(side=tk.LEFT, padx=5)
            
            # Value label
            value_var = tk.StringVar(value="0%")
            ttk.Label(row, textvariable=value_var, width=6, font=("Arial", 9)).pack(side=tk.LEFT)
            
            self.monitors[resource] = {
                "progress": progress,
                "value": value_var
            }
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self._update_resources()
    
    def _update_resources(self):
        """Update resource displays"""
        try:
            # Try to get real values
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.monitors["CPU"]["progress"]["value"] = cpu_percent
            self.monitors["CPU"]["value"].set(f"{cpu_percent:.0f}%")
            
            # Memory
            mem_percent = psutil.virtual_memory().percent
            self.monitors["Memory"]["progress"]["value"] = mem_percent
            self.monitors["Memory"]["value"].set(f"{mem_percent:.0f}%")
            
        except ImportError:
            # Use demo values
            self.monitors["CPU"]["progress"]["value"] = 45
            self.monitors["CPU"]["value"].set("45%")
            self.monitors["Memory"]["progress"]["value"] = 62
            self.monitors["Memory"]["value"].set("62%")
        
        # Task count (check active tasks)
        task_count = self._count_active_tasks()
        task_percent = min(100, task_count * 20)  # 5 tasks = 100%
        self.monitors["Tasks"]["progress"]["value"] = task_percent
        self.monitors["Tasks"]["value"].set(f"{task_count}/5")
        
        # Schedule next update
        self.parent_frame.after(3000, self._update_resources)
    
    def _count_active_tasks(self):
        """Count active AI tasks"""
        count = 0
        workflow_file = Path(__file__).parent.parent / "ai_workflow_status.json"
        if workflow_file.exists():
            try:
                with open(workflow_file, 'r') as f:
                    status = json.load(f)
                    count = len(status.get("active_agents", {}))
            except:
                pass
        return count


def add_status_indicators(parent_frame):
    """Add both status indicators to a frame"""
    container = ttk.Frame(parent_frame)
    container.pack(fill=tk.X, pady=10)
    
    # Add interleaving status
    interleaving_status = InterleavingStatusIndicator(container)
    
    # Add resource monitor
    resource_monitor = ResourceMonitorWidget(container)
    
    return container