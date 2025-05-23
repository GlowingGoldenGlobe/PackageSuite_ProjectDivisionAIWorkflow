"""
Test Script for ROS2 Integration

This script tests the ROS2 integration functionality.
"""

import os
import sys
import time
import logging
import threading
import json
from typing import Dict, List, Any, Optional

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ros2_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def test_ros2_bridge():
    """Test ROS2 bridge functionality"""
    print("\n=== Testing ROS2 Bridge ===")
    
    # Create ROS2 bridge with mock implementation
    bridge = ROS2Bridge("test_bridge", use_mock=True)
    
    try:
        # Create publishers
        bridge.create_publisher("test_component", CommunicationType.COMMAND)
        bridge.create_publisher("test_component", CommunicationType.TELEMETRY)
        
        # Start bridge
        bridge.start()
        
        # Create and publish messages
        command_message = bridge.create_command_message(
            source_id="source",
            target_id="test_component",
            command="test_command",
            params={"value": 123}
        )
        
        telemetry_message = bridge.create_telemetry_message(
            source_id="source",
            telemetry_type="test_telemetry",
            values={"value": 456}
        )
        
        # Publish messages
        success1 = bridge.publish_message("test_component", CommunicationType.COMMAND, command_message)
        success2 = bridge.publish_message("test_component", CommunicationType.TELEMETRY, telemetry_message)
        
        if success1 and success2:
            print("✅ Published messages successfully")
        else:
            print("❌ Failed to publish messages")
            return False
        
        # Stop bridge
        bridge.stop()
        
        print("✅ ROS2 bridge test completed successfully")
        return True
    except Exception as e:
        print(f"❌ ROS2 bridge test failed: {e}")
        return False
    finally:
        # Ensure bridge is stopped
        bridge.stop()


def test_component_communicator():
    """Test component communicator functionality"""
    print("\n=== Testing Component Communicator ===")
    
    # Create ROS2 bridge with mock implementation
    bridge = ROS2Bridge("test_bridge", use_mock=True)
    
    try:
        # Create communicators
        source_communicator = ComponentCommunicator("source", "test", bridge)
        target_communicator = ComponentCommunicator("target", "test", bridge)
        
        # Message received flag
        message_received = threading.Event()
        received_command = [None]
        
        # Register command handler
        def handle_command(command, params, message):
            print(f"Received command: {command}, params: {params}")
            received_command[0] = (command, params)
            message_received.set()
        
        target_communicator.register_command_handler("test_command", handle_command)
        
        # Start communicators
        source_communicator.start()
        target_communicator.start()
        
        # Send command
        success = source_communicator.send_command(
            target_id="target",
            command="test_command",
            params={"value": 789}
        )
        
        if not success:
            print("❌ Failed to send command")
            return False
        
        # Wait for message to be received
        if not message_received.wait(timeout=2.0):
            print("❌ Command was not received")
            return False
        
        # Verify received command
        command, params = received_command[0]
        if command != "test_command" or params.get("value") != 789:
            print(f"❌ Received different command: {command}, params: {params}")
            return False
        
        print("✅ Command was received correctly")
        
        # Stop communicators
        source_communicator.stop()
        target_communicator.stop()
        
        # Stop bridge
        bridge.stop()
        
        print("✅ Component communicator test completed successfully")
        return True
    except Exception as e:
        print(f"❌ Component communicator test failed: {e}")
        return False
    finally:
        # Ensure bridge is stopped
        bridge.stop()


def test_component_interface():
    """Test component interface functionality"""
    print("\n=== Testing Component Interface ===")
    
    # Create ROS2 bridge with mock implementation
    bridge = ROS2Bridge("test_bridge", use_mock=True)
    
    try:
        # Create component interfaces
        component1 = ComponentInterface("component1", ComponentType.SPHERE, bridge)
        component2 = ComponentInterface("component2", ComponentType.ACTUATOR, bridge)
        
        # Message received flags
        state_updated = threading.Event()
        received_states = []
        
        # Register state update handler
        def handle_state_update(component_id, state):
            print(f"Received state update from {component_id}: {state.status}")
            received_states.append((component_id, state))
            state_updated.set()
        
        component1.register_state_update_callback(handle_state_update)
        
        # Start components
        component1.start()
        component2.start()
        
        # Wait for components to initialize
        time.sleep(0.5)
        
        # Connect components
        component1.connect_to_component("component2")
        
        # Wait for state update
        if not state_updated.wait(timeout=2.0):
            print("❌ State update was not received")
            return False
        
        # Verify received state
        if not received_states or received_states[0][0] != "component2":
            print("❌ State from component2 was not received")
            return False
        
        print("✅ State update was received correctly")
        
        # Send command
        motion_received = threading.Event()
        received_motion = [None]
        
        # Register motion handler
        def handle_motion(motion_command):
            print(f"Received motion command: {motion_command}")
            received_motion[0] = motion_command
            motion_received.set()
        
        component2.register_motion_callback(handle_motion)
        
        # Send motion command
        component1.send_command(
            target_id="component2",
            command="motion",
            params={
                "target_position": [1.0, 2.0, 3.0],
                "motion_type": "linear",
                "duration": 1.0
            }
        )
        
        # Wait for motion command
        if not motion_received.wait(timeout=2.0):
            print("❌ Motion command was not received")
            return False
        
        # Verify received motion command
        motion = received_motion[0]
        if not motion or motion.target_position != [1.0, 2.0, 3.0]:
            print(f"❌ Received different motion command: {motion}")
            return False
        
        print("✅ Motion command was received correctly")
        
        # Stop components
        component1.stop()
        component2.stop()
        
        # Stop bridge
        bridge.stop()
        
        print("✅ Component interface test completed successfully")
        return True
    except Exception as e:
        print(f"❌ Component interface test failed: {e}")
        return False
    finally:
        # Ensure bridge is stopped
        bridge.stop()


def test_pub_sub_patterns():
    """Test publisher/subscriber patterns"""
    print("\n=== Testing Publisher/Subscriber Patterns ===")
    
    # Create ROS2 bridge with mock implementation
    bridge = ROS2Bridge("test_bridge", use_mock=True)
    
    try:
        # Create communicators
        comm1 = ComponentCommunicator("component1", "test", bridge)
        comm2 = ComponentCommunicator("component2", "test", bridge)
        
        # Start bridge and communicators
        bridge.start()
        
        # Test publish-subscribe pattern
        print("\nTesting Publish-Subscribe Pattern...")
        
        # Message received flag
        message_received = threading.Event()
        received_message = [None]
        
        # Create subscriber
        subscriber = Subscriber(
            communicator=comm2,
            message_type="test_messages",
            topic="test_topic",
            callback=lambda source_id, message: (
                received_message.__setitem__(0, (source_id, message)),
                message_received.set()
            ),
            message_class=ComponentState,
            pattern=MessagePattern.PUBLISH_SUBSCRIBE
        )
        
        # Create publisher
        publisher = Publisher(
            communicator=comm1,
            message_type="test_messages",
            topic="test_topic",
            pattern=MessagePattern.PUBLISH_SUBSCRIBE
        )
        
        # Create test message
        test_state = ComponentState(
            component_id="test_component",
            component_type="test",
            position=[1.0, 2.0, 3.0],
            status="active"
        )
        
        # Publish message
        success = publisher.publish(test_state)
        
        if not success:
            print("❌ Failed to publish message")
            return False
        
        # Wait for message to be received
        if not message_received.wait(timeout=2.0):
            print("❌ Message was not received")
            return False
        
        # Verify received message
        source_id, received = received_message[0]
        if not received or received.component_id != "test_component":
            print(f"❌ Received different message: {received}")
            return False
        
        print("✅ Publish-subscribe pattern tested successfully")
        
        # Test request-response pattern
        print("\nTesting Request-Response Pattern...")
        
        # Create request-response patterns
        req_resp1 = RequestResponsePattern(comm1, "test_requests")
        req_resp2 = RequestResponsePattern(comm2, "test_requests")
        
        # Register request handler
        def handle_request(source_id, request_data):
            print(f"Received request from {source_id}: {request_data}")
            return {
                "response": "hello",
                "value": request_data.get("value", 0) * 2
            }
        
        req_resp2.register_request_handler("test_request", handle_request)
        
        # Send request
        success, response = req_resp1.send_request_sync(
            target_id="component2",
            request_action="test_request",
            request_data={"value": 42}
        )
        
        if not success:
            print("❌ Request failed")
            return False
        
        # Verify response
        if not response or response.get("response") != "hello" or response.get("value") != 84:
            print(f"❌ Received different response: {response}")
            return False
        
        print("✅ Request-response pattern tested successfully")
        
        # Stop communicators
        
        # Stop bridge
        bridge.stop()
        
        print("✅ Publisher/subscriber patterns test completed successfully")
        return True
    except Exception as e:
        print(f"❌ Publisher/subscriber patterns test failed: {e}")
        return False
    finally:
        # Ensure bridge is stopped
        bridge.stop()


def run_all_tests():
    """Run all ROS2 integration tests"""
    tests = [
        ("ROS2 Bridge", test_ros2_bridge),
        ("Component Communicator", test_component_communicator),
        ("Component Interface", test_component_interface),
        ("Pub/Sub Patterns", test_pub_sub_patterns)
    ]
    
    success = True
    results = []
    
    print("=== ROS2 Integration Tests ===\n")
    
    for name, test_func in tests:
        print(f"\n=== Running Test: {name} ===")
        try:
            test_success = test_func()
            results.append((name, test_success))
            if not test_success:
                success = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((name, False))
            success = False
    
    print("\n=== Test Results ===")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)