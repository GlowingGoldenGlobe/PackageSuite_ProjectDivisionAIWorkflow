#!/usr/bin/env python
"""
Documentation Summarizer for GlowingGoldenGlobe

This module provides utilities to summarize long documentation files
to reduce token usage when they are needed by API LLM Agent mode and
Pyautogen AI Agents mode.
"""

import os
import re
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("documentation_summarizer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("DocumentationSummarizer")

class DocumentationSummarizer:
    """
    Summarizes documentation files to reduce token usage when they are needed
    by API LLM Agent mode and Pyautogen AI Agents mode.
    """
    
    def __init__(self, base_dir=None):
        """Initialize the Documentation Summarizer with project base directory"""
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.summaries_file = os.path.join(self.base_dir, "ai_managers", "doc_summaries.json")
        self.summaries = self._load_summaries()
        
    def _load_summaries(self):
        """Load existing summaries from file"""
        if os.path.exists(self.summaries_file):
            try:
                with open(self.summaries_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading summaries: {e}")
                
        return {
            "file_locations": {},
            "readme_files": {},
            "gui_files": {},
            "scripts": {},
            "last_updated": None
        }
    
    def _save_summaries(self):
        """Save summaries to file"""
        try:
            self.summaries["last_updated"] = self._get_timestamp()
            with open(self.summaries_file, "w") as f:
                json.dump(self.summaries, f, indent=2)
            logger.info(f"Saved summaries to {self.summaries_file}")
        except Exception as e:
            logger.error(f"Error saving summaries: {e}")
    
    def _get_timestamp(self):
        """Return current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def summarize_markdown_file(self, file_path):
        """
        Summarize a markdown file by extracting:
        - Main headings
        - First paragraph after each heading
        - Any code blocks (shortened if too long)
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Extract headings and first paragraph after each
            summary = []
            
            # Get title (level 1 heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                summary.append(f"# {title_match.group(1)}")
            
            # Find all headings
            headings = re.findall(r'^(#{2,4})\s+(.+)$', content, re.MULTILINE)
            
            for heading_level, heading_text in headings:
                summary.append(f"{heading_level} {heading_text}")
                
                # Find content after this heading until next heading or end of file
                pattern = f"^{heading_level}\\s+{re.escape(heading_text)}$((.*?))^#"
                content_match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                
                if content_match:
                    # Get first paragraph only (limited chars)
                    paragraphs = content_match.group(1).strip().split('\n\n')
                    if paragraphs:
                        first_para = paragraphs[0].strip()
                        # Limit paragraph length
                        if len(first_para) > 200:
                            first_para = first_para[:197] + "..."
                        summary.append(first_para + "\n")
            
            return "\n".join(summary)
                
        except Exception as e:
            logger.error(f"Error summarizing {file_path}: {e}")
            return None
    
    def summarize_python_script(self, file_path):
        """
        Summarize a Python script by extracting:
        - Module docstring
        - Class and function names with their docstrings
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            summary = []
            
            # Extract module docstring
            module_docstring = re.search(r'^"""(.+?)"""', content, re.DOTALL)
            if module_docstring:
                doc = module_docstring.group(1).strip()
                # Limit docstring length
                if len(doc) > 300:
                    doc = doc[:297] + "..."
                summary.append(f"# Module: {os.path.basename(file_path)}\n{doc}\n")
            
            # Extract class definitions
            classes = re.findall(r'class\s+(\w+)(?:\(.+?\))?:\s*(?:"""(.+?)""")?', content, re.DOTALL)
            for class_name, class_doc in classes:
                class_doc = class_doc.strip() if class_doc else "No description"
                if len(class_doc) > 200:
                    class_doc = class_doc[:197] + "..."
                summary.append(f"## Class: {class_name}\n{class_doc}\n")
            
            # Extract function definitions
            functions = re.findall(r'def\s+(\w+)\((.+?)\):\s*(?:"""(.+?)""")?', content, re.DOTALL)
            for func_name, func_params, func_doc in functions:
                if func_name.startswith('_') and func_name != '__init__':
                    continue  # Skip private methods except __init__
                func_doc = func_doc.strip() if func_doc else "No description"
                if len(func_doc) > 150:
                    func_doc = func_doc[:147] + "..."
                summary.append(f"### Function: {func_name}\n{func_doc}\n")
            
            return "\n".join(summary)
                
        except Exception as e:
            logger.error(f"Error summarizing {file_path}: {e}")
            return None
    
    def summarize_powershell_script(self, file_path):
        """
        Summarize a PowerShell script by extracting:
        - Script header comments
        - Function names and their comments
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            summary = []
            
            # Extract header comments
            header_comments = re.search(r'^<#(.+?)#>', content, re.DOTALL)
            if header_comments:
                header = header_comments.group(1).strip()
                if len(header) > 300:
                    header = header[:297] + "..."
                summary.append(f"# PowerShell Script: {os.path.basename(file_path)}\n{header}\n")
            else:
                # Try single-line comments at the beginning
                first_lines = content.split('\n')[:10]
                header_lines = []
                for line in first_lines:
                    if line.strip().startswith('#'):
                        header_lines.append(line.strip()[1:].strip())
                    elif line.strip() and not line.strip().startswith('#'):
                        break
                
                if header_lines:
                    header = '\n'.join(header_lines)
                    summary.append(f"# PowerShell Script: {os.path.basename(file_path)}\n{header}\n")
            
            # Extract function definitions
            functions = re.findall(r'function\s+(\w+|-\w+)\s*{(.+?)}', content, re.DOTALL)
            for func_name, func_body in functions:
                # Try to get comments above function
                func_comment_match = re.search(r'(#.+?)function\s+' + re.escape(func_name), content, re.DOTALL)
                func_comment = ""
                if func_comment_match:
                    func_comment = func_comment_match.group(1).strip()
                    # Extract only lines with #
                    comment_lines = []
                    for line in func_comment.split('\n'):
                        if line.strip().startswith('#'):
                            comment_lines.append(line.strip()[1:].strip())
                    func_comment = '\n'.join(comment_lines)
                
                summary.append(f"## Function: {func_name}\n{func_comment or 'No description'}\n")
            
            return "\n".join(summary)
                
        except Exception as e:
            logger.error(f"Error summarizing {file_path}: {e}")
            return None

    def summarize_file_locations(self):
        """
        Create a summary of important file locations needed by API LLM Agent mode
        and Pyautogen AI Agents mode
        """
        try:
            # Define important directories to scan
            dirs_to_scan = [
                "",  # Root
                "ai_managers",
                "gui",
                "api",
                "models",
                "scripts"
            ]
            
            file_locations = {}
            
            for dir_name in dirs_to_scan:
                dir_path = os.path.join(self.base_dir, dir_name)
                if not os.path.exists(dir_path):
                    continue
                    
                # Get all files in this directory
                files = []
                try:
                    for file in os.listdir(dir_path):
                        if file.endswith(('.py', '.md', '.json', '.ps1')):
                            file_path = os.path.join(dir_path, file)
                            if os.path.isfile(file_path):
                                files.append({
                                    "name": file,
                                    "path": os.path.relpath(file_path, self.base_dir),
                                    "size": os.path.getsize(file_path),
                                    "type": file.split('.')[-1]
                                })
                except Exception as e:
                    logger.warning(f"Error listing directory {dir_path}: {e}")
                
                # Sort by type and name
                files.sort(key=lambda x: (x['type'], x['name']))
                
                if files:
                    file_locations[dir_name or "root"] = files
            
            # Update summaries
            self.summaries["file_locations"] = file_locations
            self._save_summaries()
            
            return file_locations
            
        except Exception as e:
            logger.error(f"Error summarizing file locations: {e}")
            return None
    
    def summarize_readme_files(self):
        """Summarize key README files in the project"""
        readme_files = [
            # Core project files
            "README.md",
            "CLAUDE.md",
            "ERROR_HANDLING_SYSTEM.md",
            "automated_workflow_integration_guide.md",
            "MEMORY_GUIDELINES.md",
            "RESOURCE_MANAGEMENT.md",
            
            # AI Managers
            os.path.join("ai_managers", "README.md"),
            os.path.join("ai_managers", "README_PARALLEL_EXECUTION.md"),
            os.path.join("ai_managers", "CLAUDE_PARALLEL_README.md"),
            
            # Agent-specific
            "Div_AI_Agent_Focus_1/README_Agent_1.md",
            
            # GUI-related (moved to gui folder)
            os.path.join("gui", "GUI_README.md"),
            os.path.join("gui", "README_GUI_ENHANCEMENTS.md"),
            
            # Feature-specific (moved to docs folder)
            os.path.join("docs", "DASHBOARD_README.md"),
            os.path.join("docs", "MODEL_VIEWER_README.md"),
            os.path.join("docs", "HARDWARE_MONITOR_README.md"),
            os.path.join("docs", "MODEL_EXPORT_IMPORT_README.md"),
            os.path.join("docs", "START_AGENT_MODE_README.md"),
            os.path.join("docs", "AI_AGENT_ERROR_HANDLING_GUIDE.md"),
            
            # Documentation
            os.path.join("docs", "README.md"),
            os.path.join("docs", "TOKEN_EFFICIENCY_RULES.md"),
            os.path.join("docs", "DEVELOPER_GUIDE.md"),
            os.path.join("docs", "duplicate_file_prevention_task.md"),
            os.path.join("docs", "README_MODULAR.md"),
            os.path.join("docs", "github", "README_GitHub.md"),
            os.path.join("docs", "github", "README_GitHub_MergeHandler.md"),
            os.path.join("docs", "github", "README_MERGE_HANDLER.md"),
            
            # Integration-specific
            os.path.join("cloud_storage", "CLOUD_STORAGE_README.md"),
            os.path.join("ros2_integration", "ROS2_INTEGRATION_README.md")
        ]
        
        summaries = {}
        for readme_file in readme_files:
            file_path = os.path.join(self.base_dir, readme_file)
            if os.path.exists(file_path):
                summary = self.summarize_markdown_file(file_path)
                if summary:
                    summaries[readme_file] = {
                        "summary": summary,
                        "last_modified": os.path.getmtime(file_path),
                        "size": os.path.getsize(file_path)
                    }
        
        # Update summaries
        self.summaries["readme_files"] = summaries
        self._save_summaries()
        
        return summaries
    
    def summarize_gui_structure(self):
        """Summarize GUI structure documentation"""
        gui_structure_file = os.path.join(self.base_dir, "gui", "GUI_Structure.md")
        
        if os.path.exists(gui_structure_file):
            summary = self.summarize_markdown_file(gui_structure_file)
            if summary:
                self.summaries["gui_files"]["GUI_Structure.md"] = {
                    "summary": summary,
                    "last_modified": os.path.getmtime(gui_structure_file),
                    "size": os.path.getsize(gui_structure_file)
                }
                self._save_summaries()
                return summary
        
        return None
    
    def summarize_script(self, file_name, script_type=None):
        """Summarize a script file (PowerShell or Python)"""
        file_path = self._find_script_file(file_name)
        
        if not file_path:
            logger.warning(f"Script not found: {file_name}")
            return None
            
        if script_type == "powershell" or file_path.endswith(".ps1"):
            summary = self.summarize_powershell_script(file_path)
        elif script_type == "python" or file_path.endswith(".py"):
            summary = self.summarize_python_script(file_path)
        else:
            logger.warning(f"Unsupported script type for {file_path}")
            return None
            
        if summary:
            rel_path = os.path.relpath(file_path, self.base_dir)
            self.summaries["scripts"][rel_path] = {
                "summary": summary,
                "last_modified": os.path.getmtime(file_path),
                "size": os.path.getsize(file_path)
            }
            self._save_summaries()
            
        return summary
    
    def _find_script_file(self, file_name):
        """Find a script file in the project"""
        for root, _, files in os.walk(self.base_dir):
            if file_name in files:
                return os.path.join(root, file_name)
        
        # Try with extension variations
        if not file_name.endswith(('.ps1', '.py')):
            for ext in ['.ps1', '.py']:
                for root, _, files in os.walk(self.base_dir):
                    if file_name + ext in files:
                        return os.path.join(root, file_name + ext)
        
        return None
    
    def run_comprehensive_summary(self):
        """Run all summarization functions and return a comprehensive summary"""
        logger.info("Starting comprehensive summarization")
        
        results = {
            "file_locations": self.summarize_file_locations(),
            "readme_files": self.summarize_readme_files(),
            "gui_structure": self.summarize_gui_structure(),
            "scripts": {}
        }
        
        # Summarize specific scripts mentioned in the requirements
        for script in ["Test-GUIFunctionality.ps1", "Update-GUIShortcuts.ps1", "Agent1_Part1.py"]:
            results["scripts"][script] = self.summarize_script(script)
            
        logger.info("Comprehensive summarization completed")
        return results

if __name__ == "__main__":
    # When run directly, perform comprehensive summarization
    summarizer = DocumentationSummarizer()
    summarizer.run_comprehensive_summary()
    print(f"Summaries saved to {summarizer.summaries_file}")
