"""
ROS2 Dashboard Integration

This module integrates ROS2 functionality with the visualization dashboard.
"""

import os
import sys
import time
import threading
import queue
import logging
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Set

from ros2_integration.ros2_bridge import (
    ROS2Bridge, ComponentCommunicator,
    CommunicationType, MessagePriority, ROS2Message
)
from ros2_integration.message_types import (
    ComponentType, MotionType, SensorType, ActuatorType, CoordinationType,
    ComponentState, MotionCommand, SensorData, ActuatorCommand,
    JointConfiguration, InterfaceSettings, TaskAssignment,
    CoordinationMessage, SimulationControl, PhysicalProperties,
    PowerState, ErrorMessage
)
from ros2_integration.component_interface import ComponentStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ros2_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ROS2DashboardIntegration:
    """Integration of ROS2 with the visualization dashboard"""
    
    def __init__(self, parent_frame, dashboard=None, status_callback=None):
        """
        Initialize ROS2 dashboard integration.
        
        Args:
            parent_frame: The tkinter frame to add the ROS2 UI to
            dashboard: Optional reference to the main dashboard
            status_callback: Optional callback for status updates
        """
        self.parent = parent_frame
        self.dashboard = dashboard
        self.status_callback = status_callback
        
        # ROS2 bridges and communicators
        self.bridges = {}
        self.communicators = {}
        
        # Component states
        self.component_states = {}
        
        # UI elements
        self.ros2_frame = None
        self.component_treeview = None
        self.message_list = None
        self.status_label = None
        
        # Message history
        self.message_history = []
        self.max_history_size = 100
        
        # Task queue for background operations
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.running = True
        
        # Initialize the UI
        self.setup_ui()
        
        # Start background worker
        self.start_worker_thread()
    
    def setup_ui(self):
        """Set up the ROS2 integration UI"""
        # Create main frame
        self.ros2_frame = ttk.LabelFrame(self.parent, text="ROS2 Integration")
        self.ros2_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top frame for controls
        top_frame = ttk.Frame(self.ros2_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add component button
        ttk.Button(
            top_frame, 
            text="Add Component", 
            command=self.show_add_component_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        # Send command button
        ttk.Button(
            top_frame, 
            text="Send Command", 
            command=self.show_send_command_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        # View messages button
        ttk.Button(
            top_frame, 
            text="View Messages", 
            command=self.show_message_viewer
        ).pack(side=tk.LEFT, padx=5)
        
        # Create paned window for components and messages
        paned_window = ttk.PanedWindow(self.ros2_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create component treeview
        tree_frame = ttk.LabelFrame(paned_window, text="Components")
        paned_window.add(tree_frame, weight=1)
        
        # Create treeview with scrollbar
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tree_scroll = ttk.Scrollbar(tree_container)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.component_treeview = ttk.Treeview(
            tree_container,
            columns=("Type", "Status", "Position"),
            show="headings",
            selectmode="browse",
            yscrollcommand=tree_scroll.set
        )
        self.component_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.component_treeview.yview)
        
        # Set up columns
        self.component_treeview.heading("Type", text="Type")
        self.component_treeview.heading("Status", text="Status")
        self.component_treeview.heading("Position", text="Position")
        
        self.component_treeview.column("Type", width=100)
        self.component_treeview.column("Status", width=100)
        self.component_treeview.column("Position", width=150)
        
        # Add context menu to treeview
        self.setup_component_context_menu()
        
        # Create message list
        message_frame = ttk.LabelFrame(paned_window, text="Recent Messages")
        paned_window.add(message_frame, weight=1)
        
        # Create message list with scrollbar
        message_container = ttk.Frame(message_frame)
        message_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        message_scroll = ttk.Scrollbar(message_container)
        message_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.message_list = tk.Listbox(
            message_container,
            yscrollcommand=message_scroll.set
        )
        self.message_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        message_scroll.config(command=self.message_list.yview)
        
        # Status frame at the bottom
        status_frame = ttk.Frame(self.ros2_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def setup_component_context_menu(self):
        """Set up the context menu for the component treeview"""
        component_menu = tk.Menu(self.component_treeview, tearoff=0)
        
        component_menu.add_command(label="View Details", command=self.view_component_details)
        component_menu.add_command(label="Remove Component", command=self.remove_component)
        component_menu.add_separator()
        component_menu.add_command(label="Send Command", command=self.send_command_to_selected)
        component_menu.add_command(label="View Messages", command=self.view_messages_for_selected)
        
        # Bind right-click to open context menu
        def show_context_menu(event):
            item = self.component_treeview.identify_row(event.y)
            if item:
                self.component_treeview.selection_set(item)
                component_menu.post(event.x_root, event.y_root)
        
        self.component_treeview.bind("<Button-3>", show_context_menu)
    
    def update_status(self, message: str):
        """Update the status label with a message"""
        if self.status_label:
            self.status_label.config(text=message)
        
        if self.status_callback:
            self.status_callback(message)
        
        logger.info(message)
    
    def show_add_component_dialog(self):
        """Show dialog for adding a new component"""
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add ROS2 Component")
        dialog.geometry("400x300")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Component ID
        ttk.Label(frame, text="Component ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        component_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=component_id_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Component type
        ttk.Label(frame, text="Component Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        component_type_var = tk.StringVar(value=ComponentType.SPHERE.value)
        ttk.Combobox(
            frame,
            textvariable=component_type_var,
            values=[t.value for t in ComponentType],
            state="readonly"
        ).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Create mock
        ttk.Label(frame, text="Use Mock ROS2:").grid(row=2, column=0, sticky=tk.W, pady=2)
        use_mock_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, variable=use_mock_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Initial position
        ttk.Label(frame, text="Initial Position:").grid(row=3, column=0, sticky=tk.W, pady=2)
        
        pos_frame = ttk.Frame(frame)
        pos_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(pos_frame, text="X:").pack(side=tk.LEFT)
        pos_x_var = tk.StringVar(value="0.0")
        ttk.Entry(pos_frame, textvariable=pos_x_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(pos_frame, text="Y:").pack(side=tk.LEFT, padx=(5, 0))
        pos_y_var = tk.StringVar(value="0.0")
        ttk.Entry(pos_frame, textvariable=pos_y_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(pos_frame, text="Z:").pack(side=tk.LEFT, padx=(5, 0))
        pos_z_var = tk.StringVar(value="0.0")
        ttk.Entry(pos_frame, textvariable=pos_z_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Create button frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Add Component",
            command=lambda: self._add_component(
                dialog,
                component_id_var.get(),
                component_type_var.get(),
                use_mock_var.get(),
                [float(pos_x_var.get()), float(pos_y_var.get()), float(pos_z_var.get())]
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _add_component(
        self,
        dialog: tk.Toplevel,
        component_id: str,
        component_type_str: str,
        use_mock: bool,
        position: List[float]
    ):
        """
        Add a new ROS2 component.
        
        Args:
            dialog: Dialog to close
            component_id: Component ID
            component_type_str: Component type string
            use_mock: Whether to use mock ROS2
            position: Initial position [x, y, z]
        """
        # Validate component ID
        if not component_id:
            messagebox.showerror("Error", "Component ID is required")
            return
        
        # Check if component already exists
        if component_id in self.communicators:
            messagebox.showerror("Error", f"Component {component_id} already exists")
            return
        
        try:
            # Parse component type
            component_type = None
            for ct in ComponentType:
                if ct.value == component_type_str:
                    component_type = ct
                    break
            
            if not component_type:
                messagebox.showerror("Error", f"Invalid component type: {component_type_str}")
                return
            
            # Create initial state
            initial_state = {
                "position": position,
                "status": "ready",
                "active": True,
                "timestamp": time.time()
            }
            
            # Close dialog
            dialog.destroy()
            
            # Add component in background
            self.add_task(
                self._add_component_task,
                component_id,
                component_type,
                use_mock,
                initial_state
            )
            
            # Update status
            self.update_status(f"Adding component {component_id}...")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding component: {e}")
    
    def _add_component_task(
        self,
        component_id: str,
        component_type: ComponentType,
        use_mock: bool,
        initial_state: Dict[str, Any]
    ):
        """
        Background task for adding a component.
        
        Args:
            component_id: Component ID
            component_type: Component type
            use_mock: Whether to use mock ROS2
            initial_state: Initial component state
        """
        try:
            # Create ROS2 bridge
            bridge = ROS2Bridge(
                node_name=f"{component_type.value}_{component_id}",
                use_mock=use_mock
            )
            
            # Create communicator
            communicator = ComponentCommunicator(
                component_id=component_id,
                component_type=component_type.value,
                bridge=bridge
            )
            
            # Store bridge and communicator
            self.bridges[component_id] = bridge
            self.communicators[component_id] = communicator
            
            # Set up message handlers
            self._register_message_handlers(component_id, communicator)
            
            # Create initial component state
            component_state = ComponentState(
                component_id=component_id,
                component_type=component_type.value,
                timestamp=time.time()
            )
            
            # Update with initial values
            for key, value in initial_state.items():
                if hasattr(component_state, key):
                    setattr(component_state, key, value)
            
            # Store component state
            self.component_states[component_id] = component_state
            
            # Start bridge
            bridge.start()
            
            # Add to UI
            self.parent.after(0, lambda: self._add_component_to_ui(component_id, component_state))
            
            # Update status
            self.parent.after(0, lambda: self.update_status(f"Added component {component_id}"))
        except Exception as e:
            # Show error
            error_msg = f"Error adding component {component_id}: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Error adding component"))
            logger.error(error_msg)
    
    def _register_message_handlers(self, component_id: str, communicator: ComponentCommunicator):
        """
        Register message handlers for a component.
        
        Args:
            component_id: Component ID
            communicator: Component communicator
        """
        # Register telemetry handler for state updates
        communicator.register_telemetry_handler(
            "state",
            lambda _, values: self._handle_state_update(component_id, values)
        )
        
        # Register telemetry handler for sensor data
        communicator.register_telemetry_handler(
            "sensor",
            lambda _, values: self._handle_sensor_data(component_id, values)
        )
        
        # Register telemetry handler for errors
        communicator.register_telemetry_handler(
            "error",
            lambda _, values: self._handle_error(component_id, values)
        )
        
        # Register coordination handler for coordination messages
        communicator.register_coordination_handler(
            "coordination",
            lambda _, action, params, message: self._handle_coordination(
                component_id, action, params, message
            )
        )
    
    def _handle_state_update(self, component_id: str, state_data: Dict[str, Any]):
        """
        Handle a state update from a component.
        
        Args:
            component_id: Component ID
            state_data: State data
        """
        try:
            # Parse component state
            component_state = ComponentState.from_dict(state_data)
            
            # Update stored state
            self.component_states[component_id] = component_state
            
            # Add to message history
            self._add_message_to_history(
                component_id,
                "state",
                f"Status: {component_state.status}, Pos: {component_state.position}"
            )
            
            # Update UI
            self.parent.after(0, lambda: self._update_component_in_ui(component_id, component_state))
        except Exception as e:
            logger.error(f"Error handling state update from {component_id}: {e}")
    
    def _handle_sensor_data(self, component_id: str, sensor_data: Dict[str, Any]):
        """
        Handle sensor data from a component.
        
        Args:
            component_id: Component ID
            sensor_data: Sensor data
        """
        try:
            # Parse sensor data
            sensor = SensorData.from_dict(sensor_data)
            
            # Add to message history
            self._add_message_to_history(
                component_id,
                "sensor",
                f"{sensor.sensor_type}: {len(sensor.values)} values"
            )
            
            # Update UI
            self.parent.after(0, self._update_message_list)
        except Exception as e:
            logger.error(f"Error handling sensor data from {component_id}: {e}")
    
    def _handle_error(self, component_id: str, error_data: Dict[str, Any]):
        """
        Handle an error from a component.
        
        Args:
            component_id: Component ID
            error_data: Error data
        """
        try:
            # Parse error message
            error = ErrorMessage.from_dict(error_data)
            
            # Add to message history
            self._add_message_to_history(
                component_id,
                "error",
                f"{error.error_type}: {error.error_message}"
            )
            
            # Update UI
            self.parent.after(0, self._update_message_list)
            
            # Show error dialog for critical errors
            if error.severity == "critical":
                self.parent.after(0, lambda: messagebox.showerror(
                    "Critical Error",
                    f"Component {component_id} reported a critical error:\n{error.error_message}"
                ))
        except Exception as e:
            logger.error(f"Error handling error from {component_id}: {e}")
    
    def _handle_coordination(
        self,
        component_id: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle a coordination message from a component.
        
        Args:
            component_id: Component ID
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        try:
            # Add to message history
            self._add_message_to_history(
                component_id,
                "coordination",
                f"{action}: {len(params)} params"
            )
            
            # Update UI
            self.parent.after(0, self._update_message_list)
        except Exception as e:
            logger.error(f"Error handling coordination from {component_id}: {e}")
    
    def _add_component_to_ui(self, component_id: str, state: ComponentState):
        """
        Add a component to the UI.
        
        Args:
            component_id: Component ID
            state: Component state
        """
        # Add to treeview
        self.component_treeview.insert(
            "",
            "end",
            component_id,
            values=(
                state.component_type,
                state.status,
                f"[{state.position[0]:.1f}, {state.position[1]:.1f}, {state.position[2]:.1f}]"
            )
        )
        
        # Update message list
        self._update_message_list()
    
    def _update_component_in_ui(self, component_id: str, state: ComponentState):
        """
        Update a component in the UI.
        
        Args:
            component_id: Component ID
            state: Component state
        """
        # Update treeview
        self.component_treeview.item(
            component_id,
            values=(
                state.component_type,
                state.status,
                f"[{state.position[0]:.1f}, {state.position[1]:.1f}, {state.position[2]:.1f}]"
            )
        )
    
    def _add_message_to_history(self, component_id: str, message_type: str, content: str):
        """
        Add a message to the history.
        
        Args:
            component_id: Component ID
            message_type: Message type
            content: Message content
        """
        # Create message entry
        message_entry = {
            "component_id": component_id,
            "type": message_type,
            "content": content,
            "timestamp": time.time()
        }
        
        # Add to history
        self.message_history.append(message_entry)
        
        # Trim history if needed
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def _update_message_list(self):
        """Update the message list in the UI"""
        # Clear list
        self.message_list.delete(0, tk.END)
        
        # Add messages in reverse order (newest first)
        for message in reversed(self.message_history):
            timestamp = time.strftime("%H:%M:%S", time.localtime(message["timestamp"]))
            self.message_list.insert(
                tk.END,
                f"{timestamp} | {message['component_id']} | {message['type']} | {message['content']}"
            )
    
    def view_component_details(self):
        """View details for the selected component"""
        # Get selected component
        selected = self.component_treeview.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a component")
            return
        
        component_id = selected[0]
        
        # Check if component exists
        if component_id not in self.component_states:
            messagebox.showerror("Error", f"Component {component_id} not found")
            return
        
        # Get component state
        state = self.component_states[component_id]
        
        # Create details dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Component Details: {component_id}")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Component ID and type
        ttk.Label(
            frame, 
            text=f"Component: {component_id} ({state.component_type})",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # State tab
        state_frame = ttk.Frame(notebook, padding=5)
        notebook.add(state_frame, text="State")
        
        # Grid layout for state info
        ttk.Label(state_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(state_frame, text=state.status).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Position:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            state_frame, 
            text=f"[{state.position[0]:.2f}, {state.position[1]:.2f}, {state.position[2]:.2f}]"
        ).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Orientation:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            state_frame, 
            text=f"[{state.orientation[0]:.2f}, {state.orientation[1]:.2f}, "
                 f"{state.orientation[2]:.2f}, {state.orientation[3]:.2f}]"
        ).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Velocity:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            state_frame, 
            text=f"[{state.velocity[0]:.2f}, {state.velocity[1]:.2f}, {state.velocity[2]:.2f}]"
        ).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Angular Velocity:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            state_frame, 
            text=f"[{state.angular_velocity[0]:.2f}, {state.angular_velocity[1]:.2f}, "
                 f"{state.angular_velocity[2]:.2f}]"
        ).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Battery Level:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Label(state_frame, text=f"{state.battery_level:.1f}%").grid(row=5, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Temperature:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Label(state_frame, text=f"{state.temperature:.1f}°C").grid(row=6, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Active:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Label(state_frame, text=str(state.active)).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(state_frame, text="Last Update:").grid(row=8, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            state_frame, 
            text=time.strftime("%H:%M:%S", time.localtime(state.timestamp))
        ).grid(row=8, column=1, sticky=tk.W, pady=2)
        
        # Connections tab
        connections_frame = ttk.Frame(notebook, padding=5)
        notebook.add(connections_frame, text="Connections")
        
        # List of connected components
        ttk.Label(connections_frame, text="Connected Components:").pack(anchor=tk.W, pady=(0, 5))
        
        connections_list = tk.Listbox(connections_frame)
        connections_list.pack(fill=tk.BOTH, expand=True)
        
        for connected_id in state.connected_components:
            connections_list.insert(tk.END, connected_id)
        
        # Messages tab
        messages_frame = ttk.Frame(notebook, padding=5)
        notebook.add(messages_frame, text="Messages")
        
        # List of messages for this component
        ttk.Label(messages_frame, text="Recent Messages:").pack(anchor=tk.W, pady=(0, 5))
        
        messages_list = tk.Listbox(messages_frame)
        messages_list.pack(fill=tk.BOTH, expand=True)
        
        for message in reversed(self.message_history):
            if message["component_id"] == component_id:
                timestamp = time.strftime("%H:%M:%S", time.localtime(message["timestamp"]))
                messages_list.insert(
                    tk.END,
                    f"{timestamp} | {message['type']} | {message['content']}"
                )
        
        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=dialog.destroy
        ).pack(pady=(10, 0))
    
    def remove_component(self):
        """Remove the selected component"""
        # Get selected component
        selected = self.component_treeview.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a component")
            return
        
        component_id = selected[0]
        
        # Confirm removal
        if not messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove component {component_id}?"
        ):
            return
        
        # Remove component in background
        self.add_task(self._remove_component_task, component_id)
        
        # Update status
        self.update_status(f"Removing component {component_id}...")
    
    def _remove_component_task(self, component_id: str):
        """
        Background task for removing a component.
        
        Args:
            component_id: Component ID to remove
        """
        try:
            # Check if component exists
            if component_id not in self.communicators:
                self.parent.after(0, lambda: messagebox.showerror(
                    "Error", f"Component {component_id} not found"
                ))
                return
            
            # Stop bridge
            if component_id in self.bridges:
                self.bridges[component_id].stop()
            
            # Clean up
            if component_id in self.communicators:
                del self.communicators[component_id]
            
            if component_id in self.bridges:
                del self.bridges[component_id]
            
            if component_id in self.component_states:
                del self.component_states[component_id]
            
            # Remove from UI
            self.parent.after(0, lambda: self.component_treeview.delete(component_id))
            
            # Update status
            self.parent.after(0, lambda: self.update_status(f"Removed component {component_id}"))
        except Exception as e:
            # Show error
            error_msg = f"Error removing component {component_id}: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Error removing component"))
            logger.error(error_msg)
    
    def send_command_to_selected(self):
        """Send a command to the selected component"""
        # Get selected component
        selected = self.component_treeview.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a component")
            return
        
        component_id = selected[0]
        
        # Show send command dialog
        self.show_send_command_dialog(component_id)
    
    def show_send_command_dialog(self, target_id: Optional[str] = None):
        """
        Show dialog for sending a command.
        
        Args:
            target_id: Optional target component ID
        """
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Send Command")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Target component
        ttk.Label(frame, text="Target Component:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        target_var = tk.StringVar(value=target_id if target_id else "")
        
        if target_id:
            # Fixed target
            ttk.Label(frame, text=target_id).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        else:
            # Dropdown of available components
            ttk.Combobox(
                frame,
                textvariable=target_var,
                values=list(self.communicators.keys()),
                state="readonly"
            ).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Command type
        ttk.Label(frame, text="Command Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        command_type_var = tk.StringVar(value="motion")
        ttk.Combobox(
            frame,
            textvariable=command_type_var,
            values=["motion", "configure", "query", "task"],
            state="readonly"
        ).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Parameter editor
        ttk.Label(frame, text="Parameters (JSON):").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        param_text = scrolledtext.ScrolledText(frame, height=10)
        param_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)
        param_text.insert(tk.END, "{\n  \n}")
        
        # Priority
        ttk.Label(frame, text="Priority:").grid(row=4, column=0, sticky=tk.W, pady=2)
        priority_var = tk.StringVar(value="NORMAL")
        ttk.Combobox(
            frame,
            textvariable=priority_var,
            values=["LOW", "NORMAL", "HIGH", "CRITICAL"],
            state="readonly"
        ).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Templates for different command types
        def update_template(*args):
            command_type = command_type_var.get()
            
            if command_type == "motion":
                param_text.delete("1.0", tk.END)
                param_text.insert(tk.END, json.dumps({
                    "target_position": [0.0, 0.0, 0.0],
                    "motion_type": "linear",
                    "duration": 1.0
                }, indent=2))
            elif command_type == "configure":
                param_text.delete("1.0", tk.END)
                param_text.insert(tk.END, json.dumps({
                    "status": "active",
                    "connected_components": []
                }, indent=2))
            elif command_type == "query":
                param_text.delete("1.0", tk.END)
                param_text.insert(tk.END, json.dumps({
                    "type": "state"
                }, indent=2))
            elif command_type == "task":
                param_text.delete("1.0", tk.END)
                param_text.insert(tk.END, json.dumps({
                    "task_id": f"task_{int(time.time())}",
                    "task_type": "move_to",
                    "assigned_components": [],
                    "priority": 1,
                    "parameters": {
                        "target_position": [0.0, 0.0, 0.0]
                    }
                }, indent=2))
        
        # Register template updater
        command_type_var.trace_add("write", update_template)
        
        # Update template initially
        update_template()
        
        # Create button frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Send Command",
            command=lambda: self._send_command(
                dialog,
                target_var.get(),
                command_type_var.get(),
                param_text.get("1.0", tk.END),
                priority_var.get()
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)
    
    def _send_command(
        self,
        dialog: tk.Toplevel,
        target_id: str,
        command_type: str,
        param_json: str,
        priority_str: str
    ):
        """
        Send a command to a component.
        
        Args:
            dialog: Dialog to close
            target_id: Target component ID
            command_type: Command type
            param_json: Parameter JSON
            priority_str: Priority string
        """
        # Validate target
        if not target_id:
            messagebox.showerror("Error", "Target component is required")
            return
        
        # Check if target exists
        if target_id not in self.communicators:
            messagebox.showerror("Error", f"Component {target_id} not found")
            return
        
        try:
            # Parse parameters
            params = json.loads(param_json)
            
            # Parse priority
            priority = MessagePriority.NORMAL
            for p in MessagePriority:
                if p.name == priority_str:
                    priority = p
                    break
            
            # Close dialog
            dialog.destroy()
            
            # Send command in background
            self.add_task(
                self._send_command_task,
                target_id,
                command_type,
                params,
                priority
            )
            
            # Update status
            self.update_status(f"Sending {command_type} command to {target_id}...")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error sending command: {e}")
    
    def _send_command_task(
        self,
        target_id: str,
        command_type: str,
        params: Dict[str, Any],
        priority: MessagePriority
    ):
        """
        Background task for sending a command.
        
        Args:
            target_id: Target component ID
            command_type: Command type
            params: Command parameters
            priority: Message priority
        """
        try:
            # Get communicator
            communicator = self.communicators.get(target_id)
            if not communicator:
                raise ValueError(f"Component {target_id} not found")
            
            # Send command
            success = communicator.send_command(
                target_id=target_id,
                command=command_type,
                params=params,
                priority=priority
            )
            
            # Add to message history
            self._add_message_to_history(
                communicator.component_id,
                "command",
                f"{command_type}: {len(params)} params"
            )
            
            # Update UI
            self.parent.after(0, self._update_message_list)
            
            # Update status
            if success:
                self.parent.after(0, lambda: self.update_status(
                    f"Sent {command_type} command to {target_id}"
                ))
            else:
                self.parent.after(0, lambda: self.update_status(
                    f"Failed to send {command_type} command to {target_id}"
                ))
        except Exception as e:
            # Show error
            error_msg = f"Error sending command to {target_id}: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Error sending command"))
            logger.error(error_msg)
    
    def view_messages_for_selected(self):
        """View messages for the selected component"""
        # Get selected component
        selected = self.component_treeview.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a component")
            return
        
        component_id = selected[0]
        
        # Show message viewer for this component
        self.show_message_viewer(component_id)
    
    def show_message_viewer(self, component_id: Optional[str] = None):
        """
        Show message viewer dialog.
        
        Args:
            component_id: Optional component ID to filter for
        """
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        
        if component_id:
            dialog.title(f"Messages for {component_id}")
        else:
            dialog.title("Message Viewer")
        
        dialog.geometry("700x500")
        dialog.resizable(True, True)
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Filter controls
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Component filter
        ttk.Label(filter_frame, text="Component:").pack(side=tk.LEFT, padx=(0, 5))
        
        component_var = tk.StringVar(value=component_id if component_id else "All")
        component_combo = ttk.Combobox(
            filter_frame,
            textvariable=component_var,
            values=["All"] + list(self.communicators.keys()),
            state="readonly",
            width=15
        )
        component_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Message type filter
        ttk.Label(filter_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        
        type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(
            filter_frame,
            textvariable=type_var,
            values=["All", "state", "command", "sensor", "error", "coordination"],
            state="readonly",
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Limit filter
        ttk.Label(filter_frame, text="Limit:").pack(side=tk.LEFT, padx=(0, 5))
        
        limit_var = tk.StringVar(value="100")
        limit_combo = ttk.Combobox(
            filter_frame,
            textvariable=limit_var,
            values=["10", "50", "100", "All"],
            state="readonly",
            width=5
        )
        limit_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Apply filter button
        ttk.Button(
            filter_frame,
            text="Apply Filter",
            command=lambda: update_messages()
        ).pack(side=tk.LEFT)
        
        # Message list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        message_tree = ttk.Treeview(
            list_frame,
            columns=("Time", "Component", "Type", "Content"),
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        message_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=message_tree.yview)
        
        # Set up columns
        message_tree.heading("Time", text="Time")
        message_tree.heading("Component", text="Component")
        message_tree.heading("Type", text="Type")
        message_tree.heading("Content", text="Content")
        
        message_tree.column("Time", width=80)
        message_tree.column("Component", width=100)
        message_tree.column("Type", width=100)
        message_tree.column("Content", width=400)
        
        # Function to update message list based on filters
        def update_messages():
            # Clear treeview
            for child in message_tree.get_children():
                message_tree.delete(child)
            
            # Get filter values
            component_filter = component_var.get()
            type_filter = type_var.get()
            limit_filter = limit_var.get()
            
            # Get messages to display
            messages = list(self.message_history)
            
            # Apply component filter
            if component_filter != "All":
                messages = [m for m in messages if m["component_id"] == component_filter]
            
            # Apply type filter
            if type_filter != "All":
                messages = [m for m in messages if m["type"] == type_filter]
            
            # Apply limit filter
            if limit_filter != "All":
                try:
                    limit = int(limit_filter)
                    messages = messages[-limit:]
                except ValueError:
                    pass
            
            # Add messages to treeview (newest first)
            for i, message in enumerate(reversed(messages)):
                timestamp = time.strftime("%H:%M:%S", time.localtime(message["timestamp"]))
                message_tree.insert(
                    "",
                    "end",
                    f"msg_{i}",
                    values=(
                        timestamp,
                        message["component_id"],
                        message["type"],
                        message["content"]
                    )
                )
        
        # Add context menu to treeview
        message_menu = tk.Menu(message_tree, tearoff=0)
        message_menu.add_command(label="View Details", command=lambda: view_message_details())
        
        # Bind right-click to open context menu
        def show_context_menu(event):
            item = message_tree.identify_row(event.y)
            if item:
                message_tree.selection_set(item)
                message_menu.post(event.x_root, event.y_root)
        
        message_tree.bind("<Button-3>", show_context_menu)
        
        # Function to view message details
        def view_message_details():
            # Get selected message
            selected = message_tree.selection()
            if not selected:
                return
            
            # Get message index
            msg_id = selected[0]
            if not msg_id.startswith("msg_"):
                return
            
            try:
                idx = int(msg_id[4:])
                
                # Get filtered messages
                component_filter = component_var.get()
                type_filter = type_var.get()
                
                messages = list(self.message_history)
                
                if component_filter != "All":
                    messages = [m for m in messages if m["component_id"] == component_filter]
                
                if type_filter != "All":
                    messages = [m for m in messages if m["type"] == type_filter]
                
                # Get selected message
                message = list(reversed(messages))[idx]
                
                # Create details dialog
                details_dialog = tk.Toplevel(dialog)
                details_dialog.title("Message Details")
                details_dialog.geometry("400x300")
                details_dialog.resizable(True, True)
                
                # Make dialog modal
                details_dialog.transient(dialog)
                details_dialog.grab_set()
                
                # Create frame
                details_frame = ttk.Frame(details_dialog, padding=10)
                details_frame.pack(fill=tk.BOTH, expand=True)
                
                # Message info
                ttk.Label(
                    details_frame, 
                    text=f"Message from {message['component_id']}",
                    font=("Helvetica", 12, "bold")
                ).pack(anchor=tk.W, pady=(0, 10))
                
                # Grid layout for message info
                ttk.Label(details_frame, text="Time:").grid(row=0, column=0, sticky=tk.W, pady=2)
                ttk.Label(
                    details_frame, 
                    text=time.strftime("%H:%M:%S", time.localtime(message["timestamp"]))
                ).grid(row=0, column=1, sticky=tk.W, pady=2)
                
                ttk.Label(details_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
                ttk.Label(details_frame, text=message["type"]).grid(row=1, column=1, sticky=tk.W, pady=2)
                
                ttk.Label(details_frame, text="Content:").grid(row=2, column=0, sticky=tk.W, pady=2)
                ttk.Label(details_frame, text=message["content"]).grid(row=2, column=1, sticky=tk.W, pady=2)
                
                # Close button
                ttk.Button(
                    details_frame,
                    text="Close",
                    command=details_dialog.destroy
                ).grid(row=3, column=0, columnspan=2, pady=(10, 0))
                
                # Configure grid
                details_frame.columnconfigure(1, weight=1)
            except (ValueError, IndexError) as e:
                logger.error(f"Error getting message details: {e}")
        
        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=dialog.destroy
        ).pack(pady=(10, 0))
        
        # Update messages initially
        update_messages()
    
    def add_task(self, func, *args):
        """
        Add a task to the background queue.
        
        Args:
            func: Function to run
            args: Arguments for the function
        """
        self.task_queue.put((func,) + args)
    
    def start_worker_thread(self):
        """Start background worker thread"""
        self.worker_thread = threading.Thread(target=self._worker_thread)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def _worker_thread(self):
        """Background worker thread function"""
        while self.running:
            try:
                # Get a task from the queue (blocking)
                task = self.task_queue.get(timeout=1.0)
                
                # Execute the task
                func, args = task[0], task[1:]
                func(*args)
                
                # Mark task as done
                self.task_queue.task_done()
            except queue.Empty:
                # No tasks available, just continue
                continue
            except Exception as e:
                # Log the error
                logger.error(f"Error in worker thread: {e}")
                
                # Mark task as done
                self.task_queue.task_done()
    
    def shutdown(self):
        """Clean up resources"""
        # Stop running
        self.running = False
        
        # Stop worker thread
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        
        # Stop all bridges
        for component_id, bridge in self.bridges.items():
            try:
                bridge.stop()
            except Exception as e:
                logger.error(f"Error stopping bridge for {component_id}: {e}")


# Helper function to create and integrate the ROS2 tab with the dashboard
def create_ros2_tab(notebook, dashboard=None):
    """
    Create a ROS2 tab in the given notebook and return the integration object.
    
    Args:
        notebook: Tkinter notebook widget
        dashboard: Optional reference to the main dashboard
        
    Returns:
        ROS2DashboardIntegration: The ROS2 dashboard integration object
    """
    # Create a frame for the ROS2 tab
    ros2_frame = ttk.Frame(notebook)
    
    # Add the frame to the notebook
    notebook.add(ros2_frame, text="ROS2 Integration")
    
    # Create the ROS2 dashboard integration
    ros2_integration = ROS2DashboardIntegration(ros2_frame, dashboard)
    
    return ros2_integration