"""
ROS2 Statements and Role-Scope Communication for Micro-Robot Components

This module implements specialized communication patterns using ROS2 Statements and Role-Scope
approaches to enable precise, formation-focused communication between micro-robot components.
"""

import time
import logging
import threading
import queue
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Set, TypeVar, Generic

from ros2_integration.ros2_bridge import (
    ROS2Bridge, ComponentCommunicator,
    CommunicationType, MessagePriority, ROS2Message
)
from ros2_integration.message_types import (
    ComponentType, BaseMessage
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pub_sub_patterns.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Type variable for message types
T = TypeVar('T', bound=BaseMessage)


class CommunicationPattern(Enum):
    """Communication pattern types for micro-robot components"""
    STATEMENT_DIRECTED = "statement_directed"    # ROS2 Statement directed to a specific component
    STATEMENT_BROADCAST = "statement_broadcast"  # ROS2 Statement broadcast to all components
    ROLE_SCOPE_FOCUSED = "role_scope_focused"    # Communication scoped to specific role contexts
    FORMATION_COMMAND = "formation_command"      # Command messages for formation coordination
    PROCESSING_SEQUENCE = "processing_sequence"  # Sequential processing across formation components


class StatementPublisher(Generic[T]):
    """
    ROS2 Statement publisher for micro-robot components.
    
    This class provides a high-level interface for issuing ROS2 Statements
    (definitive communications) about component state, capabilities, and intentions.
    Statements are made with authority and precision, enabling tight coordination 
    between micro-robot components in formation activities.
    """
    
    def __init__(
        self,
        communicator: ComponentCommunicator,
        statement_type: str,
        context_topic: str,
        pattern: CommunicationPattern = CommunicationPattern.ROLE_SCOPE_FOCUSED,
        reliable: bool = True
    ):
        """
        Initialize ROS2 Statement publisher.
        
        Args:
            communicator: Component communicator
            statement_type: Type of statements to publish (formation, status, capability, etc.)
            context_topic: Topic/context in which statements are made
            pattern: Communication pattern for statement delivery
            reliable: Whether to use reliable QoS
        """
        self.communicator = communicator
        self.statement_type = statement_type
        self.context_topic = context_topic
        self.pattern = pattern
        self.reliable = reliable
        
        # Statement tracking
        self.statements_made = 0
        self.failed_statements = 0
        
        # Role-based recipients (components with specific roles in formation)
        self.role_recipients: Set[str] = set()
        
        # Create appropriate communication channel based on pattern
        if pattern in [CommunicationPattern.ROLE_SCOPE_FOCUSED, CommunicationPattern.FORMATION_COMMAND]:
            comm_type = CommunicationType.COORDINATION
            
            # Create statement publisher for the context topic
            self.communicator.bridge.create_publisher(
                self.context_topic,
                comm_type,
                reliable=reliable
            )
        
        logger.info(f"Initialized {pattern.value} statement publisher for {statement_type} in {context_topic} context")
    
    def make_statement(
        self,
        statement_content: T,
        target_role: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Issue a ROS2 Statement to other components.
        
        Args:
            statement_content: The statement content/data to publish
            target_role: Target component role or ID within the formation
            priority: Statement priority for formation coordination
            
        Returns:
            bool: True if statement was successfully delivered, False otherwise
        """
        try:
            success = False
            
            if self.pattern == CommunicationPattern.STATEMENT_DIRECTED:
                # Statement directed to a specific component
                if not target_role:
                    logger.error("Directed statement requires a target_role")
                    self.failed_statements += 1
                    return False
                
                # Create coordination message with statement semantics
                coord_message = self.communicator.bridge.create_coordination_message(
                    source_id=self.communicator.component_id,
                    coordination_type=self.statement_type,
                    action="directed_statement",
                    params={
                        "statement": statement_content.to_dict(),
                        "context": self.context_topic,
                        "formation_role": "precise"
                    },
                    target_id=target_role,
                    priority=priority
                )
                
                # Send statement to target
                success = self.communicator.bridge.publish_message(
                    target_role,
                    CommunicationType.COORDINATION,
                    coord_message
                )
            
            elif self.pattern == CommunicationPattern.STATEMENT_BROADCAST:
                # Create coordination message for broadcast statement
                coord_message = self.communicator.bridge.create_coordination_message(
                    source_id=self.communicator.component_id,
                    coordination_type=self.statement_type,
                    action="formation_statement",
                    params={
                        "statement": statement_content.to_dict(),
                        "context": self.context_topic,
                        "formation_role": "broadcast"
                    },
                    target_id=None,
                    priority=priority
                )
                
                # Broadcast statement to all formation components
                success = self.communicator.bridge.publish_message(
                    self.communicator.component_id,
                    CommunicationType.COORDINATION,
                    coord_message
                )
            
            elif self.pattern == CommunicationPattern.ROLE_SCOPE_FOCUSED:
                # Create coordination message with role-scoped focus
                coord_message = self.communicator.bridge.create_coordination_message(
                    source_id=self.communicator.component_id,
                    coordination_type=self.statement_type,
                    action="role_statement",
                    params={
                        "statement": statement_content.to_dict(),
                        "context": self.context_topic,
                        "formation_role": "defined_scope"
                    },
                    target_id=None,
                    priority=priority
                )
                
                # Publish to context topic with role-scope focus
                success = self.communicator.bridge.publish_message(
                    self.context_topic,
                    CommunicationType.COORDINATION,
                    coord_message
                )
            
            elif self.pattern == CommunicationPattern.PROCESSING_SEQUENCE:
                # Get role-based processing sequence
                if not self.role_recipients:
                    logger.error("Processing sequence pattern requires defined role recipients")
                    self.failed_statements += 1
                    return False
                
                # Get first component in processing sequence
                first_component = list(self.role_recipients)[0]
                
                # Create coordination message for sequential processing
                coord_message = self.communicator.bridge.create_coordination_message(
                    source_id=self.communicator.component_id,
                    coordination_type=self.statement_type,
                    action="sequence_statement",
                    params={
                        "statement": statement_content.to_dict(),
                        "context": self.context_topic,
                        "formation_sequence": list(self.role_recipients),
                        "sequence_position": 0,
                        "formation_role": "sequence"
                    },
                    target_id=first_component,
                    priority=priority
                )
                
                # Send to first component in sequence
                success = self.communicator.bridge.publish_message(
                    first_component,
                    CommunicationType.COORDINATION,
                    coord_message
                )
            
            # Update statement counters
            if success:
                self.statements_made += 1
            else:
                self.failed_statements += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error making statement: {e}")
            self.failed_statements += 1
            return False
    
    def add_role_recipient(self, component_id: str, role: str = "standard"):
        """
        Add a role-based recipient for statements.
        
        Args:
            component_id: Component ID to add
            role: The component's role in the formation ("coordinator", "relay", etc.)
        """
        self.role_recipients.add(component_id)
        logger.debug(f"Added {role} recipient {component_id} to statement publisher")
    
    def remove_role_recipient(self, component_id: str):
        """
        Remove a role-based recipient from this statement publisher.
        
        Args:
            component_id: Component ID to remove from the formation communication
        """
        if component_id in self.role_recipients:
            self.role_recipients.remove(component_id)
            logger.debug(f"Removed role recipient {component_id} from statement publisher")


class RoleScopeReceiver(Generic[T]):
    """
    Role-Scope focused receiver for micro-robot components.
    
    This class provides a high-level interface for receiving and processing
    statements within specific role contexts. It enables components to interpret
    and respond to communications based on their role in the formation and the
    required coordination specificity.
    """
    
    def __init__(
        self,
        communicator: ComponentCommunicator,
        statement_type: str,
        context_topic: str,
        statement_handler: Callable[[str, T], None],
        statement_class: type,
        role_in_formation: str,
        pattern: CommunicationPattern = CommunicationPattern.ROLE_SCOPE_FOCUSED,
        reliable: bool = True,
        scope_filter: Optional[Callable[[T], bool]] = None
    ):
        """
        Initialize role-scope receiver.
        
        Args:
            communicator: Component communicator
            statement_type: Type of statements to receive and process
            context_topic: Topic/context in which statements are made
            statement_handler: Handler function for received statements (source_id, statement)
            statement_class: Class for deserializing statement content
            role_in_formation: This component's role in the formation (determines which statements to process)
            pattern: Communication pattern
            reliable: Whether to use reliable QoS
            scope_filter: Optional function to filter statements based on formation scope
        """
        self.communicator = communicator
        self.statement_type = statement_type
        self.context_topic = context_topic
        self.statement_handler = statement_handler
        self.statement_class = statement_class
        self.role_in_formation = role_in_formation
        self.pattern = pattern
        self.reliable = reliable
        self.scope_filter = scope_filter
        
        # Statement tracking
        self.statements_received = 0
        self.statements_filtered = 0
        self.statements_processed = 0
        
        # Register coordination handlers based on role
        self._register_role_handlers()
        
        logger.info(f"Initialized {pattern.value} role-scope receiver for {statement_type} statements in {context_topic} context, with role: {role_in_formation}")
    
    def _register_role_handlers(self):
        """Register role-specific statement handlers"""
        # Register coordination handler based on role and statement type
        self.communicator.register_coordination_handler(
            self.statement_type,
            self._handle_role_statement
        )
        
        # Create subscriptions based on communication pattern
        if self.pattern in [CommunicationPattern.ROLE_SCOPE_FOCUSED, CommunicationPattern.FORMATION_COMMAND]:
            comm_type = CommunicationType.COORDINATION
            
            # Create subscription for the context topic with role awareness
            self.communicator.bridge.create_subscription(
                self.context_topic,
                comm_type,
                self._handle_context_statement,
                reliable=self.reliable
            )
    
    def _handle_role_statement(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle a role-based statement in formation coordination.
        
        Args:
            coordination_type: Statement type in coordination
            action: Statement action/intent
            params: Statement parameters
            message: Original message
        """
        # Check if this statement matches our statement type
        if coordination_type != self.statement_type:
            return
        
        # Handle statements based on pattern and role-specific action
        if self.pattern == CommunicationPattern.STATEMENT_DIRECTED and action == "directed_statement":
            # Check if this statement is for our context
            if params.get("context") != self.context_topic:
                return
            
            # Get statement content
            statement_data = params.get("statement")
            
            if statement_data:
                # Process statement with role awareness
                self._process_statement(message.source_id, statement_data, params.get("formation_role"))
        
        elif self.pattern == CommunicationPattern.STATEMENT_BROADCAST and action == "formation_statement":
            # Check if this statement is for our context
            if params.get("context") != self.context_topic:
                return
            
            # Get statement data
            statement_data = params.get("statement")
            
            if statement_data:
                # Process broadcast statement with role awareness
                self._process_statement(message.source_id, statement_data, params.get("formation_role"))
        
        elif self.pattern == CommunicationPattern.PROCESSING_SEQUENCE and action == "sequence_statement":
            # Check if this statement is for our context
            if params.get("context") != self.context_topic:
                return
            
            # Get sequence information
            sequence = params.get("formation_sequence", [])
            position = params.get("sequence_position", 0)
            
            # Check if this component's role is the current recipient in sequence
            if (position < len(sequence) and 
                sequence[position] == self.communicator.component_id):
                
                # Get statement data
                statement_data = params.get("statement")
                
                if statement_data:
                    # Process statement based on role in sequence
                    self._process_statement(message.source_id, statement_data, params.get("formation_role"))
                    
                    # Forward to next component in sequence based on role
                    self._forward_sequence_statement(
                        message.source_id,
                        statement_data,
                        sequence,
                        position,
                        params.get("formation_role")
                    )
    
    def _handle_context_statement(self, message: ROS2Message):
        """
        Handle a context-specific statement (role-scoped).
        
        Args:
            message: Received statement message
        """
        # Check if this is a relevant statement for our role
        if message.message_type != self.statement_type or message.data.get("action") != "role_statement":
            return
        
        # Check if this statement is for our context topic
        if message.data.get("params", {}).get("context") != self.context_topic:
            return
        
        # Get statement data
        statement_data = message.data.get("params", {}).get("statement")
        formation_role = message.data.get("params", {}).get("formation_role")
        
        # Verify statement applies to this component's role in formation
        if formation_role and formation_role != "defined_scope" and formation_role != self.role_in_formation:
            # This statement is not applicable to this component's role
            return
        
        if statement_data:
            # Process statement with role context awareness
            self._process_statement(message.source_id, statement_data, formation_role)
    
    def _process_statement(self, source_id: str, statement_data: Dict[str, Any], formation_role: Optional[str] = None):
        """
        Process a received statement with role-scope awareness.
        
        Args:
            source_id: Source component ID making the statement
            statement_data: Statement content data
            formation_role: Role context of the statement in formation
        """
        try:
            # Create statement instance from data
            statement = self.statement_class.from_dict(statement_data)
            
            # Track statement receipt
            self.statements_received += 1
            
            # Apply role-scope filter if provided
            if self.scope_filter and not self.scope_filter(statement):
                self.statements_filtered += 1
                logger.debug(f"Statement filtered out due to scope constraints (role: {formation_role})")
                return
            
            # Verify this component has appropriate role to process the statement
            if (formation_role and formation_role != "broadcast" and 
                formation_role != "defined_scope" and formation_role != self.role_in_formation):
                logger.debug(f"Statement not applicable to this component's role: {self.role_in_formation}")
                return
                
            # Update processing counter
            self.statements_processed += 1
            
            # Handle statement with role context
            self.statement_handler(source_id, statement)
        except Exception as e:
            logger.error(f"Error processing statement: {e}")
    
    def _forward_sequence_statement(
        self,
        original_source: str,
        statement_data: Dict[str, Any],
        sequence: List[str],
        current_position: int,
        formation_role: Optional[str] = None
    ):
        """
        Forward a statement to the next component in a role-defined sequence.
        
        Args:
            original_source: Original source component ID (statement issuer)
            statement_data: Statement content data
            sequence: List of components in the role-defined sequence
            current_position: Current position in the sequence
            formation_role: Role context for the statement in formation
        """
        try:
            # Check if there are more components in the sequence
            next_position = current_position + 1
            if next_position >= len(sequence):
                # End of sequence - statement processing complete
                logger.debug(f"Completed sequence processing for statement from {original_source}")
                return
            
            # Get next component in sequence based on role
            next_component = sequence[next_position]
            
            # Create coordination message with role-scope awareness
            coord_message = self.communicator.bridge.create_coordination_message(
                source_id=original_source,  # Preserve original statement issuer
                coordination_type=self.statement_type,
                action="sequence_statement",
                params={
                    "statement": statement_data,
                    "context": self.context_topic,
                    "formation_sequence": sequence,
                    "sequence_position": next_position,
                    "formation_role": formation_role
                },
                target_id=next_component,
                priority=MessagePriority.NORMAL
            )
            
            # Send to next component in sequence
            success = self.communicator.bridge.publish_message(
                next_component,
                CommunicationType.COORDINATION,
                coord_message
            )
            
            if success:
                logger.debug(f"Forwarded statement to next component in sequence: {next_component} (position {next_position})")
            else:
                logger.warning(f"Failed to forward statement to next component in sequence: {next_component}")
                
        except Exception as e:
            logger.error(f"Error forwarding sequence statement: {e}")


class FormationCommandPattern:
    """
    Implementation of the formation command and response pattern.
    
    This class provides a high-level interface for issuing formation commands
    and receiving responses, enabling precise coordination between micro-robot
    components in formation activities.
    """
    
    def __init__(
        self,
        communicator: ComponentCommunicator,
        request_type: str,
        response_timeout: float = 5.0
    ):
        """
        Initialize request-response pattern.
        
        Args:
            communicator: Component communicator
            request_type: Type of requests to handle
            response_timeout: Timeout for waiting for responses (seconds)
        """
        self.communicator = communicator
        self.request_type = request_type
        self.response_timeout = response_timeout
        
        # Pending requests
        self.pending_requests: Dict[str, Any] = {}
        
        # Response handlers
        self.response_handlers: Dict[str, Callable[[str, Dict[str, Any]], None]] = {}
        
        # Register coordination handlers
        self.communicator.register_coordination_handler(
            self.request_type,
            self._handle_request_message
        )
        
        # Request handlers
        self.request_handlers: Dict[str, Callable[[str, Dict[str, Any]], Dict[str, Any]]] = {}
        
        logger.info(f"Initialized request-response pattern for {request_type}")
    
    def register_request_handler(
        self,
        request_action: str,
        handler: Callable[[str, Dict[str, Any]], Dict[str, Any]]
    ):
        """
        Register a handler for a specific request action.
        
        Args:
            request_action: Request action to handle
            handler: Handler function (source_id, request_data) -> response_data
        """
        self.request_handlers[request_action] = handler
        logger.debug(f"Registered handler for request action: {request_action}")
    
    def send_request(
        self,
        target_id: str,
        request_action: str,
        request_data: Dict[str, Any],
        response_handler: Callable[[str, Dict[str, Any]], None],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """
        Send a request to a target component.
        
        Args:
            target_id: Target component ID
            request_action: Request action
            request_data: Request data
            response_handler: Handler for the response
            priority: Message priority
            
        Returns:
            str: Request ID
        """
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        # Store response handler
        self.response_handlers[request_id] = response_handler
        
        # Store pending request with timeout
        self.pending_requests[request_id] = {
            "target_id": target_id,
            "request_action": request_action,
            "request_data": request_data,
            "timestamp": time.time(),
            "timeout": time.time() + self.response_timeout
        }
        
        # Create coordination message
        coord_message = self.communicator.bridge.create_coordination_message(
            source_id=self.communicator.component_id,
            coordination_type=self.request_type,
            action=request_action,
            params={
                "request_id": request_id,
                "request_data": request_data
            },
            target_id=target_id,
            priority=priority
        )
        
        # Send request
        success = self.communicator.bridge.publish_message(
            target_id,
            CommunicationType.COORDINATION,
            coord_message
        )
        
        if not success:
            # Request failed to send
            logger.error(f"Failed to send request {request_id} to {target_id}")
            del self.response_handlers[request_id]
            del self.pending_requests[request_id]
            return ""
        
        logger.debug(f"Sent request {request_id} to {target_id}")
        
        # Start timeout checker if not already running
        self._check_request_timeouts()
        
        return request_id
    
    def send_request_sync(
        self,
        target_id: str,
        request_action: str,
        request_data: Dict[str, Any],
        timeout: Optional[float] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send a request and wait for response (blocking).
        
        Args:
            target_id: Target component ID
            request_action: Request action
            request_data: Request data
            timeout: Timeout for waiting for response (seconds, None for default)
            priority: Message priority
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Success flag and response data
        """
        # Use default timeout if not specified
        if timeout is None:
            timeout = self.response_timeout
        
        # Create synchronization objects
        response_received = threading.Event()
        response_data = {"success": False, "data": None}
        
        # Define response handler
        def sync_response_handler(source_id, data):
            response_data["success"] = True
            response_data["data"] = data
            response_received.set()
        
        # Send request
        request_id = self.send_request(
            target_id=target_id,
            request_action=request_action,
            request_data=request_data,
            response_handler=sync_response_handler,
            priority=priority
        )
        
        if not request_id:
            # Request failed to send
            return False, None
        
        # Wait for response or timeout
        response_received.wait(timeout=timeout)
        
        # Clean up if timed out
        if not response_received.is_set() and request_id in self.pending_requests:
            del self.pending_requests[request_id]
            if request_id in self.response_handlers:
                del self.response_handlers[request_id]
        
        return response_data["success"], response_data["data"]
    
    def send_response(
        self,
        request_id: str,
        target_id: str,
        response_data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Send a response to a request.
        
        Args:
            request_id: Request ID
            target_id: Target component ID
            response_data: Response data
            priority: Message priority
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create coordination message
        coord_message = self.communicator.bridge.create_coordination_message(
            source_id=self.communicator.component_id,
            coordination_type=self.request_type,
            action="response",
            params={
                "request_id": request_id,
                "response_data": response_data
            },
            target_id=target_id,
            priority=priority
        )
        
        # Send response
        success = self.communicator.bridge.publish_message(
            target_id,
            CommunicationType.COORDINATION,
            coord_message
        )
        
        if success:
            logger.debug(f"Sent response for request {request_id} to {target_id}")
        else:
            logger.error(f"Failed to send response for request {request_id} to {target_id}")
        
        return success
    
    def _handle_request_message(
        self,
        coordination_type: str,
        action: str,
        params: Dict[str, Any],
        message: ROS2Message
    ):
        """
        Handle a request or response message.
        
        Args:
            coordination_type: Coordination type
            action: Coordination action
            params: Action parameters
            message: Original message
        """
        # Handle response message
        if action == "response":
            # Get request ID
            request_id = params.get("request_id")
            
            if not request_id or request_id not in self.pending_requests:
                logger.warning(f"Received response for unknown request: {request_id}")
                return
            
            # Get response data
            response_data = params.get("response_data", {})
            
            # Call response handler
            if request_id in self.response_handlers:
                try:
                    self.response_handlers[request_id](message.source_id, response_data)
                except Exception as e:
                    logger.error(f"Error in response handler: {e}")
            
            # Clean up
            del self.pending_requests[request_id]
            if request_id in self.response_handlers:
                del self.response_handlers[request_id]
            
            logger.debug(f"Handled response for request {request_id} from {message.source_id}")
            return
        
        # Handle request message
        # Get request ID
        request_id = params.get("request_id")
        
        if not request_id:
            logger.warning("Received request without request_id")
            return
        
        # Get request data
        request_data = params.get("request_data", {})
        
        # Find handler for this request action
        if action in self.request_handlers:
            try:
                # Call request handler
                response_data = self.request_handlers[action](message.source_id, request_data)
                
                # Send response
                self.send_response(
                    request_id=request_id,
                    target_id=message.source_id,
                    response_data=response_data
                )
                
                logger.debug(f"Handled request {request_id} ({action}) from {message.source_id}")
            except Exception as e:
                logger.error(f"Error in request handler: {e}")
                
                # Send error response
                self.send_response(
                    request_id=request_id,
                    target_id=message.source_id,
                    response_data={
                        "error": str(e)
                    }
                )
        else:
            logger.warning(f"No handler for request action: {action}")
            
            # Send error response
            self.send_response(
                request_id=request_id,
                target_id=message.source_id,
                response_data={
                    "error": f"No handler for request action: {action}"
                }
            )
    
    def _check_request_timeouts(self):
        """Check for timed out requests"""
        # Run in a separate thread
        threading.Thread(target=self._timeout_checker).start()
    
    def _timeout_checker(self):
        """Thread function for checking request timeouts"""
        while self.pending_requests:
            now = time.time()
            timed_out = []
            
            # Find timed out requests
            for request_id, request in self.pending_requests.items():
                if request["timeout"] <= now:
                    timed_out.append(request_id)
            
            # Handle timed out requests
            for request_id in timed_out:
                # Call response handler with timeout error
                if request_id in self.response_handlers:
                    try:
                        self.response_handlers[request_id]("", {"error": "timeout"})
                    except Exception as e:
                        logger.error(f"Error in response handler for timeout: {e}")
                
                # Clean up
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
                if request_id in self.response_handlers:
                    del self.response_handlers[request_id]
                
                logger.debug(f"Request {request_id} timed out")
            
            # Sleep
            time.sleep(0.1)