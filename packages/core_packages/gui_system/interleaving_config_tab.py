"""
Interleaving Configuration Tab for GlowingGoldenGlobe GUI
Provides controls for managing Claude interleaving settings per session and per agent/task.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from interleaving_config_manager import get_config_manager, InterleavingConfigManager

class InterleavingConfigTab:
    """Configuration tab for Claude interleaving settings."""
    
    def __init__(self, parent_notebook):
        """Initialize the Interleaving Config tab."""
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="Interleaving Config")
        
        self.config_manager = get_config_manager()
        
        # Variables for UI controls
        self.global_enabled = tk.BooleanVar()
        self.global_locked = tk.BooleanVar()
        self.agent_vars = {}
        self.agent_lock_vars = {}
        
        # Initialize variables from config
        self._load_current_settings()
        
        self._create_widgets()
        
        # Auto-refresh every 2 seconds
        self._refresh_display()
    
    def _load_current_settings(self):
        """Load current settings from config manager."""
        # Global settings
        enabled, locked = self.config_manager.get_global_setting()
        self.global_enabled.set(enabled)
        self.global_locked.set(locked)
        
        # Agent settings
        for agent in ["Div_AI_Agent_Focus_1", "Div_AI_Agent_Focus_2", "Div_AI_Agent_Focus_3", "Div_AI_Agent_Focus_4", "Div_AI_Agent_Focus_5"]:
            enabled, locked = self.config_manager.get_agent_setting(agent)
            self.agent_vars[agent] = tk.BooleanVar(value=enabled)
            self.agent_lock_vars[agent] = tk.BooleanVar(value=locked)
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Main container with scrollbar
        canvas = tk.Canvas(self.tab)
        scrollbar = ttk.Scrollbar(self.tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Claude Interleaving Configuration", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Description
        desc_label = ttk.Label(scrollable_frame, 
                              text="Configure whether to use Claude's tool interleaving with extended thinking capabilities.",
                              wraplength=600)
        desc_label.grid(row=1, column=0, columnspan=3, pady=5, padx=20)
        
        # Global Settings Section
        global_frame = ttk.LabelFrame(scrollable_frame, text="Global Settings", padding=10)
        global_frame.grid(row=2, column=0, columnspan=3, pady=10, padx=20, sticky="ew")
        
        # Global enable checkbox
        global_check = ttk.Checkbutton(
            global_frame, 
            text="Enable Claude Interleaving for All Agents",
            variable=self.global_enabled,
            command=self._on_global_change
        )
        global_check.grid(row=0, column=0, sticky="w", padx=5)
        
        # Global lock checkbox
        global_lock = ttk.Checkbutton(
            global_frame,
            text="Lock (prevent AI workflow from changing)",
            variable=self.global_locked,
            command=self._on_global_lock_change
        )
        global_lock.grid(row=0, column=1, sticky="w", padx=20)
        
        # Info about global setting
        info_label = ttk.Label(global_frame, 
                              text="When enabled, agents will use direct Claude API with enhanced capabilities.",
                              font=("Arial", 9), foreground="gray")
        info_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Per-Agent Settings Section
        agent_frame = ttk.LabelFrame(scrollable_frame, text="Per-Agent Settings", padding=10)
        agent_frame.grid(row=3, column=0, columnspan=3, pady=10, padx=20, sticky="ew")
        
        # Headers
        ttk.Label(agent_frame, text="Agent", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5)
        ttk.Label(agent_frame, text="Enable Interleaving", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5)
        ttk.Label(agent_frame, text="Lock", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5)
        ttk.Label(agent_frame, text="Status", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5)
        
        # Agent controls
        for i, agent in enumerate(["Div_AI_Agent_Focus_1", "Div_AI_Agent_Focus_2", "Div_AI_Agent_Focus_3", "Div_AI_Agent_Focus_4", "Div_AI_Agent_Focus_5"], 1):
            # Agent name
            ttk.Label(agent_frame, text=agent).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            # Enable checkbox
            agent_check = ttk.Checkbutton(
                agent_frame,
                variable=self.agent_vars[agent],
                command=lambda a=agent: self._on_agent_change(a)
            )
            agent_check.grid(row=i, column=1, pady=2)
            
            # Lock checkbox
            lock_check = ttk.Checkbutton(
                agent_frame,
                variable=self.agent_lock_vars[agent],
                command=lambda a=agent: self._on_agent_lock_change(a)
            )
            lock_check.grid(row=i, column=2, pady=2)
            
            # Status indicator
            status_label = ttk.Label(agent_frame, text="●", font=("Arial", 12))
            status_label.grid(row=i, column=3, pady=2)
            setattr(self, f"{agent}_status", status_label)
            self._update_status_indicator(agent)
        
        # Task Override Section
        task_frame = ttk.LabelFrame(scrollable_frame, text="Active Task Overrides", padding=10)
        task_frame.grid(row=4, column=0, columnspan=3, pady=10, padx=20, sticky="ew")
        
        # Task override info
        self.task_info_label = ttk.Label(task_frame, text="No active task overrides")
        self.task_info_label.grid(row=0, column=0, sticky="w", padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Apply to All Agents", 
                  command=self._apply_to_all).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self._reset_to_defaults).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="View Session History", 
                  command=self._view_history).grid(row=0, column=2, padx=5)
        
        # Status summary
        self.summary_label = ttk.Label(scrollable_frame, text="", font=("Arial", 9))
        self.summary_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update summary
        self._update_summary()
    
    def _on_global_change(self):
        """Handle global setting change."""
        enabled = self.global_enabled.get()
        locked = self.global_locked.get()
        
        if self.config_manager.set_global_setting(enabled, locked):
            self._update_summary()
            messagebox.showinfo("Success", f"Global interleaving {'enabled' if enabled else 'disabled'}")
        else:
            messagebox.showwarning("Locked", "Cannot change locked setting")
            self._load_current_settings()
    
    def _on_global_lock_change(self):
        """Handle global lock change."""
        enabled = self.global_enabled.get()
        locked = self.global_locked.get()
        self.config_manager.set_global_setting(enabled, locked)
        self._update_summary()
    
    def _on_agent_change(self, agent: str):
        """Handle agent setting change."""
        enabled = self.agent_vars[agent].get()
        locked = self.agent_lock_vars[agent].get()
        
        if self.config_manager.set_agent_setting(agent, enabled, locked):
            self._update_status_indicator(agent)
            self._update_summary()
        else:
            messagebox.showwarning("Locked", f"Cannot change locked setting for {agent}")
            self._load_current_settings()
    
    def _on_agent_lock_change(self, agent: str):
        """Handle agent lock change."""
        enabled = self.agent_vars[agent].get()
        locked = self.agent_lock_vars[agent].get()
        self.config_manager.set_agent_setting(agent, enabled, locked)
        self._update_summary()
    
    def _update_status_indicator(self, agent: str):
        """Update the status indicator for an agent."""
        enabled = self.agent_vars[agent].get()
        status_label = getattr(self, f"{agent}_status")
        
        if enabled:
            status_label.config(text="●", foreground="green")
        else:
            status_label.config(text="●", foreground="red")
    
    def _update_summary(self):
        """Update the summary label."""
        summary = self.config_manager.get_status_summary()
        
        global_text = "Enabled" if summary["global"][0] else "Disabled"
        if summary["global"][1]:
            global_text += " (Locked)"
        
        active_agents = sum(1 for enabled, _ in summary["agents"].values() if enabled)
        
        text = f"Global: {global_text} | Active Agents: {active_agents}/5 | Task Overrides: {summary['active_task_overrides']}"
        self.summary_label.config(text=text)
        
        # Update task info
        if summary["active_task_overrides"] > 0:
            self.task_info_label.config(text=f"{summary['active_task_overrides']} active task-specific overrides")
        else:
            self.task_info_label.config(text="No active task overrides")
    
    def _apply_to_all(self):
        """Apply current global setting to all agents."""
        enabled = self.global_enabled.get()
        
        if messagebox.askyesno("Confirm", f"Apply global setting ({'Enabled' if enabled else 'Disabled'}) to all agents?"):
            for agent in self.agent_vars:
                self.config_manager.set_agent_setting(agent, enabled)
                self.agent_vars[agent].set(enabled)
                self._update_status_indicator(agent)
            
            self._update_summary()
            messagebox.showinfo("Success", "Settings applied to all agents")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Confirm", "Reset all interleaving settings to defaults?\n\nThis will enable interleaving for all agents and remove all locks."):
            # Reset global
            self.config_manager.set_global_setting(True, False)
            
            # Reset all agents
            for agent in self.agent_vars:
                self.config_manager.set_agent_setting(agent, True, False)
            
            # Reload UI
            self._load_current_settings()
            for agent in self.agent_vars:
                self._update_status_indicator(agent)
            
            self._update_summary()
            messagebox.showinfo("Success", "Settings reset to defaults")
    
    def _view_history(self):
        """View session history in a new window."""
        history_window = tk.Toplevel(self.tab)
        history_window.title("Interleaving Session History")
        history_window.geometry("800x600")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(history_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, width=80, height=30)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get history
        history = self.config_manager.config.get("session_history", [])
        
        if history:
            text_widget.insert(tk.END, "Session History (Most Recent First)\n" + "="*50 + "\n\n")
            
            for event in reversed(history[-50:]):  # Show last 50 events
                text_widget.insert(tk.END, f"Time: {event['timestamp']}\n")
                text_widget.insert(tk.END, f"Agent: {event['agent']}\n")
                text_widget.insert(tk.END, f"Task: {event['task_id']}\n")
                text_widget.insert(tk.END, f"Event: {event['event_type']}\n")
                if event.get('details'):
                    text_widget.insert(tk.END, f"Details: {event['details']}\n")
                text_widget.insert(tk.END, "-"*30 + "\n\n")
        else:
            text_widget.insert(tk.END, "No session history available")
        
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(history_window, text="Close", 
                  command=history_window.destroy).pack(pady=10)
    
    def _refresh_display(self):
        """Refresh the display periodically."""
        try:
            # Reload settings in case they were changed externally
            self._load_current_settings()
            
            # Update all status indicators
            for agent in self.agent_vars:
                self._update_status_indicator(agent)
            
            # Update summary
            self._update_summary()
            
        except Exception as e:
            print(f"Error refreshing interleaving config display: {e}")
        
        # Schedule next refresh
        self.tab.after(2000, self._refresh_display)


# Integration function for main GUI
def add_interleaving_config_tab(notebook):
    """Add the interleaving configuration tab to a notebook widget."""
    return InterleavingConfigTab(notebook)