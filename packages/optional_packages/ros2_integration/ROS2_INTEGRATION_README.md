# ROS2 Integration for Micro-Robot Components

This module provides ROS2 (Robot Operating System 2) integration for the GlowingGoldenGlobe micro-robot components, enabling distributed communication and control.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Components](#components)
5. [Usage](#usage)
   - [Basic Usage](#basic-usage)
   - [Dashboard Integration](#dashboard-integration)
   - [Message Types](#message-types)
   - [Communication Patterns](#communication-patterns)
6. [Examples](#examples)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)

## Overview

The ROS2 Integration module allows micro-robot components to communicate with each other in a distributed manner, enabling complex behaviors and coordination. Components can share state, receive commands, report sensor data, and coordinate actions.

This module includes a mock implementation for development and testing without an actual ROS2 installation, making it accessible for all users.

## Features

- **ROS2 Bridge**: Core bridge between GlowingGoldenGlobe and ROS2 (or mock implementation)
- **Component Interface**: High-level interface for components to communicate
- **Message Types**: Rich set of message types for component communication
- **Communication Patterns**: Special patterns for component coordination and formation movements
- **Dashboard Integration**: Visual interface for monitoring and controlling components
- **Mock Implementation**: Development and testing without actual ROS2 installation

## Installation

### Prerequisites

- Python 3.8+
- GlowingGoldenGlobe project

### Optional ROS2 Installation

For actual ROS2 functionality (not required with mock implementation):

```bash
# For Ubuntu 20.04
sudo apt update
sudo apt install ros-foxy-desktop

# Setup environment
source /opt/ros/foxy/setup.bash
```

### Python Dependencies

```bash
pip install rclpy  # Only for actual ROS2 functionality
```

## Components

The ROS2 integration consists of several key components:

### ROS2 Bridge

`ROS2Bridge` provides the core communication bridge between GlowingGoldenGlobe and ROS2. It handles message publishing and subscribing, either through actual ROS2 or a mock implementation.

```python
from ros2_integration.ros2_bridge import ROS2Bridge, CommunicationType

# Create bridge with mock implementation
bridge = ROS2Bridge("my_bridge", use_mock=True)

# Create publishers
bridge.create_publisher("component_id", CommunicationType.COMMAND)

# Start bridge
bridge.start()
```

### Component Communicator

`ComponentCommunicator` provides a simpler interface for components to communicate, with predefined message structures.

```python
from ros2_integration.ros2_bridge import ComponentCommunicator

# Create communicator
communicator = ComponentCommunicator("component_id", "component_type", bridge)

# Send command
communicator.send_command(target_id, command, params)
```

### Component Interface

`ComponentInterface` provides a high-level interface for components to communicate, manage state, and coordinate with other components.

```python
from ros2_integration.component_interface import ComponentInterface
from ros2_integration.message_types import ComponentType

# Create interface
component = ComponentInterface("component_id", ComponentType.SPHERE)

# Start component
component.start()

# Send command
component.send_command(target_id, command, params)
```

### ROS2 Statements and Role-Scope Communication

The module includes implementations of specialized ROS2 Statements and Role-Scope communication patterns for micro-robot components:

```python
from ros2_integration.pub_sub_patterns import (
    StatementPublisher, RoleScopeReceiver, FormationCommandPattern, CommunicationPattern
)

# Create ROS2 Statement publisher
statement_publisher = StatementPublisher(
    communicator=communicator,
    statement_type="formation_status",
    context_topic="formation_coordination",
    pattern=CommunicationPattern.ROLE_SCOPE_FOCUSED
)

# Create Role-Scope receiver with component role awareness
role_receiver = RoleScopeReceiver(
    communicator=communicator,
    statement_type="formation_status",
    context_topic="formation_coordination",
    statement_handler=handle_formation_statement,
    statement_class=ComponentState,
    role_in_formation="relay",  # Specific role in formation
    pattern=CommunicationPattern.ROLE_SCOPE_FOCUSED
)
```

### Dashboard Integration

The module includes a dashboard integration for visualizing and controlling components.

```python
from ros2_integration.dashboard_integration import create_ros2_tab

# Create ROS2 tab in notebook
ros2_tab = create_ros2_tab(notebook, dashboard)
```

## Usage

### Basic Usage

```python
from ros2_integration.component_interface import ComponentInterface
from ros2_integration.message_types import ComponentType

# Create component interface
component = ComponentInterface("component_id", ComponentType.SPHERE)

# Start component
component.start()

# Connect to another component
component.connect_to_component("other_component_id")

# Send command
component.send_command(
    target_id="other_component_id",
    command="motion",
    params={
        "target_position": [1.0, 2.0, 3.0],
        "motion_type": "linear",
        "duration": 1.0
    }
)

# Send sensor data
component.send_sensor_data(
    sensor_id="sensor1",
    sensor_type="position",
    values={
        "x": 1.0,
        "y": 2.0,
        "z": 3.0
    }
)

# Coordinate motion
component.coordinate_motion(
    action="sync_position",
    params={
        "relative_offset": [0.0, 0.0, 1.0]
    }
)
```

### Dashboard Integration

To run the ROS2 dashboard as a standalone application:

```bash
python run_ros2_dashboard.py
```

The dashboard provides a graphical interface for:

- Adding and removing components
- Monitoring component state
- Sending commands to components
- Viewing messages between components
- Visualizing component relationships

### Message Types

The module includes several message types for component communication:

- `ComponentState`: State of a component (position, orientation, status, etc.)
- `MotionCommand`: Command to change the motion of a component
- `SensorData`: Data from a sensor component
- `ActuatorCommand`: Command for an actuator component
- `JointConfiguration`: Configuration data for a joint between components
- `InterfaceSettings`: Interface settings between components
- `TaskAssignment`: Task assignment for a component
- `CoordinationMessage`: Coordination message between components
- `SimulationControl`: Control message for simulation
- `PhysicalProperties`: Physical properties of a component
- `PowerState`: Power state of a component
- `ErrorMessage`: Error message from a component

### Communication Patterns

The module provides specialized ROS2 Statements and Role-Scope communication patterns for precise micro-robot component coordination:

#### Statement-Directed

Definitive ROS2 Statements directed to a specific component with a defined role. This enables precise coordination where one component needs to issue authoritative statements to another about state, intentions or commands.

#### Statement-Broadcast

Broadcast ROS2 Statements to all components in formation. Used for formation-wide announcements, state declarations, and coordinated transitions that all roles must respond to.

#### Role-Scope Focused

Exact, role-scoped communication where statements are filtered and processed based on a component's specific role in the formation. This establishes tight relationships and precise coordination within formation contexts.

#### Formation Command

Specialized coordination pattern for issuing commands and receiving responses within a formation. Enables synchronized movement, position coordination, and formation-specific behaviors.

#### Processing Sequence

Role-aware sequential processing of statements by multiple components in a defined formation order. Creates precise, step-by-step coordination across formation components.

#### Important Note on ROS2 Statements and Role-Scope Communication

These specialized communication patterns use ROS2 Statements (definitive communications with authority) and Role-Scope (context and role-aware processing) approaches built on top of ROS2's native mechanisms. They are essential for:

1. **Formation Precision**: Enabling exact, tightly-coupled formation movements through definitive statements.
2. **Role-Based Coordination**: Components respond based on their specific role in the formation, creating specialized responses.
3. **Tight Relationships**: Components establish true, fixed relationships rather than loose coupling.
4. **Formation Integrity**: Maintaining exact formation specifications through precise communication.
5. **Dynamic Role Assignment**: Components can take on different roles in different formation contexts.

These patterns use ROS2's native capabilities but extend them with formation-specific semantics and role-aware processing that enables the advanced coordination required for micro-robot formations.

## Examples

### Creating a Component

```python
from ros2_integration.component_interface import ComponentInterface
from ros2_integration.message_types import ComponentType

# Create component
component = ComponentInterface(
    component_id="sphere1",
    component_type=ComponentType.SPHERE,
    initial_state={
        "position": [0.0, 0.0, 0.0],
        "status": "ready"
    }
)

# Start component
component.start()
```

### Handling Commands

```python
# Register command handler
def handle_motion(motion_command):
    print(f"Received motion command: {motion_command}")
    # Implement motion handling logic

component.register_motion_callback(handle_motion)
```

### Using ROS2 Statements and Role-Scope Communication

```python
from ros2_integration.pub_sub_patterns import StatementPublisher, RoleScopeReceiver, CommunicationPattern
from ros2_integration.message_types import ComponentState

# Create statement publisher for formation coordination
formation_statement_publisher = StatementPublisher(
    communicator=component.communicator,
    statement_type="formation_state",
    context_topic="formation_coordination",
    pattern=CommunicationPattern.ROLE_SCOPE_FOCUSED
)

# Create role-scope receiver for formation updates
def handle_formation_statement(source_id, state):
    print(f"Received formation statement from {source_id} with role: {component.role_in_formation}")
    # Update local formation model based on component's role

formation_role_receiver = RoleScopeReceiver(
    communicator=component.communicator,
    statement_type="formation_state",
    context_topic="formation_coordination",
    statement_handler=handle_formation_statement,
    statement_class=ComponentState,
    role_in_formation="coordinator",  # This component's role in the formation
    pattern=CommunicationPattern.ROLE_SCOPE_FOCUSED
)

# Add other components with their specific roles
formation_statement_publisher.add_role_recipient("component_123", role="relay")
formation_statement_publisher.add_role_recipient("component_456", role="endpoint")

# Issue a formation statement with role-scope focus
formation_statement_publisher.make_statement(component.state)
```

### Coordinating Components

```python
# Register coordination handler
def handle_coordination(coordination_message):
    print(f"Received coordination message: {coordination_message}")
    # Implement coordination handling logic

component.register_coordination_callback(handle_coordination)

# Send coordination message
component.coordinate_motion(
    action="form_grid",
    params={
        "center": [0.0, 0.0, 0.0],
        "spacing": 1.0,
        "dimensions": [3, 3, 1],
        "index": {"sphere1": [0, 0, 0]}
    }
)
```

## Testing

The module includes a test script for verifying functionality:

```bash
python -m ros2_integration.test_ros2_integration
```

The test script includes tests for:

- ROS2 bridge
- Component communicator
- Component interface
- Publisher/subscriber patterns

## Troubleshooting

### Mock Implementation

If you're using the mock implementation and experiencing issues:

- Ensure you've started the ROS2 bridge with `bridge.start()`
- Check that components are properly initialized and started
- Verify that message handlers are registered before starting components

### Actual ROS2 Implementation

If you're using the actual ROS2 implementation and experiencing issues:

- Ensure ROS2 is properly installed and configured
- Check environment variables: `source /opt/ros/foxy/setup.bash`
- Verify ROS2 daemon is running: `ros2 daemon status`
- Try running a simple ROS2 test: `ros2 topic list`

### Logging

The module includes extensive logging for troubleshooting:

- ROS2 bridge: `ros2_bridge.log`
- Component interface: `component_interface.log`
- Publisher/subscriber patterns: `pub_sub_patterns.log`
- Dashboard integration: `ros2_dashboard.log`

## Contributing

Contributions to the ROS2 integration module are welcome! Here are some areas for potential improvement:

- Additional message types for specific micro-robot components
- Enhanced visualization capabilities
- Integration with ROS2 tools like RViz
- Performance optimizations for large numbers of components
- Additional communication patterns for complex coordination scenarios