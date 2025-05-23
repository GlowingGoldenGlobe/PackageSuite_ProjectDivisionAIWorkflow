#!/usr/bin/env python3
"""
Simplified interleaving controls for Agent Configuration tab
Focuses on core functionality without complex layouts
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
    """Simplified interleaving controls with lazy loading"""
    
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
        """Create simple control interface"""
        # Use existing container
        container = self.container
        
        # Debug: Make sure container is visible
        print(f"[DEBUG] Creating interleaving controls in {self.parent_frame}")
        
        # Separator
        ttk.Separator(container, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        # Title with background color for visibility
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=tk.X)
        
        # Add a colored label to make it very visible
        title_label = ttk.Label(
            title_frame,
            text="🔧 Claude Interleaving Settings",
            font=("Arial", 14, "bold"),
            foreground="blue"
        )
        title_label.pack(side=tk.LEFT)
        
        # Add test button to verify controls are working
        ttk.Button(
            title_frame,
            text="Test",
            command=lambda: print("[TEST] Interleaving controls are active!")
        ).pack(side=tk.RIGHT, padx=5)
        
        # Description
        ttk.Label(
            container,
            text="Enable tool interleaving with extended thinking for better optimization and debugging",
            font=("Arial", 9),
            foreground="gray"
        ).pack(anchor="w", pady=(5, 10))
        
        # Main controls frame
        controls_frame = ttk.LabelFrame(container, text="Global Settings", padding=10)
        controls_frame.pack(fill=tk.X, pady=5)
        
        # Enable checkbox
        self.enable_check = ttk.Checkbutton(
            controls_frame,
            text="Enable Claude Interleaving",
            variable=self.global_enabled,
            command=self._on_enable_change
        )
        self.enable_check.pack(anchor="w", pady=2)
        
        # Lock checkbox
        self.lock_check = ttk.Checkbutton(
            controls_frame,
            text="Lock setting (prevent automated changes)",
            variable=self.global_locked,
            command=self._on_lock_change
        )
        self.lock_check.pack(anchor="w", padx=20, pady=2)
        
        # Status
        self.status_label = ttk.Label(
            controls_frame,
            text="",
            font=("Arial", 9)
        )
        self.status_label.pack(anchor="w", pady=(10, 0))
        
        # Agent-specific section
        agent_frame = ttk.LabelFrame(container, text="Per-Agent Status", padding=10)
        agent_frame.pack(fill=tk.X, pady=10)
        
        # Simple agent status display
        agent_info = ttk.Frame(agent_frame)
        agent_info.pack(fill=tk.X)
        
        for i in range(1, 6):
            agent = f"AI_Agent_{i}"
            agent_line = ttk.Frame(agent_info)
            agent_line.pack(fill=tk.X, pady=2)
            
            ttk.Label(agent_line, text=f"{agent}:", width=12).pack(side=tk.LEFT)
            
            # Status indicator
            status_var = tk.StringVar()
            status_label = ttk.Label(agent_line, textvariable=status_var, width=20)
            status_label.pack(side=tk.LEFT, padx=10)
            
            # Store for updates
            setattr(self, f"{agent}_status", status_var)
            
            # Update status
            self._update_agent_status(agent)
        
        # Task-specific controls section
        task_frame = ttk.LabelFrame(container, text="Task-Level Control", padding=10)
        task_frame.pack(fill=tk.X, pady=10)
        
        # Control mode selection
        mode_frame = ttk.Frame(task_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="Control Mode:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.control_mode = tk.StringVar(value="session")
        ttk.Radiobutton(
            mode_frame,
            text="Session-Level (Option 1)",
            variable=self.control_mode,
            value="session",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="Task-Level (Option 2)",
            variable=self.control_mode,
            value="task",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        # Task override controls
        self.task_controls_frame = ttk.Frame(task_frame)
        self.task_controls_frame.pack(fill=tk.X)
        
        # Create task control UI
        self._create_task_controls()
        
        # Update visibility based on mode
        self._on_mode_change()
        
        # Info section
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            info_frame,
            text="ℹ️ When enabled, agents will use direct Claude API with enhanced capabilities",
            font=("Arial", 8),
            foreground="blue"
        ).pack(anchor="w")
        
        ttk.Label(
            info_frame,
            text="🔒 Lock prevents AI workflow from changing this setting automatically",
            font=("Arial", 8),
            foreground="darkgreen"
        ).pack(anchor="w", pady=(2, 0))
        
        # Update global status
        self._update_status()
    
    def _on_enable_change(self):
        """Handle enable/disable change"""
        try:
            enabled = self.global_enabled.get()
            locked = self.global_locked.get()
            
            if self.config_manager.set_global_setting(enabled, locked):
                self._update_status()
                # Update all agent statuses
                for i in range(1, 6):
                    self._update_agent_status(f"AI_Agent_{i}")
            else:
                messagebox.showwarning("Locked", "Cannot change locked setting")
                self._load_settings()
        except Exception as e:
            print(f"Error changing setting: {e}")
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
    
    def _update_agent_status(self, agent):
        """Update individual agent status"""
        try:
            enabled, locked = self.config_manager.get_agent_setting(agent)
            
            # Get the status variable
            status_var = getattr(self, f"{agent}_status", None)
            if status_var:
                status_text = "Enabled" if enabled else "Disabled"
                if locked:
                    status_text += " (Locked)"
                status_var.set(status_text)
        except Exception as e:
            print(f"Error updating {agent} status: {e}")
    
    def _create_task_controls(self):
        """Create task-specific control UI"""
        # Description
        desc_label = ttk.Label(
            self.task_controls_frame,
            text="When in Task-Level mode, you can override settings for specific agent:task combinations",
            font=("Arial", 9),
            foreground="gray"
        )
        desc_label.pack(anchor="w", pady=(0, 10))
        
        # Task entry area
        entry_frame = ttk.Frame(self.task_controls_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(entry_frame, text="Agent:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.task_agent_var = tk.StringVar()
        agent_combo = ttk.Combobox(
            entry_frame,
            textvariable=self.task_agent_var,
            values=[f"AI_Agent_{i}" for i in range(1, 6)],
            width=15,
            state="readonly"
        )
        agent_combo.pack(side=tk.LEFT, padx=5)
        agent_combo.current(0)
        
        ttk.Label(entry_frame, text="Task ID:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.task_id_var = tk.StringVar()
        task_entry = ttk.Entry(entry_frame, textvariable=self.task_id_var, width=20)
        task_entry.pack(side=tk.LEFT, padx=5)
        
        # Task control buttons
        button_frame = ttk.Frame(self.task_controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.task_enable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            button_frame,
            text="Enable for this task",
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
        
        # Overrides list
        self.overrides_frame = ttk.Frame(self.task_controls_frame)
        self.overrides_frame.pack(fill=tk.X)
        
        self._update_overrides_display()
    
    def _on_mode_change(self):
        """Handle control mode change"""
        mode = self.control_mode.get()
        if mode == "task":
            # Show task controls
            for widget in self.task_controls_frame.winfo_children():
                widget.pack_configure()
        else:
            # Hide task controls
            for widget in self.task_controls_frame.winfo_children():
                widget.pack_forget()
    
    def _apply_task_override(self):
        """Apply task-specific override"""
        agent = self.task_agent_var.get()
        task_id = self.task_id_var.get().strip()
        
        if not task_id:
            messagebox.showwarning("Missing Task ID", "Please enter a task ID")
            return
        
        enabled = self.task_enable_var.get()
        locked = self.task_lock_var.get()
        
        try:
            # Set task override using config manager
            task_key = f"{agent}:{task_id}"
            success = self.config_manager.set_task_override(task_key, enabled, locked)
            
            if success:
                messagebox.showinfo("Success", f"Override applied for {task_key}")
                self._update_overrides_display()
                self.task_id_var.set("")  # Clear task ID
            else:
                messagebox.showerror("Error", "Failed to apply override")
        except Exception as e:
            messagebox.showerror("Error", f"Error applying override: {e}")
    
    def _remove_task_override(self):
        """Remove task-specific override"""
        agent = self.task_agent_var.get()
        task_id = self.task_id_var.get().strip()
        
        if not task_id:
            messagebox.showwarning("Missing Task ID", "Please enter a task ID")
            return
        
        try:
            task_key = f"{agent}:{task_id}"
            success = self.config_manager.remove_task_override(task_key)
            
            if success:
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