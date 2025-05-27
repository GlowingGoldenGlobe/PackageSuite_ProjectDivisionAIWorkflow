#!/usr/bin/env python3
"""
AI Assessment Controls for Session Management
Provides AI with decision-making capabilities during session startup and task completion
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import time

class AISessionAssessmentControls:
    """Controls for AI to assess and configure session startup"""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "ai_session_assessment.json"
        self.assessment_lock = threading.Lock()
        self.load_config()
    
    def load_config(self):
        """Load or create assessment configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "session_assessments": {},
                "auto_adjustments": {
                    "enabled": True,
                    "max_agents": 5,
                    "resource_thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 85,
                        "gpu_percent": 90
                    }
                },
                "interleaving_decisions": {},
                "task_distribution": {}
            }
            self.save_config()
    
    def save_config(self):
        """Save assessment configuration"""
        with self.assessment_lock:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
    
    def assess_session_startup(self, session_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI assessment at session startup to determine optimal configuration
        
        Returns assessment with recommendations for:
        - Interleaving mode per agent
        - Resource allocation
        - Task prioritization
        - Parallel execution strategy
        """
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_params.get("session_id", f"session_{int(time.time())}"),
            "recommendations": {}
        }
        
        # Assess task requirements
        tasks = session_params.get("planned_tasks", [])
        task_complexity = self._analyze_task_complexity(tasks)
        
        # Assess available resources
        resources = self._check_system_resources()
        
        # Make interleaving decisions
        for agent in ["Div_AI_Agent_Focus_1", "Div_AI_Agent_Focus_2", "Div_AI_Agent_Focus_3", "Div_AI_Agent_Focus_4", "Div_AI_Agent_Focus_5"]:
            agent_tasks = [t for t in tasks if t.get("agent") == agent]
            
            if agent_tasks:
                # Determine if this agent should use interleaving
                use_interleaving = self._should_use_interleaving(
                    agent, 
                    agent_tasks, 
                    task_complexity,
                    resources
                )
                
                assessment["recommendations"][agent] = {
                    "use_interleaving": use_interleaving,
                    "reason": self._get_interleaving_reason(agent, agent_tasks, use_interleaving),
                    "resource_allocation": self._calculate_resource_allocation(agent, resources),
                    "priority_tasks": [t["id"] for t in agent_tasks if t.get("priority") == "high"]
                }
        
        # Determine parallel execution strategy
        assessment["parallel_strategy"] = self._determine_parallel_strategy(
            tasks, resources, assessment["recommendations"]
        )
        
        # Save assessment
        self.config["session_assessments"][assessment["session_id"]] = assessment
        self.save_config()
        
        return assessment
    
    def _analyze_task_complexity(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze complexity of planned tasks"""
        complexity = {
            "total_tasks": len(tasks),
            "high_complexity": 0,
            "requires_extended_thinking": 0,
            "multi_step_reasoning": 0
        }
        
        for task in tasks:
            desc = task.get("description", "").lower()
            
            # Check for complexity indicators
            if any(word in desc for word in ["optimize", "analyze", "debug", "refactor"]):
                complexity["high_complexity"] += 1
            
            if any(word in desc for word in ["design", "architect", "plan", "strategy"]):
                complexity["requires_extended_thinking"] += 1
            
            if any(word in desc for word in ["multi", "complex", "integrate", "coordinate"]):
                complexity["multi_step_reasoning"] += 1
        
        return complexity
    
    def _check_system_resources(self) -> Dict[str, float]:
        """Check current system resource availability"""
        try:
            import psutil
            return {
                "cpu_available": 100 - psutil.cpu_percent(interval=1),
                "memory_available": 100 - psutil.virtual_memory().percent,
                "disk_available": 100 - psutil.disk_usage('/').percent
            }
        except ImportError:
            # Fallback if psutil not available
            return {
                "cpu_available": 50.0,
                "memory_available": 40.0,
                "disk_available": 60.0
            }
    
    def _should_use_interleaving(self, agent: str, tasks: List[Dict], 
                                complexity: Dict, resources: Dict) -> bool:
        """Determine if agent should use interleaving based on tasks and resources"""
        # High complexity tasks benefit from interleaving
        complex_tasks = sum(1 for t in tasks if "complex" in t.get("description", "").lower())
        
        # Agent-specific logic
        if agent == "Div_AI_Agent_Focus_1":  # 3D modeling
            # Use interleaving for complex geometry or optimization tasks
            return complex_tasks > 0 or complexity["high_complexity"] > 2
        
        elif agent == "Div_AI_Agent_Focus_2":  # Simulation
            # Use interleaving for physics optimization
            return any("optim" in t.get("description", "").lower() for t in tasks)
        
        elif agent == "Div_AI_Agent_Focus_3":  # Utility
            # Generally doesn't need interleaving unless complex analysis
            return complexity["requires_extended_thinking"] > 1
        
        elif agent == "Div_AI_Agent_Focus_4":  # Testing
            # Use interleaving for test generation and debugging
            return any("debug" in t.get("description", "").lower() for t in tasks)
        
        elif agent == "Div_AI_Agent_Focus_5":  # Documentation
            # Use interleaving for comprehensive documentation
            return len(tasks) > 3 or complexity["multi_step_reasoning"] > 0
        
        return False
    
    def _get_interleaving_reason(self, agent: str, tasks: List[Dict], use_interleaving: bool) -> str:
        """Get human-readable reason for interleaving decision"""
        if use_interleaving:
            if len(tasks) > 3:
                return f"Multiple complex tasks ({len(tasks)}) require extended thinking"
            elif any("optim" in t.get("description", "").lower() for t in tasks):
                return "Optimization tasks benefit from tool interleaving"
            else:
                return "Task complexity warrants enhanced reasoning capabilities"
        else:
            return "Standard execution mode sufficient for current tasks"
    
    def _calculate_resource_allocation(self, agent: str, resources: Dict) -> Dict[str, Any]:
        """Calculate resource allocation for agent"""
        base_allocation = {
            "cpu_cores": 2,
            "memory_mb": 2048,
            "priority": "normal"
        }
        
        # Adjust based on agent role
        if agent == "Div_AI_Agent_Focus_1":  # 3D modeling needs more resources
            base_allocation["cpu_cores"] = 4
            base_allocation["memory_mb"] = 4096
        elif agent == "Div_AI_Agent_Focus_2":  # Simulation
            base_allocation["cpu_cores"] = 3
            base_allocation["memory_mb"] = 3072
        
        # Adjust based on available resources
        if resources["cpu_available"] < 30:
            base_allocation["cpu_cores"] = max(1, base_allocation["cpu_cores"] - 1)
        
        return base_allocation
    
    def _determine_parallel_strategy(self, tasks: List[Dict], resources: Dict, 
                                   recommendations: Dict) -> Dict[str, Any]:
        """Determine optimal parallel execution strategy"""
        active_agents = [a for a, r in recommendations.items() if r.get("priority_tasks")]
        
        strategy = {
            "max_parallel": 3,  # Default
            "execution_order": [],
            "resource_sharing": "dynamic"
        }
        
        # Adjust based on resources
        if resources["cpu_available"] > 60 and resources["memory_available"] > 50:
            strategy["max_parallel"] = 5
        elif resources["cpu_available"] < 30 or resources["memory_available"] < 30:
            strategy["max_parallel"] = 2
        
        # Determine execution order
        high_priority = []
        normal_priority = []
        
        for agent in active_agents:
            if recommendations[agent].get("priority_tasks"):
                high_priority.append(agent)
            else:
                normal_priority.append(agent)
        
        strategy["execution_order"] = high_priority + normal_priority
        
        return strategy
    
    def handle_task_completion(self, completed_agent: str, completed_task: str, 
                             remaining_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Handle AI assessment when a task completes and agent becomes available
        
        Returns recommendations for:
        - Reassigning the free agent
        - Adjusting interleaving settings
        - Resource reallocation
        """
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "completed_agent": completed_agent,
            "completed_task": completed_task,
            "action": "none",
            "recommendations": {}
        }
        
        # Check if there are high-priority tasks waiting
        high_priority_waiting = [t for t in remaining_tasks 
                               if t.get("priority") == "high" and t.get("status") == "queued"]
        
        if high_priority_waiting:
            # Reassign to high priority task
            next_task = high_priority_waiting[0]
            assessment["action"] = "reassign"
            assessment["recommendations"] = {
                "assign_task": next_task["id"],
                "use_interleaving": self._should_use_interleaving(
                    completed_agent, [next_task], {}, {}
                ),
                "reason": f"High priority task '{next_task['id']}' requires immediate attention"
            }
        else:
            # Check if other agents need help
            overloaded_agents = self._check_overloaded_agents(remaining_tasks)
            
            if overloaded_agents:
                # Help overloaded agent
                agent_to_help = overloaded_agents[0]
                tasks_to_take = self._select_tasks_to_redistribute(
                    agent_to_help, completed_agent, remaining_tasks
                )
                
                if tasks_to_take:
                    assessment["action"] = "redistribute"
                    assessment["recommendations"] = {
                        "take_tasks": [t["id"] for t in tasks_to_take],
                        "from_agent": agent_to_help,
                        "reason": f"Helping overloaded {agent_to_help} by taking {len(tasks_to_take)} tasks"
                    }
            else:
                # Check for optimization opportunities
                if self._can_optimize_parallel_execution(completed_agent, remaining_tasks):
                    assessment["action"] = "optimize"
                    assessment["recommendations"] = {
                        "optimization": "increase_parallel_capacity",
                        "reason": "Resources available for increased parallelization"
                    }
        
        return assessment
    
    def _check_overloaded_agents(self, tasks: List[Dict]) -> List[str]:
        """Check which agents have too many pending tasks"""
        agent_loads = {}
        
        for task in tasks:
            if task.get("status") in ["queued", "pending"]:
                agent = task.get("agent")
                if agent:
                    agent_loads[agent] = agent_loads.get(agent, 0) + 1
        
        # Agents with more than 3 pending tasks are considered overloaded
        return [agent for agent, load in agent_loads.items() if load > 3]
    
    def _select_tasks_to_redistribute(self, from_agent: str, to_agent: str, 
                                    tasks: List[Dict]) -> List[Dict]:
        """Select appropriate tasks to redistribute"""
        agent_tasks = [t for t in tasks 
                      if t.get("agent") == from_agent and t.get("status") == "queued"]
        
        # Select tasks suitable for the receiving agent
        suitable_tasks = []
        
        for task in agent_tasks:
            # Check if task is suitable for the receiving agent's capabilities
            if self._is_task_suitable_for_agent(task, to_agent):
                suitable_tasks.append(task)
                if len(suitable_tasks) >= 2:  # Take at most 2 tasks
                    break
        
        return suitable_tasks
    
    def _is_task_suitable_for_agent(self, task: Dict, agent: str) -> bool:
        """Check if a task is suitable for a specific agent"""
        task_type = task.get("type", "").lower()
        task_desc = task.get("description", "").lower()
        
        # Agent capability mapping
        capabilities = {
            "Div_AI_Agent_Focus_1": ["model", "3d", "geometry", "mesh", "render"],
            "Div_AI_Agent_Focus_2": ["simulation", "physics", "dynamics", "optimize"],
            "Div_AI_Agent_Focus_3": ["utility", "convert", "process", "analyze"],
            "Div_AI_Agent_Focus_4": ["test", "validate", "debug", "verify"],
            "Div_AI_Agent_Focus_5": ["document", "report", "describe", "explain"]
        }
        
        agent_caps = capabilities.get(agent, [])
        
        # Check if task matches agent capabilities
        return any(cap in task_type or cap in task_desc for cap in agent_caps)
    
    def _can_optimize_parallel_execution(self, free_agent: str, tasks: List[Dict]) -> bool:
        """Check if parallel execution can be optimized"""
        pending_tasks = [t for t in tasks if t.get("status") in ["queued", "pending"]]
        resources = self._check_system_resources()
        
        # Can optimize if resources are available and tasks are waiting
        return (len(pending_tasks) > 5 and 
                resources["cpu_available"] > 50 and 
                resources["memory_available"] > 40)
    
    def get_assessment_summary(self) -> Dict[str, Any]:
        """Get summary of all assessments made"""
        return {
            "total_sessions": len(self.config["session_assessments"]),
            "auto_adjustments_enabled": self.config["auto_adjustments"]["enabled"],
            "recent_assessments": list(self.config["session_assessments"].values())[-5:]
        }


# Singleton instance
_assessment_controls = None

def get_assessment_controls():
    """Get singleton instance of assessment controls"""
    global _assessment_controls
    if _assessment_controls is None:
        _assessment_controls = AISessionAssessmentControls()
    return _assessment_controls