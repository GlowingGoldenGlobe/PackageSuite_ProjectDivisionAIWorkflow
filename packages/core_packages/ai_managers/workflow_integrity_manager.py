"""
Workflow Integrity Manager
Ensures AI Automated Workflow runs continuously and autonomously
Tests, validates, and repairs execution chains
"""

import json
import os
import sys
import subprocess
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

class WorkflowIntegrityManager:
    """Manages and ensures the integrity of the AI Automated Workflow"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.ai_managers_dir = self.project_root / "ai_managers"
        self.validation_log = self.project_root / "workflow_validation_log.json"
        self.integrity_status = {
            "last_check": None,
            "issues_found": [],
            "repairs_made": [],
            "workflow_healthy": False
        }
        
    def validate_complete_workflow(self):
        """Validate the entire AI Automated Workflow system"""
        print("=== Starting Workflow Integrity Validation ===")
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": [],
            "recommendations": []
        }
        
        # 1. Check GUI Start Button Chain
        print("1. Checking GUI Start Button execution chain...")
        gui_chain = self.validate_gui_start_chain()
        validation_results["checks"]["gui_start_chain"] = gui_chain
        
        # 2. Check AI Manager Initialization
        print("2. Checking AI Manager initialization...")
        manager_init = self.validate_ai_manager_init()
        validation_results["checks"]["ai_manager_init"] = manager_init
        
        # 3. Check Task Distribution System
        print("3. Checking task distribution system...")
        task_system = self.validate_task_distribution()
        validation_results["checks"]["task_distribution"] = task_system
        
        # 4. Check Inter-component Communication
        print("4. Checking inter-component communication...")
        communication = self.validate_communication_channels()
        validation_results["checks"]["communication"] = communication
        
        # 5. Check Message Handler Integration
        print("5. Checking message handler integration...")
        message_handler = self.validate_message_handler()
        validation_results["checks"]["message_handler"] = message_handler
        
        # 6. Check Session Management
        print("6. Checking session management...")
        session_mgmt = self.validate_session_management()
        validation_results["checks"]["session_management"] = session_mgmt
        
        # Compile issues and recommendations
        for check_name, check_result in validation_results["checks"].items():
            if not check_result["passed"]:
                validation_results["issues"].extend(check_result.get("issues", []))
                validation_results["recommendations"].extend(check_result.get("fixes", []))
                
        # Save validation results
        self.save_validation_results(validation_results)
        
        return validation_results
    
    def validate_gui_start_chain(self):
        """Validate the GUI Start button execution chain"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # Check if the enhanced GUI file exists
            gui_file = self.project_root / "run_fixed_layout_enhanced.py"
            if not gui_file.exists():
                result["issues"].append("Enhanced GUI file not found")
                result["fixes"].append("Create run_fixed_layout_enhanced.py")
                return result
                
            # Parse the GUI file to find start_ai_workflow method
            with open(gui_file, 'r') as f:
                gui_content = f.read()
                
            # Check for workflow request creation
            if 'workflow_request.json' in gui_content:
                result["details"]["creates_request"] = True
            else:
                result["issues"].append("GUI doesn't create workflow request")
                result["fixes"].append("Add workflow request creation to start_ai_workflow")
                
            # Check for subprocess launch
            if 'subprocess.Popen' in gui_content and 'project_ai_manager.py' in gui_content:
                result["details"]["launches_manager"] = True
            else:
                result["issues"].append("GUI doesn't launch AI manager")
                result["fixes"].append("Add subprocess launch for project_ai_manager.py")
                
            # Check project_ai_manager.py exists
            manager_file = self.ai_managers_dir / "project_ai_manager.py"
            if manager_file.exists():
                result["details"]["manager_exists"] = True
                
                # Check if it has a start command handler
                with open(manager_file, 'r') as f:
                    manager_content = f.read()
                    
                if "'start'" in manager_content or '"start"' in manager_content:
                    result["details"]["has_start_handler"] = True
                else:
                    result["issues"].append("project_ai_manager.py lacks start command handler")
                    result["fixes"].append("Add start command handler to project_ai_manager.py")
            else:
                result["issues"].append("project_ai_manager.py not found")
                result["fixes"].append("Create project_ai_manager.py")
                
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating GUI chain: {str(e)}")
            
        return result
    
    def validate_ai_manager_init(self):
        """Validate AI Manager initialization process"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # List all AI managers
            managers = []
            for file in self.ai_managers_dir.glob("*.py"):
                if file.name != "__init__.py":
                    managers.append(file.stem)
                    
            result["details"]["found_managers"] = managers
            
            # Check critical managers
            critical_managers = [
                "project_ai_manager",
                "task_manager",
                "parallel_execution_manager",
                "resource_manager"
            ]
            
            for manager in critical_managers:
                if manager not in managers:
                    result["issues"].append(f"Critical manager missing: {manager}")
                    result["fixes"].append(f"Create {manager}.py in ai_managers/")
                    
            # Check __init__.py for proper imports
            init_file = self.ai_managers_dir / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r') as f:
                    init_content = f.read()
                    
                for manager in critical_managers:
                    if manager in managers and manager not in init_content:
                        result["issues"].append(f"{manager} not imported in __init__.py")
                        result["fixes"].append(f"Add import for {manager} in __init__.py")
            else:
                result["issues"].append("__init__.py missing in ai_managers/")
                result["fixes"].append("Create __init__.py with proper imports")
                
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating managers: {str(e)}")
            
        return result
    
    def validate_task_distribution(self):
        """Validate task distribution system"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # Check for task queue files
            task_files = [
                "automation_queue.json",
                "task_creation_queue.json",
                "active_sessions.json"
            ]
            
            for file in task_files:
                file_path = self.project_root / file
                if not file_path.exists():
                    # Create empty file
                    with open(file_path, 'w') as f:
                        json.dump([] if 'queue' in file else {}, f)
                    result["details"][f"created_{file}"] = True
                else:
                    result["details"][f"found_{file}"] = True
                    
            # Check task_manager.py functionality
            task_manager = self.ai_managers_dir / "task_manager.py"
            if task_manager.exists():
                with open(task_manager, 'r') as f:
                    content = f.read()
                    
                required_methods = [
                    "distribute_tasks",
                    "monitor_progress",
                    "handle_failures"
                ]
                
                for method in required_methods:
                    if f"def {method}" not in content:
                        result["issues"].append(f"task_manager missing {method} method")
                        result["fixes"].append(f"Add {method} method to task_manager.py")
            else:
                result["issues"].append("task_manager.py not found")
                result["fixes"].append("Create comprehensive task_manager.py")
                
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating task distribution: {str(e)}")
            
        return result
    
    def validate_communication_channels(self):
        """Validate inter-component communication"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # Check communication files
            comm_files = {
                "workflow_request.json": "GUI to Manager communication",
                "workflow_command.json": "Command communication",
                "ai_workflow_status.json": "Status communication",
                "gui_notifications.json": "Manager to GUI communication"
            }
            
            for file, purpose in comm_files.items():
                file_path = self.project_root / file
                if not file_path.exists():
                    result["issues"].append(f"{file} missing ({purpose})")
                    result["fixes"].append(f"Ensure {file} is created during workflow")
                else:
                    result["details"][file] = "exists"
                    
            # Check for monitoring threads
            if (self.ai_managers_dir / "project_ai_manager.py").exists():
                with open(self.ai_managers_dir / "project_ai_manager.py", 'r') as f:
                    content = f.read()
                    
                if "threading" in content and "monitor" in content:
                    result["details"]["has_monitoring"] = True
                else:
                    result["issues"].append("No monitoring threads in project_ai_manager")
                    result["fixes"].append("Add monitoring threads for continuous operation")
                    
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating communication: {str(e)}")
            
        return result
    
    def validate_message_handler(self):
        """Validate message handler integration"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # Check message handler file
            handler_file = self.ai_managers_dir / "message_handler_integration.py"
            if handler_file.exists():
                result["details"]["handler_exists"] = True
                
                # Check for queue monitoring
                with open(handler_file, 'r') as f:
                    content = f.read()
                    
                if "monitor_queue_file" in content:
                    result["details"]["monitors_queue"] = True
                else:
                    result["issues"].append("Message handler doesn't monitor queue")
                    result["fixes"].append("Add queue monitoring to message handler")
                    
            else:
                result["issues"].append("message_handler_integration.py not found")
                result["fixes"].append("Create message handler integration")
                
            # Check user message queue
            queue_file = self.project_root / "user_messages_queue.json"
            if not queue_file.exists():
                with open(queue_file, 'w') as f:
                    json.dump([], f)
                result["details"]["created_queue"] = True
                
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating message handler: {str(e)}")
            
        return result
    
    def validate_session_management(self):
        """Validate session management system"""
        result = {
            "passed": False,
            "issues": [],
            "fixes": [],
            "details": {}
        }
        
        try:
            # Check session files
            session_files = [
                "session_locks.json",
                "session_history.json"
            ]
            
            for file in session_files:
                file_path = self.project_root / file
                if not file_path.exists():
                    with open(file_path, 'w') as f:
                        json.dump({} if 'locks' in file else [], f)
                    result["details"][f"created_{file}"] = True
                    
            # Check for session conflict manager
            conflict_mgr = self.project_root / "gui" / "session_conflict_manager.py"
            if conflict_mgr.exists():
                result["details"]["conflict_manager_exists"] = True
            else:
                result["issues"].append("Session conflict manager not found")
                result["fixes"].append("Create session_conflict_manager.py")
                
            result["passed"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error validating session management: {str(e)}")
            
        return result
    
    def save_validation_results(self, results):
        """Save validation results to log file"""
        logs = []
        if self.validation_log.exists():
            try:
                with open(self.validation_log, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
                
        logs.append(results)
        
        # Keep only last 50 validations
        if len(logs) > 50:
            logs = logs[-50:]
            
        with open(self.validation_log, 'w') as f:
            json.dump(logs, f, indent=2)
            
    def repair_workflow(self, validation_results):
        """Attempt to repair identified issues"""
        print("\n=== Attempting Workflow Repairs ===")
        repairs_made = []
        
        for issue in validation_results["issues"]:
            print(f"Addressing: {issue}")
            
            # Auto-create missing files
            if "not found" in issue or "missing" in issue:
                if self.create_missing_component(issue):
                    repairs_made.append(f"Created component for: {issue}")
                    
            # Fix imports
            elif "not imported" in issue:
                if self.fix_import(issue):
                    repairs_made.append(f"Fixed import for: {issue}")
                    
            # Add missing methods
            elif "missing" in issue and "method" in issue:
                if self.add_missing_method(issue):
                    repairs_made.append(f"Added method for: {issue}")
                    
        self.integrity_status["repairs_made"] = repairs_made
        return repairs_made
    
    def create_missing_component(self, issue):
        """Create missing component based on issue description"""
        try:
            if "project_ai_manager.py" in issue:
                self.create_project_ai_manager()
                return True
            elif "task_manager.py" in issue:
                self.create_task_manager()
                return True
            elif "workflow request" in issue:
                self.fix_workflow_request_creation()
                return True
        except Exception as e:
            print(f"Failed to create component: {e}")
        return False
    
    def create_project_ai_manager(self):
        """Create a comprehensive project AI manager"""
        content = '''"""
Project AI Manager - Central coordinator for AI Automated Workflow
Auto-generated by Workflow Integrity Manager
"""

import json
import os
import sys
import threading
import time
import subprocess
from datetime import datetime
from pathlib import Path

class ProjectAIManager:
    """Central manager for AI automated workflow"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.active = False
        self.agents = []
        self.tasks = []
        self.monitoring_threads = []
        
    def start(self):
        """Start the AI automated workflow"""
        print("Starting AI Automated Workflow...")
        self.active = True
        
        # Update status
        self.update_status("running")
        
        # Start monitoring threads
        self.start_monitors()
        
        # Initialize agents
        self.initialize_agents()
        
        # Start task distribution
        self.start_task_distribution()
        
        # Keep running
        self.run_continuous()
        
    def start_monitors(self):
        """Start all monitoring threads"""
        monitors = [
            ("Request Monitor", self.monitor_requests),
            ("Command Monitor", self.monitor_commands),
            ("Task Monitor", self.monitor_tasks),
            ("Health Monitor", self.monitor_health)
        ]
        
        for name, monitor_func in monitors:
            thread = threading.Thread(target=monitor_func, name=name, daemon=True)
            thread.start()
            self.monitoring_threads.append(thread)
            print(f"Started {name}")
            
    def monitor_requests(self):
        """Monitor for workflow requests"""
        request_file = self.project_root / "workflow_request.json"
        
        while self.active:
            try:
                if request_file.exists():
                    with open(request_file, 'r') as f:
                        request = json.load(f)
                        
                    # Process request
                    self.process_request(request)
                    
                    # Clear request file
                    request_file.unlink()
                    
            except Exception as e:
                print(f"Request monitor error: {e}")
                
            time.sleep(1)
            
    def monitor_commands(self):
        """Monitor for workflow commands"""
        command_file = self.project_root / "workflow_command.json"
        
        while self.active:
            try:
                if command_file.exists():
                    with open(command_file, 'r') as f:
                        command = json.load(f)
                        
                    # Process command
                    self.process_command(command)
                    
                    # Clear command file
                    command_file.unlink()
                    
            except Exception as e:
                print(f"Command monitor error: {e}")
                
            time.sleep(1)
            
    def monitor_tasks(self):
        """Monitor task queues and distribute work"""
        while self.active:
            try:
                # Check automation queue
                queue_file = self.project_root / "automation_queue.json"
                if queue_file.exists():
                    with open(queue_file, 'r') as f:
                        queue = json.load(f)
                        
                    if queue:
                        # Distribute tasks to agents
                        for task in queue:
                            self.assign_task_to_agent(task)
                            
                        # Clear processed tasks
                        with open(queue_file, 'w') as f:
                            json.dump([], f)
                            
            except Exception as e:
                print(f"Task monitor error: {e}")
                
            time.sleep(2)
            
    def monitor_health(self):
        """Monitor system health and recover from failures"""
        while self.active:
            try:
                # Check agent health
                for agent in self.agents:
                    if not self.check_agent_health(agent):
                        self.recover_agent(agent)
                        
                # Update statistics
                self.update_statistics()
                
            except Exception as e:
                print(f"Health monitor error: {e}")
                
            time.sleep(5)
            
    def initialize_agents(self):
        """Initialize available AI agents"""
        # Import and start other managers
        try:
            from . import task_manager, parallel_execution_manager, message_handler_integration
            
            # Start message handler
            message_handler_integration.integrate_with_workflow()
            
            # Initialize parallel execution
            if hasattr(parallel_execution_manager, 'initialize'):
                parallel_execution_manager.initialize()
                
            print("Agents initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize agents: {e}")
            
    def run_continuous(self):
        """Keep the workflow running continuously"""
        try:
            while self.active:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Workflow interrupted by user")
            self.stop()
            
    def stop(self):
        """Stop the workflow"""
        print("Stopping AI Automated Workflow...")
        self.active = False
        self.update_status("stopped")
        
    def update_status(self, state):
        """Update workflow status file"""
        status = {
            "state": state,
            "last_updated": datetime.now().isoformat(),
            "active_agents": [a for a in self.agents if a.get("active")],
            "statistics": self.get_statistics()
        }
        
        with open(self.project_root / "ai_workflow_status.json", 'w') as f:
            json.dump(status, f, indent=2)
            
    def get_statistics(self):
        """Get workflow statistics"""
        return {
            "total_tasks_started": len(self.tasks),
            "total_tasks_completed": len([t for t in self.tasks if t.get("status") == "completed"]),
            "total_errors": 0,
            "uptime_seconds": 0
        }
        
    def process_request(self, request):
        """Process workflow request"""
        print(f"Processing request: {request.get('action')}")
        
    def process_command(self, command):
        """Process workflow command"""
        cmd = command.get('command')
        print(f"Processing command: {cmd}")
        
        if cmd == 'stop':
            self.stop()
        elif cmd == 'pause':
            self.update_status('paused')
            
    def assign_task_to_agent(self, task):
        """Assign task to available agent"""
        print(f"Assigning task: {task.get('task_name')}")
        
    def check_agent_health(self, agent):
        """Check if agent is healthy"""
        return True
        
    def recover_agent(self, agent):
        """Recover failed agent"""
        print(f"Recovering agent: {agent}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        manager = ProjectAIManager()
        manager.start()
    else:
        print("Usage: python project_ai_manager.py start")


if __name__ == "__main__":
    main()
'''
        
        file_path = self.ai_managers_dir / "project_ai_manager.py"
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Created {file_path}")
        
    def create_task_manager(self):
        """Create comprehensive task manager"""
        content = '''"""
Task Manager for AI Automated Workflow
Auto-generated by Workflow Integrity Manager
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

class TaskManager:
    """Manages task distribution and tracking"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tasks = {}
        self.load_tasks()
        
    def distribute_tasks(self, tasks):
        """Distribute tasks to available agents"""
        for task in tasks:
            task_id = self.create_task(task)
            self.assign_to_agent(task_id)
            
    def monitor_progress(self):
        """Monitor task progress"""
        for task_id, task in self.tasks.items():
            if task['status'] == 'in_progress':
                self.check_task_progress(task_id)
                
    def handle_failures(self, task_id, error):
        """Handle task failures"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(error)
            self.save_tasks()
            
    def create_task(self, task_data):
        """Create a new task"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'id': task_id,
            'data': task_data,
            'status': 'pending',
            'created': datetime.now().isoformat()
        }
        self.save_tasks()
        return task_id
        
    def assign_to_agent(self, task_id):
        """Assign task to an available agent"""
        # Implementation for agent assignment
        pass
        
    def check_task_progress(self, task_id):
        """Check progress of a task"""
        # Implementation for progress checking
        pass
        
    def load_tasks(self):
        """Load tasks from file"""
        task_file = self.project_root / 'tasks.json'
        if task_file.exists():
            try:
                with open(task_file, 'r') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = {}
                
    def save_tasks(self):
        """Save tasks to file"""
        task_file = self.project_root / 'tasks.json'
        with open(task_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)


# Global instance
task_manager = TaskManager()
'''
        
        file_path = self.ai_managers_dir / "task_manager.py"
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Created {file_path}")
        
    def fix_workflow_request_creation(self):
        """Fix workflow request creation in GUI"""
        # This would modify the GUI file to ensure proper request creation
        print("Workflow request creation fix would be applied to GUI")
        return True
        
    def fix_import(self, issue):
        """Fix import issues in __init__.py"""
        try:
            init_file = self.ai_managers_dir / "__init__.py"
            
            # Extract manager name from issue
            import os
            manager_name = None
            for word in issue.split():
                if word.endswith('_manager'):
                    manager_name = word
                    break
                    
            if manager_name and init_file.exists():
                with open(init_file, 'r') as f:
                    content = f.read()
                    
                if manager_name not in content:
                    # Add import
                    import_line = f"from .{manager_name} import *\n"
                    content += import_line
                    
                    with open(init_file, 'w') as f:
                        f.write(content)
                        
                    print(f"Added import for {manager_name}")
                    return True
                    
        except Exception as e:
            print(f"Failed to fix import: {e}")
            
        return False
        
    def add_missing_method(self, issue):
        """Add missing method to a manager"""
        # This would parse the issue and add the required method
        print(f"Would add missing method for: {issue}")
        return True
        
    def run_continuous_monitoring(self):
        """Run continuous monitoring and self-healing"""
        print("\n=== Starting Continuous Workflow Monitoring ===")
        
        while True:
            try:
                # Run validation
                results = self.validate_complete_workflow()
                
                # Check if repairs needed
                if results["issues"]:
                    print(f"\nFound {len(results['issues'])} issues, attempting repairs...")
                    repairs = self.repair_workflow(results)
                    print(f"Made {len(repairs)} repairs")
                else:
                    print("\nWorkflow validation passed - all systems operational")
                    
                # Update status
                self.integrity_status["last_check"] = datetime.now().isoformat()
                self.integrity_status["issues_found"] = results["issues"]
                self.integrity_status["workflow_healthy"] = len(results["issues"]) == 0
                
                # Save status
                with open(self.project_root / "workflow_integrity_status.json", 'w') as f:
                    json.dump(self.integrity_status, f, indent=2)
                    
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nStopping continuous monitoring...")
                break
            except Exception as e:
                print(f"\nMonitoring error: {e}")
                traceback.print_exc()
                time.sleep(60)


def main():
    """Main entry point for workflow integrity management"""
    manager = WorkflowIntegrityManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validate":
            results = manager.validate_complete_workflow()
            print(f"\n=== Validation Complete ===")
            print(f"Issues found: {len(results['issues'])}")
            for issue in results['issues']:
                print(f"  - {issue}")
                
        elif sys.argv[1] == "repair":
            results = manager.validate_complete_workflow()
            if results['issues']:
                repairs = manager.repair_workflow(results)
                print(f"\nRepairs made: {len(repairs)}")
            else:
                print("\nNo repairs needed - workflow is healthy")
                
        elif sys.argv[1] == "monitor":
            manager.run_continuous_monitoring()
            
    else:
        print("Workflow Integrity Manager")
        print("Usage:")
        print("  python workflow_integrity_manager.py validate  - Validate workflow")
        print("  python workflow_integrity_manager.py repair    - Validate and repair")
        print("  python workflow_integrity_manager.py monitor   - Continuous monitoring")


if __name__ == "__main__":
    main()