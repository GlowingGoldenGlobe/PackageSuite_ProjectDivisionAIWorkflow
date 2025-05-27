#!/usr/bin/env python3
"""
Fixed version of simplified interleaving controls with correct terminology
IMPORTANT: Div_AI_Agent_Focus_1 through Div_AI_Agent_Focus_5 are FOLDERS (project divisions), not AI agents!
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from interleaving_config_manager import get_config_manager
except ImportError:
    # Create a mock if not available
    class MockConfigManager:
        def __init__(self):
            self.task_overrides = {}
            
        def get_global_setting(self):
            return True, False
        def set_global_setting(self, enabled, locked):
            return True
        def get_agent_setting(self, agent):
            return True, False
        def set_agent_setting(self, agent, enabled, locked=None):
            return True
        def set_task_override(self, task_key, enabled, locked):
            self.task_overrides[task_key] = {"use_interleaving": enabled, "locked": locked}
            return True
        def remove_task_override(self, task_key):
            if task_key in self.task_overrides:
                del self.task_overrides[task_key]
                return True
            return False
        def get_all_task_overrides(self):
            return self.task_overrides
    
    def get_config_manager():
        return MockConfigManager()

class SimpleInterleavingControls:
    """Simplified interleaving controls with correct terminology"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.config_manager = None  # Lazy load
        self.controls_created = False
        
        # Variables
        self.global_enabled = tk.BooleanVar()
        self.global_locked = tk.BooleanVar()
        
        # Create minimal UI first
        self._create_placeholder()
    
    def _create_placeholder(self):
        """Create placeholder that loads full controls on demand"""
        self.container = ttk.Frame(self.parent_frame)
        self.container.pack(fill=tk.X, padx=10, pady=(20, 10))
        
        # Placeholder button
        self.expand_button = ttk.Button(
            self.container,
            text="⚙️ Click to Configure Claude Interleaving Settings",
            command=self._expand_controls
        )
        self.expand_button.pack(fill=tk.X, pady=10)
        
        # Quick status
        self.quick_status = ttk.Label(
            self.container,
            text="Interleaving controls ready - click to expand",
            font=("Arial", 9),
            foreground="gray"
        )
        self.quick_status.pack()
    
    def _expand_controls(self):
        """Expand to show full controls"""
        if not self.controls_created:
            # Remove placeholder
            self.expand_button.destroy()
            self.quick_status.destroy()
            
            # Lazy load config manager
            if self.config_manager is None:
                self.config_manager = get_config_manager()
            
            # Load settings
            self._load_settings()
            
            # Create full controls
            self._create_controls()
            self.controls_created = True
    
    def _load_settings(self):
        """Load current settings"""
        try:
            enabled, locked = self.config_manager.get_global_setting()
            self.global_enabled.set(enabled)
            self.global_locked.set(locked)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.global_enabled.set(True)
            self.global_locked.set(False)
    
    def _create_controls(self):
        """Create simple control interface with correct terminology"""
        # Use existing container
        container = self.container
        
        # IMPORTANT CLARIFICATION
        clarification_frame = ttk.Frame(container)
        clarification_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            clarification_frame,
            text="⚠️ IMPORTANT: Div_AI_Agent_Focus_1 through Div_AI_Agent_Focus_5 are PROJECT FOLDERS (divisions/roles), NOT AI agents!",
            font=("Arial", 10, "bold"),
            foreground="red"
        ).pack(anchor="w")
        
        ttk.Label(
            clarification_frame,
            text="These folders contain tasks/roles. The actual AI agents are: API Key mode, Claude Code, VSCode Agent, etc.",
            font=("Arial", 9),
            foreground="gray"
        ).pack(anchor="w", pady=(2, 0))
        
        # Separator
        ttk.Separator(container, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        # Title with background color for visibility
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame,
            text="Claude Interleaving Settings",
            font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        # Global settings
        global_frame = ttk.LabelFrame(container, text="Global Interleaving Control", padding=10)
        global_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Enable/disable
        enable_frame = ttk.Frame(global_frame)
        enable_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(
            enable_frame,
            text="Enable Claude Interleaving (allows AI to switch contexts)",
            variable=self.global_enabled,
            command=self._on_global_change
        ).pack(side=tk.LEFT)
        
        ttk.Checkbutton(
            enable_frame,
            text="Lock setting",
            variable=self.global_locked,
            command=self._on_lock_change
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # Status display
        self.status_label = ttk.Label(
            global_frame,
            text="",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(anchor="w", pady=(10, 0))
        self._update_status()
        
        # Mode selection
        mode_frame = ttk.LabelFrame(container, text="Interleaving Control Scope", padding=10)
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.control_mode = tk.StringVar(value="global")
        
        modes = [
            ("global", "Global - Apply to all AI agents and tasks"),
            ("per_agent", "Per AI Agent Type - Different settings for API Key, Claude Code, VSCode"),
            ("per_folder", "Per Project Folder - Different settings for Div_AI_Agent_Focus_1, Div_AI_Agent_Focus_2, etc."),
            ("per_task", "Per Task - Override for specific folder:task combinations")
        ]
        
        for value, text in modes:
            ttk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.control_mode,
                value=value,
                command=self._on_mode_change
            ).pack(anchor="w", pady=2)
        
        # Create frames for different modes (initially hidden)
        self.agent_controls_frame = ttk.Frame(container)
        self.folder_controls_frame = ttk.Frame(container)
        self.task_controls_frame = ttk.Frame(container)
        
        # Setup controls for each mode
        self._create_agent_controls()
        self._create_folder_controls()
        self._create_task_controls()
        
        # Show initial mode
        self._on_mode_change()
    
    def _create_agent_controls(self):
        """Create controls for per-AI-agent settings"""
        ttk.Label(
            self.agent_controls_frame,
            text="Configure interleaving for each AI agent type:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Real AI agents
        ai_agents = [
            ("api_key", "API Key AI Agent (Claude, GPT-4, etc.)"),
            ("claude_code", "Claude Code (Standalone subscription)"),
            ("vscode", "VSCode Agent Mode"),
            ("pyautogen", "PyAutoGen/AutoGen Agents")
        ]
        
        for agent_key, agent_name in ai_agents:
            frame = ttk.Frame(self.agent_controls_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{agent_name}:", width=40).pack(side=tk.LEFT)
            
            # Status var
            status_var = tk.StringVar(value="Enabled")
            setattr(self, f"{agent_key}_status", status_var)
            
            ttk.Label(frame, textvariable=status_var, width=15).pack(side=tk.LEFT)
            
            ttk.Button(
                frame,
                text="Configure",
                command=lambda a=agent_key: self._configure_agent(a)
            ).pack(side=tk.LEFT, padx=5)
    
    def _create_folder_controls(self):
        """Create controls for per-project-folder settings"""
        ttk.Label(
            self.folder_controls_frame,
            text="Configure interleaving for each project folder (division/role):",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Project folders
        for i in range(1, 6):
            folder = f"AI_Agent_{i}"
            frame = ttk.Frame(self.folder_controls_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{folder} (Project Folder):", width=25).pack(side=tk.LEFT)
            
            # Status var
            status_var = tk.StringVar(value="Enabled")
            setattr(self, f"{folder}_status", status_var)
            
            ttk.Label(frame, textvariable=status_var, width=15).pack(side=tk.LEFT)
            
            ttk.Button(
                frame,
                text="Configure",
                command=lambda f=folder: self._configure_folder(f)
            ).pack(side=tk.LEFT, padx=5)
            
        # Note about folders
        note_frame = ttk.Frame(self.folder_controls_frame)
        note_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(
            note_frame,
            text="Note: These are project folders containing tasks, not AI agents",
            font=("Arial", 9, "italic"),
            foreground="gray"
        ).pack(anchor="w")
    
    def _create_task_controls(self):
        """Create task-specific control UI with correct labels"""
        # Description
        desc_label = ttk.Label(
            self.task_controls_frame,
            text="Override interleaving for specific project folder + task combinations",
            font=("Arial", 9),
            foreground="gray"
        )
        desc_label.pack(anchor="w", pady=(0, 10))
        
        # Task entry area
        entry_frame = ttk.Frame(self.task_controls_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(entry_frame, text="Project Folder:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.task_folder_var = tk.StringVar()
        folder_combo = ttk.Combobox(
            entry_frame,
            textvariable=self.task_folder_var,
            values=[f"AI_Agent_{i}" for i in range(1, 6)],
            width=15,
            state="readonly"
        )
        folder_combo.pack(side=tk.LEFT, padx=5)
        folder_combo.current(0)
        
        ttk.Label(entry_frame, text="Task ID:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.task_id_var = tk.StringVar()
        task_entry = ttk.Entry(entry_frame, textvariable=self.task_id_var, width=20)
        task_entry.pack(side=tk.LEFT, padx=5)
        
        # Clarify what this means
        ttk.Label(
            self.task_controls_frame,
            text="This controls interleaving for tasks running in the selected project folder",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        # Task control buttons
        button_frame = ttk.Frame(self.task_controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.task_enable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            button_frame,
            text="Enable interleaving for this task",
            variable=self.task_enable_var
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.task_lock_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            button_frame,
            text="Lock",
            variable=self.task_lock_var
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Apply Override",
            command=self._apply_task_override
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Remove Override", 
            command=self._remove_task_override
        ).pack(side=tk.LEFT, padx=5)
        
        # Active overrides display
        overrides_label = ttk.Label(
            self.task_controls_frame,
            text="Active Task Overrides:",
            font=("Arial", 9, "bold")
        )
        overrides_label.pack(anchor="w", pady=(10, 5))
        
        self.overrides_frame = ttk.Frame(self.task_controls_frame)
        self.overrides_frame.pack(fill=tk.X)
        
        self._update_overrides_display()
    
    def _on_mode_change(self):
        """Handle control mode change"""
        mode = self.control_mode.get()
        
        # Hide all frames
        self.agent_controls_frame.pack_forget()
        self.folder_controls_frame.pack_forget() 
        self.task_controls_frame.pack_forget()
        
        # Show selected frame
        if mode == "per_agent":
            self.agent_controls_frame.pack(fill=tk.X, pady=10)
        elif mode == "per_folder":
            self.folder_controls_frame.pack(fill=tk.X, pady=10)
        elif mode == "per_task":
            self.task_controls_frame.pack(fill=tk.X, pady=10)
    
    def _configure_agent(self, agent):
        """Configure settings for a specific AI agent type"""
        messagebox.showinfo("Configure AI Agent", 
                          f"Configure interleaving settings for {agent} AI agent type")
    
    def _configure_folder(self, folder):
        """Configure settings for a specific project folder"""
        messagebox.showinfo("Configure Project Folder", 
                          f"Configure interleaving settings for {folder} project folder")
    
    def _on_global_change(self):
        """Handle global enable/disable change"""
        try:
            enabled = self.global_enabled.get()
            locked = self.global_locked.get()
            self.config_manager.set_global_setting(enabled, locked)
            self._update_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update setting: {e}")
    
    def _on_lock_change(self):
        """Handle lock change"""
        try:
            enabled = self.global_enabled.get()
            locked = self.global_locked.get()
            self.config_manager.set_global_setting(enabled, locked)
            self._update_status()
        except Exception as e:
            print(f"Error changing lock: {e}")
    
    def _update_status(self):
        """Update status display"""
        enabled = self.global_enabled.get()
        locked = self.global_locked.get()
        
        status = "Interleaving is "
        status += "ENABLED" if enabled else "DISABLED"
        if locked:
            status += " (LOCKED)"
        
        self.status_label.config(
            text=status,
            foreground="green" if enabled else "red"
        )
    
    def _apply_task_override(self):
        """Apply task-specific override"""
        folder = self.task_folder_var.get()
        task_id = self.task_id_var.get().strip()
        
        if not task_id:
            messagebox.showwarning("Input Required", "Please enter a Task ID")
            return
        
        try:
            task_key = f"{folder}:{task_id}"
            enabled = self.task_enable_var.get()
            locked = self.task_lock_var.get()
            
            self.config_manager.set_task_override(task_key, enabled, locked)
            messagebox.showinfo("Success", f"Override applied for {task_key}")
            self._update_overrides_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply override: {e}")
    
    def _remove_task_override(self):
        """Remove task-specific override"""
        folder = self.task_folder_var.get()
        task_id = self.task_id_var.get().strip()
        
        if not task_id:
            messagebox.showwarning("Input Required", "Please enter a Task ID")
            return
        
        try:
            task_key = f"{folder}:{task_id}"
            if self.config_manager.remove_task_override(task_key):
                messagebox.showinfo("Success", f"Override removed for {task_key}")
                self._update_overrides_display()
                self.task_id_var.set("")  # Clear task ID
            else:
                messagebox.showwarning("Not Found", f"No override found for {task_key}")
        except Exception as e:
            messagebox.showerror("Error", f"Error removing override: {e}")
    
    def _update_overrides_display(self):
        """Update the display of active overrides"""
        # Clear existing display
        for widget in self.overrides_frame.winfo_children():
            widget.destroy()
        
        try:
            # Get overrides from config manager
            overrides = getattr(self.config_manager, 'get_all_task_overrides', lambda: {})()
            
            if not overrides:
                ttk.Label(
                    self.overrides_frame,
                    text="No active overrides",
                    font=("Arial", 9),
                    foreground="gray"
                ).pack(anchor="w")
            else:
                for task_key, settings in overrides.items():
                    override_line = ttk.Frame(self.overrides_frame)
                    override_line.pack(fill=tk.X, pady=2)
                    
                    status = "Enabled" if settings.get("use_interleaving", True) else "Disabled"
                    if settings.get("locked", False):
                        status += " (Locked)"
                    
                    ttk.Label(
                        override_line,
                        text=f"• {task_key}: {status}",
                        font=("Arial", 9)
                    ).pack(side=tk.LEFT)
        except Exception as e:
            print(f"Error updating overrides display: {e}")


def add_interleaving_to_agent_config(agent_config_frame):
    """Add simple interleaving controls to Agent Configuration tab"""
    return SimpleInterleavingControls(agent_config_frame)

def add_interleaving_controls(agent_config_frame):
    """Alias for add_interleaving_to_agent_config for compatibility"""
    return add_interleaving_to_agent_config(agent_config_frame)