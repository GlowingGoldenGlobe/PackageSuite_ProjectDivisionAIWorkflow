#!/usr/bin/env python
"""
AI Workflow Integration - Main Entry Point
Provides easy integration of the restricted automation system for AI agents
"""

import os
import sys
from typing import Dict, Any, Optional

# Add ai_managers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_managers'))

def check_file_access(file_path: str, operation: str = "read", task_description: str = "") -> Dict[str, Any]:
    """
    Check if AI agent can access a file with token optimization
    
    Args:
        file_path: Path to the file
        operation: Operation type (read, write, delete, etc.)
        task_description: What the AI is trying to accomplish
        
    Returns:
        Dict with 'allowed': bool, 'reason': str, 'token_saved': bool
        
    Example:
        result = check_file_access("Log_Modifications_to_Project_Folder_GGG.txt", "read", "logging task")
        if result['allowed']:
            # Read the file
        else:
            print(f"Access denied: {result['reason']}")
            if result['token_saved']:
                print("Token usage optimized - file skipped")
    """
    try:
        from ai_managers.auto_conflict_handler import safe_file_operation, initialize_conflict_handling
        
        # Initialize system if not already done
        initialize_conflict_handling()
        
        # Check access
        return safe_file_operation(file_path, operation, task_description, user_request=False)
        
    except Exception as e:
        # Fallback - allow access if system fails
        return {
            "allowed": True,
            "reason": f"System error - defaulting to allow: {e}",
            "token_saved": False,
            "requires_override": False
        }

def user_requested_file_access(file_path: str, operation: str = "read") -> Dict[str, Any]:
    """
    Check file access when user explicitly requested the file
    
    Args:
        file_path: Path to the file
        operation: Operation type
        
    Returns:
        Dict with access decision
    """
    try:
        from ai_managers.auto_conflict_handler import safe_file_operation, initialize_conflict_handling
        
        # Initialize system if not already done
        initialize_conflict_handling()
        
        # Check access with user_request=True to bypass contingency
        return safe_file_operation(file_path, operation, "", user_request=True)
        
    except Exception as e:
        # Fallback - allow access if system fails
        return {
            "allowed": True,
            "reason": f"System error - defaulting to allow: {e}",
            "token_saved": False,
            "requires_override": False
        }

def is_token_optimized_file(file_path: str) -> bool:
    """
    Quick check if a file is in the token optimization list (contingent files)
    
    Args:
        file_path: Path to check
        
    Returns:
        bool: True if file is contingent (can save tokens)
    """
    try:
        from ai_managers.auto_conflict_handler import _load_automation_schema
        
        schema = _load_automation_schema()
        if not schema:
            return False
            
        contingent_files = schema.get("restricted_automation_mode", {}).get("contingent_files", {})
        file_name = os.path.basename(file_path)
        
        return file_name in contingent_files
        
    except Exception:
        return False

def get_task_guidelines(task_description: str) -> Optional[str]:
    """
    Get AI agent guidelines for the current task
    
    Args:
        task_description: What the AI is working on
        
    Returns:
        str: Guidelines text or None if not available
    """
    try:
        from ai_managers.auto_conflict_handler import get_task_guidelines, initialize_conflict_handling
        
        # Initialize system if not already done
        initialize_conflict_handling()
        
        return get_task_guidelines(task_description)
        
    except Exception as e:
        return f"Guidelines system error: {e}"

# Convenience functions for common operations
def can_read_file(file_path: str, task_context: str = "") -> bool:
    """Simple check if file can be read"""
    result = check_file_access(file_path, "read", task_context)
    return result["allowed"]

def can_write_file(file_path: str, task_context: str = "") -> bool:
    """Simple check if file can be written"""
    result = check_file_access(file_path, "write", task_context)
    return result["allowed"]

def should_skip_file_for_tokens(file_path: str, task_context: str = "") -> bool:
    """Check if file should be skipped to save tokens"""
    result = check_file_access(file_path, "read", task_context)
    return not result["allowed"] and result.get("token_saved", False)

# Template Integration Patterns - EMBEDDED FOR AI AGENTS
REQUIRED_IMPORTS = {
    "gui_tab": [
        "import tkinter as tk",
        "from tkinter import ttk, messagebox",
        "import threading",
        "import sys",
        "from pathlib import Path",
        "sys.path.append(str(Path(__file__).parent.parent))",
        "from ai_workflow_integration import check_file_access"
    ],
    "ai_manager": [
        "import os", "import sys", "import json", "import logging",
        "from pathlib import Path",
        "from typing import Dict, Any, Optional, List",
        "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
        "from ai_workflow_integration import check_file_access"
    ],
    "utility_script": [
        "#!/usr/bin/env python",
        "import os", "import sys", "import argparse", "import logging",
        "from pathlib import Path",
        "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
        "from ai_workflow_integration import check_file_access"
    ]
}

REQUIRED_PATTERNS = {
    "gui_tab": {
        "class_suffix": "Tab",
        "constructor_param": "parent_notebook", 
        "integration_function": "integrate_with_gui",
        "thread_safety": "self.tab.after(0, lambda: ...)"
    },
    "ai_manager": {
        "singleton_pattern": "get_*_manager()",
        "cleanup_function": "cleanup_*_manager()",
        "logging_required": True,
        "config_loading": "_load_config() and _save_config()"
    },
    "utility_script": {
        "cli_required": "argparse with main()",
        "shebang": "#!/usr/bin/env python",
        "exit_code": "exit(main())"
    }
}

def get_template_imports(file_type: str) -> List[str]:
    """Get required imports for file type"""
    return REQUIRED_IMPORTS.get(file_type, [])

def get_template_patterns(file_type: str) -> Dict[str, Any]:
    """Get required patterns for file type"""
    return REQUIRED_PATTERNS.get(file_type, {})

# Auto-initialize on import
try:
    from ai_managers.auto_conflict_handler import initialize_conflict_handling
    initialize_conflict_handling()
except Exception:
    pass  # Silent fail - system will work in fallback mode

if __name__ == "__main__":
    # Test the integration
    print("Testing AI Workflow Integration...")
    
    # Test contingent file
    result = check_file_access("Log_Modifications_to_Project_Folder_GGG.txt", "read", "testing system")
    print(f"Log file access: {result}")
    
    # Test with logging context
    result = check_file_access("Log_Modifications_to_Project_Folder_GGG.txt", "read", "logging task to record modifications")
    print(f"Log file access (with logging context): {result}")
    
    # Test user request
    result = user_requested_file_access("Log_Modifications_to_Project_Folder_GGG.txt", "read")
    print(f"Log file access (user requested): {result}")
    
    print("Integration test complete!")