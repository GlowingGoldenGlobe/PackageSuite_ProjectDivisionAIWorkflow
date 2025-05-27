#!/usr/bin/env python
"""
Nested Git Repository Handler

Automatically detects and handles nested .git directories in third-party folders.
Prevents VSCode from showing thousands of untracked files from dependencies.

Usage:
    python utils/nested_git_handler.py [--check-only] [--auto-clean]
"""

import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class NestedGitHandler:
    """Handles detection and cleanup of nested git repositories"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.gitignore_path = self.project_root / '.gitignore'
        self.log_file = self.project_root / 'utils' / 'nested_git_cleanup.log'
        
        # Directories that commonly have unwanted .git folders
        self.third_party_patterns = [
            'open3d_direct',
            'open3d_build',
            'node_modules',
            'vendor',
            'third_party',
            'external',
            'dependencies',
            'libs',
            'packages'
        ]
        
    def find_nested_git_repos(self) -> List[Path]:
        """Find all .git directories within the project"""
        nested_repos = []
        
        # Read gitignore to identify ignored directories
        ignored_dirs = self._get_ignored_directories()
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip the main .git directory
            if root == str(self.project_root):
                if '.git' in dirs:
                    dirs.remove('.git')
                continue
            
            # Check if current directory has .git
            if '.git' in dirs:
                git_path = Path(root) / '.git'
                relative_path = git_path.relative_to(self.project_root)
                
                # Check if parent directory is in gitignore
                parent_ignored = any(
                    str(relative_path).startswith(ignored) 
                    for ignored in ignored_dirs
                )
                
                # Check if it matches third-party patterns
                is_third_party = any(
                    pattern in str(relative_path) 
                    for pattern in self.third_party_patterns
                )
                
                if parent_ignored or is_third_party:
                    nested_repos.append(git_path)
            
            # Don't descend into .git directories
            if '.git' in dirs:
                dirs.remove('.git')
        
        return nested_repos
    
    def _get_ignored_directories(self) -> List[str]:
        """Parse .gitignore to find ignored directories"""
        ignored = []
        
        if not self.gitignore_path.exists():
            return ignored
        
        with open(self.gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Remove leading slash for comparison
                if line.startswith('/'):
                    line = line[1:]
                
                # Only consider directory patterns
                if line.endswith('/') or '/' not in line:
                    ignored.append(line.rstrip('/'))
        
        return ignored
    
    def analyze_git_directory(self, git_path: Path) -> Dict[str, any]:
        """Analyze a .git directory to provide information"""
        info = {
            'path': str(git_path),
            'size_mb': 0,
            'has_remotes': False,
            'has_local_changes': False,
            'is_likely_third_party': False
        }
        
        # Calculate size
        total_size = 0
        for root, dirs, files in os.walk(git_path):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except:
                    pass
        info['size_mb'] = round(total_size / (1024 * 1024), 2)
        
        # Check for remotes
        config_file = git_path / 'config'
        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()
                info['has_remotes'] = '[remote' in content
        
        # Check if it's likely third-party
        parent_dir = git_path.parent.name
        info['is_likely_third_party'] = any(
            pattern in parent_dir.lower() 
            for pattern in self.third_party_patterns
        )
        
        return info
    
    def remove_git_directory(self, git_path: Path, dry_run: bool = False) -> bool:
        """Remove a .git directory"""
        if dry_run:
            print(f"[DRY RUN] Would remove: {git_path}")
            return True
        
        try:
            shutil.rmtree(git_path)
            self._log_action(f"Removed nested .git: {git_path}")
            return True
        except Exception as e:
            self._log_action(f"Failed to remove {git_path}: {e}", level='ERROR')
            return False
    
    def _log_action(self, message: str, level: str = 'INFO'):
        """Log an action to the log file"""
        self.log_file.parent.mkdir(exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def create_report(self, nested_repos: List[Tuple[Path, Dict]]) -> str:
        """Create a report of found nested repositories"""
        report = ["\nNested Git Repository Report"]
        report.append("=" * 50)
        report.append(f"Found {len(nested_repos)} nested .git directories:\n")
        
        total_size = 0
        for git_path, info in nested_repos:
            report.append(f"Path: {git_path.relative_to(self.project_root)}")
            report.append(f"  Size: {info['size_mb']} MB")
            report.append(f"  Has remotes: {info['has_remotes']}")
            report.append(f"  Likely third-party: {info['is_likely_third_party']}")
            report.append("")
            total_size += info['size_mb']
        
        report.append(f"Total size: {total_size:.2f} MB")
        report.append("\nRecommendations:")
        
        for git_path, info in nested_repos:
            if info['is_likely_third_party'] and not info['has_local_changes']:
                report.append(f"- Safe to remove: {git_path.relative_to(self.project_root)}")
        
        return "\n".join(report)
    
    def auto_clean(self, dry_run: bool = False) -> int:
        """Automatically clean safe-to-remove nested git repos"""
        cleaned = 0
        nested_repos = self.find_nested_git_repos()
        
        for git_path in nested_repos:
            info = self.analyze_git_directory(git_path)
            
            # Only auto-remove if it's clearly third-party and has no local changes
            if info['is_likely_third_party'] and not info['has_remotes']:
                if self.remove_git_directory(git_path, dry_run):
                    cleaned += 1
                    print(f"Cleaned: {git_path.relative_to(self.project_root)}")
        
        return cleaned


def main():
    parser = argparse.ArgumentParser(
        description='Handle nested git repositories in third-party directories'
    )
    parser.add_argument(
        '--check-only', action='store_true',
        help='Only check for nested repos, do not remove'
    )
    parser.add_argument(
        '--auto-clean', action='store_true',
        help='Automatically remove safe third-party .git directories'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    args = parser.parse_args()
    
    handler = NestedGitHandler()
    
    # Find nested repositories
    nested_repos = handler.find_nested_git_repos()
    
    if not nested_repos:
        print("No nested git repositories found.")
        return 0
    
    # Analyze each repository
    analyzed = [(repo, handler.analyze_git_directory(repo)) for repo in nested_repos]
    
    # Show report
    print(handler.create_report(analyzed))
    
    if args.check_only:
        return 0
    
    if args.auto_clean:
        cleaned = handler.auto_clean(args.dry_run)
        print(f"\nCleaned {cleaned} nested git repositories.")
    else:
        print("\nTo automatically clean safe repositories, run with --auto-clean")
        print("To see what would be done, add --dry-run")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
