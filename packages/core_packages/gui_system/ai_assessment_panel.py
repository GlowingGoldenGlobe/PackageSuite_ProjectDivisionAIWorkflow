#!/usr/bin/env python3
"""
AI Assessment Panel for GUI
Displays AI assessment controls and recommendations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ai_managers.ai_assessment_controls import get_assessment_controls
except ImportError:
    # Mock for development
    class MockAssessmentControls:
        def assess_session_startup(self, params):
            return {
                "timestamp": datetime.now().isoformat(),
                "session_id": "mock_session",
                "recommendations": {
                    "AI_Agent_1": {"use_interleaving": True, "reason": "Complex 3D modeling"},
                    "AI_Agent_2": {"use_interleaving": False, "reason": "Simple simulation"}
                }
            }
        def get_assessment_summary(self):
            return {"total_sessions": 0, "auto_adjustments_enabled": True}
    
    def get_assessment_controls():
        return MockAssessmentControls()

class AIAssessmentPanel:
    """Panel showing AI assessment controls and status with lazy loading"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.assessment_controls = None  # Lazy load
        self.panel_created = False
        self._create_placeholder()
    
    def _create_placeholder(self):
        """Create lightweight placeholder"""
        self.container = ttk.LabelFrame(self.parent_frame, text="AI Session Assessment & Control", padding=10)
        self.container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Placeholder content
        placeholder_frame = ttk.Frame(self.container)
        placeholder_frame.pack(expand=True)
        
        ttk.Label(
            placeholder_frame,
            text="🤖 AI Assessment Ready",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        self.load_button = ttk.Button(
            placeholder_frame,
            text="Load AI Assessment Controls",
            command=self._load_full_panel
        )
        self.load_button.pack(pady=5)
        
        ttk.Label(
            placeholder_frame,
            text="Click to initialize AI assessment features",
            font=("Arial", 9),
            foreground="gray"
        ).pack()
    
    def _load_full_panel(self):
        """Load the full panel on demand"""
        if not self.panel_created:
            # Clear placeholder
            for widget in self.container.winfo_children():
                widget.destroy()
            
            # Lazy load assessment controls
            if self.assessment_controls is None:
                self.assessment_controls = get_assessment_controls()
            
            # Create full panel
            self._create_panel_content()
            self.panel_created = True
    
    def _create_panel_content(self):
        """Create the actual panel content"""
        # Use existing container
        container = self.container
        
        # Rest of the panel creation code...
        self._create_panel_controls(container)
        self._create_panel_display(container)
    
    def _create_panel_controls(self, container):
        """Create control buttons"""
        # Control buttons
        control_frame = ttk.Frame(container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            control_frame,
            text="Run Startup Assessment",
            command=self._run_startup_assessment
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="View Current Recommendations",
            command=self._show_recommendations
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-adjustment toggle
        self.auto_adjust_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame,
            text="Enable Auto-Adjustments",
            variable=self.auto_adjust_var,
            command=self._toggle_auto_adjust
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_panel_display(self, container):
        """Create display area"""
        # Assessment display area
        display_frame = ttk.Frame(container)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different views
        self.assessment_notebook = ttk.Notebook(display_frame)
        self.assessment_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Startup assessment tab
        startup_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(startup_frame, text="Startup Assessment")
        self._create_startup_view(startup_frame)
        
        # Task completion tab
        completion_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(completion_frame, text="Task Completion Handling")
        self._create_completion_view(completion_frame)
        
        # Resource optimization tab
        resource_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(resource_frame, text="Resource Optimization")
        self._create_resource_view(resource_frame)
    
    def _create_panel(self):
        """Create the assessment panel UI"""
        # Main container
        container = ttk.LabelFrame(self.parent_frame, text="AI Session Assessment & Control", padding=10)
        container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Control buttons
        control_frame = ttk.Frame(container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            control_frame,
            text="Run Startup Assessment",
            command=self._run_startup_assessment
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="View Current Recommendations",
            command=self._show_recommendations
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-adjustment toggle
        self.auto_adjust_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame,
            text="Enable Auto-Adjustments",
            variable=self.auto_adjust_var,
            command=self._toggle_auto_adjust
        ).pack(side=tk.RIGHT, padx=5)
        
        # Assessment display area
        display_frame = ttk.Frame(container)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different views
        self.assessment_notebook = ttk.Notebook(display_frame)
        self.assessment_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Startup assessment tab
        startup_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(startup_frame, text="Startup Assessment")
        self._create_startup_view(startup_frame)
        
        # Task completion tab
        completion_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(completion_frame, text="Task Completion Handling")
        self._create_completion_view(completion_frame)
        
        # Resource optimization tab
        resource_frame = ttk.Frame(self.assessment_notebook)
        self.assessment_notebook.add(resource_frame, text="Resource Optimization")
        self._create_resource_view(resource_frame)
    
    def _create_startup_view(self, parent):
        """Create startup assessment view"""
        # Assessment results
        self.startup_text = scrolledtext.ScrolledText(parent, height=15, width=80, wrap=tk.WORD)
        self.startup_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize with placeholder
        self.startup_text.insert(tk.END, "AI Startup Assessment Results:\n" + "="*50 + "\n\n")
        self.startup_text.insert(tk.END, "Click 'Run Startup Assessment' to analyze session requirements\n")
        self.startup_text.insert(tk.END, "and receive AI recommendations for:\n\n")
        self.startup_text.insert(tk.END, "• Interleaving mode per agent\n")
        self.startup_text.insert(tk.END, "• Resource allocation\n")
        self.startup_text.insert(tk.END, "• Task prioritization\n")
        self.startup_text.insert(tk.END, "• Parallel execution strategy\n")
    
    def _create_completion_view(self, parent):
        """Create task completion handling view"""
        # Instructions
        ttk.Label(
            parent,
            text="AI monitors task completions and makes real-time decisions:",
            font=("Arial", 10, "bold")
        ).pack(pady=10)
        
        # Completion events display
        columns = ("Time", "Agent", "Completed Task", "AI Action", "Reason")
        self.completion_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.completion_tree.heading(col, text=col)
            self.completion_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.completion_tree.yview)
        self.completion_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.completion_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        self._add_sample_completions()
    
    def _create_resource_view(self, parent):
        """Create resource optimization view"""
        # Resource thresholds
        threshold_frame = ttk.LabelFrame(parent, text="Resource Thresholds", padding=10)
        threshold_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # CPU threshold
        cpu_frame = ttk.Frame(threshold_frame)
        cpu_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cpu_frame, text="CPU Threshold:").pack(side=tk.LEFT, padx=(0, 10))
        self.cpu_threshold = tk.Scale(cpu_frame, from_=50, to=95, orient=tk.HORIZONTAL, length=200)
        self.cpu_threshold.set(80)
        self.cpu_threshold.pack(side=tk.LEFT)
        ttk.Label(cpu_frame, text="%").pack(side=tk.LEFT)
        
        # Memory threshold
        mem_frame = ttk.Frame(threshold_frame)
        mem_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mem_frame, text="Memory Threshold:").pack(side=tk.LEFT, padx=(0, 10))
        self.mem_threshold = tk.Scale(mem_frame, from_=50, to=95, orient=tk.HORIZONTAL, length=200)
        self.mem_threshold.set(85)
        self.mem_threshold.pack(side=tk.LEFT)
        ttk.Label(mem_frame, text="%").pack(side=tk.LEFT)
        
        # Optimization actions
        action_frame = ttk.LabelFrame(parent, text="AI Optimization Actions", padding=10)
        action_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.action_text = scrolledtext.ScrolledText(action_frame, height=10, width=60, wrap=tk.WORD)
        self.action_text.pack(fill=tk.BOTH, expand=True)
        
        # Add sample optimization actions
        self.action_text.insert(tk.END, "AI Resource Optimization Log:\n" + "="*40 + "\n\n")
        self.action_text.insert(tk.END, "• When CPU > 80%: Reduce parallel agents\n")
        self.action_text.insert(tk.END, "• When Memory > 85%: Pause low-priority tasks\n")
        self.action_text.insert(tk.END, "• When GPU > 90%: Queue rendering tasks\n")
        self.action_text.insert(tk.END, "• When All resources low: Increase parallelization\n")
    
    def _run_startup_assessment(self):
        """Run AI startup assessment"""
        # Clear previous results
        self.startup_text.delete(1.0, tk.END)
        
        # Get current session parameters (mock data for demo)
        session_params = {
            "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "planned_tasks": [
                {"id": "model_robot_001", "agent": "AI_Agent_1", "priority": "high", 
                 "description": "Create complex 3D micro-robot model with retractable components"},
                {"id": "physics_sim_002", "agent": "AI_Agent_2", "priority": "medium",
                 "description": "Run physics simulation for joint movements"},
                {"id": "optimize_mesh_003", "agent": "AI_Agent_1", "priority": "high",
                 "description": "Optimize mesh geometry for rendering performance"},
                {"id": "generate_docs_004", "agent": "AI_Agent_5", "priority": "low",
                 "description": "Generate technical documentation"},
                {"id": "test_animation_005", "agent": "AI_Agent_4", "priority": "medium",
                 "description": "Test and debug animation sequences"}
            ]
        }
        
        # Run assessment
        assessment = self.assessment_controls.assess_session_startup(session_params)
        
        # Display results
        self.startup_text.insert(tk.END, f"AI Startup Assessment Results\n")
        self.startup_text.insert(tk.END, f"Session ID: {assessment['session_id']}\n")
        self.startup_text.insert(tk.END, f"Timestamp: {assessment['timestamp']}\n")
        self.startup_text.insert(tk.END, "="*60 + "\n\n")
        
        # Display recommendations per agent
        self.startup_text.insert(tk.END, "AGENT RECOMMENDATIONS:\n\n")
        
        for agent, rec in assessment.get("recommendations", {}).items():
            self.startup_text.insert(tk.END, f"{agent}:\n")
            self.startup_text.insert(tk.END, f"  • Interleaving: {'ENABLED' if rec['use_interleaving'] else 'DISABLED'}\n")
            self.startup_text.insert(tk.END, f"  • Reason: {rec['reason']}\n")
            if 'resource_allocation' in rec:
                self.startup_text.insert(tk.END, f"  • Resources: {rec['resource_allocation']['cpu_cores']} cores, "
                                               f"{rec['resource_allocation']['memory_mb']}MB RAM\n")
            if 'priority_tasks' in rec and rec['priority_tasks']:
                self.startup_text.insert(tk.END, f"  • Priority Tasks: {', '.join(rec['priority_tasks'])}\n")
            self.startup_text.insert(tk.END, "\n")
        
        # Display parallel strategy
        if "parallel_strategy" in assessment:
            strategy = assessment["parallel_strategy"]
            self.startup_text.insert(tk.END, "\nPARALLEL EXECUTION STRATEGY:\n")
            self.startup_text.insert(tk.END, f"  • Max Parallel Agents: {strategy['max_parallel']}\n")
            self.startup_text.insert(tk.END, f"  • Execution Order: {' → '.join(strategy['execution_order'])}\n")
            self.startup_text.insert(tk.END, f"  • Resource Sharing: {strategy['resource_sharing']}\n")
        
        # Highlight important decisions
        self.startup_text.tag_add("highlight", "1.0", "4.0")
        self.startup_text.tag_config("highlight", background="yellow")
    
    def _show_recommendations(self):
        """Show current AI recommendations"""
        from tkinter import messagebox
        summary = self.assessment_controls.get_assessment_summary()
        
        msg = "Current AI Assessment Status:\n\n"
        msg += f"Total Sessions Assessed: {summary['total_sessions']}\n"
        msg += f"Auto-Adjustments: {'Enabled' if summary['auto_adjustments_enabled'] else 'Disabled'}\n\n"
        
        if summary.get('recent_assessments'):
            msg += "Recent Assessment Decisions:\n"
            for assess in summary['recent_assessments'][-3:]:
                msg += f"• {assess.get('session_id', 'Unknown')}: "
                msg += f"{len(assess.get('recommendations', {}))} agents configured\n"
        
        messagebox.showinfo("AI Recommendations", msg)
    
    def _toggle_auto_adjust(self):
        """Toggle auto-adjustment setting"""
        enabled = self.auto_adjust_var.get()
        # Update configuration
        print(f"Auto-adjustments {'enabled' if enabled else 'disabled'}")
    
    def _add_sample_completions(self):
        """Add sample completion events"""
        sample_events = [
            ("10:15:23", "AI_Agent_1", "model_robot_001", "Reassign", "High priority task waiting"),
            ("10:22:45", "AI_Agent_3", "utility_task_002", "Redistribute", "Help overloaded AI_Agent_2"),
            ("10:28:12", "AI_Agent_4", "test_task_003", "Optimize", "Increase parallel capacity"),
            ("10:35:07", "AI_Agent_2", "physics_sim_004", "None", "No urgent tasks pending"),
        ]
        
        for event in sample_events:
            self.completion_tree.insert('', 'end', values=event)


def add_ai_assessment_panel(parent_frame):
    """Add AI assessment panel to a frame"""
    return AIAssessmentPanel(parent_frame)