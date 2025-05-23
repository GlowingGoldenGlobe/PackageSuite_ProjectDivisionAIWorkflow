"""
ROS2 Message Types for Micro-Robot Components

This module defines the message types for communication between micro-robot components.
"""

import json
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict


class ComponentType(Enum):
    """Types of micro-robot components"""
    SPHERE = "sphere"
    ACTUATOR = "actuator"
    SENSOR = "sensor"
    CONTROLLER = "controller"
    JOINT = "joint"
    INTERFACE = "interface"
    POWER = "power"
    COMMUNICATION = "communication"


class MotionType(Enum):
    """Types of motion for micro-robot components"""
    LINEAR = "linear"
    ROTATIONAL = "rotational"
    COMBINED = "combined"
    ARTICULATED = "articulated"
    DEFORMABLE = "deformable"


class SensorType(Enum):
    """Types of sensors for micro-robot components"""
    POSITION = "position"
    VELOCITY = "velocity"
    ACCELERATION = "acceleration"
    FORCE = "force"
    TORQUE = "torque"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    PROXIMITY = "proximity"
    TOUCH = "touch"
    VISUAL = "visual"
    AUDIO = "audio"


class ActuatorType(Enum):
    """Types of actuators for micro-robot components"""
    MOTOR = "motor"
    SERVO = "servo"
    PNEUMATIC = "pneumatic"
    HYDRAULIC = "hydraulic"
    PIEZOELECTRIC = "piezoelectric"
    ELECTROMAGNETIC = "electromagnetic"
    SHAPE_MEMORY = "shape_memory"


class CoordinationType(Enum):
    """Types of coordination between micro-robot components"""
    MOTION_SYNC = "motion_sync"
    STATE_SYNC = "state_sync"
    TASK_DISTRIBUTION = "task_distribution"
    RESOURCE_ALLOCATION = "resource_allocation"
    FORMATION = "formation"
    SWARM = "swarm"


@dataclass
class BaseMessage:
    """Base class for all message types"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseMessage':
        """Create message from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BaseMessage':
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ComponentState(BaseMessage):
    """State of a micro-robot component"""
    component_id: str
    component_type: str
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    angular_velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    status: str = "idle"
    battery_level: float = 100.0
    temperature: float = 25.0
    connected_components: List[str] = field(default_factory=list)
    active: bool = True
    timestamp: float = 0.0


@dataclass
class MotionCommand(BaseMessage):
    """Command to change the motion of a component"""
    target_position: Optional[List[float]] = None
    target_orientation: Optional[List[float]] = None
    target_velocity: Optional[List[float]] = None
    target_angular_velocity: Optional[List[float]] = None
    motion_type: str = "linear"
    duration: float = 0.0
    relative: bool = False
    priority: int = 1


@dataclass
class SensorData(BaseMessage):
    """Data from a sensor component"""
    sensor_id: str
    sensor_type: str
    values: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    confidence: float = 1.0
    units: Dict[str, str] = field(default_factory=dict)


@dataclass
class ActuatorCommand(BaseMessage):
    """Command for an actuator component"""
    actuator_id: str
    actuator_type: str
    action: str = "move"
    parameters: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    priority: int = 1


@dataclass
class JointConfiguration(BaseMessage):
    """Configuration data for a joint between components"""
    joint_id: str
    joint_type: str
    connected_components: List[str] = field(default_factory=list)
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])
    limits: Dict[str, Any] = field(default_factory=dict)
    stiffness: float = 1.0
    damping: float = 0.1


@dataclass
class InterfaceSettings(BaseMessage):
    """Interface settings between components"""
    interface_id: str
    interface_type: str
    connected_components: List[str] = field(default_factory=list)
    connection_strength: float = 1.0
    communication_enabled: bool = True
    power_transfer_enabled: bool = False
    data_transfer_rate: float = 1.0
    flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class TaskAssignment(BaseMessage):
    """Task assignment for a component"""
    task_id: str
    task_type: str
    assigned_components: List[str] = field(default_factory=list)
    priority: int = 1
    deadline: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "assigned"


@dataclass
class CoordinationMessage(BaseMessage):
    """Coordination message between components"""
    coordination_type: str
    source_component: str
    target_components: List[str] = field(default_factory=list)
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    response_required: bool = False
    group_id: Optional[str] = None


@dataclass
class SimulationControl(BaseMessage):
    """Control message for simulation"""
    command: str = "start"
    parameters: Dict[str, Any] = field(default_factory=dict)
    affected_components: List[str] = field(default_factory=list)
    time_scale: float = 1.0
    physics_parameters: Dict[str, Any] = field(default_factory=dict)
    random_seed: Optional[int] = None


@dataclass
class PhysicalProperties(BaseMessage):
    """Physical properties of a component"""
    component_id: str
    mass: float = 1.0
    inertia_tensor: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    center_of_mass: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    material: str = "default"
    friction: float = 0.5
    restitution: float = 0.5
    dimensions: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    collision_shape: str = "box"


@dataclass
class PowerState(BaseMessage):
    """Power state of a component"""
    component_id: str
    battery_level: float = 100.0
    power_consumption: float = 0.0
    power_generation: float = 0.0
    charging: bool = False
    available_power: float = 100.0
    power_mode: str = "normal"


@dataclass
class ErrorMessage(BaseMessage):
    """Error message from a component"""
    component_id: str
    error_code: int = 0
    error_type: str = "unknown"
    error_message: str = ""
    severity: str = "info"
    recoverable: bool = True
    suggested_actions: List[str] = field(default_factory=list)
    timestamp: float = 0.0