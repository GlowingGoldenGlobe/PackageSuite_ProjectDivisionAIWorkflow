"""
GlowingGoldenGlobe AI Managers Package

This package contains AI Manager modules that function as specialized mini-brains
with specific responsibilities in the GlowingGoldenGlobe project.

AI Managers are defined by their ability to make observations and assessments within
their domain of responsibility, in contrast to implementation files that simply
process information.
"""

# Re-export the original modules for backward compatibility
import sys
import os

# Add parent directory to path to allow relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import original modules directly
from ai_managers.project_ai_manager import ProjectAIManager
from ai_managers.project_resource_manager import ProjectResourceManager
from ai_managers.refined_model_manager import RefinedModelManager
from ai_managers.task_manager import TaskManager
from ai_managers.git_task_manager import register_git_task, process_git_error, check_credentials
from ai_managers.parallel_execution_manager import ParallelExecutionManager

# Make the modules available at their original import paths for backward compatibility
sys.modules['project_ai_manager'] = sys.modules['ai_managers.project_ai_manager']
sys.modules['project_resource_manager'] = sys.modules['ai_managers.project_resource_manager']
sys.modules['refined_model_manager'] = sys.modules['ai_managers.refined_model_manager']
sys.modules['task_manager'] = sys.modules['ai_managers.task_manager']
sys.modules['git_task_manager'] = sys.modules['ai_managers.git_task_manager']
sys.modules['parallel_execution_manager'] = sys.modules['ai_managers.parallel_execution_manager']
