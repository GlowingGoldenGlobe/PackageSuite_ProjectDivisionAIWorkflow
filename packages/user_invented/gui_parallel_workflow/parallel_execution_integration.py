#!/usr/bin/env python
"""
Integration Example for Parallel Execution Manager in GlowingGoldenGlobe project
"""

import os
import sys
import time
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parallel_execution_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ParallelExecutionIntegration")

# Get the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Import directly from file
pem_path = os.path.join(base_dir, "ai_managers", "parallel_execution_manager.py")
spec = importlib.util.spec_from_file_location("parallel_execution_manager", pem_path)
if spec and spec.loader:
    pem_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pem_module)
    ParallelExecutionManager = pem_module.ParallelExecutionManager
else:
    logger.error(f"Could not import ParallelExecutionManager from {pem_path}")
    sys.exit(1)

class GGGParallelSystem:
    """Integration class for the Parallel Execution Manager"""
    
    def __init__(self):
        """Initialize the parallel system"""
        logger.info("Initializing GGG Parallel System")
        self.pem = ParallelExecutionManager()
        
    def start(self):
        """Start the parallel execution system"""
        logger.info("Starting parallel execution system")
        
        # Start the system with monitoring
        self.pem.start_monitoring()
        
        # Start high-priority roles first
        logger.info("Starting resource management")
        self.pem._start_role_thread(self.pem.ROLE_RESOURCE_MANAGEMENT)
        time.sleep(2)  # Give it time to initialize
        
        logger.info("Starting project management")
        self.pem._start_role_thread(self.pem.ROLE_PROJECT_MANAGEMENT)
        time.sleep(2)
        
        logger.info("Starting task management")
        self.pem._start_role_thread(self.pem.ROLE_TASK_MANAGEMENT)
        time.sleep(2)
        
        # Check if we have resources for more roles
        if self.pem.current_resources["cpu_percent"] < 70 and self.pem.current_resources["memory_percent"] < 70:
            logger.info("Resources available, starting script assessment")
            self.pem._start_role_thread(self.pem.ROLE_SCRIPT_ASSESSMENT)
            
            # Queue some initial script assessment tasks
            self._queue_initial_assessments()
            
        logger.info("Parallel system started successfully")
        return True
        
    def stop(self):
        """Stop the parallel execution system"""
        logger.info("Stopping parallel execution system")
        self.pem.stop_all_roles()
        logger.info("Parallel system stopped")
        return True
    
    def _queue_initial_assessments(self):
        """Queue initial script assessment tasks"""
        # Find Python files that might need assessment
        py_files = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('_'):
                    # Skip files in certain directories
                    if any(skip_dir in root for skip_dir in ['__pycache__', '.git', 'venv', 'Lib']):
                        continue
                    py_files.append(os.path.join(root, file))
        
        # Queue up to 5 files for assessment
        for script_path in py_files[:5]:
            task = {
                "name": f"Initial assessment: {os.path.basename(script_path)}",
                "script_path": script_path,
                "priority": "normal"
            }
            self.pem.queue_task(self.pem.ROLE_SCRIPT_ASSESSMENT, task)
            logger.info(f"Queued assessment for {os.path.basename(script_path)}")

    def status(self):
        """Get the current status of the parallel execution system"""
        status = {
            "active_roles": list(self.pem.active_roles),
            "resources": {
                "cpu_percent": self.pem.current_resources["cpu_percent"],
                "memory_percent": self.pem.current_resources["memory_percent"],
                "disk_percent": self.pem.current_resources["disk_percent"]
            },
            "queue_sizes": {}
        }
        
        # Add queue sizes
        for role, queue_obj in self.pem.execution_queues.items():
            status["queue_sizes"][role] = queue_obj.qsize()
        
        return status

# Simple command-line interface for testing
if __name__ == "__main__":
    print("GlowingGoldenGlobe Parallel Execution System Integration")
    print("=" * 60)
    
    # Create and start the system
    system = GGGParallelSystem()
    
    try:
        # Start the system
        system.start()
        
        # Display status every 5 seconds
        for i in range(6):  # Run for about 30 seconds
            time.sleep(5)
            status = system.status()
            
            print(f"\nStatus Update {i+1}/6:")
            print(f"  Active Roles: {', '.join(status['active_roles'])}")
            print(f"  CPU Usage: {status['resources']['cpu_percent']}%")
            print(f"  Memory Usage: {status['resources']['memory_percent']}%")
            
            # Show queues with tasks
            for role, size in status["queue_sizes"].items():
                if size > 0:
                    print(f"  Queue '{role}': {size} tasks pending")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down...")
    finally:
        # Stop the system
        system.stop()
        print("System stopped.")
