#!/usr/bin/env python
"""
Scheduled Git Cleanup Task

Integrates nested git repository cleanup with the scheduled tasks manager.
Runs weekly to automatically detect and clean third-party .git directories.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.nested_git_handler import NestedGitHandler


class ScheduledGitCleanupTask:
    """Scheduled task for cleaning nested git repositories"""
    
    def __init__(self):
        self.handler = NestedGitHandler()
        self.task_name = "nested_git_cleanup"
        self.description = "Clean nested .git directories from third-party folders"
        self.interval_hours = 168  # Weekly
        self.log_file = Path(__file__).parent / 'git_cleanup_log.json'
        
    def should_run(self, last_run_time: datetime = None) -> bool:
        """Check if the task should run"""
        if not last_run_time:
            return True
        
        hours_since_last_run = (datetime.now() - last_run_time).total_seconds() / 3600
        return hours_since_last_run >= self.interval_hours
    
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """Execute the git cleanup task"""
        result = {
            'task_name': self.task_name,
            'start_time': datetime.now().isoformat(),
            'nested_repos_found': 0,
            'repos_cleaned': 0,
            'total_size_mb': 0,
            'errors': [],
            'details': []
        }
        
        try:
            # Find nested repositories
            nested_repos = self.handler.find_nested_git_repos()
            result['nested_repos_found'] = len(nested_repos)
            
            if not nested_repos:
                result['message'] = "No nested git repositories found"
                return result
            
            # Analyze and clean
            for git_path in nested_repos:
                info = self.handler.analyze_git_directory(git_path)
                result['total_size_mb'] += info['size_mb']
                
                # Determine if safe to clean
                if info['is_likely_third_party'] and not info['has_remotes']:
                    if not dry_run:
                        if self.handler.remove_git_directory(git_path):
                            result['repos_cleaned'] += 1
                            result['details'].append({
                                'action': 'cleaned',
                                'path': str(git_path.relative_to(self.handler.project_root)),
                                'size_mb': info['size_mb']
                            })
                    else:
                        result['details'].append({
                            'action': 'would_clean',
                            'path': str(git_path.relative_to(self.handler.project_root)),
                            'size_mb': info['size_mb']
                        })
                else:
                    result['details'].append({
                        'action': 'skipped',
                        'path': str(git_path.relative_to(self.handler.project_root)),
                        'reason': 'has_remotes' if info['has_remotes'] else 'not_third_party'
                    })
            
            result['end_time'] = datetime.now().isoformat()
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(str(e))
            result['success'] = False
        
        # Log the result
        self._log_result(result)
        
        return result
    
    def _log_result(self, result: Dict[str, Any]):
        """Log the task result"""
        # Load existing log
        log_data = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    log_data = json.load(f)
            except:
                log_data = []
        
        # Add new result
        log_data.append(result)
        
        # Keep only last 10 runs
        if len(log_data) > 10:
            log_data = log_data[-10:]
        
        # Save log
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def get_task_definition(self) -> Dict[str, Any]:
        """Get task definition for scheduled_tasks_manager"""
        return {
            'id': self.task_name,
            'name': self.task_name,
            'description': self.description,
            'interval': self.interval_hours * 3600,  # Convert to seconds
            'module': 'ai_managers.scheduled_git_cleanup_task',
            'function': 'run_cleanup_task',
            'enabled': True,
            'auto_run': True
        }


def run_cleanup_task():
    """Entry point for scheduled task manager"""
    task = ScheduledGitCleanupTask()
    return task.run(dry_run=False)


def get_task_info():
    """Get task information for registration"""
    task = ScheduledGitCleanupTask()
    return task.get_task_definition()


if __name__ == "__main__":
    # Test run in dry-run mode
    task = ScheduledGitCleanupTask()
    result = task.run(dry_run=True)
    
    print("\nGit Cleanup Task Test Run")
    print("=" * 50)
    print(f"Nested repos found: {result['nested_repos_found']}")
    print(f"Would clean: {sum(1 for d in result['details'] if d['action'] == 'would_clean')}")
    print(f"Total size: {result['total_size_mb']:.2f} MB")
    
    if result['details']:
        print("\nDetails:")
        for detail in result['details']:
            print(f"  {detail['action']}: {detail['path']}")
