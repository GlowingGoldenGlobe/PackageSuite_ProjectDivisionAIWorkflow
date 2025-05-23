"""
ROS2 Bridge Module for GlowingGoldenGlobe

This module provides a bridge between the GlowingGoldenGlobe micro-robot components
and ROS2 (Robot Operating System 2) for distributed communication and control.
"""

import os
import sys
import time
import threading
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ros2_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if ROS2 is available
ROS2_AVAILABLE = False
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
    ROS2_AVAILABLE = True
except ImportError:
    logger.warning("ROS2 (rclpy) not found. Using mock ROS2 implementation.")


class CommunicationType(Enum):
    """Types of communication for micro-robot components"""
    COMMAND = "command"          # Control commands
    TELEMETRY = "telemetry"      # Status and sensor data
    COORDINATION = "coordination" # Inter-component coordination
    SIMULATION = "simulation"    # Simulation data
    VISUALIZATION = "visualization" # Visualization data


class MessagePriority(Enum):
    """Priority levels for messages"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class ROS2Message:
    """Base class for ROS2 messages"""
    
    def __init__(
        self,
        message_type: str,
        source_id: str,
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        timestamp: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ROS2 message.
        
        Args:
            message_type: Type of message
            source_id: ID of the source component
            target_id: ID of the target component (None for broadcasts)
            priority: Message priority
            timestamp: Message timestamp (defaults to current time)
            data: Message data
        """
        self.message_id = str(uuid.uuid4())
        self.message_type = message_type
        self.source_id = source_id
        self.target_id = target_id
        self.priority = priority
        self.timestamp = timestamp or time.time()
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ROS2Message':
        """Create message from dictionary"""
        # Create new instance
        message = cls(
            message_type=data["message_type"],
            source_id=data["source_id"],
            target_id=data.get("target_id"),
            priority=MessagePriority(data["priority"]),
            timestamp=data["timestamp"],
            data=data["data"]
        )
        
        # Set message ID
        message.message_id = data["message_id"]
        
        return message
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ROS2Message':
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))


class MockROS2Node:
    """Mock implementation of a ROS2 node for testing without ROS2"""
    
    def __init__(self, node_name: str):
        """
        Initialize mock ROS2 node.
        
        Args:
            node_name: Name of the node
        """
        self.node_name = node_name
        self.publishers = {}
        self.subscriptions = {}
        self.message_queue = []
        self.running = False
        self.thread = None
        
        logger.info(f"Created mock ROS2 node: {node_name}")
    
    def create_publisher(self, topic: str, qos_profile: Optional[Dict[str, Any]] = None) -> 'MockPublisher':
        """
        Create a mock publisher.
        
        Args:
            topic: Topic to publish to
            qos_profile: Quality of service profile
            
        Returns:
            MockPublisher: Mock publisher
        """
        publisher = MockPublisher(self, topic)
        self.publishers[topic] = publisher
        logger.info(f"Created mock publisher for topic: {topic}")
        return publisher
    
    def create_subscription(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], None],
        qos_profile: Optional[Dict[str, Any]] = None
    ) -> 'MockSubscription':
        """
        Create a mock subscription.
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function for received messages
            qos_profile: Quality of service profile
            
        Returns:
            MockSubscription: Mock subscription
        """
        subscription = MockSubscription(self, topic, callback)
        self.subscriptions[topic] = subscription
        logger.info(f"Created mock subscription for topic: {topic}")
        return subscription
    
    def start(self):
        """Start the mock node"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_messages)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started mock ROS2 node: {self.node_name}")
    
    def stop(self):
        """Stop the mock node"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info(f"Stopped mock ROS2 node: {self.node_name}")
    
    def _process_messages(self):
        """Process messages in the queue"""
        while self.running:
            if self.message_queue:
                topic, message = self.message_queue.pop(0)
                
                # Find subscriptions for this topic
                if topic in self.subscriptions:
                    self.subscriptions[topic].callback(message)
            
            time.sleep(0.01)  # Avoid busy waiting


class MockPublisher:
    """Mock implementation of a ROS2 publisher"""
    
    def __init__(self, node: MockROS2Node, topic: str):
        """
        Initialize mock publisher.
        
        Args:
            node: Parent node
            topic: Topic to publish to
        """
        self.node = node
        self.topic = topic
    
    def publish(self, message: Dict[str, Any]):
        """
        Publish a message.
        
        Args:
            message: Message to publish
        """
        self.node.message_queue.append((self.topic, message))
        logger.debug(f"Published mock message to topic: {self.topic}")


class MockSubscription:
    """Mock implementation of a ROS2 subscription"""
    
    def __init__(self, node: MockROS2Node, topic: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize mock subscription.
        
        Args:
            node: Parent node
            topic: Topic to subscribe to
            callback: Callback function for received messages
        """
        self.node = node
        self.topic = topic
        self.callback = callback


class ROS2Bridge:
    """Bridge between GlowingGoldenGlobe and ROS2"""
    
    def __init__(self, node_name: str, use_mock: bool = not ROS2_AVAILABLE):
        """
        Initialize ROS2 bridge.
        
        Args:
            node_name: Name of the ROS2 node
            use_mock: Whether to use mock ROS2 implementation
        """
        self.node_name = node_name
        self.use_mock = use_mock
        self.node = None
        self.publishers = {}
        self.subscriptions = {}
        self.message_handlers = {}
        
        # Initialize ROS2 node
        self._initialize_node()
    
    def _initialize_node(self):
        """Initialize ROS2 node"""
        if self.use_mock:
            # Use mock implementation
            self.node = MockROS2Node(self.node_name)
            logger.info(f"Using mock ROS2 implementation for node: {self.node_name}")
        else:
            # Use actual ROS2
            try:
                rclpy.init()
                self.node = Node(self.node_name)
                logger.info(f"Initialized ROS2 node: {self.node_name}")
            except Exception as e:
                logger.error(f"Failed to initialize ROS2 node: {e}")
                # Fall back to mock implementation
                self.use_mock = True
                self.node = MockROS2Node(self.node_name)
                logger.info(f"Falling back to mock ROS2 implementation for node: {self.node_name}")
    
    def _create_topic_name(self, component_id: str, comm_type: CommunicationType) -> str:
        """
        Create a topic name for a component and communication type.
        
        Args:
            component_id: Component ID
            comm_type: Communication type
            
        Returns:
            str: Topic name
        """
        return f"/micro_robot/{comm_type.value}/{component_id}"
    
    def create_publisher(
        self,
        component_id: str,
        comm_type: CommunicationType,
        reliable: bool = True,
        history_depth: int = 10
    ):
        """
        Create a publisher for a component.
        
        Args:
            component_id: Component ID
            comm_type: Communication type
            reliable: Whether to use reliable QoS
            history_depth: History depth for QoS
        """
        topic = self._create_topic_name(component_id, comm_type)
        
        # Check if publisher already exists
        if topic in self.publishers:
            logger.warning(f"Publisher already exists for topic: {topic}")
            return
        
        if self.use_mock:
            # Create mock publisher
            publisher = self.node.create_publisher(topic)
        else:
            # Create actual ROS2 publisher with QoS
            qos = QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE if reliable else ReliabilityPolicy.BEST_EFFORT,
                history=HistoryPolicy.KEEP_LAST,
                depth=history_depth,
                durability=DurabilityPolicy.VOLATILE
            )
            publisher = self.node.create_publisher(topic, qos)
        
        # Store publisher
        self.publishers[topic] = publisher
        logger.info(f"Created publisher for topic: {topic}")
    
    def create_subscription(
        self,
        component_id: str,
        comm_type: CommunicationType,
        callback: Callable[[ROS2Message], None],
        reliable: bool = True,
        history_depth: int = 10
    ):
        """
        Create a subscription for a component.
        
        Args:
            component_id: Component ID
            comm_type: Communication type
            callback: Callback function for received messages
            reliable: Whether to use reliable QoS
            history_depth: History depth for QoS
        """
        topic = self._create_topic_name(component_id, comm_type)
        
        # Check if subscription already exists
        if topic in self.subscriptions:
            logger.warning(f"Subscription already exists for topic: {topic}")
            return
        
        # Create message handler
        def message_handler(msg):
            try:
                # Parse message
                if isinstance(msg, dict):
                    # Mock implementation returns dict
                    message = ROS2Message.from_dict(msg)
                else:
                    # Real ROS2 implementation returns ROS2 message
                    message = ROS2Message.from_json(msg.data)
                
                # Call callback
                callback(message)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
        
        # Store message handler
        self.message_handlers[topic] = message_handler
        
        if self.use_mock:
            # Create mock subscription
            subscription = self.node.create_subscription(topic, message_handler)
        else:
            # Create actual ROS2 subscription with QoS
            qos = QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE if reliable else ReliabilityPolicy.BEST_EFFORT,
                history=HistoryPolicy.KEEP_LAST,
                depth=history_depth,
                durability=DurabilityPolicy.VOLATILE
            )
            subscription = self.node.create_subscription(topic, message_handler, qos)
        
        # Store subscription
        self.subscriptions[topic] = subscription
        logger.info(f"Created subscription for topic: {topic}")
    
    def publish_message(
        self,
        component_id: str,
        comm_type: CommunicationType,
        message: ROS2Message
    ) -> bool:
        """
        Publish a message.
        
        Args:
            component_id: Component ID
            comm_type: Communication type
            message: Message to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        topic = self._create_topic_name(component_id, comm_type)
        
        # Check if publisher exists
        if topic not in self.publishers:
            logger.error(f"No publisher found for topic: {topic}")
            return False
        
        try:
            # Get publisher
            publisher = self.publishers[topic]
            
            if self.use_mock:
                # Mock implementation accepts dict
                publisher.publish(message.to_dict())
            else:
                # Create ROS2 message
                from std_msgs.msg import String
                ros2_msg = String()
                ros2_msg.data = message.to_json()
                
                # Publish message
                publisher.publish(ros2_msg)
            
            logger.debug(f"Published message to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def create_command_message(
        self,
        source_id: str,
        target_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> ROS2Message:
        """
        Create a command message.
        
        Args:
            source_id: Source component ID
            target_id: Target component ID
            command: Command name
            params: Command parameters
            priority: Message priority
            
        Returns:
            ROS2Message: Command message
        """
        return ROS2Message(
            message_type="command",
            source_id=source_id,
            target_id=target_id,
            priority=priority,
            data={
                "command": command,
                "params": params or {}
            }
        )
    
    def create_telemetry_message(
        self,
        source_id: str,
        telemetry_type: str,
        values: Dict[str, Any],
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> ROS2Message:
        """
        Create a telemetry message.
        
        Args:
            source_id: Source component ID
            telemetry_type: Type of telemetry data
            values: Telemetry values
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            ROS2Message: Telemetry message
        """
        return ROS2Message(
            message_type="telemetry",
            source_id=source_id,
            target_id=target_id,
            priority=priority,
            data={
                "telemetry_type": telemetry_type,
                "values": values
            }
        )
    
    def create_coordination_message(
        self,
        source_id: str,
        coordination_type: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> ROS2Message:
        """
        Create a coordination message.
        
        Args:
            source_id: Source component ID
            coordination_type: Type of coordination
            action: Coordination action
            params: Action parameters
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            ROS2Message: Coordination message
        """
        return ROS2Message(
            message_type="coordination",
            source_id=source_id,
            target_id=target_id,
            priority=priority,
            data={
                "coordination_type": coordination_type,
                "action": action,
                "params": params or {}
            }
        )
    
    def start(self):
        """Start the ROS2 bridge"""
        if self.use_mock:
            # Start mock node
            self.node.start()
        else:
            # Start ROS2 spin in a separate thread
            threading.Thread(target=self._ros2_spin).start()
        
        logger.info(f"Started ROS2 bridge: {self.node_name}")
    
    def stop(self):
        """Stop the ROS2 bridge"""
        if self.use_mock:
            # Stop mock node
            self.node.stop()
        else:
            # Stop ROS2 node
            try:
                self.node.destroy_node()
                rclpy.shutdown()
            except Exception as e:
                logger.error(f"Error stopping ROS2 node: {e}")
        
        logger.info(f"Stopped ROS2 bridge: {self.node_name}")
    
    def _ros2_spin(self):
        """Spin the ROS2 node"""
        try:
            rclpy.spin(self.node)
        except Exception as e:
            logger.error(f"Error in ROS2 spin: {e}")


class ComponentCommunicator:
    """
    High-level component communicator using ROS2.
    
    This class provides a simpler interface for micro-robot components
    to communicate with each other using ROS2.
    """
    
    def __init__(
        self,
        component_id: str,
        component_type: str,
        bridge: Optional[ROS2Bridge] = None
    ):
        """
        Initialize component communicator.
        
        Args:
            component_id: Component ID
            component_type: Component type
            bridge: ROS2 bridge (created if not provided)
        """
        self.component_id = component_id
        self.component_type = component_type
        
        # Create bridge if not provided
        if bridge is None:
            self.bridge = ROS2Bridge(f"{component_type}_{component_id}")
            self.owns_bridge = True
        else:
            self.bridge = bridge
            self.owns_bridge = False
        
        # Message handlers
        self.command_handlers = {}
        self.telemetry_handlers = {}
        self.coordination_handlers = {}
        
        # Create publishers for each communication type
        self._create_publishers()
        
        # Create subscriptions for incoming messages
        self._create_subscriptions()
        
        logger.info(f"Initialized ComponentCommunicator for {component_type} {component_id}")
    
    def _create_publishers(self):
        """Create publishers for each communication type"""
        for comm_type in CommunicationType:
            self.bridge.create_publisher(
                self.component_id,
                comm_type
            )
    
    def _create_subscriptions(self):
        """Create subscriptions for incoming messages"""
        # Subscribe to commands
        self.bridge.create_subscription(
            self.component_id,
            CommunicationType.COMMAND,
            self._handle_command_message
        )
        
        # Subscribe to telemetry
        self.bridge.create_subscription(
            self.component_id,
            CommunicationType.TELEMETRY,
            self._handle_telemetry_message
        )
        
        # Subscribe to coordination
        self.bridge.create_subscription(
            self.component_id,
            CommunicationType.COORDINATION,
            self._handle_coordination_message
        )
    
    def _handle_command_message(self, message: ROS2Message):
        """
        Handle a command message.
        
        Args:
            message: Command message
        """
        # Check message type
        if message.message_type != "command":
            logger.warning(f"Received non-command message on command topic: {message.message_type}")
            return
        
        # Check target
        if message.target_id != self.component_id:
            logger.warning(f"Received command for different target: {message.target_id}")
            return
        
        # Get command
        command = message.data.get("command")
        if not command:
            logger.warning("Received command message with no command")
            return
        
        # Get parameters
        params = message.data.get("params", {})
        
        # Find handler for this command
        if command in self.command_handlers:
            # Call handler
            try:
                self.command_handlers[command](command, params, message)
            except Exception as e:
                logger.error(f"Error handling command {command}: {e}")
        else:
            logger.warning(f"No handler for command: {command}")
    
    def _handle_telemetry_message(self, message: ROS2Message):
        """
        Handle a telemetry message.
        
        Args:
            message: Telemetry message
        """
        # Check message type
        if message.message_type != "telemetry":
            logger.warning(f"Received non-telemetry message on telemetry topic: {message.message_type}")
            return
        
        # Check target (if specified)
        if message.target_id and message.target_id != self.component_id:
            logger.warning(f"Received telemetry for different target: {message.target_id}")
            return
        
        # Get telemetry type
        telemetry_type = message.data.get("telemetry_type")
        if not telemetry_type:
            logger.warning("Received telemetry message with no type")
            return
        
        # Get values
        values = message.data.get("values", {})
        
        # Find handler for this telemetry type
        if telemetry_type in self.telemetry_handlers:
            # Call handler
            try:
                self.telemetry_handlers[telemetry_type](telemetry_type, values, message)
            except Exception as e:
                logger.error(f"Error handling telemetry {telemetry_type}: {e}")
        else:
            logger.warning(f"No handler for telemetry type: {telemetry_type}")
    
    def _handle_coordination_message(self, message: ROS2Message):
        """
        Handle a coordination message.
        
        Args:
            message: Coordination message
        """
        # Check message type
        if message.message_type != "coordination":
            logger.warning(f"Received non-coordination message on coordination topic: {message.message_type}")
            return
        
        # Check target (if specified)
        if message.target_id and message.target_id != self.component_id:
            logger.warning(f"Received coordination for different target: {message.target_id}")
            return
        
        # Get coordination type
        coordination_type = message.data.get("coordination_type")
        if not coordination_type:
            logger.warning("Received coordination message with no type")
            return
        
        # Get action
        action = message.data.get("action")
        if not action:
            logger.warning("Received coordination message with no action")
            return
        
        # Get parameters
        params = message.data.get("params", {})
        
        # Find handler for this coordination type
        if coordination_type in self.coordination_handlers:
            # Call handler
            try:
                self.coordination_handlers[coordination_type](coordination_type, action, params, message)
            except Exception as e:
                logger.error(f"Error handling coordination {coordination_type}: {e}")
        else:
            logger.warning(f"No handler for coordination type: {coordination_type}")
    
    def register_command_handler(
        self,
        command: str,
        handler: Callable[[str, Dict[str, Any], ROS2Message], None]
    ):
        """
        Register a handler for a command.
        
        Args:
            command: Command name
            handler: Handler function (command, params, message)
        """
        self.command_handlers[command] = handler
        logger.info(f"Registered handler for command: {command}")
    
    def register_telemetry_handler(
        self,
        telemetry_type: str,
        handler: Callable[[str, Dict[str, Any], ROS2Message], None]
    ):
        """
        Register a handler for telemetry.
        
        Args:
            telemetry_type: Telemetry type
            handler: Handler function (telemetry_type, values, message)
        """
        self.telemetry_handlers[telemetry_type] = handler
        logger.info(f"Registered handler for telemetry type: {telemetry_type}")
    
    def register_coordination_handler(
        self,
        coordination_type: str,
        handler: Callable[[str, str, Dict[str, Any], ROS2Message], None]
    ):
        """
        Register a handler for coordination.
        
        Args:
            coordination_type: Coordination type
            handler: Handler function (coordination_type, action, params, message)
        """
        self.coordination_handlers[coordination_type] = handler
        logger.info(f"Registered handler for coordination type: {coordination_type}")
    
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
        # Create command message
        message = self.bridge.create_command_message(
            source_id=self.component_id,
            target_id=target_id,
            command=command,
            params=params,
            priority=priority
        )
        
        # Publish command message
        return self.bridge.publish_message(
            target_id,
            CommunicationType.COMMAND,
            message
        )
    
    def send_telemetry(
        self,
        telemetry_type: str,
        values: Dict[str, Any],
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Send telemetry data.
        
        Args:
            telemetry_type: Type of telemetry data
            values: Telemetry values
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create telemetry message
        message = self.bridge.create_telemetry_message(
            source_id=self.component_id,
            telemetry_type=telemetry_type,
            values=values,
            target_id=target_id,
            priority=priority
        )
        
        # Publish telemetry message
        return self.bridge.publish_message(
            self.component_id,
            CommunicationType.TELEMETRY,
            message
        )
    
    def send_coordination(
        self,
        coordination_type: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        target_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Send a coordination message.
        
        Args:
            coordination_type: Type of coordination
            action: Coordination action
            params: Action parameters
            target_id: Target component ID (None for broadcasts)
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create coordination message
        message = self.bridge.create_coordination_message(
            source_id=self.component_id,
            coordination_type=coordination_type,
            action=action,
            params=params,
            target_id=target_id,
            priority=priority
        )
        
        # Publish coordination message
        return self.bridge.publish_message(
            self.component_id,
            CommunicationType.COORDINATION,
            message
        )
    
    def start(self):
        """Start the component communicator"""
        self.bridge.start()
        logger.info(f"Started ComponentCommunicator for {self.component_type} {self.component_id}")
    
    def stop(self):
        """Stop the component communicator"""
        if self.owns_bridge:
            self.bridge.stop()
        logger.info(f"Stopped ComponentCommunicator for {self.component_type} {self.component_id}")
    
    def __del__(self):
        """Clean up resources"""
        self.stop()