"""
Message Handler Integration for AI Workflow
Processes messages from GUI Message & Instructions field
"""

import json
import os
import threading
import time
from datetime import datetime
import queue

class MessageHandlerIntegration:
    """Handles message processing from GUI to AI agents"""
    
    def __init__(self):
        self.message_queue = queue.Queue()
        self.queue_file = 'user_messages_queue.json'
        self.response_file = 'message_responses.json'
        self.active = False
        self.load_pending_messages()
        
    def start(self):
        """Start the message handler"""
        self.active = True
        
        # Update workflow status
        self.update_workflow_status(True)
        
        # Start processing thread
        thread = threading.Thread(target=self._process_messages, daemon=True)
        thread.start()
        
        # Start queue monitor
        monitor_thread = threading.Thread(target=self._monitor_queue_file, daemon=True)
        monitor_thread.start()
        
    def stop(self):
        """Stop the message handler"""
        self.active = False
        self.update_workflow_status(False)
        
    def update_workflow_status(self, active):
        """Update workflow status to indicate message handler state"""
        status_file = 'ai_workflow_status.json'
        status = {}
        
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status = json.load(f)
            except:
                status = {}
                
        status['message_handler_active'] = active
        status['message_handler_started'] = datetime.now().isoformat()
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
            
    def load_pending_messages(self):
        """Load any pending messages from queue file"""
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r') as f:
                    messages = json.load(f)
                    
                for msg in messages:
                    self.message_queue.put(msg)
                    
                # Clear the file after loading
                with open(self.queue_file, 'w') as f:
                    json.dump([], f)
                    
            except Exception as e:
                print(f"Error loading pending messages: {e}")
                
    def _monitor_queue_file(self):
        """Monitor queue file for new messages"""
        while self.active:
            try:
                if os.path.exists(self.queue_file):
                    with open(self.queue_file, 'r') as f:
                        messages = json.load(f)
                        
                    if messages:
                        # Add new messages to queue
                        for msg in messages:
                            self.message_queue.put(msg)
                            
                        # Clear the file
                        with open(self.queue_file, 'w') as f:
                            json.dump([], f)
                            
            except Exception as e:
                pass
                
            time.sleep(1)  # Check every second
            
    def _process_messages(self):
        """Process messages from the queue"""
        while self.active:
            try:
                # Get message with timeout
                msg = self.message_queue.get(timeout=1)
                
                # Process the message
                response = self.process_user_message(msg)
                
                # Save response
                self.save_response(msg, response)
                
                # Notify GUI of response
                self.notify_gui_response(response)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
                
    def process_user_message(self, message_data):
        """Process a user message and route to appropriate handler"""
        message = message_data.get('message', '')
        timestamp = message_data.get('timestamp', '')
        priority = message_data.get('priority', 'normal')
        
        response = {
            'original_message': message,
            'timestamp': timestamp,
            'processed_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Analyze message intent
        intent = self.analyze_message_intent(message)
        response['intent'] = intent
        
        # Route based on intent
        if intent == 'task_creation':
            response['action'] = 'create_task'
            response['task_data'] = self.extract_task_info(message)
            self.create_task_from_message(response['task_data'])
            response['status'] = 'completed'
            
        elif intent == 'status_query':
            response['action'] = 'provide_status'
            response['status_info'] = self.get_current_status()
            response['status'] = 'completed'
            
        elif intent == 'command':
            response['action'] = 'execute_command'
            response['command'] = self.extract_command(message)
            response['result'] = self.execute_command(response['command'])
            response['status'] = 'completed'
            
        elif intent == 'agent_instruction':
            response['action'] = 'forward_to_agent'
            response['agent'] = self.determine_target_agent(message)
            self.forward_to_agent(message, response['agent'])
            response['status'] = 'forwarded'
            
        else:
            response['action'] = 'general_processing'
            response['status'] = 'processed'
            
        return response
        
    def analyze_message_intent(self, message):
        """Analyze the intent of the user message"""
        message_lower = message.lower()
        
        # Task creation keywords
        if any(keyword in message_lower for keyword in 
               ['create task', 'add task', 'new task', 'schedule task']):
            return 'task_creation'
            
        # Status query keywords
        if any(keyword in message_lower for keyword in 
               ['status', 'how many', 'what tasks', 'show progress']):
            return 'status_query'
            
        # Command keywords
        if any(keyword in message_lower for keyword in 
               ['start', 'stop', 'pause', 'resume', 'cancel']):
            return 'command'
            
        # Agent instruction keywords
        if any(keyword in message_lower for keyword in 
               ['tell agent', 'ask claude', 'instruct', 'have the ai']):
            return 'agent_instruction'
            
        return 'general'
        
    def extract_task_info(self, message):
        """Extract task information from message"""
        # Simple extraction logic - could be enhanced with NLP
        task_info = {
            'description': message,
            'priority': 'medium',
            'agent': 'auto'
        }
        
        # Check for priority indicators
        if 'urgent' in message.lower() or 'high priority' in message.lower():
            task_info['priority'] = 'high'
        elif 'low priority' in message.lower():
            task_info['priority'] = 'low'
            
        return task_info
        
    def create_task_from_message(self, task_data):
        """Create a task based on message content"""
        # Write to task creation queue
        task_queue_file = 'task_creation_queue.json'
        
        queue = []
        if os.path.exists(task_queue_file):
            try:
                with open(task_queue_file, 'r') as f:
                    queue = json.load(f)
            except:
                queue = []
                
        task_data['created_from'] = 'message_handler'
        task_data['created_at'] = datetime.now().isoformat()
        queue.append(task_data)
        
        with open(task_queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
            
    def get_current_status(self):
        """Get current system status"""
        status_info = {
            'workflow_active': False,
            'active_agents': 0,
            'pending_tasks': 0,
            'completed_tasks': 0
        }
        
        # Read from workflow status
        if os.path.exists('ai_workflow_status.json'):
            try:
                with open('ai_workflow_status.json', 'r') as f:
                    status = json.load(f)
                    
                status_info['workflow_active'] = status.get('state') == 'running'
                status_info['active_agents'] = len(status.get('active_agents', []))
                
                stats = status.get('statistics', {})
                status_info['completed_tasks'] = stats.get('total_tasks_completed', 0)
                
            except:
                pass
                
        return status_info
        
    def extract_command(self, message):
        """Extract command from message"""
        message_lower = message.lower()
        
        commands = ['start', 'stop', 'pause', 'resume', 'cancel']
        for cmd in commands:
            if cmd in message_lower:
                return cmd
                
        return None
        
    def execute_command(self, command):
        """Execute a command"""
        if not command:
            return "No command recognized"
            
        # Write command to workflow
        command_data = {
            'command': command,
            'source': 'message_handler',
            'timestamp': datetime.now().isoformat()
        }
        
        with open('workflow_command.json', 'w') as f:
            json.dump(command_data, f, indent=2)
            
        return f"Command '{command}' sent to workflow"
        
    def determine_target_agent(self, message):
        """Determine which agent should handle the message"""
        message_lower = message.lower()
        
        if 'claude' in message_lower:
            return 'Claude-3-Opus'
        elif 'gpt' in message_lower:
            return 'GPT-4'
        elif 'vscode' in message_lower:
            return 'VSCode-Agent'
            
        # Default to best available
        return 'Claude-3-Opus'
        
    def forward_to_agent(self, message, agent):
        """Forward message to specific agent"""
        agent_message = {
            'message': message,
            'target_agent': agent,
            'timestamp': datetime.now().isoformat(),
            'from': 'user_gui'
        }
        
        # Write to agent message queue
        agent_queue_file = f'agent_messages_{agent.lower()}.json'
        
        messages = []
        if os.path.exists(agent_queue_file):
            try:
                with open(agent_queue_file, 'r') as f:
                    messages = json.load(f)
            except:
                messages = []
                
        messages.append(agent_message)
        
        with open(agent_queue_file, 'w') as f:
            json.dump(messages, f, indent=2)
            
    def save_response(self, original_message, response):
        """Save message response for GUI retrieval"""
        responses = []
        if os.path.exists(self.response_file):
            try:
                with open(self.response_file, 'r') as f:
                    responses = json.load(f)
            except:
                responses = []
                
        response_entry = {
            'id': f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'original': original_message,
            'response': response,
            'saved_at': datetime.now().isoformat()
        }
        
        responses.append(response_entry)
        
        # Keep only last 100 responses
        if len(responses) > 100:
            responses = responses[-100:]
            
        with open(self.response_file, 'w') as f:
            json.dump(responses, f, indent=2)
            
    def notify_gui_response(self, response):
        """Notify GUI that a response is available"""
        notification = {
            'type': 'message_response',
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        # Write to GUI notification file
        notif_file = 'gui_notifications.json'
        
        notifications = []
        if os.path.exists(notif_file):
            try:
                with open(notif_file, 'r') as f:
                    notifications = json.load(f)
            except:
                notifications = []
                
        notifications.append(notification)
        
        with open(notif_file, 'w') as f:
            json.dump(notifications, f, indent=2)


# Global instance
message_handler = MessageHandlerIntegration()


def integrate_with_workflow():
    """Integrate message handler with AI workflow"""
    message_handler.start()
    return message_handler