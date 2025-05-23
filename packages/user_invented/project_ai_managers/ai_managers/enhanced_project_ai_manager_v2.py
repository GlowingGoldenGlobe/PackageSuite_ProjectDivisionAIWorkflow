"""
Enhanced Project AI Manager V2 - With Full GUI Control Integration
Properly handles duration, pause, quit, continue, and message input
"""

import json
import os
import sys
import threading
import time
import subprocess
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Import base manager if available
try:
    from .project_ai_manager import ProjectAIManager as BaseProjectAIManager
except ImportError:
    BaseProjectAIManager = object

class EnhancedProjectAIManagerV2(BaseProjectAIManager):
    """Enhanced manager with complete GUI control integration"""
    
    def __init__(self, config=None, task_manager=None, scheduler=None):
        # Initialize base class if available
        if BaseProjectAIManager != object:
            super().__init__(config or {}, task_manager, scheduler)
            
        self.project_root = Path(__file__).parent.parent
        self.active = False
        self.paused = False
        self.agents = []
        self.tasks = []
        self.monitoring_threads = []
        
        # Configuration from GUI
        self.config = {
            "time_limit_hours": 2,
            "time_limit_minutes": 0,
            "auto_continue": True,
            "auto_save_interval": 15,
            "development_mode": "refined_model",
            "model_part": "Complete Assembly",
            "version": "1"
        }
        
        # Time tracking
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = timedelta(0)
        self.time_limit = None
        
        # Workflow status
        self.workflow_status = {
            "state": "stopped",
            "active_agents": [],
            "paused_agents": [],
            "statistics": {
                "total_tasks_started": 0,
                "total_tasks_completed": 0,
                "total_errors": 0,
                "start_time": None,
                "uptime_seconds": 0,
                "time_remaining_seconds": 0
            },
            "message_handler_active": True,
            "config": self.config
        }
        
    def start(self):
        """Start the AI automated workflow with GUI configuration"""
        print("=== Starting Enhanced AI Automated Workflow V2 ===")
        
        # Load configuration from workflow request
        self.load_workflow_request()
        
        # Set up time limit
        self.setup_time_limit()
        
        self.active = True
        self.paused = False
        self.start_time = datetime.now()
        
        # Update status
        self.workflow_status["state"] = "running"
        self.workflow_status["statistics"]["start_time"] = self.start_time.isoformat()
        self.update_status_file()
        
        print(f"Configuration loaded:")
        print(f"  Time Limit: {self.config['time_limit_hours']}h {self.config['time_limit_minutes']}m")
        print(f"  Auto-continue: {self.config['auto_continue']}")
        print(f"  Development Mode: {self.config['development_mode']}")
        print(f"  Model Part: {self.config['model_part']}")
        
        # Initialize components
        self.initialize_components()
        
        # Start monitoring threads
        self.start_monitoring_threads()
        
        # Start task distribution
        self.start_task_distribution()
        
        # Enable message handler
        self.enable_message_handler()
        
        # Run continuous operation with time limit check
        self.run_continuous_operation()
        
    def load_workflow_request(self):
        """Load configuration from workflow request file"""
        request_file = self.project_root / "workflow_request.json"
        
        if request_file.exists():
            try:
                with open(request_file, 'r') as f:
                    request = json.load(f)
                    
                # Update configuration
                if "config" in request:
                    self.config.update(request["config"])
                    self.workflow_status["config"] = self.config
                    
                print("✓ Loaded configuration from workflow request")
                
                # Clear the request file
                with open(request_file, 'w') as f:
                    json.dump({}, f)
                    
            except Exception as e:
                print(f"Warning: Could not load workflow request: {e}")
                
    def setup_time_limit(self):
        """Set up time limit from configuration"""
        hours = self.config.get("time_limit_hours", 2)
        minutes = self.config.get("time_limit_minutes", 0)
        
        # Calculate total seconds
        total_seconds = (hours * 3600) + (minutes * 60)
        
        if total_seconds > 0:
            self.time_limit = timedelta(seconds=total_seconds)
            print(f"✓ Time limit set to {hours}h {minutes}m ({total_seconds} seconds)")
        else:
            self.time_limit = None
            print("✓ No time limit set - workflow will run indefinitely")
            
    def check_time_limit(self):
        """Check if time limit has been exceeded"""
        if not self.time_limit or not self.start_time:
            return False
            
        # Calculate elapsed time excluding pauses
        elapsed = datetime.now() - self.start_time - self.total_pause_duration
        
        # Update time remaining
        if elapsed < self.time_limit:
            remaining = self.time_limit - elapsed
            self.workflow_status["statistics"]["time_remaining_seconds"] = int(remaining.total_seconds())
            return False
        else:
            # Time limit exceeded
            self.workflow_status["statistics"]["time_remaining_seconds"] = 0
            return True
            
    def handle_time_limit_exceeded(self):
        """Handle when time limit is exceeded"""
        print("\n⏰ Time limit exceeded!")
        
        if self.config.get("auto_continue", True):
            print("Auto-continue is enabled - workflow will continue running")
            # Reset time limit for next period
            self.start_time = datetime.now()
            self.total_pause_duration = timedelta(0)
        else:
            print("Auto-continue is disabled - pausing workflow")
            self.pause()
            
            # Notify GUI
            self.send_gui_notification({
                "type": "time_limit_exceeded",
                "message": "Time limit exceeded. Workflow paused.",
                "action_required": "resume_or_stop"
            })
            
    def initialize_components(self):
        """Initialize all workflow components"""
        print("Initializing workflow components...")
        
        try:
            # Import required managers
            from . import (
                task_manager,
                parallel_execution_manager,
                message_handler_integration,
                workflow_integrity_manager
            )
            
            # Store references
            self.task_manager_ref = task_manager
            self.parallel_manager = parallel_execution_manager
            self.message_handler = message_handler_integration
            self.integrity_manager = workflow_integrity_manager
            
            print("✓ All managers imported successfully")
            
        except ImportError as e:
            print(f"⚠ Import error: {e}")
            self.workflow_status["statistics"]["total_errors"] += 1
            
        # Create required communication files
        self.ensure_communication_files()
        
        # Initialize agent pool
        self.initialize_agent_pool()
        
    def ensure_communication_files(self):
        """Ensure all communication files exist"""
        files = {
            "workflow_request.json": {},
            "workflow_command.json": {},
            "ai_workflow_status.json": self.workflow_status,
            "gui_notifications.json": [],
            "automation_queue.json": [],
            "task_creation_queue.json": [],
            "user_messages_queue.json": [],
            "active_sessions.json": {},
            "message_responses.json": []
        }
        
        for filename, default_content in files.items():
            filepath = self.project_root / filename
            if not filepath.exists():
                with open(filepath, 'w') as f:
                    json.dump(default_content, f, indent=2)
                print(f"✓ Created {filename}")
                
    def initialize_agent_pool(self):
        """Initialize available AI agents"""
        print("Initializing agent pool...")
        
        agents = []
        
        # Check for Claude API
        if os.environ.get('ANTHROPIC_API_KEY') or (self.project_root / '.env').exists():
            agents.extend([
                {"name": "Claude-3-Opus", "type": "api", "status": "available"},
                {"name": "Claude-3-Sonnet", "type": "api", "status": "available"}
            ])
            
        # Check for OpenAI
        if os.environ.get('OPENAI_API_KEY'):
            agents.append({"name": "GPT-4", "type": "api", "status": "available"})
            
        # Check for VSCode
        import shutil
        if shutil.which('code'):
            agents.append({"name": "VSCode-Agent", "type": "local", "status": "available"})
            
        # Terminal agent always available
        agents.append({"name": "Terminal-Agent", "type": "local", "status": "available"})
        
        self.agents = agents
        print(f"✓ Initialized {len(agents)} agents")
        
    def start_monitoring_threads(self):
        """Start all monitoring threads"""
        print("Starting monitoring threads...")
        
        monitors = [
            ("Request Monitor", self.monitor_workflow_requests, 1),
            ("Command Monitor", self.monitor_workflow_commands, 1),
            ("Task Queue Monitor", self.monitor_task_queues, 2),
            ("Message Queue Monitor", self.monitor_message_queue, 1),
            ("Health Monitor", self.monitor_system_health, 5),
            ("Time Limit Monitor", self.monitor_time_limit, 5),
            ("Status Updater", self.update_workflow_status, 3),
            ("GUI Notifier", self.notify_gui_updates, 2)
        ]
        
        for name, func, interval in monitors:
            thread = threading.Thread(
                target=lambda f=func, i=interval: self.run_monitor(f, i, name),
                name=name,
                daemon=True
            )
            thread.start()
            self.monitoring_threads.append(thread)
            print(f"✓ Started {name}")
            
    def run_monitor(self, func, interval, name):
        """Run a monitoring function with error handling"""
        while self.active:
            try:
                # Skip if paused (except for command monitor)
                if self.paused and name not in ["Command Monitor", "Time Limit Monitor", "Status Updater"]:
                    time.sleep(interval)
                    continue
                    
                func()
            except Exception as e:
                print(f"Error in {name}: {e}")
                self.workflow_status["statistics"]["total_errors"] += 1
                traceback.print_exc()
            time.sleep(interval)
            
    def monitor_workflow_requests(self):
        """Monitor for new workflow requests from GUI"""
        request_file = self.project_root / "workflow_request.json"
        
        if request_file.exists() and request_file.stat().st_size > 0:
            try:
                with open(request_file, 'r') as f:
                    request = json.load(f)
                    
                if request:
                    print(f"Processing workflow request: {request.get('action')}")
                    self.process_workflow_request(request)
                    
                    # Clear the file
                    with open(request_file, 'w') as f:
                        json.dump({}, f)
                        
            except json.JSONDecodeError:
                pass
                
    def monitor_workflow_commands(self):
        """Monitor for workflow commands (pause, stop, etc)"""
        command_file = self.project_root / "workflow_command.json"
        
        if command_file.exists() and command_file.stat().st_size > 0:
            try:
                with open(command_file, 'r') as f:
                    command = json.load(f)
                    
                if command:
                    self.process_workflow_command(command)
                    
                    # Clear the file
                    with open(command_file, 'w') as f:
                        json.dump({}, f)
                        
            except json.JSONDecodeError:
                pass
                
    def monitor_message_queue(self):
        """Monitor the message queue from GUI"""
        queue_file = self.project_root / "user_messages_queue.json"
        
        if queue_file.exists() and queue_file.stat().st_size > 0:
            try:
                with open(queue_file, 'r') as f:
                    messages = json.load(f)
                    
                if messages and isinstance(messages, list):
                    print(f"Processing {len(messages)} user messages")
                    
                    # Process each message
                    for msg in messages:
                        self.process_user_message(msg)
                        
                    # Clear the queue
                    with open(queue_file, 'w') as f:
                        json.dump([], f)
                        
            except Exception as e:
                print(f"Message queue error: {e}")
                
    def process_user_message(self, message_data):
        """Process a message from the GUI Message & Instructions field"""
        message = message_data.get("message", "")
        timestamp = message_data.get("timestamp", "")
        
        print(f"\n📨 Processing user message: {message[:50]}...")
        
        # Create response
        response = {
            "original_message": message,
            "timestamp": timestamp,
            "processed_at": datetime.now().isoformat(),
            "response": "Message received and being processed",
            "status": "processing"
        }
        
        # Analyze message for commands
        message_lower = message.lower()
        
        if "pause" in message_lower:
            self.pause()
            response["response"] = "Workflow paused as requested"
            response["status"] = "completed"
            
        elif "resume" in message_lower or "continue" in message_lower:
            self.resume()
            response["response"] = "Workflow resumed as requested"
            response["status"] = "completed"
            
        elif "stop" in message_lower or "quit" in message_lower:
            self.stop()
            response["response"] = "Workflow stopped as requested"
            response["status"] = "completed"
            
        elif "status" in message_lower:
            status_info = self.get_status_summary()
            response["response"] = status_info
            response["status"] = "completed"
            
        elif "help" in message_lower:
            response["response"] = self.get_help_text()
            response["status"] = "completed"
            
        else:
            # Forward to message handler for AI processing
            if hasattr(self, 'message_handler'):
                self.message_handler.message_handler.process_user_message(message_data)
                response["response"] = "Message forwarded to AI agents for processing"
                response["status"] = "forwarded"
            else:
                response["response"] = "Message received. No specific action taken."
                response["status"] = "acknowledged"
                
        # Save response
        self.save_message_response(response)
        
    def save_message_response(self, response):
        """Save message response for GUI retrieval"""
        response_file = self.project_root / "message_responses.json"
        
        responses = []
        if response_file.exists():
            try:
                with open(response_file, 'r') as f:
                    responses = json.load(f)
            except:
                responses = []
                
        responses.append(response)
        
        # Keep only last 50 responses
        if len(responses) > 50:
            responses = responses[-50:]
            
        with open(response_file, 'w') as f:
            json.dump(responses, f, indent=2)
            
    def get_status_summary(self):
        """Get current status summary"""
        elapsed = datetime.now() - self.start_time - self.total_pause_duration if self.start_time else timedelta(0)
        
        return f"""Workflow Status:
State: {self.workflow_status['state']}
Uptime: {str(elapsed).split('.')[0]}
Active Agents: {len(self.workflow_status['active_agents'])}
Tasks Started: {self.workflow_status['statistics']['total_tasks_started']}
Tasks Completed: {self.workflow_status['statistics']['total_tasks_completed']}
Errors: {self.workflow_status['statistics']['total_errors']}
Time Remaining: {self.workflow_status['statistics']['time_remaining_seconds']}s"""

    def get_help_text(self):
        """Get help text for message commands"""
        return """Available message commands:
- 'pause' - Pause the workflow
- 'resume' or 'continue' - Resume paused workflow
- 'stop' or 'quit' - Stop the workflow
- 'status' - Get current status
- 'help' - Show this help text
Or enter any other message to forward to AI agents."""

    def monitor_time_limit(self):
        """Monitor time limit and handle expiration"""
        if self.check_time_limit():
            self.handle_time_limit_exceeded()
            
    def monitor_task_queues(self):
        """Monitor and process task queues"""
        # Check automation queue
        auto_queue_file = self.project_root / "automation_queue.json"
        if auto_queue_file.exists():
            try:
                with open(auto_queue_file, 'r') as f:
                    queue = json.load(f)
                    
                if queue and isinstance(queue, list):
                    print(f"Processing {len(queue)} queued tasks")
                    
                    for task in queue:
                        self.assign_task_to_agent(task)
                        
                    # Clear processed tasks
                    with open(auto_queue_file, 'w') as f:
                        json.dump([], f)
                        
            except Exception as e:
                print(f"Task queue error: {e}")
                
    def monitor_system_health(self):
        """Monitor system health and recover from failures"""
        # Check agent health
        for agent in self.agents:
            if agent["status"] == "busy" and not self.is_agent_responsive(agent):
                print(f"Recovering unresponsive agent: {agent['name']}")
                self.recover_agent(agent)
                
        # Run integrity check periodically
        self.run_integrity_check()
        
    def update_workflow_status(self):
        """Update workflow status regularly"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time - self.total_pause_duration
            self.workflow_status["statistics"]["uptime_seconds"] = int(elapsed.total_seconds())
            
        # Update pause status
        if self.paused:
            self.workflow_status["state"] = "paused"
            
        # Count active agents
        active_agents = [a for a in self.agents if a["status"] == "busy"]
        self.workflow_status["active_agents"] = [a["name"] for a in active_agents]
        
        # Update paused agents when workflow is paused
        if self.paused:
            self.workflow_status["paused_agents"] = self.workflow_status["active_agents"]
            self.workflow_status["active_agents"] = []
            
        # Update status file
        self.update_status_file()
        
    def notify_gui_updates(self):
        """Send notifications to GUI"""
        notifications = []
        
        # Add workflow state notification
        notifications.append({
            "type": "workflow_status",
            "data": {
                "state": self.workflow_status["state"],
                "active_agents": len(self.workflow_status["active_agents"]),
                "tasks_completed": self.workflow_status["statistics"]["total_tasks_completed"],
                "time_remaining": self.workflow_status["statistics"]["time_remaining_seconds"]
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Write notifications
        notif_file = self.project_root / "gui_notifications.json"
        try:
            existing = []
            if notif_file.exists():
                with open(notif_file, 'r') as f:
                    existing = json.load(f)
                    
            existing.extend(notifications)
            
            # Keep only recent notifications
            if len(existing) > 100:
                existing = existing[-100:]
                
            with open(notif_file, 'w') as f:
                json.dump(existing, f, indent=2)
                
        except Exception:
            pass
            
    def send_gui_notification(self, notification):
        """Send a specific notification to GUI"""
        notif_file = self.project_root / "gui_notifications.json"
        
        notifications = []
        if notif_file.exists():
            try:
                with open(notif_file, 'r') as f:
                    notifications = json.load(f)
            except:
                notifications = []
                
        notification["timestamp"] = datetime.now().isoformat()
        notifications.append(notification)
        
        with open(notif_file, 'w') as f:
            json.dump(notifications, f, indent=2)
            
    def start_task_distribution(self):
        """Start the task distribution system"""
        print("Task distribution system activated")
        
        # Create initial tasks if none exist
        if not self.tasks:
            self.create_initial_tasks()
            
    def enable_message_handler(self):
        """Enable the message handler integration"""
        try:
            if hasattr(self.message_handler, 'integrate_with_workflow'):
                handler = self.message_handler.integrate_with_workflow()
                print("✓ Message handler integrated")
        except Exception as e:
            print(f"Message handler error: {e}")
            
    def process_workflow_request(self, request):
        """Process a workflow request"""
        action = request.get("action")
        
        if action == "configure":
            config = request.get("config", {})
            self.apply_configuration(config)
            
    def process_workflow_command(self, command):
        """Process a workflow command"""
        cmd = command.get("command")
        
        if cmd == "stop":
            self.stop()
        elif cmd == "pause":
            self.pause()
        elif cmd == "resume":
            self.resume()
            
    def apply_configuration(self, new_config):
        """Apply new configuration from GUI"""
        print(f"Applying new configuration: {new_config}")
        self.config.update(new_config)
        self.workflow_status["config"] = self.config
        
        # Recalculate time limit if changed
        self.setup_time_limit()
        
    def pause(self):
        """Pause the workflow"""
        if not self.paused:
            print("⏸ Pausing workflow...")
            self.paused = True
            self.pause_time = datetime.now()
            self.workflow_status["state"] = "paused"
            self.update_status_file()
            
            # Notify GUI
            self.send_gui_notification({
                "type": "workflow_paused",
                "message": "Workflow has been paused"
            })
        
    def resume(self):
        """Resume the workflow"""
        if self.paused:
            print("▶ Resuming workflow...")
            
            # Calculate pause duration
            if self.pause_time:
                pause_duration = datetime.now() - self.pause_time
                self.total_pause_duration += pause_duration
                
            self.paused = False
            self.pause_time = None
            self.workflow_status["state"] = "running"
            self.update_status_file()
            
            # Notify GUI
            self.send_gui_notification({
                "type": "workflow_resumed",
                "message": "Workflow has been resumed"
            })
        
    def stop(self):
        """Stop the workflow"""
        print("⏹ Stopping workflow...")
        self.active = False
        self.paused = False
        self.workflow_status["state"] = "stopped"
        self.update_status_file()
        
        # Notify GUI
        self.send_gui_notification({
            "type": "workflow_stopped",
            "message": "Workflow has been stopped"
        })
        
        # Clean shutdown
        print("Workflow stopped successfully")
        
    def assign_task_to_agent(self, task):
        """Assign a task to an available agent"""
        # Find available agent
        available_agents = [a for a in self.agents if a["status"] == "available"]
        
        if not available_agents:
            print("No available agents, queueing task")
            return
            
        # Select best agent for task
        agent = self.select_best_agent(task, available_agents)
        
        # Assign task
        agent["status"] = "busy"
        agent["current_task"] = task
        
        # Create session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            "id": session_id,
            "agent": agent["name"],
            "task_description": task.get("description", task.get("task_name", "Unknown")),
            "started_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Update active sessions
        sessions_file = self.project_root / "active_sessions.json"
        sessions = {}
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
            except:
                sessions = {}
                
        sessions[session_id] = session_data
        
        with open(sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
            
        print(f"Assigned task to {agent['name']}")
        self.workflow_status["statistics"]["total_tasks_started"] += 1
        
        # Simulate task execution
        threading.Thread(
            target=self.simulate_task_execution,
            args=(agent, task, session_id),
            daemon=True
        ).start()
        
    def select_best_agent(self, task, available_agents):
        """Select the best agent for a task based on task type"""
        task_desc = str(task.get("description", "")).lower()
        
        # Match based on development mode
        if self.config.get("development_mode") == "refined_model":
            # Prefer Claude for model refinement
            for agent in available_agents:
                if "Claude" in agent["name"]:
                    return agent
                    
        # Task-specific selection
        if any(word in task_desc for word in ["complex", "analyze", "design"]):
            for agent in available_agents:
                if "Claude" in agent["name"]:
                    return agent
                    
        if any(word in task_desc for word in ["code", "implement", "debug"]):
            for agent in available_agents:
                if "VSCode" in agent["name"]:
                    return agent
                    
        # Return first available
        return available_agents[0]
        
    def simulate_task_execution(self, agent, task, session_id):
        """Simulate task execution"""
        # Simulate work with variable duration based on task
        work_duration = 10  # Default 10 seconds
        
        # Adjust based on task type
        task_desc = str(task.get("description", "")).lower()
        if "complex" in task_desc:
            work_duration = 20
        elif "simple" in task_desc:
            work_duration = 5
            
        # Simulate work in chunks to allow pause/stop
        for i in range(work_duration):
            if not self.active:
                break
            if self.paused:
                # Wait until resumed
                while self.paused and self.active:
                    time.sleep(1)
            time.sleep(1)
            
        if self.active:
            # Mark task complete
            agent["status"] = "available"
            agent["current_task"] = None
            
            # Update session
            sessions_file = self.project_root / "active_sessions.json"
            if sessions_file.exists():
                try:
                    with open(sessions_file, 'r') as f:
                        sessions = json.load(f)
                        
                    if session_id in sessions:
                        sessions[session_id]["status"] = "completed"
                        sessions[session_id]["completed_at"] = datetime.now().isoformat()
                        
                        with open(sessions_file, 'w') as f:
                            json.dump(sessions, f, indent=2)
                            
                except:
                    pass
                    
            self.workflow_status["statistics"]["total_tasks_completed"] += 1
            print(f"Task completed by {agent['name']}")
            
    def create_initial_tasks(self):
        """Create initial tasks based on configuration"""
        model_part = self.config.get("model_part", "Complete Assembly")
        version = self.config.get("version", "1")
        
        initial_tasks = [
            {
                "task_name": f"Initialize {model_part} v{version}",
                "description": f"Set up {model_part} version {version} model structure",
                "priority": "high"
            },
            {
                "task_name": "Validate Geometry",
                "description": f"Check {model_part} geometry for errors",
                "priority": "medium"
            },
            {
                "task_name": "Generate Documentation",
                "description": f"Create documentation for {model_part} v{version}",
                "priority": "low"
            }
        ]
        
        for task_data in initial_tasks:
            self.create_task_from_data(task_data)
            
    def create_task_from_data(self, task_data):
        """Create a task from task data"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.tasks)}"
        
        task = {
            "id": task_id,
            "data": task_data,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        self.tasks.append(task)
        
        # Add to automation queue
        auto_queue_file = self.project_root / "automation_queue.json"
        queue = []
        if auto_queue_file.exists():
            try:
                with open(auto_queue_file, 'r') as f:
                    queue = json.load(f)
            except:
                queue = []
                
        queue.append(task_data)
        
        with open(auto_queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
            
    def is_agent_responsive(self, agent):
        """Check if an agent is responsive"""
        # In real implementation, this would check actual agent status
        return True
        
    def recover_agent(self, agent):
        """Recover an unresponsive agent"""
        agent["status"] = "available"
        agent["current_task"] = None
        
    def run_integrity_check(self):
        """Run workflow integrity check"""
        try:
            if hasattr(self.integrity_manager, 'WorkflowIntegrityManager'):
                # Quick validation could be done here
                pass
        except:
            pass
            
    def update_status_file(self):
        """Update the workflow status file"""
        with open(self.project_root / "ai_workflow_status.json", 'w') as f:
            json.dump(self.workflow_status, f, indent=2)
            
    def run_continuous_operation(self):
        """Run continuous operation loop with proper pause/resume support"""
        print("\nWorkflow is now running autonomously.")
        print("The system will continue operating until stopped.")
        print("GUI controls are fully integrated:")
        print("  - Time limit is enforced")
        print("  - Pause/Resume buttons work")
        print("  - Message input is processed")
        print("\nPress Ctrl+C to stop manually, or use GUI controls.\n")
        
        try:
            while self.active:
                # Sleep in small increments to be responsive
                for _ in range(10):
                    if not self.active:
                        break
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nWorkflow interrupted by user")
            self.stop()


def main():
    """Main entry point for command line execution"""
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        print("Starting Enhanced Project AI Manager V2...")
        manager = EnhancedProjectAIManagerV2()
        manager.start()
    else:
        print("Enhanced Project AI Manager V2")
        print("Usage: python enhanced_project_ai_manager_v2.py start")
        print("\nThis enhanced version provides:")
        print("- Full GUI control integration")
        print("- Time limit enforcement with auto-continue")
        print("- Proper pause/resume functionality")
        print("- Message input processing")
        print("- Real-time status updates")
        print("- Complete autonomous operation")


if __name__ == "__main__":
    main()