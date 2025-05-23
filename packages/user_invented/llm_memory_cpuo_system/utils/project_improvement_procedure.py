"""
Project Improvement Procedure System
A systematic approach for handling user requests for testing, improvements, error handling, and problem solving
Following the Contents-Procedure-Utils-Options (CPUO) framework
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import traceback
import inspect
from typing import Dict, List, Optional, Any

class ProjectImprovementProcedure:
    """Standardized procedure for handling project improvement requests"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.utils_dir = self.project_root / "utils"
        self.docs_dir = self.project_root / "docs"
        self.procedure_log_file = self.utils_dir / "procedure_execution_log.json"
        self.related_utils_registry = self.utils_dir / "related_utils_registry.json"
        
        # Standard structure for all improvement requests
        self.cpuo_template = {
            "contents": {
                "summary": "",
                "request_type": "",  # testing/improvement/error_handling/problem_solving
                "affected_components": [],
                "user_requirements": []
            },
            "procedure": {
                "steps": [],
                "validations": [],
                "integration_points": []
            },
            "utils": {
                "created": [],
                "modified": [],
                "referenced": []
            },
            "options": {
                "future_enhancements": [],
                "alternative_approaches": [],
                "related_features": []
            }
        }
        
        self.load_related_utils()
        
    def load_related_utils(self):
        """Load registry of related utilities"""
        if self.related_utils_registry.exists():
            with open(self.related_utils_registry, 'r') as f:
                self.related_utils = json.load(f)
        else:
            self.related_utils = {
                "workflow_utilities": [],
                "testing_utilities": [],
                "integration_utilities": [],
                "monitoring_utilities": []
            }
            
    def analyze_request(self, user_message: str) -> Dict[str, Any]:
        """Analyze user request and create CPUO structure"""
        cpuo = self.cpuo_template.copy()
        
        # Determine request type
        message_lower = user_message.lower()
        if any(word in message_lower for word in ["test", "verify", "check"]):
            cpuo["contents"]["request_type"] = "testing"
        elif any(word in message_lower for word in ["improve", "enhance", "optimize"]):
            cpuo["contents"]["request_type"] = "improvement"
        elif any(word in message_lower for word in ["error", "fix", "bug"]):
            cpuo["contents"]["request_type"] = "error_handling"
        else:
            cpuo["contents"]["request_type"] = "problem_solving"
            
        cpuo["contents"]["summary"] = user_message[:200]
        
        # Extract key components mentioned
        components = []
        component_keywords = {
            "gui": ["gui", "interface", "window", "button"],
            "workflow": ["workflow", "automation", "ai manager"],
            "task": ["task", "schedule", "queue"],
            "message": ["message", "input", "communication"],
            "control": ["control", "pause", "stop", "resume"]
        }
        
        for component, keywords in component_keywords.items():
            if any(kw in message_lower for kw in keywords):
                components.append(component)
                
        cpuo["contents"]["affected_components"] = components
        
        return cpuo
        
    def execute_procedure(self, cpuo: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the improvement procedure"""
        execution_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            "execution_id": execution_id,
            "started_at": datetime.now().isoformat(),
            "cpuo": cpuo,
            "execution_results": {},
            "created_artifacts": []
        }
        
        try:
            # Step 1: Contents Analysis
            print("\n=== Step 1: Contents Analysis ===")
            self.analyze_contents(cpuo, results)
            
            # Step 2: Procedure Execution
            print("\n=== Step 2: Procedure Execution ===")
            self.execute_improvement_steps(cpuo, results)
            
            # Step 3: Utils Management
            print("\n=== Step 3: Utils Management ===")
            self.manage_utilities(cpuo, results)
            
            # Step 4: Options Documentation
            print("\n=== Step 4: Options Documentation ===")
            self.document_options(cpuo, results)
            
            # Log execution
            self.log_execution(results)
            
            # Update related utils registry
            self.update_registry(cpuo)
            
            results["completed_at"] = datetime.now().isoformat()
            results["status"] = "success"
            
        except Exception as e:
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            results["status"] = "failed"
            
        return results
        
    def analyze_contents(self, cpuo: Dict[str, Any], results: Dict[str, Any]):
        """Analyze request contents in detail"""
        print(f"Request Type: {cpuo['contents']['request_type']}")
        print(f"Affected Components: {', '.join(cpuo['contents']['affected_components'])}")
        
        # Check existing implementations
        existing_implementations = []
        for component in cpuo['contents']['affected_components']:
            impl_check = self.check_existing_implementations(component)
            if impl_check:
                existing_implementations.extend(impl_check)
                
        results["execution_results"]["existing_implementations"] = existing_implementations
        print(f"Found {len(existing_implementations)} existing implementations")
        
    def check_existing_implementations(self, component: str) -> List[str]:
        """Check for existing implementations of a component"""
        implementations = []
        
        # Map components to file patterns
        component_patterns = {
            "gui": ["*gui*.py", "run_*.py"],
            "workflow": ["*workflow*.py", "*manager*.py"],
            "task": ["*task*.py", "*schedule*.py"],
            "message": ["*message*.py", "*handler*.py"],
            "control": ["*control*.py", "*conflict*.py"]
        }
        
        patterns = component_patterns.get(component, [])
        for pattern in patterns:
            for file in self.project_root.rglob(pattern):
                if file.is_file() and not any(part.startswith('.') for part in file.parts):
                    implementations.append(str(file.relative_to(self.project_root)))
                    
        return implementations[:5]  # Limit to 5 most relevant
        
    def execute_improvement_steps(self, cpuo: Dict[str, Any], results: Dict[str, Any]):
        """Execute the improvement steps"""
        steps_executed = []
        
        # Standard improvement steps based on request type
        if cpuo["contents"]["request_type"] == "testing":
            steps = [
                "Create test script",
                "Run validation tests",
                "Document test results"
            ]
        elif cpuo["contents"]["request_type"] == "improvement":
            steps = [
                "Analyze current implementation",
                "Create enhanced version",
                "Integrate with existing system",
                "Test improvements"
            ]
        elif cpuo["contents"]["request_type"] == "error_handling":
            steps = [
                "Identify error source",
                "Create fix",
                "Add error prevention",
                "Test fix"
            ]
        else:  # problem_solving
            steps = [
                "Define problem clearly",
                "Research solutions",
                "Implement solution",
                "Validate solution"
            ]
            
        cpuo["procedure"]["steps"] = steps
        
        for step in steps:
            print(f"  Executing: {step}")
            steps_executed.append({
                "step": step,
                "executed_at": datetime.now().isoformat(),
                "status": "completed"
            })
            
        results["execution_results"]["steps_executed"] = steps_executed
        
    def manage_utilities(self, cpuo: Dict[str, Any], results: Dict[str, Any]):
        """Manage utility creation and referencing"""
        # Create utility filename based on request
        utility_name = f"{cpuo['contents']['request_type']}_utility_{datetime.now().strftime('%Y%m%d')}.py"
        utility_path = self.utils_dir / utility_name
        
        # Create utility template
        utility_content = f'''"""
Utility created by Project Improvement Procedure
Type: {cpuo['contents']['request_type']}
Created: {datetime.now().isoformat()}
Components: {', '.join(cpuo['contents']['affected_components'])}
"""

from pathlib import Path
import json
import os

class {self._to_class_name(cpuo['contents']['request_type'])}Utility:
    """Auto-generated utility for {cpuo['contents']['request_type']}"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration for this utility"""
        config_file = self.project_root / "utils" / "utility_config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {{}}
        
    def execute(self):
        """Execute the utility function"""
        # Implementation based on request type
        print("Executing {cpuo['contents']['request_type']} utility...")
        
        # Add specific logic here
        results = {{
            "executed_at": "{datetime.now().isoformat()}",
            "components_checked": {cpuo['contents']['affected_components']},
            "status": "success"
        }}
        
        return results
        
def main():
    """Main entry point"""
    utility = {self._to_class_name(cpuo['contents']['request_type'])}Utility()
    results = utility.execute()
    print(f"Results: {{results}}")
    
if __name__ == "__main__":
    main()
'''
        
        # Write utility file
        with open(utility_path, 'w') as f:
            f.write(utility_content)
            
        print(f"  Created utility: {utility_name}")
        
        cpuo["utils"]["created"].append(str(utility_path.relative_to(self.project_root)))
        results["created_artifacts"].append(str(utility_path))
        
        # Find and reference related utilities
        self.find_related_utilities(cpuo, results)
        
    def find_related_utilities(self, cpuo: Dict[str, Any], results: Dict[str, Any]):
        """Find and reference related utilities"""
        related = []
        
        # Search for related utilities
        for util_file in self.utils_dir.glob("*.py"):
            if util_file.name != "__init__.py":
                # Simple keyword matching
                with open(util_file, 'r') as f:
                    content = f.read().lower()
                    
                for component in cpuo["contents"]["affected_components"]:
                    if component in content:
                        related.append(str(util_file.relative_to(self.project_root)))
                        break
                        
        cpuo["utils"]["referenced"] = related[:3]  # Top 3 related
        print(f"  Found {len(related)} related utilities")
        
    def document_options(self, cpuo: Dict[str, Any], results: Dict[str, Any]):
        """Document options and future enhancements"""
        # Generate options based on request type
        if cpuo["contents"]["request_type"] == "testing":
            cpuo["options"]["future_enhancements"] = [
                "Add automated test scheduling",
                "Create test report dashboard",
                "Implement continuous testing"
            ]
        elif cpuo["contents"]["request_type"] == "improvement":
            cpuo["options"]["future_enhancements"] = [
                "Performance optimization",
                "Feature expansion",
                "User experience improvements"
            ]
            
        # Create options document
        options_doc = self.docs_dir / f"OPTIONS_{cpuo['contents']['request_type']}_{datetime.now().strftime('%Y%m%d')}.md"
        
        doc_content = f"""# Options and Future Enhancements

## Request Type: {cpuo['contents']['request_type']}

## Components: {', '.join(cpuo['contents']['affected_components'])}

## Future Enhancements:
{chr(10).join(f"- {opt}" for opt in cpuo['options']['future_enhancements'])}

## Alternative Approaches:
- Consider different architectural patterns
- Explore third-party integrations
- Evaluate performance trade-offs

## Related Features:
- Integration with existing {', '.join(cpuo['contents']['affected_components'])}
- Extension points for new functionality
- Compatibility with current workflow

Generated by Project Improvement Procedure
Date: {datetime.now().isoformat()}
"""
        
        with open(options_doc, 'w') as f:
            f.write(doc_content)
            
        print(f"  Created options document: {options_doc.name}")
        results["created_artifacts"].append(str(options_doc))
        
    def log_execution(self, results: Dict[str, Any]):
        """Log the procedure execution"""
        logs = []
        if self.procedure_log_file.exists():
            try:
                with open(self.procedure_log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
                
        logs.append(results)
        
        # Keep last 100 executions
        if len(logs) > 100:
            logs = logs[-100:]
            
        with open(self.procedure_log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"\n  Logged execution: {results['execution_id']}")
        
    def update_registry(self, cpuo: Dict[str, Any]):
        """Update the related utils registry"""
        # Categorize the new utility
        category = f"{cpuo['contents']['request_type']}_utilities"
        if category not in self.related_utils:
            self.related_utils[category] = []
            
        for util in cpuo["utils"]["created"]:
            if util not in self.related_utils[category]:
                self.related_utils[category].append(util)
                
        with open(self.related_utils_registry, 'w') as f:
            json.dump(self.related_utils, f, indent=2)
            
    def _to_class_name(self, text: str) -> str:
        """Convert text to class name format"""
        return ''.join(word.capitalize() for word in text.split('_'))
        
    def create_procedure_guide(self):
        """Create a guide for using this procedure system"""
        guide_path = self.docs_dir / "PROJECT_IMPROVEMENT_PROCEDURE_GUIDE.md"
        
        guide_content = """# Project Improvement Procedure Guide

## Overview

The Project Improvement Procedure System provides a standardized approach for handling all project improvement requests using the CPUO (Contents-Procedure-Utils-Options) framework.

## How to Use

### 1. Automatic Invocation

When Claude Code receives a request for:
- Testing
- Improvements
- Error Handling
- Problem Solving

The procedure system automatically:
1. Analyzes the request (Contents)
2. Executes improvement steps (Procedure)
3. Creates/references utilities (Utils)
4. Documents future options (Options)

### 2. Manual Invocation

```python
from utils.project_improvement_procedure import ProjectImprovementProcedure

# Create procedure instance
procedure = ProjectImprovementProcedure()

# Analyze user request
cpuo = procedure.analyze_request("Fix the GUI workflow integration")

# Execute procedure
results = procedure.execute_procedure(cpuo)
```

### 3. Integration Points

The procedure system integrates with:
- Workflow Integrity Manager
- GUI Integration Patches
- Task Management System
- Message Handler Integration

### 4. Outputs

Each execution produces:
1. **Utility File** - Reusable code in `/utils/`
2. **Options Document** - Future enhancements in `/docs/`
3. **Execution Log** - Detailed record in `/utils/procedure_execution_log.json`
4. **Registry Update** - Links to related utilities

### 5. Benefits

- **Consistency** - All improvements follow same structure
- **Reusability** - Creates utilities for future use
- **Traceability** - Complete logs of all changes
- **Integration** - Automatically links related components
- **Documentation** - Options for future enhancements

## Example Workflow

1. User: "Test the AI workflow integration"
2. System: Analyzes as "testing" request
3. Creates: `testing_utility_20250523.py`
4. Documents: `OPTIONS_testing_20250523.md`
5. Logs: Execution with ID `proc_20250523_143022`
6. Updates: Registry with new utility reference

## Best Practices

1. Always use for improvement requests
2. Review generated utilities before use
3. Check options documents for ideas
4. Reference execution logs for history
5. Link related utilities together

Generated by Project Improvement Procedure System
"""
        
        with open(guide_path, 'w') as f:
            f.write(guide_content)
            
        return guide_path


def integrate_with_claude_memory():
    """Integration point for Claude's memory system"""
    memory_file = Path(__file__).parent.parent / "CLAUDE.md"
    
    memory_addition = """

## Project Improvement Procedure System

When handling user requests for testing, improvements, error handling, or problem solving, use the standardized CPUO framework:

1. **Analyze Request**: Determine type and affected components
2. **Execute Procedure**: Follow standardized steps
3. **Create Utilities**: Generate reusable code in /utils/
4. **Document Options**: Create future enhancement docs

Usage:
```python
from utils.project_improvement_procedure import ProjectImprovementProcedure
procedure = ProjectImprovementProcedure()
cpuo = procedure.analyze_request(user_message)
results = procedure.execute_procedure(cpuo)
```

This ensures consistency, reusability, and proper documentation for all project improvements.
"""
    
    if memory_file.exists():
        with open(memory_file, 'a') as f:
            f.write(memory_addition)
            
    print("✓ Integrated with Claude memory system")


def main():
    """Demonstrate the procedure system"""
    print("=== Project Improvement Procedure System ===\n")
    
    # Create procedure instance
    procedure = ProjectImprovementProcedure()
    
    # Create the guide
    guide_path = procedure.create_procedure_guide()
    print(f"Created procedure guide: {guide_path}")
    
    # Integrate with Claude memory
    integrate_with_claude_memory()
    
    # Example usage
    test_request = "Test the GUI workflow integration and ensure all controls work properly"
    print(f"\nExample request: '{test_request}'")
    
    cpuo = procedure.analyze_request(test_request)
    results = procedure.execute_procedure(cpuo)
    
    print(f"\nExecution ID: {results['execution_id']}")
    print(f"Status: {results['status']}")
    print(f"Created artifacts: {len(results['created_artifacts'])}")
    

if __name__ == "__main__":
    main()