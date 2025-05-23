"""
ROS2 Integration for Micro-Robot Components

This package provides ROS2 (Robot Operating System 2) integration for the 
GlowingGoldenGlobe micro-robot components, enabling distributed communication and control.
"""

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
from ros2_integration.component_interface import ComponentInterface, ComponentStatus
from ros2_integration.pub_sub_patterns import (
    Publisher, Subscriber, RequestResponsePattern, MessagePattern
)
from ros2_integration.dashboard_integration import create_ros2_tab

__version__ = '1.0.0'