"""
Component Communication Interface for Micro-Robot Components

This module provides a high-level interface for micro-robot components
to communicate with each other using ROS2.
"""

import time
import logging
import threading
import queue
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from enum import Enum

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('component_interface.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Status of a micro-robot component"""
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ComponentInterface:
    """
    Interface for micro-robot components to communicate using ROS2.
    
    This class provides a high-level interface for components to send and
    receive messages, manage state, and coordinate with other components.
    """
    
    def __init__(
        self,
        component_id: str,
        component_type: ComponentType,
        bridge: Optional[ROS2Bridge] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize component interface.
        
        Args:
            component_id: Component ID
            component_type: Component type
            bridge: ROS2 bridge (created if not provided)
            initial_state: Initial component state
        """
        self.component_id = component_id
        self.component_type = component_type
        
        # Create communicator
        self.communicator = ComponentCommunicator(
            component_id=component_id,
            component_type=component_type.value,
            bridge=bridge
        )
        
        # Component state
        self.state = ComponentState(
            component_id=component_id,
            component_type=component_type.value,
            timestamp=time.time()
        )
        
        # Update state with initial values if provided
        if initial_state:
            for key, value in initial_state.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
        
        # Connected components
        self.connected_components = {}
        
        # Task queue
        self.task_queue = queue.PriorityQueue()
        
        # Callback handlers
        self.motion_callbacks = []
        self.sensor_callbacks = []
        self.error_callbacks = []
        self.task_callbacks = []
        self.coordination_callbacks = []
        self.state_update_callbacks = []
        
        # Register message handlers
        self._register_message_handlers()
        
        # Status
        self.status = ComponentStatus.INITIALIZING
        
        # Processing thread
        self.processing_thread = None
        self.running = False
        
        logger.info(f"Initialized ComponentInterface for {component_type.value} {component_id}")
    
    def _register_message_handlers(self):
        """Register handlers for different message types"""
        # Command handlers
        self.communicator.register_command_handler("motion", self._handle_motion_command)
        self.communicator.register_command_handler("configure", self._handle_configure_command)
        self.communicator.register_command_handler("query", self._handle_query_command)
        self.communicator.register_command_handler("task", self._handle_task_command)
        
        # Telemetry handlers
        self.communicator.register_telemetry_handler("state", self._handle_state_telemetry)
        self.communicator.register_telemetry_handler("sensor", self._handle_sensor_telemetry)
        self.communicator.register_telemetry_handler("power", self._handle_power_telemetry)
        self.communicator.register_telemetry_handler("error", self._handle_error_telemetry)
        
        # Coordination handlers
        self.communicator.register_coordination_handler("motion_sync", self._handle_motion_sync)
        self.communicator.register_coordination_handler("state_sync", self._handle_state_sync)
        self.communicator.register_coordination_handler("task_distribution", self._handle_task_distribution)
        self.communicator.register_coordination_handler("formation", self._handle_formation)
    
    def _handle_motion_command(self, command: str, params: Dict[str, Any], message: ROS2Message):
        """
        Handle a motion command.
        
        Args:
            command: Command name
            params: Command parameters
            message: Original message
        """
        logger.debug(f"Received motion command: {params}")
        
        try:
            # Parse motion command
            motion_command = MotionCommand(**params)
            
            # Add to task queue
            self.task_queue.put((
                message.priority.value,
                ("motion", motion_command, message.timestamp)
            ))
            
            # Notify callbacks
            for callback in self.motion_callbacks:
                try:
                    callback(motion_command)
                except Exception as e:
                    logger.error(f"Error in motion callback: {e}")
            
            # Update state
            self.state.status = "moving"
            self.state.timestamp = time.time()
            
            # Broadcast state update
            self._broadcast_state()
        except Exception as e:
            logger.error(f"Error handling motion command: {e}")
            self._report_error(f"motion_command_error", str(e))
    
    def _handle_configure_command(self, command: str, params: Dict[str, Any], message: ROS2Message):
        """
        Handle a configure command.
        
        Args:
            command: Command name
            params: Command parameters
            message: Original message
        """
        logger.debug(f"Received configure command: {params}")
        
        try:
            # Update state with configuration
            for key, value in params.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            
            # Update timestamp
            self.state.timestamp = time.time()
            
            # Broadcast state update
            self._broadcast_state()
        except Exception as e:
            logger.error(f"Error handling configure command: {e}")
            self._report_error(f"configure_command_error", str(e))
    
    def _handle_query_command(self, command: str, params: Dict[str, Any], message: ROS2Message):
        """
        Handle a query command.
        
        Args:
            command: Command name
            params: Command parameters
            message: Original message
        """
        logger.debug(f"Received query command: {params}")
        
        try:
            # Get query type
            query_type = params.get("type", "state")
            
            # Respond with requested data
            if query_type == "state":
                # Send current state
                self._send_state_to(message.source_id)
            elif query_type == "capabilities":
                # Send capabilities
                self._send_capabilities_to(message.source_id)
            elif query_type == "connections":
                # Send connections
                self._send_connections_to(message.source_id)
            else:
                logger.warning(f"Unknown query type: {query_type}")
        except Exception as e:
            logger.error(f"Error handling query command: {e}")
            self._report_error(f"query_command_error", str(e))
    
    def _handle_task_command(self, command: str, params: Dict[str, Any], message: ROS2Message):
        """
        Handle a task command.
        
        Args:
            command: Command name
            params: Command parameters
            message: Original message
        """
        logger.debug(f"Received task command: {params}")
        
        try:
            # Parse task assignment
            task_assignment = TaskAssignment(**params)
            
            # Check if this component is assigned
            if self.component_id in task_assignment.assigned_components:
                # Add to task queue
                self.task_queue.put((
                    task_assignment.priority,
                    ("task", task_assignment, message.timestamp)
                ))
                
                # Notify callbacks
                for callback in self.task_callbacks:
                    try:
                        callback(task_assignment)
                    except Exception as e:
                        logger.error(f"Error in task callback: {e}")
                
                # Update state
                self.state.status = "task_assigned"
                self.state.timestamp = time.time()
                
                # Broadcast state update
                self._broadcast_state()
        except Exception as e:
            logger.error(f"Error handling task command: {e}")
            self._report_error(f"task_command_error", str(e))
    
    def _handle_state_telemetry(self, telemetry_type: str, values: Dict[str, Any], message: ROS2Message):
        """
        Handle state telemetry.
        
        Args:
            telemetry_type: Telemetry type
            values: Telemetry values
            message: Original message
        """
        logger.debug(f"Received state telemetry from {message.source_id}")
        
        try:
            # Parse component state
            component_state = ComponentState.from_dict(values)
            
            # Update connected component state
            self.connected_components[message.source_id] = component_state
            
            # Notify state update callbacks
            for callback in self.state_update_callbacks:
                try:
                    callback(message.source_id, component_state)
                except Exception as e:
                    logger.error(f"Error in state update callback: {e}")
        except Exception as e:
            logger.error(f"Error handling state telemetry: {e}")
    
    def _handle_sensor_telemetry(self, telemetry_type: str, values: Dict[str, Any], message: ROS2Message):
        """
        Handle sensor telemetry.
        
        Args:
            telemetry_type: Telemetry type
            values: Telemetry values
            message: Original message
        """
        logger.debug(f"Received sensor telemetry from {message.source_id}")
        
        try:
            # Parse sensor data
            sensor_data = SensorData.from_dict(values)
            
            # Notify sensor callbacks
            for callback in self.sensor_callbacks:
                try:
                    callback(message.source_id, sensor_data)
                except Exception as e:
                    logger.error(f"Error in sensor callback: {e}")
        except Exception as e:
            logger.error(f"Error handling sensor telemetry: {e}")
    
    def _handle_power_telemetry(self, telemetry_type: str, values: Dict[str, Any], message: ROS2Message):
        """
        Handle power telemetry.
        
        Args:
            telemetry_type: Telemetry type
            values: Telemetry values
            message: Original message
        """
        logger.debug(f"Received power telemetry from {message.source_id}")
        
        try:
            # Parse power state
            power_state = PowerState.from_dict(values)
            
            # Update connected component power state
            if message.source_id in self.connected_components:
                component_state = self.connected_components[message.source_id]
                component_state.battery_level = power_state.battery_level
                
                # Update timestamp
                component_state.timestamp = time.time()
        except Exception as e:
            logger.error(f"Error handling power telemetry: {e}")
    
    def _handle_error_telemetry(self, telemetry_type: str, values: Dict[str, Any], message: ROS2Message):
        """
        Handle error telemetry.
        
        Args:
            telemetry_type: Telemetry type
            values: Telemetry values
            message: Original message
        """
        logger.debug(f"Received error telemetry from {message.source_id}")
        
        try:
            # Parse error message
            error_message = ErrorMessage.from_dict(values)
            
            # Notify error callbacks
            for callback in self.error_callbacks:
                try:
                    callback(message.source_id, error_message)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
            
            # Update connected component state if critical error
            if error_message.severity == "critical" and message.source_id in self.connected_components:
                component_state = self.connected_components[message.source_id]
                component_state.status = "error"
                
                # Update timestamp
                component_state.timestamp = time.time()
        except Exception as e:
            logger.error(f"Error handling error telemetry: {e}")
    
    def _handle_motion_sync(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle motion synchronization.
        
        Args:
            coordination_type: Coordination type
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        logger.debug(f"Received motion sync coordination: {action}")
        
        try:
            # Parse coordination message
            coordination_message = CoordinationMessage(
                coordination_type=coordination_type,
                source_component=message.source_id,
                action=action,
                parameters=params
            )
            
            # Notify coordination callbacks
            for callback in self.coordination_callbacks:
                try:
                    callback(coordination_message)
                except Exception as e:
                    logger.error(f"Error in coordination callback: {e}")
            
            # Handle specific actions
            if action == "sync_position":
                # Synchronize position with source component
                if message.source_id in self.connected_components:
                    source_state = self.connected_components[message.source_id]
                    relative_offset = params.get("relative_offset", [0.0, 0.0, 0.0])
                    
                    # Update position with offset
                    self.state.position = [
                        source_state.position[0] + relative_offset[0],
                        source_state.position[1] + relative_offset[1],
                        source_state.position[2] + relative_offset[2]
                    ]
                    
                    # Update timestamp
                    self.state.timestamp = time.time()
                    
                    # Broadcast state update
                    self._broadcast_state()
        except Exception as e:
            logger.error(f"Error handling motion sync coordination: {e}")
            self._report_error(f"motion_sync_error", str(e))
    
    def _handle_state_sync(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle state synchronization.
        
        Args:
            coordination_type: Coordination type
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        logger.debug(f"Received state sync coordination: {action}")
        
        try:
            # Parse coordination message
            coordination_message = CoordinationMessage(
                coordination_type=coordination_type,
                source_component=message.source_id,
                action=action,
                parameters=params
            )
            
            # Notify coordination callbacks
            for callback in self.coordination_callbacks:
                try:
                    callback(coordination_message)
                except Exception as e:
                    logger.error(f"Error in coordination callback: {e}")
            
            # Handle specific actions
            if action == "request_state":
                # Send state to source component
                self._send_state_to(message.source_id)
            elif action == "synchronize_group":
                # Get group ID
                group_id = params.get("group_id")
                
                if group_id:
                    # Add this component to the group
                    self._join_group(group_id)
                    
                    # Broadcast state to group
                    self._broadcast_state_to_group(group_id)
        except Exception as e:
            logger.error(f"Error handling state sync coordination: {e}")
            self._report_error(f"state_sync_error", str(e))
    
    def _handle_task_distribution(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle task distribution.
        
        Args:
            coordination_type: Coordination type
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        logger.debug(f"Received task distribution coordination: {action}")
        
        try:
            # Parse coordination message
            coordination_message = CoordinationMessage(
                coordination_type=coordination_type,
                source_component=message.source_id,
                action=action,
                parameters=params
            )
            
            # Notify coordination callbacks
            for callback in self.coordination_callbacks:
                try:
                    callback(coordination_message)
                except Exception as e:
                    logger.error(f"Error in coordination callback: {e}")
            
            # Handle specific actions
            if action == "task_offer":
                # Get task assignment
                task_data = params.get("task")
                
                if task_data:
                    # Parse task assignment
                    task_assignment = TaskAssignment.from_dict(task_data)
                    
                    # Check if this component is suitable for the task
                    if self._can_perform_task(task_assignment):
                        # Accept the task
                        self._accept_task(task_assignment)
                    else:
                        # Decline the task
                        self._decline_task(task_assignment)
        except Exception as e:
            logger.error(f"Error handling task distribution coordination: {e}")
            self._report_error(f"task_distribution_error", str(e))
    
    def _handle_formation(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle formation coordination.
        
        Args:
            coordination_type: Coordination type
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        logger.debug(f"Received formation coordination: {action}")
        
        try:
            # Parse coordination message
            coordination_message = CoordinationMessage(
                coordination_type=coordination_type,
                source_component=message.source_id,
                action=action,
                parameters=params
            )
            
            # Notify coordination callbacks
            for callback in self.coordination_callbacks:
                try:
                    callback(coordination_message)
                except Exception as e:
                    logger.error(f"Error in coordination callback: {e}")
            
            # Handle specific actions
            if action == "form_grid":
                # Get grid parameters
                grid_center = params.get("center", [0.0, 0.0, 0.0])
                grid_spacing = params.get("spacing", 1.0)
                grid_dimensions = params.get("dimensions", [3, 3, 1])
                grid_index = params.get("index", {})
                
                # Check if this component has an assigned position
                component_index = grid_index.get(self.component_id)
                
                if component_index:
                    # Calculate position in grid
                    x = grid_center[0] + (component_index[0] - (grid_dimensions[0] - 1) / 2) * grid_spacing
                    y = grid_center[1] + (component_index[1] - (grid_dimensions[1] - 1) / 2) * grid_spacing
                    z = grid_center[2] + (component_index[2] - (grid_dimensions[2] - 1) / 2) * grid_spacing
                    
                    # Create motion command
                    motion_command = MotionCommand(
                        target_position=[x, y, z],
                        motion_type="linear"
                    )
                    
                    # Add to task queue
                    self.task_queue.put((
                        MessagePriority.NORMAL.value,
                        ("motion", motion_command, time.time())
                    ))
                    
                    # Update state
                    self.state.status = "moving"
                    self.state.timestamp = time.time()
                    
                    # Broadcast state update
                    self._broadcast_state()
        except Exception as e:
            logger.error(f"Error handling formation coordination: {e}")
            self._report_error(f"formation_error", str(e))
    
    def _broadcast_state(self):
        """Broadcast component state to all components"""
        try:
            # Send telemetry message with current state
            self.communicator.send_telemetry(
                telemetry_type="state",
                values=self.state.to_dict()
            )
            
            logger.debug(f"Broadcasted state update")
        except Exception as e:
            logger.error(f"Error broadcasting state: {e}")
    
    def _send_state_to(self, target_id: str):
        """
        Send component state to a specific target.
        
        Args:
            target_id: Target component ID
        """
        try:
            # Send telemetry message with current state
            self.communicator.send_telemetry(
                telemetry_type="state",
                values=self.state.to_dict(),
                target_id=target_id
            )
            
            logger.debug(f"Sent state to {target_id}")
        except Exception as e:
            logger.error(f"Error sending state to {target_id}: {e}")
    
    def _send_capabilities_to(self, target_id: str):
        """
        Send component capabilities to a specific target.
        
        Args:
            target_id: Target component ID
        """
        try:
            # Create capabilities dict
            capabilities = {
                "component_type": self.component_type.value,
                "motion_capabilities": self._get_motion_capabilities(),
                "sensor_capabilities": self._get_sensor_capabilities(),
                "actuator_capabilities": self._get_actuator_capabilities(),
                "communication_capabilities": self._get_communication_capabilities()
            }
            
            # Send telemetry message with capabilities
            self.communicator.send_telemetry(
                telemetry_type="capabilities",
                values=capabilities,
                target_id=target_id
            )
            
            logger.debug(f"Sent capabilities to {target_id}")
        except Exception as e:
            logger.error(f"Error sending capabilities to {target_id}: {e}")
    
    def _send_connections_to(self, target_id: str):
        """
        Send component connections to a specific target.
        
        Args:
            target_id: Target component ID
        """
        try:
            # Create connections dict
            connections = {
                "connected_components": list(self.connected_components.keys()),
                "connection_details": {}
            }
            
            # Add connection details for each connected component
            for component_id, state in self.connected_components.items():
                connections["connection_details"][component_id] = {
                    "component_type": state.component_type,
                    "status": state.status,
                    "active": state.active
                }
            
            # Send telemetry message with connections
            self.communicator.send_telemetry(
                telemetry_type="connections",
                values=connections,
                target_id=target_id
            )
            
            logger.debug(f"Sent connections to {target_id}")
        except Exception as e:
            logger.error(f"Error sending connections to {target_id}: {e}")
    
    def _broadcast_state_to_group(self, group_id: str):
        """
        Broadcast component state to a group.
        
        Args:
            group_id: Group ID
        """
        try:
            # Send coordination message with state
            self.communicator.send_coordination(
                coordination_type="state_sync",
                action="group_state_update",
                params={
                    "group_id": group_id,
                    "state": self.state.to_dict()
                }
            )
            
            logger.debug(f"Broadcasted state to group {group_id}")
        except Exception as e:
            logger.error(f"Error broadcasting state to group {group_id}: {e}")
    
    def _join_group(self, group_id: str):
        """
        Join a coordination group.
        
        Args:
            group_id: Group ID
        """
        try:
            # Send coordination message to join group
            self.communicator.send_coordination(
                coordination_type="formation",
                action="join_group",
                params={
                    "group_id": group_id
                }
            )
            
            logger.debug(f"Joined group {group_id}")
        except Exception as e:
            logger.error(f"Error joining group {group_id}: {e}")
    
    def _can_perform_task(self, task: TaskAssignment) -> bool:
        """
        Check if this component can perform a task.
        
        Args:
            task: Task assignment
            
        Returns:
            bool: True if this component can perform the task
        """
        # This method should be overridden by subclasses
        return True
    
    def _accept_task(self, task: TaskAssignment):
        """
        Accept a task.
        
        Args:
            task: Task assignment
        """
        try:
            # Send coordination message to accept task
            self.communicator.send_coordination(
                coordination_type="task_distribution",
                action="task_accept",
                params={
                    "task_id": task.task_id
                },
                target_id=task.assigned_components[0]  # Assume first component is coordinator
            )
            
            # Add to task queue
            self.task_queue.put((
                task.priority,
                ("task", task, time.time())
            ))
            
            # Update state
            self.state.status = "task_assigned"
            self.state.timestamp = time.time()
            
            # Broadcast state update
            self._broadcast_state()
            
            logger.debug(f"Accepted task {task.task_id}")
        except Exception as e:
            logger.error(f"Error accepting task {task.task_id}: {e}")
    
    def _decline_task(self, task: TaskAssignment):
        """
        Decline a task.
        
        Args:
            task: Task assignment
        """
        try:
            # Send coordination message to decline task
            self.communicator.send_coordination(
                coordination_type="task_distribution",
                action="task_decline",
                params={
                    "task_id": task.task_id,
                    "reason": "not_capable"
                },
                target_id=task.assigned_components[0]  # Assume first component is coordinator
            )
            
            logger.debug(f"Declined task {task.task_id}")
        except Exception as e:
            logger.error(f"Error declining task {task.task_id}: {e}")
    
    def _report_error(self, error_type: str, error_message: str, severity: str = "error"):
        """
        Report an error.
        
        Args:
            error_type: Type of error
            error_message: Error message
            severity: Error severity
        """
        try:
            # Create error message
            error = ErrorMessage(
                component_id=self.component_id,
                error_type=error_type,
                error_message=error_message,
                severity=severity,
                timestamp=time.time()
            )
            
            # Send telemetry message with error
            self.communicator.send_telemetry(
                telemetry_type="error",
                values=error.to_dict()
            )
            
            # Update state
            if severity == "critical":
                self.state.status = "error"
                self.state.timestamp = time.time()
                
                # Broadcast state update
                self._broadcast_state()
            
            logger.error(f"Reported error: {error_type} - {error_message}")
        except Exception as e:
            logger.error(f"Error reporting error: {e}")
    
    def _get_motion_capabilities(self) -> List[str]:
        """
        Get motion capabilities.
        
        Returns:
            List[str]: List of motion capabilities
        """
        # This method should be overridden by subclasses
        return ["linear", "rotational"]
    
    def _get_sensor_capabilities(self) -> List[str]:
        """
        Get sensor capabilities.
        
        Returns:
            List[str]: List of sensor capabilities
        """
        # This method should be overridden by subclasses
        return []
    
    def _get_actuator_capabilities(self) -> List[str]:
        """
        Get actuator capabilities.
        
        Returns:
            List[str]: List of actuator capabilities
        """
        # This method should be overridden by subclasses
        return []
    
    def _get_communication_capabilities(self) -> List[str]:
        """
        Get communication capabilities.
        
        Returns:
            List[str]: List of communication capabilities
        """
        # This method should be overridden by subclasses
        return ["telemetry", "command", "coordination"]
    
    def _process_tasks(self):
        """Process tasks in the queue"""
        while self.running:
            try:
                # Get next task (non-blocking)
                try:
                    priority, (task_type, task_data, timestamp) = self.task_queue.get(block=False)
                except queue.Empty:
                    # No tasks, sleep and continue
                    time.sleep(0.01)
                    continue
                
                # Process task
                if task_type == "motion":
                    self._process_motion_task(task_data)
                elif task_type == "task":
                    self._process_general_task(task_data)
                
                # Mark task as done
                self.task_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing tasks: {e}")
    
    def _process_motion_task(self, motion_command: MotionCommand):
        """
        Process a motion task.
        
        Args:
            motion_command: Motion command
        """
        # This method should be overridden by subclasses
        logger.debug(f"Processing motion task: {motion_command}")
        
        # Simulate motion
        time.sleep(0.5)
        
        # Update state
        if motion_command.target_position:
            self.state.position = motion_command.target_position
        
        if motion_command.target_orientation:
            self.state.orientation = motion_command.target_orientation
        
        if motion_command.target_velocity:
            self.state.velocity = motion_command.target_velocity
        
        if motion_command.target_angular_velocity:
            self.state.angular_velocity = motion_command.target_angular_velocity
        
        # Update status and timestamp
        self.state.status = "idle"
        self.state.timestamp = time.time()
        
        # Broadcast state update
        self._broadcast_state()
    
    def _process_general_task(self, task: TaskAssignment):
        """
        Process a general task.
        
        Args:
            task: Task assignment
        """
        # This method should be overridden by subclasses
        logger.debug(f"Processing general task: {task.task_id}")
        
        # Simulate task execution
        time.sleep(1.0)
        
        # Update task status
        task.status = "completed"
        
        # Update component state
        self.state.status = "idle"
        self.state.timestamp = time.time()
        
        # Broadcast state update
        self._broadcast_state()
        
        # Report task completion
        self._report_task_completed(task)
    
    def _report_task_completed(self, task: TaskAssignment):
        """
        Report task completion.
        
        Args:
            task: Task assignment
        """
        try:
            # Send coordination message for task completion
            self.communicator.send_coordination(
                coordination_type="task_distribution",
                action="task_completed",
                params={
                    "task_id": task.task_id,
                    "result": {
                        "status": "success",
                        "completion_time": time.time()
                    }
                },
                target_id=task.assigned_components[0]  # Assume first component is coordinator
            )
            
            logger.debug(f"Reported completion of task {task.task_id}")
        except Exception as e:
            logger.error(f"Error reporting task completion: {e}")
    
    def register_motion_callback(self, callback: Callable[[MotionCommand], None]):
        """
        Register a callback for motion commands.
        
        Args:
            callback: Callback function (motion_command)
        """
        self.motion_callbacks.append(callback)
    
    def register_sensor_callback(self, callback: Callable[[str, SensorData], None]):
        """
        Register a callback for sensor data.
        
        Args:
            callback: Callback function (source_id, sensor_data)
        """
        self.sensor_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable[[str, ErrorMessage], None]):
        """
        Register a callback for error messages.
        
        Args:
            callback: Callback function (source_id, error_message)
        """
        self.error_callbacks.append(callback)
    
    def register_task_callback(self, callback: Callable[[TaskAssignment], None]):
        """
        Register a callback for task assignments.
        
        Args:
            callback: Callback function (task_assignment)
        """
        self.task_callbacks.append(callback)
    
    def register_coordination_callback(self, callback: Callable[[CoordinationMessage], None]):
        """
        Register a callback for coordination messages.
        
        Args:
            callback: Callback function (coordination_message)
        """
        self.coordination_callbacks.append(callback)
    
    def register_state_update_callback(self, callback: Callable[[str, ComponentState], None]):
        """
        Register a callback for state updates.
        
        Args:
            callback: Callback function (component_id, component_state)
        """
        self.state_update_callbacks.append(callback)
    
    def connect_to_component(self, component_id: str):
        """
        Connect to another component.
        
        Args:
            component_id: Target component ID
        """
        # Send query command to get component state
        self.send_command(
            target_id=component_id,
            command="query",
            params={
                "type": "state"
            }
        )
        
        # Add to connected components (will be updated when state is received)
        if component_id not in self.connected_components:
            self.connected_components[component_id] = None
            
            # Update state
            if component_id not in self.state.connected_components:
                self.state.connected_components.append(component_id)
            
            # Update timestamp
            self.state.timestamp = time.time()
            
            # Broadcast state update
            self._broadcast_state()
    
    def disconnect_from_component(self, component_id: str):
        """
        Disconnect from another component.
        
        Args:
            component_id: Target component ID
        """
        # Remove from connected components
        if component_id in self.connected_components:
            del self.connected_components[component_id]
            
            # Update state
            if component_id in self.state.connected_components:
                self.state.connected_components.remove(component_id)
            
            # Update timestamp
            self.state.timestamp = time.time()
            
            # Broadcast state update
            self._broadcast_state()
    
    def send_command(
        self,
        target_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Send a command to a target component.
        
        Args:
            target_id: Target component ID
            command: Command name
            params: Command parameters
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.communicator.send_command(
            target_id=target_id,
            command=command,
            params=params,
            priority=priority
        )
    
    def send_sensor_data(
        self,
        sensor_id: str,
        sensor_type: str,
        values: Dict[str, Any],
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Send sensor data.
        
        Args:
            sensor_id: Sensor ID
            sensor_type: Sensor type
            values: Sensor values
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create sensor data
        sensor_data = SensorData(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            values=values,
            timestamp=time.time()
        )
        
        # Send telemetry
        return self.communicator.send_telemetry(
            telemetry_type="sensor",
            values=sensor_data.to_dict(),
            target_id=target_id,
            priority=priority
        )
    
    def broadcast_task(
        self,
        task_id: str,
        task_type: str,
        params: Dict[str, Any],
        assigned_components: Optional[List[str]] = None,
        priority: int = 1
    ) -> bool:
        """
        Broadcast a task to other components.
        
        Args:
            task_id: Task ID
            task_type: Task type
            params: Task parameters
            assigned_components: List of component IDs (None for all)
            priority: Task priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create task assignment
        task = TaskAssignment(
            task_id=task_id,
            task_type=task_type,
            assigned_components=assigned_components or [],
            parameters=params,
            priority=priority,
            status="assigned"
        )
        
        # Send coordination message
        return self.communicator.send_coordination(
            coordination_type="task_distribution",
            action="task_offer",
            params={
                "task": task.to_dict()
            },
            target_id=None  # Broadcast
        )
    
    def coordinate_motion(
        self,
        action: str,
        params: Dict[str, Any],
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Coordinate motion with other components.
        
        Args:
            action: Coordination action
            params: Action parameters
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.communicator.send_coordination(
            coordination_type="motion_sync",
            action=action,
            params=params,
            target_id=target_id,
            priority=priority
        )
    
    def start(self):
        """Start the component interface"""
        # Set status to ready
        self.status = ComponentStatus.READY
        
        # Start communicator
        self.communicator.start()
        
        # Start processing thread
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_tasks)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Update state
        self.state.status = "ready"
        self.state.active = True
        self.state.timestamp = time.time()
        
        # Broadcast initial state
        self._broadcast_state()
        
        logger.info(f"Started ComponentInterface for {self.component_type.value} {self.component_id}")
    
    def stop(self):
        """Stop the component interface"""
        # Set status to disconnected
        self.status = ComponentStatus.DISCONNECTED
        
        # Stop processing thread
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        
        # Update state
        self.state.status = "disconnected"
        self.state.active = False
        self.state.timestamp = time.time()
        
        # Broadcast final state
        self._broadcast_state()
        
        # Stop communicator
        self.communicator.stop()
        
        logger.info(f"Stopped ComponentInterface for {self.component_type.value} {self.component_id}")