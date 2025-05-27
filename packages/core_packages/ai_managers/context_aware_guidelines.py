#!/usr/bin/env python
"""
Context-Aware Guidelines System

Automatically provides AI agents with relevant guidelines based on their current tasks
and session context. This system integrates with the session detector to provide
task-specific guidance from README files and documentation.
"""

import os
import re
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContextAwareGuidelines")

class ContextAwareGuidelines:
    """Provides task-specific guidelines to AI agents based on their current context"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.guidelines_cache = {}
        self.last_cache_update = 0
        self.cache_duration = 300  # 5 minutes
        
        # Initialize session detector integration
        self.session_detector = None
        self._init_session_integration()
        
        # Task keyword mapping to guideline files
        self.task_keywords = {
            # 3D/Modeling tasks
            "3d": ["README_Agent_1.md", "ai_managers/README.md"],
            "blender": ["README_Agent_1.md", "automated_workflow_integration_guide.md"],
            "model": ["README_Agent_1.md", "CLAUDE.md"],
            "simulation": ["README_Agent_1.md", "ai_managers/README_PARALLEL_EXECUTION.md"],
            "open3d": ["README_Agent_1.md", "START_AGENT_MODE_README.md"],
            
            # GUI/Interface tasks
            "gui": ["CLAUDE.md", "docs/DEVELOPER_GUIDE.md"],
            "interface": ["docs/DEVELOPER_GUIDE.md", "CLAUDE.md"],
            "layout": ["CLAUDE.md"],
            
            # File/Resource management
            "file": ["docs/TOKEN_EFFICIENCY_RULES.md", "ai_managers/README.md"],
            "resource": ["ai_managers/README_PARALLEL_EXECUTION.md", "docs/TOKEN_EFFICIENCY_RULES.md"],
            "memory": ["MEMORY_GUIDELINES.md", "docs/TOKEN_EFFICIENCY_RULES.md"],
            
            # Error handling
            "error": ["ERROR_HANDLING_SYSTEM.md", "automated_workflow_integration_guide.md"],
            "debug": ["ERROR_HANDLING_SYSTEM.md", "ai_managers/README.md"],
            "fix": ["ERROR_HANDLING_SYSTEM.md", "CLAUDE.md"],
            
            # Development tasks
            "code": ["CLAUDE.md", "docs/DEVELOPER_GUIDE.md"],
            "development": ["docs/DEVELOPER_GUIDE.md", "CLAUDE.md"],
            "testing": ["docs/DEVELOPER_GUIDE.md", "START_AGENT_MODE_README.md"],
            
            # Workflow/Automation
            "workflow": ["automated_workflow_integration_guide.md", "ai_managers/README.md"],
            "automation": ["ai_managers/README.md", "automated_workflow_integration_guide.md"],
            "agent": ["ai_managers/README.md", "START_AGENT_MODE_README.md"],
        }
        
        # Load guidelines cache
        self._load_guidelines_cache()
    
    def _init_session_integration(self):
        """Initialize integration with session detector"""
        try:
            from session_detector import get_session_detector
            self.session_detector = get_session_detector()
            logger.info("Session detector integration initialized")
        except ImportError:
            logger.warning("Session detector not available - context detection will be limited")
    
    def _load_guidelines_cache(self):
        """Load and cache all guideline files using existing documentation summarizer"""
        current_time = time.time()
        
        # Check if cache is still valid
        if (current_time - self.last_cache_update) < self.cache_duration and self.guidelines_cache:
            return
        
        logger.info("Loading guidelines cache using documentation summarizer")
        
        # Use existing documentation summarizer
        try:
            from documentation_summarizer import DocumentationSummarizer
            doc_summarizer = DocumentationSummarizer(self.base_dir)
            
            # Run comprehensive summary to get updated file locations
            summary_results = doc_summarizer.run_comprehensive_summary()
            
            # Load summarized README files
            readme_summaries = summary_results.get("readme_files", {})
            
            logger.info(f"Using documentation summarizer with {len(readme_summaries)} README files")
            
        except ImportError:
            logger.warning("Documentation summarizer not available, using manual file list")
            readme_summaries = {}
        
        # Core guideline files - updated with new file locations after consolidation
        core_files = [
            "README.md",
            "CLAUDE.md", 
            "ERROR_HANDLING_SYSTEM.md",
            "automated_workflow_integration_guide.md",
            "MEMORY_GUIDELINES.md",
            "RESOURCE_MANAGEMENT.md",
            
            # AI Managers
            "ai_managers/README.md",
            "ai_managers/README_PARALLEL_EXECUTION.md",
            "ai_managers/CLAUDE_PARALLEL_README.md",
            
            # Agent-specific
            "Div_AI_Agent_Focus_1/README_Agent_1.md",
            
            # GUI-related (moved to gui folder)
            "gui/GUI_README.md",
            "gui/README_GUI_ENHANCEMENTS.md",
            
            # Documentation (moved to docs folder)
            "docs/README.md",
            "docs/TOKEN_EFFICIENCY_RULES.md",
            "docs/DEVELOPER_GUIDE.md",
            "docs/START_AGENT_MODE_README.md",
            "docs/AI_AGENT_ERROR_HANDLING_GUIDE.md",
            "docs/DASHBOARD_README.md",
            "docs/MODEL_VIEWER_README.md",
            "docs/HARDWARE_MONITOR_README.md",
            "docs/MODEL_EXPORT_IMPORT_README.md"
        ]
        
        self.guidelines_cache = {}
        
        # First, try to use summarized content from documentation_summarizer
        for file_path in core_files:
            if file_path in readme_summaries:
                # Use pre-summarized content
                summary_data = readme_summaries[file_path]
                summary_content = summary_data.get("summary", "")
                
                self.guidelines_cache[file_path] = {
                    "content": summary_content,  # Use summarized content to save tokens
                    "sections": self._parse_sections(summary_content),
                    "keywords": self._extract_keywords(summary_content),
                    "last_modified": summary_data.get("last_modified", 0),
                    "size": summary_data.get("size", 0),
                    "is_summarized": True
                }
                logger.debug(f"Loaded summarized guidelines from {file_path}")
                continue
            
            # Fall back to loading full content if not in summarizer
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.guidelines_cache[file_path] = {
                        "content": content,
                        "sections": self._parse_sections(content),
                        "keywords": self._extract_keywords(content),
                        "last_modified": os.path.getmtime(full_path),
                        "is_summarized": False
                    }
                    logger.debug(f"Loaded full guidelines from {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
            else:
                logger.warning(f"Guideline file not found: {file_path}")
        
        self.last_cache_update = current_time
        logger.info(f"Guidelines cache loaded with {len(self.guidelines_cache)} files")
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown sections from content"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for markdown headers
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_keywords(self, content: str) -> Set[str]:
        """Extract relevant keywords from content"""
        # Convert to lowercase for matching
        content_lower = content.lower()
        
        # Common technical keywords
        keywords = set()
        
        # Extract words that might be relevant
        words = re.findall(r'\b[a-z]{3,}\b', content_lower)
        
        # Filter for relevant terms
        relevant_terms = {
            'blender', 'gui', 'error', 'file', 'memory', 'token', 'agent', 'workflow',
            'automation', 'resource', 'parallel', 'session', 'conflict', 'guideline',
            'rule', 'principle', 'model', 'simulation', 'development', 'testing',
            'debugging', 'optimization', 'efficiency', 'management', 'integration'
        }
        
        keywords = set(word for word in words if word in relevant_terms)
        
        return keywords
    
    def get_relevant_guidelines(self, task_description: str = "", 
                              session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get guidelines relevant to the current task and context
        
        Args:
            task_description: Description of the current task
            session_context: Additional context about the session
            
        Returns:
            Dict containing relevant guidelines and sections
        """
        # Refresh cache if needed
        self._load_guidelines_cache()
        
        # Get session context if not provided
        if not session_context and self.session_detector:
            session_context = {
                "session_type": self.session_detector.get_current_session_type(),
                "session_id": self.session_detector.get_current_session_id(),
            }
        
        # Analyze task for keywords
        task_keywords = self._analyze_task_keywords(task_description)
        
        # Find relevant guideline files
        relevant_files = self._find_relevant_files(task_keywords, session_context)
        
        # Extract relevant sections
        relevant_guidelines = self._extract_relevant_sections(relevant_files, task_keywords)
        
        return {
            "task_description": task_description,
            "detected_keywords": list(task_keywords),
            "session_context": session_context,
            "relevant_files": list(relevant_files),
            "guidelines": relevant_guidelines,
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_task_keywords(self, task_description: str) -> Set[str]:
        """Analyze task description to extract relevant keywords"""
        keywords = set()
        
        task_lower = task_description.lower()
        
        # Check for explicit keywords
        for keyword in self.task_keywords.keys():
            if keyword in task_lower:
                keywords.add(keyword)
        
        # Check for related terms
        word_patterns = {
            "3d": ["three.?dimensional", "modeling", "mesh", "vertex"],
            "gui": ["interface", "window", "button", "layout", "form"],
            "error": ["bug", "exception", "failure", "crash", "problem"],
            "file": ["document", "save", "load", "read", "write"],
            "workflow": ["process", "procedure", "step", "automation"],
        }
        
        for main_keyword, patterns in word_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    keywords.add(main_keyword)
        
        return keywords
    
    def _find_relevant_files(self, task_keywords: Set[str], 
                           session_context: Optional[Dict[str, Any]]) -> Set[str]:
        """Find guideline files relevant to the task and session"""
        relevant_files = set()
        
        # Always include core files
        core_files = ["CLAUDE.md", "README.md", "docs/TOKEN_EFFICIENCY_RULES.md"]
        relevant_files.update(core_files)
        
        # Add files based on task keywords
        for keyword in task_keywords:
            if keyword in self.task_keywords:
                relevant_files.update(self.task_keywords[keyword])
        
        # Add files based on session context
        if session_context:
            session_type = session_context.get("session_type", "")
            
            if session_type == "gui_workflow":
                relevant_files.add("automated_workflow_integration_guide.md")
                relevant_files.add("ai_managers/README_PARALLEL_EXECUTION.md")
            elif session_type == "terminal":
                relevant_files.add("CLAUDE.md")
                relevant_files.add("docs/TOKEN_EFFICIENCY_RULES.md")
            elif session_type == "vscode_agent":
                relevant_files.add("docs/DEVELOPER_GUIDE.md")
                relevant_files.add("CLAUDE.md")
        
        # Filter to only files that exist in cache
        return {f for f in relevant_files if f in self.guidelines_cache}
    
    def _extract_relevant_sections(self, relevant_files: Set[str], 
                                 task_keywords: Set[str]) -> Dict[str, Any]:
        """Extract the most relevant sections from guideline files"""
        guidelines = {}
        
        for file_path in relevant_files:
            if file_path not in self.guidelines_cache:
                continue
            
            file_data = self.guidelines_cache[file_path]
            sections = file_data["sections"]
            
            # Find most relevant sections
            relevant_sections = {}
            
            for section_name, section_content in sections.items():
                relevance_score = self._calculate_section_relevance(
                    section_content, task_keywords
                )
                
                if relevance_score > 0:
                    relevant_sections[section_name] = {
                        "content": section_content,
                        "relevance_score": relevance_score
                    }
            
            if relevant_sections:
                guidelines[file_path] = {
                    "file_path": file_path,
                    "sections": relevant_sections,
                    "total_relevance": sum(s["relevance_score"] for s in relevant_sections.values())
                }
        
        return guidelines
    
    def _calculate_section_relevance(self, section_content: str, 
                                   task_keywords: Set[str]) -> float:
        """Calculate how relevant a section is to the current task"""
        content_lower = section_content.lower()
        score = 0.0
        
        # Check for keyword matches
        for keyword in task_keywords:
            if keyword in content_lower:
                score += 1.0
        
        # Boost score for sections with implementation details
        implementation_terms = ["should", "must", "guideline", "rule", "principle", "important"]
        for term in implementation_terms:
            if term in content_lower:
                score += 0.5
        
        # Boost score for actionable content
        if any(word in content_lower for word in ["follow", "use", "implement", "apply"]):
            score += 0.3
        
        return score
    
    def format_guidelines_for_agent(self, guidelines_data: Dict[str, Any]) -> str:
        """Format guidelines in a readable format for AI agents"""
        if not guidelines_data.get("guidelines"):
            return "No specific guidelines found for this task."
        
        output = []
        output.append("# Task-Specific Guidelines")
        output.append(f"**Task**: {guidelines_data.get('task_description', 'Not specified')}")
        output.append(f"**Keywords**: {', '.join(guidelines_data.get('detected_keywords', []))}")
        output.append("")
        
        # Sort guidelines by relevance
        sorted_guidelines = sorted(
            guidelines_data["guidelines"].items(),
            key=lambda x: x[1]["total_relevance"],
            reverse=True
        )
        
        for file_path, file_data in sorted_guidelines:
            output.append(f"## From {file_path}")
            
            # Sort sections by relevance
            sorted_sections = sorted(
                file_data["sections"].items(),
                key=lambda x: x[1]["relevance_score"],
                reverse=True
            )
            
            for section_name, section_data in sorted_sections[:3]:  # Top 3 most relevant sections
                output.append(f"### {section_name}")
                output.append(section_data["content"])
                output.append("")
        
        return "\n".join(output)
    
    def get_quick_guidelines(self, task_description: str) -> str:
        """Get formatted guidelines quickly for immediate use"""
        guidelines_data = self.get_relevant_guidelines(task_description)
        return self.format_guidelines_for_agent(guidelines_data)
    
    def should_agent_read_guidelines(self, task_description: str = "") -> bool:
        """Determine if an agent should read guidelines for the current task"""
        # Always read guidelines for complex tasks
        complex_keywords = {"error", "workflow", "automation", "gui", "model", "development"}
        
        task_lower = task_description.lower()
        
        # Check for complex task indicators
        if any(keyword in task_lower for keyword in complex_keywords):
            return True
        
        # Check for guideline violations in recent history
        # This could be expanded to track common mistakes
        
        return len(task_description) > 50  # Read guidelines for detailed tasks


# Global instance
_guidelines_system = None

def get_guidelines_system() -> ContextAwareGuidelines:
    """Get the global guidelines system instance"""
    global _guidelines_system
    if _guidelines_system is None:
        _guidelines_system = ContextAwareGuidelines()
    return _guidelines_system

def get_task_guidelines(task_description: str) -> str:
    """Quick function to get guidelines for a task"""
    system = get_guidelines_system()
    return system.get_quick_guidelines(task_description)

def should_read_guidelines(task_description: str) -> bool:
    """Quick function to check if guidelines should be read"""
    system = get_guidelines_system()
    return system.should_agent_read_guidelines(task_description)

# Example usage
if __name__ == "__main__":
    print("Testing Context-Aware Guidelines System")
    
    system = ContextAwareGuidelines()
    
    # Test different task types
    test_tasks = [
        "Fix GUI layout issues in the main window",
        "Create a 3D model in Blender",
        "Handle file access errors in the workflow",
        "Optimize memory usage for large datasets",
        "Debug the automated workflow system"
    ]
    
    for task in test_tasks:
        print(f"\n=== Task: {task} ===")
        print(f"Should read guidelines: {system.should_agent_read_guidelines(task)}")
        
        guidelines = system.get_quick_guidelines(task)
        print("Guidelines preview:")
        print(guidelines[:300] + "..." if len(guidelines) > 300 else guidelines)
        print("-" * 50)