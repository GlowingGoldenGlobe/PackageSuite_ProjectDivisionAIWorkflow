#!/usr/bin/env python
"""
Scheduled Tasks for GlowingGoldenGlobe Parallel Execution Manager

This module manages scheduled tasks for the Parallel Execution Manager,
including periodic package updates, system assessments, and maintenance tasks.
"""

import os
import sys
import json
import time
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parallel_execution_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ParallelExecutionScheduler")

class ScheduledTaskManager:
    """Manages scheduled tasks for the Parallel Execution Manager"""
    
    def __init__(self, config_path: str = "parallel_execution_tasks.json"):
        """Initialize the Scheduled Task Manager"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, config_path)
        
        # Load tasks configuration
        self.tasks = self._load_tasks_config()
        
        # Track last run time for each task
        self.last_run = {}
        
        # Critical packages that need regular updates
        self.critical_packages = [
            "psutil",         # Hardware monitoring
            "flask",          # Web interface & webhooks
            "requests",       # API communication
            "numpy",          # Numerical computing
            "matplotlib",     # Visualization
            "pillow",         # Image processing
            "torch",          # Machine learning
            "tensorflow",     # Machine learning
            "scipy",          # Scientific computing
            "pandas",         # Data analysis
        ]
    
    def _load_tasks_config(self) -> Dict[str, Any]:
        """Load tasks configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    tasks = json.load(f)
                logger.info(f"Loaded tasks configuration from {self.config_path}")
                return tasks
            except Exception as e:
                logger.error(f"Error loading tasks config: {e}")
        
        # Create default tasks configuration
        default_tasks = {
            "package_update_check": {
                "enabled": True,
                "interval_hours": 24,
                "description": "Check for updates to critical packages",
                "last_run": None,
                "priority": "high"
            },
            "system_health_check": {
                "enabled": True,
                "interval_hours": 4,
                "description": "Verify system health and resource usage",
                "last_run": None,
                "priority": "critical"
            },
            "script_syntax_validation": {
                "enabled": True,
                "interval_hours": 12,
                "description": "Validate syntax for all Python scripts",
                "last_run": None,
                "priority": "medium"
            },
            "model_assessment": {
                "enabled": True,
                "interval_hours": 48,
                "description": "Assess AI models for quality and improvements",
                "last_run": None,
                "priority": "high"
            },
            "log_cleanup": {
                "enabled": True,
                "interval_hours": 168,  # Once a week
                "description": "Clean up old log files",
                "last_run": None,
                "priority": "low"
            },
            "utils_assessment_cleanup": {
                "enabled": True,
                "interval_hours": 720,  # Once a month (30 days)
                "description": "Assessment-based cleanup of /utils/ folder",
                "last_run": None,
                "priority": "medium"
            },
            "template_consistency_check": {
                "enabled": True,
                "interval_hours": 168,  # Once a week
                "description": "Check template consistency and detect required updates",
                "last_run": None,
                "priority": "high"
            },
            "documentation_sync": {
                "enabled": True,
                "interval_hours": 72,
                "description": "Verify documentation is up to date",
                "last_run": None,
                "priority": "medium"
            }
        }
        
        # Save default configuration
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_tasks, f, indent=2)
            logger.info(f"Created default tasks configuration at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating default tasks config: {e}")
        
        return default_tasks
    
    def _save_tasks_config(self):
        """Save tasks configuration to file"""
        try:
            # Update last_run times in the configuration
            for task_id, last_run_time in self.last_run.items():
                if task_id in self.tasks:
                    self.tasks[task_id]["last_run"] = last_run_time.isoformat() if last_run_time else None
            
            with open(self.config_path, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            logger.info(f"Saved tasks configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving tasks config: {e}")
    
    def should_run(self, task_id: str) -> bool:
        """Check if a task should be run based on its interval"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        
        # Skip disabled tasks
        if not task.get("enabled", False):
            return False
        
        # Get the last run time
        last_run = None
        if task_id in self.last_run:
            last_run = self.last_run[task_id]
        elif task.get("last_run"):
            try:
                last_run = datetime.datetime.fromisoformat(task["last_run"])
                self.last_run[task_id] = last_run
            except ValueError:
                # Invalid date format, treat as never run
                last_run = None
        
        # If never run, should run now
        if last_run is None:
            return True
        
        # Check if enough time has passed
        interval_hours = task.get("interval_hours", 24)
        now = datetime.datetime.now()
        time_since_last_run = now - last_run
        
        # Convert to hours
        hours_since_last_run = time_since_last_run.total_seconds() / 3600
        
        return hours_since_last_run >= interval_hours
    
    def run_task(self, task_id: str) -> bool:
        """Run a specified task"""
        if task_id not in self.tasks:
            logger.error(f"Unknown task: {task_id}")
            return False
        
        task = self.tasks[task_id]
        logger.info(f"Running task: {task_id} - {task.get('description', 'No description')}")
        
        try:
            # Run the specific task
            if task_id == "package_update_check":
                success = self._check_package_updates()
            elif task_id == "system_health_check":
                success = self._check_system_health()
            elif task_id == "script_syntax_validation":
                success = self._validate_script_syntax()
            elif task_id == "model_assessment":
                success = self._assess_models()
            elif task_id == "log_cleanup":
                success = self._cleanup_logs()
            elif task_id == "utils_assessment_cleanup":
                success = self._utils_assessment_cleanup()
            elif task_id == "template_consistency_check":
                success = self._check_template_consistency()
            elif task_id == "documentation_sync":
                success = self._sync_documentation()
            else:
                logger.warning(f"No implementation for task: {task_id}")
                return False
            
            # Update last run time
            if success:
                self.last_run[task_id] = datetime.datetime.now()
                self._save_tasks_config()
                logger.info(f"Task completed successfully: {task_id}")
            else:
                logger.warning(f"Task failed: {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error running task {task_id}: {str(e)}")
            return False
    
    def check_all_scheduled_tasks(self):
        """Check all scheduled tasks and run those that are due"""
        logger.info("Checking scheduled tasks")
        
        for task_id in self.tasks:
            if self.should_run(task_id):
                logger.info(f"Task {task_id} is due to run")
                self.run_task(task_id)
            else:
                # Calculate when it will next run
                task = self.tasks[task_id]
                interval_hours = task.get("interval_hours", 24)
                
                last_run = None
                if task_id in self.last_run:
                    last_run = self.last_run[task_id]
                elif task.get("last_run"):
                    try:
                        last_run = datetime.datetime.fromisoformat(task["last_run"])
                    except ValueError:
                        last_run = None
                
                if last_run:
                    next_run = last_run + datetime.timedelta(hours=interval_hours)
                    now = datetime.datetime.now()
                    time_until_next = next_run - now
                    hours_until_next = max(0, time_until_next.total_seconds() / 3600)
                    
                    logger.debug(f"Task {task_id} will run in {hours_until_next:.1f} hours")
    
    def _check_package_updates(self) -> bool:
        """Check for updates to critical packages"""
        logger.info("Checking for package updates")
        
        update_needed = []
        installed_versions = {}
        latest_versions = {}
        
        for package in self.critical_packages:
            try:
                # Check if package is installed
                try:
                    module = importlib.import_module(package)
                    installed = True
                    if hasattr(module, "__version__"):
                        version = module.__version__
                    else:
                        # Try to get version using pip
                        pip_result = subprocess.run(
                            [sys.executable, "-m", "pip", "show", package],
                            capture_output=True,
                            text=True
                        )
                        
                        if pip_result.returncode == 0:
                            for line in pip_result.stdout.split("\n"):
                                if line.startswith("Version:"):
                                    version = line.split(":", 1)[1].strip()
                                    break
                            else:
                                version = "Unknown"
                        else:
                            version = "Unknown"
                            
                except ImportError:
                    installed = False
                    version = "Not installed"
                
                installed_versions[package] = version
                
                # Check latest version from PyPI
                pypi_result = subprocess.run(
                    [sys.executable, "-m", "pip", "index", "versions", package],
                    capture_output=True,
                    text=True
                )
                
                if pypi_result.returncode == 0:
                    output_lines = pypi_result.stdout.strip().split("\n")
                    
                    # Find the latest version
                    for line in output_lines:
                        if "Available versions:" in line:
                            versions_part = line.split("Available versions:")[1].strip()
                            if versions_part:
                                latest_version = versions_part.split(",")[0].strip()
                                latest_versions[package] = latest_version
                                
                                # Compare versions
                                if installed and version != latest_version:
                                    update_needed.append(package)
                                break
                
                logger.info(f"Package {package}: Installed={version}, Latest={latest_versions.get(package, 'Unknown')}")
                
            except Exception as e:
                logger.error(f"Error checking package {package}: {str(e)}")
        
        # Log results
        if update_needed:
            logger.warning(f"Updates available for: {', '.join(update_needed)}")
            
            # Create a recommendation file
            try:
                with open(os.path.join(self.base_dir, "package_updates_needed.txt"), 'w') as f:
                    f.write("# GlowingGoldenGlobe Package Updates Needed\n\n")
                    f.write(f"Report generated on {datetime.datetime.now().isoformat()}\n\n")
                    
                    f.write("## Packages Needing Updates\n\n")
                    for package in update_needed:
                        f.write(f"* {package}: {installed_versions.get(package, 'Unknown')} → {latest_versions.get(package, 'Unknown')}\n")
                    
                    f.write("\n## Update Command\n\n")
                    f.write("```\npip install --upgrade " + " ".join(update_needed) + "\n```\n")
            except Exception as e:
                logger.error(f"Error creating update recommendation file: {str(e)}")
        else:
            logger.info("All critical packages are up to date")
        
        return True
    
    def _check_system_health(self) -> bool:
        """Check system health and resource usage"""
        logger.info("Checking system health")
        
        try:
            # Import hardware monitor if available
            sys.path.insert(0, self.base_dir)
            
            try:
                from hardware_monitor import HardwareMonitor
                hw_monitor = HardwareMonitor()
                
                # Get current status
                hw_status = hw_monitor.get_status()
                
                # Check if any thresholds are exceeded
                warnings = []
                if hw_status.get("cpu_percent", 0) > 80:
                    warnings.append(f"High CPU usage: {hw_status.get('cpu_percent')}%")
                if hw_status.get("memory_percent", 0) > 85:
                    warnings.append(f"High memory usage: {hw_status.get('memory_percent')}%")
                if hw_status.get("disk_percent", 0) > 90:
                    warnings.append(f"High disk usage: {hw_status.get('disk_percent')}%")
                
                if warnings:
                    logger.warning("System health warnings: " + ", ".join(warnings))
                else:
                    logger.info("System health check passed, no issues found")
                
            except ImportError:
                # Fall back to psutil if available
                try:
                    import psutil
                    
                    # Check CPU
                    cpu_percent = psutil.cpu_percent(interval=1)
                    if cpu_percent > 80:
                        logger.warning(f"High CPU usage: {cpu_percent}%")
                    
                    # Check memory
                    mem = psutil.virtual_memory()
                    if mem.percent > 85:
                        logger.warning(f"High memory usage: {mem.percent}%")
                    
                    # Check disk
                    disk = psutil.disk_usage('/')
                    if disk.percent > 90:
                        logger.warning(f"High disk usage: {disk.percent}%")
                    
                    logger.info(f"System health: CPU={cpu_percent}%, Memory={mem.percent}%, Disk={disk.percent}%")
                    
                except ImportError:
                    logger.warning("Could not perform detailed system health check: missing psutil and hardware_monitor")
                    return False
        
        except Exception as e:
            logger.error(f"Error in system health check: {str(e)}")
            return False
            
        return True
    
    def _validate_script_syntax(self) -> bool:
        """Validate syntax for all Python scripts"""
        logger.info("Validating script syntax")
        
        try:
            invalid_scripts = []
            
            # Find Python files
            py_files = []
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    if file.endswith('.py'):
                        # Skip files in certain directories
                        if any(skip_dir in root for skip_dir in ['__pycache__', '.git', 'venv', 'Lib']):
                            continue
                        py_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(py_files)} Python files to validate")
            
            # Check syntax of each file
            for file_path in py_files:
                try:
                    # Use py_compile to check syntax
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        invalid_scripts.append((file_path, result.stderr))
                        logger.warning(f"Syntax error in {os.path.basename(file_path)}: {result.stderr}")
                except Exception as e:
                    invalid_scripts.append((file_path, str(e)))
                    logger.error(f"Error checking {os.path.basename(file_path)}: {str(e)}")
            
            # Generate report if there are invalid scripts
            if invalid_scripts:
                logger.warning(f"Found {len(invalid_scripts)} scripts with syntax errors")
                
                # Create a report file
                try:
                    with open(os.path.join(self.base_dir, "syntax_validation_report.md"), 'w') as f:
                        f.write("# Python Script Syntax Validation Report\n\n")
                        f.write(f"Report generated on {datetime.datetime.now().isoformat()}\n\n")
                        
                        f.write("## Scripts with Errors\n\n")
                        for file_path, error in invalid_scripts:
                            rel_path = os.path.relpath(file_path, self.base_dir)
                            f.write(f"### {rel_path}\n\n")
                            f.write("```\n")
                            f.write(error)
                            f.write("\n```\n\n")
                except Exception as e:
                    logger.error(f"Error creating syntax validation report: {str(e)}")
            else:
                logger.info("All scripts passed syntax validation")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in script syntax validation: {str(e)}")
            return False
    
    def _assess_models(self) -> bool:
        """Assess AI models for quality and improvements"""
        logger.info("Assessing AI models")
        
        try:
            # Check if model assessment tools are available
            model_evaluator_path = os.path.join(self.base_dir, "ai_agent_model_evaluator.py")
            
            if os.path.exists(model_evaluator_path):
                # Run the model evaluator
                result = subprocess.run(
                    [sys.executable, model_evaluator_path, "--scheduled", "--report"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("Model assessment completed successfully")
                else:
                    logger.warning(f"Model assessment failed: {result.stderr}")
            else:
                logger.warning("Model evaluator not found at: " + model_evaluator_path)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in model assessment: {str(e)}")
            return False
    
    def _cleanup_logs(self) -> bool:
        """Clean up old log files"""
        logger.info("Cleaning up old log files")
        
        try:
            # Find log files older than 30 days
            log_files = []
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        
                        # Check file age
                        mod_time = os.path.getmtime(file_path)
                        file_age_days = (time.time() - mod_time) / (60 * 60 * 24)
                        
                        if file_age_days > 30:
                            log_files.append(file_path)
            
            # Archive old logs
            if log_files:
                logger.info(f"Found {len(log_files)} old log files to archive")
                
                # Create archive directory
                archive_dir = os.path.join(self.base_dir, "archived_logs")
                os.makedirs(archive_dir, exist_ok=True)
                
                # Move files to archive
                archived_count = 0
                for file_path in log_files:
                    try:
                        file_name = os.path.basename(file_path)
                        archive_path = os.path.join(archive_dir, file_name)
                        
                        # Add timestamp to avoid overwriting
                        if os.path.exists(archive_path):
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            archive_path = os.path.join(archive_dir, f"{os.path.splitext(file_name)[0]}_{timestamp}.log")
                        
                        os.rename(file_path, archive_path)
                        archived_count += 1
                    except Exception as e:
                        logger.error(f"Error archiving log file {file_path}: {str(e)}")
                
                logger.info(f"Archived {archived_count} old log files")
            else:
                logger.info("No old log files to archive")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in log cleanup: {str(e)}")
            return False
    
    def _sync_documentation(self) -> bool:
        """Verify documentation is up to date"""
        logger.info("Syncing documentation")
        
        try:
            # Check for docs directory
            docs_dir = os.path.join(self.base_dir, "docs")
            if not os.path.exists(docs_dir):
                logger.warning("Docs directory not found")
                return False
            
            # Generate documentation index
            index_path = os.path.join(docs_dir, "index.md")
            
            with open(index_path, 'w') as f:
                f.write("# GlowingGoldenGlobe Documentation Index\n\n")
                f.write(f"Generated on {datetime.datetime.now().isoformat()}\n\n")
                
                # List all markdown files in docs directory
                md_files = []
                for root, _, files in os.walk(docs_dir):
                    for file in files:
                        if file.endswith('.md') and file != "index.md":
                            rel_path = os.path.relpath(os.path.join(root, file), docs_dir)
                            md_files.append(rel_path)
                
                md_files.sort()
                
                # Add links to all documentation files
                for file_path in md_files:
                    # Extract title from file if possible
                    full_path = os.path.join(docs_dir, file_path)
                    title = file_path  # Default to file path
                    
                    try:
                        with open(full_path, 'r') as doc_file:
                            first_line = doc_file.readline().strip()
                            if first_line.startswith('#'):
                                title = first_line[1:].strip()
                    except Exception:
                        pass
                    
                    # Add to index
                    f.write(f"- [{title}]({file_path.replace(' ', '%20')})\n")
            
            logger.info(f"Documentation index updated with {len(md_files)} entries")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing documentation: {str(e)}")
            return False
    
    def _utils_assessment_cleanup(self) -> bool:
        """Run assessment-based cleanup on /utils/ directory"""
        logger.info("Running assessment-based cleanup on /utils/ directory")
        
        try:
            # Import the assessment cleanup module
            utils_dir = os.path.join(self.base_dir, "utils")
            
            # Check if assessment cleanup module exists
            cleanup_module_path = os.path.join(utils_dir, "assessment_based_cleanup.py")
            if not os.path.exists(cleanup_module_path):
                logger.warning("Assessment-based cleanup module not found")
                return False
            
            # Import and run assessment cleanup
            sys.path.insert(0, utils_dir)
            
            try:
                import assessment_based_cleanup
                
                # Initialize cleanup system
                cleanup = assessment_based_cleanup.AssessmentBasedCleanup(utils_dir)
                
                # Run full assessment
                results = cleanup.run_full_assessment()
                
                # Save assessment report
                report_path = cleanup.save_assessment_report()
                logger.info(f"Assessment report saved to: {report_path}")
                
                # Log summary
                logger.info(f"Assessment Summary: {results['total_files']} files assessed, "
                           f"{len(results['files_to_delete'])} to delete, "
                           f"{len(results['files_to_archive'])} to archive")
                
                # Execute cleanup (not dry run for scheduled execution)
                if len(results['files_to_delete']) > 0 or len(results['files_to_archive']) > 0:
                    execution_log = cleanup.execute_cleanup(dry_run=False)
                    
                    # Log actions taken
                    for action in execution_log['actions_taken']:
                        logger.info(f"Cleanup action: {action}")
                    
                    # Log any errors
                    for error in execution_log['errors']:
                        logger.error(f"Cleanup error: {error}")
                    
                    logger.info(f"Cleanup completed: {len(execution_log['actions_taken'])} actions taken")
                else:
                    logger.info("No cleanup actions needed")
                
                return True
                
            finally:
                # Remove from path
                if utils_dir in sys.path:
                    sys.path.remove(utils_dir)
                    
        except Exception as e:
            logger.error(f"Error in utils assessment cleanup: {str(e)}")
            return False
    
    def _check_template_consistency(self) -> bool:
        """Check template consistency and detect required updates"""
        logger.info("Checking template consistency")
        
        try:
            import re
            from collections import defaultdict
            
            # Analyze current project files for import patterns
            pattern_analysis = self._analyze_import_patterns()
            
            # Load current template requirements
            current_templates = self._load_current_template_requirements()
            
            # Detect inconsistencies
            inconsistencies = self._detect_template_inconsistencies(pattern_analysis, current_templates)
            
            # Generate report
            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "analysis": pattern_analysis,
                "inconsistencies": inconsistencies,
                "recommendations": self._generate_template_recommendations(inconsistencies)
            }
            
            # Save report
            report_path = os.path.join(self.base_dir, "template_consistency_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Template consistency report saved to: {report_path}")
            
            # Log critical findings
            if inconsistencies:
                logger.warning(f"Found {len(inconsistencies)} template inconsistencies")
                for inconsistency in inconsistencies[:3]:  # Log first 3
                    logger.warning(f"Template issue: {inconsistency}")
            else:
                logger.info("All templates are consistent with current project patterns")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in template consistency check: {str(e)}")
            return False
    
    def _analyze_import_patterns(self) -> dict:
        """Analyze import patterns across the project"""
        import_patterns = defaultdict(lambda: defaultdict(int))
        file_type_patterns = defaultdict(list)
        
        # Define file type patterns
        file_type_map = {
            "gui_tab": ["gui/*tab*.py", "gui/*_tab.py"],
            "ai_manager": ["ai_managers/*.py"],
            "utility_script": ["utils/*.py", "*_utility.py", "*_tool.py"]
        }
        
        try:
            # Scan project files
            for root, dirs, files in os.walk(self.base_dir):
                # Skip certain directories
                if any(skip_dir in root for skip_dir in ['.git', '__pycache__', 'Lib', 'Scripts', 'Include']):
                    continue
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.base_dir)
                        
                        # Determine file type
                        file_type = self._determine_file_type(rel_path, file_type_map)
                        if not file_type:
                            continue
                        
                        # Analyze imports in this file
                        imports = self._extract_imports_from_file(file_path)
                        
                        for import_stmt in imports:
                            import_patterns[file_type][import_stmt] += 1
                        
                        file_type_patterns[file_type].append(rel_path)
            
            return {
                "import_patterns": dict(import_patterns),
                "file_type_patterns": dict(file_type_patterns),
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing import patterns: {e}")
            return {}
    
    def _determine_file_type(self, rel_path: str, file_type_map: dict) -> str:
        """Determine file type based on path patterns"""
        import fnmatch
        
        for file_type, patterns in file_type_map.items():
            for pattern in patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return file_type
        return None
    
    def _extract_imports_from_file(self, file_path: str) -> list:
        """Extract import statements from a Python file"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line_num > 50:  # Only check first 50 lines for imports
                        break
                    
                    # Match import statements
                    if (line.startswith('import ') or 
                        line.startswith('from ') or
                        'sys.path' in line):
                        imports.append(line)
        except Exception:
            pass  # Skip files that can't be read
        
        return imports
    
    def _load_current_template_requirements(self) -> dict:
        """Load current template requirements from ai_workflow_integration.py"""
        try:
            integration_path = os.path.join(self.base_dir, "ai_workflow_integration.py")
            if not os.path.exists(integration_path):
                return {}
            
            # Import the template requirements
            sys.path.insert(0, self.base_dir)
            try:
                import ai_workflow_integration
                return {
                    "required_imports": getattr(ai_workflow_integration, 'REQUIRED_IMPORTS', {}),
                    "required_patterns": getattr(ai_workflow_integration, 'REQUIRED_PATTERNS', {})
                }
            finally:
                if self.base_dir in sys.path:
                    sys.path.remove(self.base_dir)
                    
        except Exception as e:
            logger.error(f"Error loading template requirements: {e}")
            return {}
    
    def _detect_template_inconsistencies(self, pattern_analysis: dict, current_templates: dict) -> list:
        """Detect inconsistencies between actual usage and template requirements"""
        inconsistencies = []
        
        if not pattern_analysis.get("import_patterns") or not current_templates.get("required_imports"):
            return inconsistencies
        
        actual_patterns = pattern_analysis["import_patterns"]
        required_imports = current_templates["required_imports"]
        
        # Check each file type
        for file_type, actual_imports in actual_patterns.items():
            if file_type not in required_imports:
                inconsistencies.append(f"File type '{file_type}' found in project but not in template requirements")
                continue
            
            template_imports = required_imports[file_type]
            
            # Find commonly used imports not in template
            for import_stmt, count in actual_imports.items():
                # If import is used in >50% of files of this type, it should be in template
                file_count = len(pattern_analysis["file_type_patterns"].get(file_type, []))
                usage_ratio = count / file_count if file_count > 0 else 0
                
                if usage_ratio > 0.5 and not any(template_import in import_stmt or import_stmt in template_import 
                                                for template_import in template_imports):
                    inconsistencies.append(
                        f"Import '{import_stmt}' used in {usage_ratio:.1%} of {file_type} files but not in template"
                    )
            
            # Find template imports not commonly used
            for template_import in template_imports:
                if not any(template_import in actual_import or actual_import in template_import 
                          for actual_import in actual_imports):
                    inconsistencies.append(
                        f"Template import '{template_import}' for {file_type} not found in actual usage"
                    )
        
        return inconsistencies
    
    def _generate_template_recommendations(self, inconsistencies: list) -> list:
        """Generate recommendations based on inconsistencies"""
        recommendations = []
        
        for inconsistency in inconsistencies:
            if "used in" in inconsistency and "but not in template" in inconsistency:
                recommendations.append(f"ADD TO TEMPLATE: {inconsistency}")
            elif "not found in actual usage" in inconsistency:
                recommendations.append(f"CONSIDER REMOVING: {inconsistency}")
            else:
                recommendations.append(f"REVIEW: {inconsistency}")
        
        # Add general recommendations
        if inconsistencies:
            recommendations.append("UPDATE ai_workflow_integration.py REQUIRED_IMPORTS")
            recommendations.append("UPDATE template files in /templates/ directory")
            recommendations.append("REGENERATE guidelines documentation if major changes")
        
        return recommendations


if __name__ == "__main__":
    # Run all scheduled tasks
    task_manager = ScheduledTaskManager()
    task_manager.check_all_scheduled_tasks()
