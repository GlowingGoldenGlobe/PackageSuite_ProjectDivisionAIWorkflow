"""
AI Manager Integration for Interleaving Control
Allows AI managers to automatically control interleaving settings based on task requirements.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from interleaving_config_manager import get_config_manager, should_use_interleaving

logger = logging.getLogger(__name__)

class InterleavingTaskManager:
    """Manages interleaving settings for AI tasks automatically."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.task_rules = self._load_task_rules()
    
    def _load_task_rules(self) -> Dict[str, Any]:
        """Load rules for when to use interleaving."""
        rules_file = Path(__file__).parent / "interleaving_rules.json"
        
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading interleaving rules: {e}")
        
        # Default rules
        return {
            "task_patterns": {
                "optimization": {"prefer_interleaving": True, "reason": "Better multi-step optimization"},
                "design": {"prefer_interleaving": True, "reason": "Enhanced design exploration"},
                "debug": {"prefer_interleaving": True, "reason": "Improved debugging with tool use"},
                "simple_execution": {"prefer_interleaving": False, "reason": "PyAutoGen sufficient"},
                "batch_processing": {"prefer_interleaving": False, "reason": "PyAutoGen better for batches"}
            },
            "agent_preferences": {
                "AI_Agent_1": {"complex_3d_modeling": True, "simple_generation": False},
                "AI_Agent_2": {"assembly_optimization": True, "component_listing": False},
                "AI_Agent_3": {"physics_simulation": True, "basic_calculations": False},
                "AI_Agent_4": {"neural_design": True, "parameter_tuning": False},
                "AI_Agent_5": {"system_integration": True, "status_reporting": False}
            }
        }
    
    def evaluate_task(self, agent: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate whether a task should use interleaving.
        
        Args:
            agent: The agent identifier
            task_data: Task information including type, complexity, etc.
            
        Returns:
            Dictionary with recommendation and reasoning
        """
        recommendation = {
            "use_interleaving": None,
            "confidence": 0.5,
            "reasons": [],
            "override_user": False
        }
        
        # Check if agent/task is locked
        _, agent_locked = self.config_manager.get_agent_setting(agent)
        if agent_locked:
            current_setting = self.config_manager.get_effective_setting(agent)
            recommendation["use_interleaving"] = current_setting
            recommendation["reasons"].append("Setting is locked by user")
            recommendation["confidence"] = 1.0
            return recommendation
        
        # Analyze task type
        task_type = task_data.get("type", "").lower()
        task_complexity = task_data.get("complexity", "medium").lower()
        
        # Check task patterns
        for pattern, rule in self.task_rules["task_patterns"].items():
            if pattern in task_type:
                recommendation["use_interleaving"] = rule["prefer_interleaving"]
                recommendation["reasons"].append(rule["reason"])
                recommendation["confidence"] += 0.2
        
        # Check agent-specific preferences
        agent_prefs = self.task_rules["agent_preferences"].get(agent, {})
        for task_category, prefer_interleaving in agent_prefs.items():
            if task_category.replace("_", " ") in task_data.get("description", "").lower():
                recommendation["use_interleaving"] = prefer_interleaving
                recommendation["reasons"].append(f"Agent prefers {'interleaving' if prefer_interleaving else 'PyAutoGen'} for {task_category}")
                recommendation["confidence"] += 0.3
        
        # Complexity-based recommendation
        if task_complexity in ["high", "very_high"]:
            if recommendation["use_interleaving"] is None:
                recommendation["use_interleaving"] = True
            recommendation["reasons"].append("High complexity task benefits from extended thinking")
            recommendation["confidence"] += 0.2
        elif task_complexity in ["low", "very_low"]:
            if recommendation["use_interleaving"] is None:
                recommendation["use_interleaving"] = False
            recommendation["reasons"].append("Low complexity task doesn't require interleaving")
            recommendation["confidence"] += 0.1
        
        # Default to current setting if no strong recommendation
        if recommendation["use_interleaving"] is None:
            recommendation["use_interleaving"] = self.config_manager.get_effective_setting(agent)
            recommendation["reasons"].append("Using current agent setting")
        
        # Cap confidence at 1.0
        recommendation["confidence"] = min(recommendation["confidence"], 1.0)
        
        # Decide if we should override user preference
        if recommendation["confidence"] >= 0.8:
            recommendation["override_user"] = True
        
        return recommendation
    
    def apply_recommendation(self, agent: str, task_id: str, recommendation: Dict[str, Any]) -> bool:
        """
        Apply the interleaving recommendation for a task.
        
        Args:
            agent: The agent identifier
            task_id: The task identifier
            recommendation: The recommendation from evaluate_task
            
        Returns:
            True if recommendation was applied
        """
        # Check if we should apply the recommendation
        if not recommendation.get("override_user", False):
            # Check current user preference
            current_setting = self.config_manager.get_effective_setting(agent)
            if current_setting != recommendation["use_interleaving"]:
                logger.info(f"Not overriding user preference for {agent}:{task_id}")
                return False
        
        # Apply the recommendation as a task override
        use_interleaving = recommendation["use_interleaving"]
        self.config_manager.set_task_override(agent, task_id, use_interleaving)
        
        # Log the decision
        self.config_manager.log_session_event(
            agent, task_id, "interleaving_decision",
            {
                "use_interleaving": use_interleaving,
                "confidence": recommendation["confidence"],
                "reasons": recommendation["reasons"]
            }
        )
        
        logger.info(f"Applied interleaving={'enabled' if use_interleaving else 'disabled'} for {agent}:{task_id}")
        return True
    
    def get_task_recommendation(self, agent: str, task_description: str, task_type: str = None) -> Dict[str, Any]:
        """
        Get a recommendation for a simple task description.
        
        Args:
            agent: The agent identifier
            task_description: Description of the task
            task_type: Optional task type
            
        Returns:
            Recommendation dictionary
        """
        # Simple task data from description
        task_data = {
            "description": task_description,
            "type": task_type or self._infer_task_type(task_description),
            "complexity": self._estimate_complexity(task_description)
        }
        
        return self.evaluate_task(agent, task_data)
    
    def _infer_task_type(self, description: str) -> str:
        """Infer task type from description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["optimize", "improve", "enhance"]):
            return "optimization"
        elif any(word in description_lower for word in ["design", "create", "build"]):
            return "design"
        elif any(word in description_lower for word in ["debug", "fix", "error"]):
            return "debug"
        elif any(word in description_lower for word in ["batch", "multiple", "bulk"]):
            return "batch_processing"
        else:
            return "general"
    
    def _estimate_complexity(self, description: str) -> str:
        """Estimate task complexity from description."""
        description_lower = description.lower()
        
        # High complexity indicators
        high_complexity_words = ["complex", "advanced", "sophisticated", "multi-step", "iterative", "optimize"]
        if any(word in description_lower for word in high_complexity_words):
            return "high"
        
        # Low complexity indicators
        low_complexity_words = ["simple", "basic", "straightforward", "quick", "single"]
        if any(word in description_lower for word in low_complexity_words):
            return "low"
        
        return "medium"
    
    def update_rules(self, new_rules: Dict[str, Any]):
        """Update the task rules."""
        self.task_rules.update(new_rules)
        
        # Save to file
        rules_file = Path(__file__).parent / "interleaving_rules.json"
        try:
            with open(rules_file, 'w') as f:
                json.dump(self.task_rules, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving interleaving rules: {e}")


# Singleton instance
_task_manager = None

def get_interleaving_task_manager() -> InterleavingTaskManager:
    """Get or create the singleton task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = InterleavingTaskManager()
    return _task_manager


# Integration functions for AI agents
def should_task_use_interleaving(agent: str, task_description: str, task_id: str = None) -> bool:
    """
    Determine if a task should use interleaving based on AI manager recommendation.
    
    Args:
        agent: The agent identifier
        task_description: Description of the task
        task_id: Optional task identifier for override
        
    Returns:
        True if interleaving should be used
    """
    manager = get_interleaving_task_manager()
    recommendation = manager.get_task_recommendation(agent, task_description)
    
    # Apply recommendation if confident enough
    if recommendation["confidence"] >= 0.7 and task_id:
        manager.apply_recommendation(agent, task_id, recommendation)
    
    # Return the effective setting
    return get_config_manager().get_effective_setting(agent, task_id)