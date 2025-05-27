#!/usr/bin/env python3
"""
AI Manager Context Builder

This module automatically consolidates and prioritizes documentation for AI Managers,
ensuring they have the most relevant context while minimizing token usage.
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIManagerContextBuilder:
    """Builds context-specific documentation summaries for AI managers"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ai_managers_dir = self.project_root / "ai_managers"
        self.agents_dirs = [self.project_root / f"AI_Agent_{i}" for i in range(1, 15)]
        self.context_file = self.ai_managers_dir / "AI_MANAGER_CONTEXT.json"
        self.summary_file = self.project_root / "PROJECT_STARTUP_SUMMARY.md"
        self.duplicate_prevention_rules = self.project_root / "docs" / "duplicate_file_prevention_task.md"
        
    def build_context(self, role: str = None) -> Dict[str, Any]:
        """Build context for a specific AI manager role or general context"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "role": role or "general",
            "project_status": self._get_project_status(),
            "recent_changes": self._get_recent_changes(),
            "active_tasks": self._get_active_tasks(),
            "critical_files": self._get_critical_files(role),
            "agent_status": self._get_agent_status(),
            "documentation_index": self._build_documentation_index(role),
            "critical_rules": self._get_critical_rules()
        }
        
        return context
    
    def _get_project_status(self) -> Dict[str, Any]:
        """Get current project status from startup summary"""
        if self.summary_file.exists():
            with open(self.summary_file, 'r') as f:
                content = f.read()
                
            # Parse key information from the summary
            status = {
                "development_mode": "refined_model",
                "execution_style": "parallel",
                "environment": "Windows native",
                "last_updated": None
            }
            
            # Extract from markdown content
            for line in content.split('\n'):
                if "Development mode:" in line:
                    status["development_mode"] = line.split(":")[-1].strip()
                elif "Last Updated" in line:
                    status["last_updated"] = line
                elif "Current Configuration:" in line:
                    status["configuration_section"] = True
                    
            return status
        return {}
    
    def _get_recent_changes(self) -> List[Dict[str, str]]:
        """Get recent changes from git or modification times"""
        changes = []
        
        # Check recently modified files
        for path in self.project_root.rglob("*.py"):
            try:
                mtime = path.stat().st_mtime
                if mtime > (datetime.now().timestamp() - 86400):  # Last 24 hours
                    changes.append({
                        "file": str(path.relative_to(self.project_root)),
                        "modified": datetime.fromtimestamp(mtime).isoformat(),
                        "type": "python"
                    })
            except Exception as e:
                logger.debug(f"Error checking file {path}: {e}")
                
        return sorted(changes, key=lambda x: x["modified"], reverse=True)[:10]
    
    def _get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active tasks from task managers"""
        tasks = []
        
        # Check for task files
        task_files = [
            self.ai_managers_dir / "active_tasks.json",
            self.project_root / "tasks.json",
            self.ai_managers_dir / "scheduled_tasks.json"
        ]
        
        for task_file in task_files:
            if task_file.exists():
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                        if isinstance(task_data, list):
                            tasks.extend(task_data)
                        elif isinstance(task_data, dict) and "tasks" in task_data:
                            tasks.extend(task_data["tasks"])
                except Exception as e:
                    logger.error(f"Error reading task file {task_file}: {e}")
                    
        return tasks
    
    def _get_critical_files(self, role: str = None) -> Dict[str, List[str]]:
        """Get critical files for specific AI manager role"""
        critical_files = {
            "common": [
                "PROJECT_STARTUP_SUMMARY.md",
                "README.md",
                "Objectives_1.py",
                "Procedure_1.py"
            ],
            "project_ai_manager": [
                "ai_managers/project_ai_manager.py",
                "ai_managers/task_manager.py",
                "ai_managers/parallel_execution_manager.py"
            ],
            "resource_manager": [
                "ai_managers/project_resource_manager.py",
                "hardware_monitor.py",
                "RESOURCE_MANAGEMENT.md"
            ],
            "git_task_manager": [
                "ai_managers/git_task_manager.py",
                "merge_conflict_handler.py",
                ".gitignore"
            ],
            "model_manager": [
                "ai_managers/refined_model_manager.py",
                "model_versions/",
                "model_comparisons/"
            ]
        }
        
        if role and role in critical_files:
            return {
                "role_specific": critical_files[role],
                "common": critical_files["common"]
            }
        
        return {"common": critical_files["common"]}
    
    def _get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all AI agents"""
        agent_status = {}
        
        for agent_dir in self.agents_dirs:
            if agent_dir.exists():
                agent_name = agent_dir.name
                status = {
                    "exists": True,
                    "has_readme": (agent_dir / "README.md").exists(),
                    "has_main_script": (agent_dir / f"{agent_name}.py").exists(),
                    "recent_activity": False
                }
                
                # Check for recent activity
                for file in agent_dir.glob("*.py"):
                    if file.stat().st_mtime > (datetime.now().timestamp() - 86400):
                        status["recent_activity"] = True
                        break
                        
                agent_status[agent_name] = status
            else:
                agent_status[agent_dir.name] = {"exists": False}
                
        return agent_status
    
    def _build_documentation_index(self, role: str = None) -> Dict[str, List[str]]:
        """Build an index of available documentation"""
        doc_index = {
            "readme_files": [],
            "guides": [],
            "specifications": [],
            "logs": []
        }
        
        # Find all README files
        for readme in self.project_root.rglob("README*.md"):
            doc_index["readme_files"].append(str(readme.relative_to(self.project_root)))
            
        # Find guides
        for guide in self.project_root.rglob("*GUIDE*.md"):
            doc_index["guides"].append(str(guide.relative_to(self.project_root)))
            
        # Find specifications
        for spec in self.project_root.rglob("*SPEC*.md"):
            doc_index["specifications"].append(str(spec.relative_to(self.project_root)))
            
        # Find logs (limit to recent)
        for log in self.project_root.rglob("*.log"):
            if log.stat().st_mtime > (datetime.now().timestamp() - 86400):
                doc_index["logs"].append(str(log.relative_to(self.project_root)))
                
        return doc_index
    
    def update_startup_summary(self, additional_info: Dict[str, Any] = None):
        """Update the PROJECT_STARTUP_SUMMARY.md with latest information"""
        summary_content = f"""# GlowingGoldenGlobe Project Startup Summary

## Project Overview
The GlowingGoldenGlobe project is an ASI system for developing micro-robot-composite humanoid workforce robots.

### Key Components:
1. **AI Managers**: Decision-making modules (Project AI Manager, Resource Manager, etc.)
2. **AI Agents 1-14**: Each responsible for different robot components
3. **GUI System**: Located in `/gui/` with launcher at `gui_launcher.py`
4. **Parallel Execution System**: Coordinates multiple roles

### Current Configuration:
- Development mode: refined_model
- Execution style: parallel 
- Time limit: 1 hour
- Auto-refinement enabled

### Environment Details:
- **Project Location**: {self.project_root}
- **Working Terminal**: VS Code integrated terminal
- **Primary Tool**: Claude Code APP
- **Execution Mode**: Parallel AI Workflow with VS Code Agent mode

### Recent Updates:
"""
        
        # Add recent changes
        recent_changes = self._get_recent_changes()
        for change in recent_changes[:5]:
            summary_content += f"- {change['file']} modified at {change['modified']}\n"
        
        summary_content += f"""
### Active AI Agents:
"""
        
        # Add agent status
        agent_status = self._get_agent_status()
        for agent, status in agent_status.items():
            if status.get("exists"):
                activity = "Active" if status.get("recent_activity") else "Inactive"
                summary_content += f"- {agent}: {activity}\n"
        
        if additional_info:
            summary_content += f"""
### Additional Information:
"""
            for key, value in additional_info.items():
                summary_content += f"- {key}: {value}\n"
        
        summary_content += f"""
### Next Steps:
1. Review recent changes
2. Check active tasks
3. Run appropriate AI managers
4. Monitor system resources

### Critical Rules:
- **Always check** `/docs/duplicate_file_prevention_task.md` before creating new files
- Use proper naming conventions (claude_, agent_, api_, unified_)
- Avoid creating duplicate files

### To Start:
```powershell
# From project directory
python start_agent_mode.py
```

## Last Updated
- Date: {datetime.now().strftime('%Y-%m-%d')}
- Updated by: AI Manager Context Builder
"""
        
        with open(self.summary_file, 'w') as f:
            f.write(summary_content)
            
        logger.info(f"Updated {self.summary_file}")
    
    def save_context(self, context: Dict[str, Any]):
        """Save context to JSON file"""
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2, default=str)
        logger.info(f"Saved context to {self.context_file}")
    
    def get_relevant_docs_for_role(self, role: str) -> List[str]:
        """Get list of most relevant documents for a specific AI manager role"""
        role_docs = {
            "project_ai_manager": [
                "README.md",
                "PROJECT_STARTUP_SUMMARY.md",
                "ai_managers/README.md",
                "Objectives_1.py",
                "AI_MANAGER_CONCEPT.md"
            ],
            "resource_manager": [
                "RESOURCE_MANAGEMENT.md",
                "hardware_monitor.py",
                "ai_managers/project_resource_manager.py",
                "parallel_execution_roles.md"
            ],
            "git_task_manager": [
                "merge_conflict_handler.py",
                "ai_managers/git_task_manager.py",
                "automated_workflow_integration_guide.md"
            ],
            "model_manager": [
                "ai_managers/refined_model_manager.py",
                "MODEL_MANAGEMENT.md",
                "Div_AI_Agent_Focus_1/README_Agent_1.md"
            ]
        }
        
        return role_docs.get(role, ["README.md", "PROJECT_STARTUP_SUMMARY.md"])
    
    def create_role_specific_summary(self, role: str, current_task: Dict[str, Any] = None) -> str:
        """Create a concise summary for a specific AI manager role"""
        context = self.build_context(role)
        relevant_docs = self.get_relevant_docs_for_role(role)
        
        # Add task-specific information if provided
        task_info = ""
        if current_task:
            task_info = f"""
## Current Task
- Name: {current_task.get('name', 'Unknown')}
- Priority: {current_task.get('priority', 'Normal')}
- Type: {current_task.get('type', 'General')}
- Status: {current_task.get('status', 'Pending')}
"""
        
        summary = f"""# {role.title()} Context Summary

## Current Status
- Timestamp: {context['timestamp']}
- Project Mode: {context['project_status'].get('development_mode', 'unknown')}
- Recent Activity: {len(context['recent_changes'])} files modified in last 24h
{task_info}
## Critical Files for {role}:
"""
        
        for doc in relevant_docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                summary += f"- {doc}: Available\n"
            else:
                summary += f"- {doc}: Not found\n"
        
        summary += f"""
## Active Tasks:
{len(context['active_tasks'])} active tasks found

## Agent Status:
"""
        
        for agent, status in context['agent_status'].items():
            if status.get('exists') and status.get('recent_activity'):
                summary += f"- {agent}: Active\n"
        
        summary += f"""
## Recent Changes:
"""
        
        for change in context['recent_changes'][:5]:
            summary += f"- {change['file']}: {change['modified']}\n"
        
        summary += f"""
## Next Actions:
1. Review critical files
2. Check task queue
3. Execute role-specific functions
4. Update status

## Quick Start:
```python
from ai_managers.{role} import main
main()
```
"""
        
        return summary
    
    def _get_critical_rules(self) -> Dict[str, str]:
        """Get critical rules that should always be followed"""
        rules = {
            "duplicate_prevention": str(self.duplicate_prevention_rules),
            "reference": "Always check /docs/duplicate_file_prevention_task.md before creating new files",
            "gui_syntax_fixer": "Use /gui/utils/syntax_fixer.py to fix common GUI syntax errors"
        }
        
        # Read the duplicate prevention rules if the file exists
        if self.duplicate_prevention_rules.exists():
            try:
                with open(self.duplicate_prevention_rules, 'r') as f:
                    content = f.read()
                    # Extract key rules
                    if "File Creation Rules" in content:
                        rules["file_creation"] = "Check for existing files before creating new ones"
                    if "claude_" in content or "agent_" in content:
                        rules["naming_convention"] = "Use proper prefixes: claude_, agent_, api_, unified_"
            except Exception as e:
                logger.warning(f"Could not read duplicate prevention rules: {e}")
        
        return rules
    
    def create_gui_problem_solving_summary(self) -> str:
        """Create a comprehensive summary for GUI problem solving"""
        gui_dir = self.project_root / "gui"
        
        summary = """# GUI Problem Solving Summary

## GUI Structure and Components
"""
        
        # List key GUI files
        if gui_dir.exists():
            key_files = {
                "gui_main.py": "Main GUI application",
                "gui_launcher.py": "GUI launcher script",
                "gui_enhanced.py": "Enhanced GUI features",
                "gui_styles.py": "GUI styling",
                "gui_selector.py": "Mode selector interface"
            }
            
            for filename, description in key_files.items():
                file_path = gui_dir / filename
                if file_path.exists():
                    summary += f"- **{filename}**: {description}\n"
        
        summary += "\n## Recent GUI Changes\n"
        
        # Get recent GUI-related changes
        recent_changes = self._get_recent_changes()
        gui_changes = [c for c in recent_changes if "gui" in c['file'].lower()][:5]
        
        for change in gui_changes:
            summary += f"- {change['file']}: {change['modified']}\n"
        
        summary += "\n## Error Logs and Issues\n"
        
        # Check for error logs
        error_logs = [
            gui_dir / "gui_launcher_error.log",
            gui_dir / "gui_launcher_error_log.txt"
        ]
        
        for log_file in error_logs:
            if log_file.exists():
                summary += f"- {log_file.name}: Found\n"
                try:
                    with open(log_file, 'r') as f:
                        last_lines = f.readlines()[-10:]  # Get last 10 lines
                        if last_lines:
                            summary += "  Last error:\n"
                            summary += "  ```\n"
                            summary += "  " + "  ".join(last_lines[-3:])  # Show last 3 lines
                            summary += "  ```\n"
                except Exception as e:
                    summary += f"  (Could not read: {e})\n"
        
        summary += "\n## GUI Documentation\n"
        
        # Reference key documentation
        gui_docs = [
            gui_dir / "GUI_STRUCTURE.md",
            gui_dir / "GUI_README.md",
            gui_dir / "README.md"
        ]
        
        for doc in gui_docs:
            if doc.exists():
                summary += f"- {doc.name}: Available\n"
        
        summary += "\n## Parallel Execution Context\n"
        
        parallel_docs = [
            self.project_root / "IMPLEMENTATION_NOTES.md",
            self.project_root / "PARALLEL_AGENT_MODE.md"
        ]
        
        for doc in parallel_docs:
            if doc.exists():
                summary += f"- {doc.name}: Available\n"
        
        summary += f"""
## Critical Files for GUI Problem Solving

1. **Structure and Design**:
   - `/gui/GUI_STRUCTURE.md`
   - `/gui/GUI_README.md`

2. **Error Logs**:
   - `/gui/gui_launcher_error.log`
   - `/gui/gui_launcher_error_log.txt`
   - `/gui/logs/`

3. **Main Implementation**:
   - `/gui/gui_main.py`
   - `/gui/gui_launcher.py`
   - `/gui/gui_enhanced.py`

4. **Configuration**:
   - `/gui/agent_mode_config.json`
   - `/gui/hardware_monitor_config.json`

5. **Integration Files**:
   - `/gui/gui_mode_integration.py`
   - `/gui/agent_mode_gui_claude_integration.py`

## Common GUI Issues

1. **Import Errors**: Check Python path and module structure
2. **tkinter Issues**: Verify tkinter installation
3. **Parallel Execution**: Review IMPLEMENTATION_NOTES.md
4. **Hardware Monitoring**: Check psutil and GPUtil availability
5. **File Paths**: Ensure Windows path compatibility
6. **Syntax Errors**: Use syntax_fixer.py in gui_utils directory

## Debugging Steps

1. Check error logs in `/gui/` directory
2. Verify all dependencies are installed
3. Test with simplified GUI first
4. Check for duplicate class definitions
5. Verify proper event loop handling
6. For syntax errors, run `/gui_utils/syntax_fixer.py` on problematic files

## Last Updated
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Generated for: GUI Problem Solving
"""
        
        return summary


def main():
    """Main function to update all context and summaries"""
    builder = AIManagerContextBuilder()
    
    logger.info("Building general context...")
    general_context = builder.build_context()
    builder.save_context(general_context)
    
    logger.info("Updating startup summary...")
    builder.update_startup_summary({
        "Advanced Physics": "Enabled in Div_AI_Agent_Focus_1",
        "Documentation": "Consolidated and indexed"
    })
    
    # Create role-specific summaries
    roles = ["project_ai_manager", "resource_manager", "git_task_manager", "model_manager"]
    
    for role in roles:
        logger.info(f"Creating summary for {role}...")
        summary = builder.create_role_specific_summary(role)
        summary_path = builder.ai_managers_dir / f"{role}_summary.md"
        
        with open(summary_path, 'w') as f:
            f.write(summary)
        
        logger.info(f"Saved {summary_path}")
    
    logger.info("Context building complete!")
    
    # Also run the existing documentation summarizer for compatibility
    try:
        from documentation_summarizer import DocumentationSummarizer
        summarizer = DocumentationSummarizer()
        summarizer.run_comprehensive_summary()
        logger.info("Also updated legacy documentation summaries")
    except Exception as e:
        logger.warning(f"Could not run legacy summarizer: {e}")


if __name__ == "__main__":
    main()