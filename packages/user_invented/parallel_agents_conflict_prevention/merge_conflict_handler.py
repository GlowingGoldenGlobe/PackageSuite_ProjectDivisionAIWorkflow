#!/usr/bin/env python3
"""
Merge Conflict Handler - Automated Conflict Resolution for Git Workflows

This script implements an improved Git workflow that:
1. Uses git stash to prevent workflow interruptions when pulling remote changes
2. Automatically resolves merge conflicts when possible
3. Creates backups of conflicted files for safety
4. Includes placeholder functionality for handling same-name-different-file scenarios
5. Can be integrated with the existing webhook receiver

Usage:
    python merge_conflict_handler.py [--pull] [--resolve] [--auto-commit]

Args:
    --pull: Pull changes from remote using stash workflow
    --resolve: Attempt to auto-resolve conflicts after a failed stash pop
    --auto-commit: Automatically commit resolved conflicts
    --process-webhook PATH: Process a webhook payload file
"""

import os
import sys
import json
import argparse
import subprocess
import logging
import difflib
import re
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("merge_conflict_handler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import the Git Task Manager for better integration with AI workflow
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from git_task_manager import register_git_task, process_git_error, check_credentials
    TASK_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("Git Task Manager not available. Git operations won't be integrated with AI workflow.")
    TASK_MANAGER_AVAILABLE = False

# Default remote and branch
DEFAULT_REMOTE = "origin"
DEFAULT_BRANCH = "main"

def run_command(command, cwd=None):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {result.stderr}")
            return None, result.stderr
        return result.stdout.strip(), None
    except Exception as e:
        logger.error(f"Error running command '{command}': {str(e)}")
        return None, str(e)

def get_repo_root():
    """Get the root directory of the Git repository"""
    root, error = run_command("git rev-parse --show-toplevel")
    return root

def git_stash_pull_workflow(remote=DEFAULT_REMOTE, branch=DEFAULT_BRANCH):
    """
    Execute the stash-pull-pop workflow to prevent interruptions.
    Returns True if successful, False otherwise.
    """
    logger.info("Starting stash-pull-pop workflow")
    
    # Check for Git credentials if task manager is available
    if TASK_MANAGER_AVAILABLE:
        credentials = check_credentials()
        if not credentials:
            logger.warning("Git credentials not available. Operations may fail.")
    
    # Check if there are local changes to stash
    status_output, status_error = run_command("git status --porcelain")
    if status_error:
        # Handle Git status error
        if TASK_MANAGER_AVAILABLE:
            process_git_error(status_error, "git status --porcelain")
        return False
        
    if not status_output:
        logger.info("No local changes to stash")
        # Just do a regular pull
        pull_output, pull_error = run_command(f"git pull {remote} {branch}")
        if pull_error:
            logger.error(f"Pull failed: {pull_error}")
            if TASK_MANAGER_AVAILABLE:
                process_git_error(pull_error, f"git pull {remote} {branch}")
            return False
        logger.info("Pull completed successfully")
        return True
    
    # Save current state with descriptive message
    stash_name = f"merge_conflict_handler_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    stash_output, stash_error = run_command(f'git stash save "{stash_name}"')
    
    if stash_error:
        logger.error(f"Stash failed: {stash_error}")
        if TASK_MANAGER_AVAILABLE:
            process_git_error(stash_error, f'git stash save "{stash_name}"')
        return False
    
    logger.info(f"Local changes stashed: {stash_output}")
    
    # Pull latest changes
    pull_output, pull_error = run_command(f"git pull {remote} {branch}")
    if pull_error:
        logger.error(f"Pull failed: {pull_error}")
        # Try to recover by applying stash
        run_command("git stash pop")
        if TASK_MANAGER_AVAILABLE:
            process_git_error(pull_error, f"git pull {remote} {branch}")
        return False
    
    logger.info("Pull completed successfully")
    
    # Apply stashed changes
    pop_output, pop_error = run_command("git stash pop")
    
    # Check for conflicts
    if "CONFLICT" in (pop_output or "") or "Merge conflict" in (pop_output or "") or pop_error:
        logger.warning("Conflicts detected when applying stashed changes")
        
        # Get list of conflicted files
        conflict_files, _ = run_command("git diff --name-only --diff-filter=U")
        if conflict_files:
            conflicts = conflict_files.split('\n')
            logger.warning(f"Conflicts in files: {', '.join(conflicts)}")
            backup_conflict_files(conflicts)
              # Register this as a task for auto-resolution and notify
            task_id = register_task_with_notification(
                task_type="merge_conflict",
                description=f"Git merge conflict in {len(conflicts)} files",
                details={
                    "conflict_files": conflicts,
                    "command": "git stash pop",
                    "stash_name": stash_name,
                    "detection_time": datetime.now().isoformat()
                },
                priority="high",
                auto_solve=True
            )
            if task_id:
                logger.info(f"Registered merge conflict task: {task_id}")
            
            return False
    else:
        logger.info("Stashed changes applied successfully")
        return True

def backup_conflict_files(file_paths):
    """Create backup copies of conflicted files"""
    logger.info("Creating backups of conflicted files")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    for file_path in file_paths:
        if not file_path.strip() or not os.path.exists(file_path):
            continue
            
        try:
            backup_path = f"{file_path}.conflict_{timestamp}.bak"
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as src:
                content = src.read()
                
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
                
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {str(e)}")

def get_conflict_markers(file_path):
    """Extract conflict markers from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Find all conflict blocks
        pattern = r'<<<<<<<.*?\n(.*?)=======\n(.*?)>>>>>>>.*?\n'
        conflicts = re.findall(pattern, content, re.DOTALL)
        
        return conflicts
    except Exception as e:
        logger.error(f"Error extracting conflict markers from {file_path}: {str(e)}")
        return []

def auto_resolve_conflicts(file_paths, favor_local=True):
    """
    Attempt to automatically resolve conflicts in the given files with AI task
    management integration
    
    Args:
        file_paths: List of conflicted file paths
        favor_local: If True, prefer local changes when conflicts can't be intelligently resolved
    
    Returns:
        List of successfully resolved file paths
    """
    resolved_files = []
    unresolved_files = []
    tasks_registered = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            continue
            
        logger.info(f"Attempting to resolve conflicts in {file_path}")
        conflicts = get_conflict_markers(file_path)
        
        if not conflicts:
            logger.warning(f"No conflict markers found in {file_path}")
            continue
        
        # Check if this is a special file that might need different handling
        file_ext = os.path.splitext(file_path)[1].lower()
        is_binary_file = file_ext in ('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.docx', '.xlsx')
        
        # For binary files, we can't do text-based merging
        if is_binary_file:
            logger.warning(f"Binary file detected: {file_path}, cannot auto-resolve")
            unresolved_files.append((file_path, "binary_file"))
            continue
            
        # For certain critical files, we might want to be more cautious
        is_critical_file = any(name in file_path for name in ['config', 'settings', 'credentials', 'password', 'key'])
        if is_critical_file:
            logger.warning(f"Critical file detected: {file_path}, using extra caution")
            
        # Check if files with identical names are actually different files
        backup_path = f"{file_path}.conflict_bak"
        if os.path.exists(backup_path) and is_different_file(file_path, backup_path):
            logger.warning(f"Detected different files with the same name: {file_path}")
              # Register a high-priority task for manual review and notify
            task_id = register_task_with_notification(
                task_type="different_files_conflict",
                description=f"Different files with same name: {os.path.basename(file_path)}",
                details={
                    "file_path": file_path,
                    "backup_path": backup_path,
                    "similarity": "very low"
                },
                priority="critical",
                auto_solve=False  # This requires manual intervention
            )
            if task_id:
                tasks_registered.append(task_id)
            
            unresolved_files.append((file_path, "different_files"))
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Track if we made any changes
            original_content = content
            resolution_strategy_used = {}
                
            # Process each conflict
            for local_block, remote_block in conflicts:
                resolved_block = resolve_conflict_block(local_block, remote_block, favor_local)
                
                # Track which strategy was used for this block
                similarity = difflib.SequenceMatcher(None, local_block, remote_block).ratio()
                if local_block.strip() == remote_block.strip():
                    resolution_strategy_used[f"{local_block[:30]}..."] = "identical"
                elif similarity > 0.8:
                    resolution_strategy_used[f"{local_block[:30]}..."] = f"high_similarity_{similarity:.2f}"
                else:
                    resolution_strategy_used[f"{local_block[:30]}..."] = f"preference_based_{similarity:.2f}"
                
                # Replace conflict with resolved content
                conflict_pattern = r'<<<<<<<.*?\n' + re.escape(local_block) + r'=======\n' + re.escape(remote_block) + r'>>>>>>>.*?\n'
                content = re.sub(conflict_pattern, resolved_block, content, flags=re.DOTALL)
            
            # Write resolved content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Verify that conflicts were resolved
            still_has_conflicts = "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content
            if still_has_conflicts:
                logger.warning(f"Failed to resolve all conflicts in {file_path}")
                unresolved_files.append((file_path, "resolution_failed"))
                
                # Check if we made partial progress
                if content != original_content:
                    logger.info(f"Made partial progress resolving {file_path}")
                      task_id = register_task_with_notification(
                        task_type="partial_merge_conflict",
                        description=f"Partially resolved conflicts in {os.path.basename(file_path)}",
                        details={
                            "file_path": file_path,
                            "strategies": resolution_strategy_used,
                            "progress": "partial"
                        },
                        priority="high",
                        auto_solve=False  # Manual attention needed for remaining conflicts
                    )
                    if task_id:
                        tasks_registered.append(task_id)
            else:
                logger.info(f"Successfully resolved conflicts in {file_path}")
                resolved_files.append(file_path)
                
                # Mark file as resolved in git
                run_command(f"git add {file_path}")
                  # For critical files, register a low-priority task for review
                if is_critical_file:
                    task_id = register_task_with_notification(
                        task_type="critical_file_resolved",
                        description=f"Automatically resolved conflicts in critical file: {os.path.basename(file_path)}",
                        details={
                            "file_path": file_path,
                            "strategies": resolution_strategy_used,
                            "critical_reason": "Contains sensitive configuration or credentials"
                        },
                        priority="medium",
                        auto_solve=False  # Should be manually reviewed
                    )
                    if task_id:
                        tasks_registered.append(task_id)
                
        except Exception as e:
            logger.error(f"Error resolving conflicts in {file_path}: {str(e)}")
            unresolved_files.append((file_path, f"error: {str(e)}"))
      # Register remaining unresolved conflicts
    if unresolved_files:
        for file_path, reason in unresolved_files:
            task_id = register_task_with_notification(
                task_type="unresolved_conflict",
                description=f"Could not auto-resolve conflicts in {os.path.basename(file_path)}",
                details={
                    "file_path": file_path,
                    "reason": reason,
                    "requires_attention": "immediate"
                },
                priority="high",
                auto_solve=False  # Manual resolution needed
            )
            if task_id:
                tasks_registered.append(task_id)
    
    # Log summary
    if resolved_files:
        logger.info(f"Auto-resolved conflicts in {len(resolved_files)} files")
    if unresolved_files:
        logger.warning(f"Could not resolve conflicts in {len(unresolved_files)} files")
    if tasks_registered:
        logger.info(f"Registered {len(tasks_registered)} tasks for AI workflow")
    
    return resolved_files

def resolve_conflict_block(local_block, remote_block, favor_local=True):
    """
    Intelligently resolve a single conflict block using sophisticated strategies
    
    This function uses multiple strategies to produce the best possible merge:
    1. Identical content detection
    2. Line-based merging for non-overlapping changes
    3. Syntax-aware merging for code blocks
    4. Configuration file merging
    5. Fallback to similarity and preference
    """
    # If blocks are identical, use either one
    if local_block.strip() == remote_block.strip():
        logger.debug("Identical blocks - using either version")
        return local_block
    
    # Calculate similarity for later use
    similarity = difflib.SequenceMatcher(None, local_block, remote_block).ratio()
    
    # 1. Try line-based merging for non-overlapping changes
    try:
        local_lines = local_block.splitlines()
        remote_lines = remote_block.splitlines()
        
        # If one side just added lines without modifying existing ones,
        # we can potentially merge them cleanly
        
        # Find common lines
        matcher = difflib.SequenceMatcher(None, local_lines, remote_lines)
        merged_lines = []
        
        # Check if we have a clean merge case (one side only adds lines)
        is_clean_merge = True
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Both sides modified the same lines, not a clean merge
                is_clean_merge = False
                break
        
        if is_clean_merge:
            # We can merge the blocks by combining all non-common lines
            seen_lines = set()
            
            # Add all lines, avoiding duplicates
            for line in local_lines + remote_lines:
                if line not in seen_lines:
                    merged_lines.append(line)
                    seen_lines.add(line)
            
            logger.debug("Non-overlapping changes - performing clean merge")
            return '\n'.join(merged_lines)
    
    except Exception as e:
        logger.debug(f"Error in line-based merging: {str(e)}")
    
    # 2. For code files, try syntax-aware merging
    if 'def ' in local_block or 'class ' in local_block or 'function ' in local_block:
        try:
            # Identify function/method definitions
            def_pattern = r'(def|class|function)\s+([a-zA-Z0-9_]+)'
            
            local_defs = dict(re.findall(def_pattern, local_block))
            remote_defs = dict(re.findall(def_pattern, remote_block))
            
            # If different functions were edited, keep both versions
            if set(local_defs.keys()) != set(remote_defs.keys()):
                # Extract function blocks and merge them
                merged_block = local_block
                
                for func_name, func_type in remote_defs.items():
                    if func_name not in local_defs:
                        # Find the entire function definition in remote
                        func_pattern = rf'{func_type}\s+{func_name}[^\n]*:(.*?)(?=(?:def|class|function)\s+\w+|\Z)'
                        func_match = re.search(func_pattern, remote_block, re.DOTALL)
                        
                        if func_match:
                            func_body = func_match.group(0)
                            merged_block += '\n\n' + func_body
                
                logger.debug("Syntax-aware merging - combined different functions")
                return merged_block
        
        except Exception as e:
            logger.debug(f"Error in syntax-aware merging: {str(e)}")
    
    # 3. Configuration file handling (JSON, YAML, etc.)
    if ('{' in local_block and '}' in local_block) or (':' in local_block and '\n' in local_block):
        try:
            # Try to detect if this is JSON content
            if '{' in local_block and '}' in local_block:
                # Extract JSON objects from both blocks
                json_pattern = r'{.*}'
                local_json_matches = re.findall(json_pattern, local_block, re.DOTALL)
                remote_json_matches = re.findall(json_pattern, remote_block, re.DOTALL)
                
                if local_json_matches and remote_json_matches:
                    try:
                        local_data = json.loads(local_json_matches[0])
                        remote_data = json.loads(remote_json_matches[0])
                        
                        # Deep merge the JSON objects
                        merged_data = {**local_data, **remote_data}
                        merged_json = json.dumps(merged_data, indent=2)
                        
                        # Replace the JSON part while keeping surrounding text
                        result = local_block.replace(local_json_matches[0], merged_json)
                        logger.debug("Configuration merging - merged JSON objects")
                        return result
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.debug(f"Error in configuration merging: {str(e)}")
    
    # 4. Fallback to similarity and preference
    if similarity > 0.8:
        logger.debug(f"High similarity ({similarity:.2f}) - using local version")
        return local_block
    
    # Default resolution based on preference
    logger.debug(f"Low similarity ({similarity:.2f}) - using {'local' if favor_local else 'remote'} version")
    return local_block if favor_local else remote_block

def is_different_file(file_path_a, file_path_b):
    """
    Advanced function to determine if two files with the same name are
    actually different files rather than different versions of the same file.
    
    Uses multiple heuristics to make the determination:
    1. Content similarity comparison
    2. Function/class signature analysis for code files
    3. File header/metadata analysis
    4. Creation history comparison
    
    Also sends enhanced notifications about detected differences
    """
    try:
        # Collect analysis details for notifications
        analysis_details = {}
        
        # 1. Basic content similarity check
        with open(file_path_a, 'r', encoding='utf-8', errors='ignore') as f_a:
            content_a = f_a.read()
            
        with open(file_path_b, 'r', encoding='utf-8', errors='ignore') as f_b:
            content_b = f_b.read()
            
        # Calculate overall similarity
        overall_similarity = difflib.SequenceMatcher(None, content_a, content_b).ratio()
        analysis_details["overall_similarity"] = overall_similarity
        
        # 2. Check file size - dramatically different sizes suggest different files
        size_ratio = len(content_a) / max(len(content_b), 1)  # Avoid division by zero
        analysis_details["size_ratio"] = size_ratio
        
        if size_ratio < 0.5 or size_ratio > 2.0:
            logger.info(f"File size difference suggests different files ({size_ratio:.2f}x)")
            analysis_details["content_difference"] = "Significant size difference"
            is_different = True
        else:
            is_different = False
            
        # 3. For code files, check function/class signatures
        function_overlap_pct = 100.0  # Default to 100% if not a code file
        
        if file_path_a.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h')):
            # Extract function and class definitions using regex
            def_pattern = r'(def|class|function|interface|struct)\s+([a-zA-Z0-9_]+)'
            
            defs_a = set(re.findall(def_pattern, content_a))
            defs_b = set(re.findall(def_pattern, content_b))
            
            # Calculate function/class overlap percentage
            if len(defs_a) > 0 and len(defs_b) > 0:
                intersection = set(d[1] for d in defs_a) & set(d[1] for d in defs_b)
                union = set(d[1] for d in defs_a) | set(d[1] for d in defs_b)
                
                function_overlap_pct = 100 * len(intersection) / max(len(union), 1)
                analysis_details["function_overlap"] = function_overlap_pct
                analysis_details["functions_a"] = len(defs_a)
                analysis_details["functions_b"] = len(defs_b)
                
                if function_overlap_pct < 30:
                    logger.info(f"Function/class signature difference suggests different files")
                    analysis_details["content_difference"] = "Different code signatures"
                    is_different = True
        
        # 4. Check file creation history
        different_origins = False
        try:
            # Get first commit for each file
            cmd_a = f'git log --format="%H" --follow --reverse {file_path_a} | head -1'
            cmd_b = f'git log --format="%H" --follow --reverse {file_path_b} | head -1'
            
            first_commit_a, _ = run_command(cmd_a)
            first_commit_b, _ = run_command(cmd_b)
            
            if first_commit_a and first_commit_b and first_commit_a != first_commit_b:
                logger.info("Different origin commits suggest different files")
                analysis_details["origin_commits"] = f"{first_commit_a[:7]} vs {first_commit_b[:7]}"
                different_origins = True
                is_different = True
        except Exception as e:
            logger.debug(f"Error checking file history: {str(e)}")
            
        # Make final decision based on overall similarity if not already determined
        if not is_different:
            is_different = overall_similarity < 0.3
            if is_different:
                logger.info(f"Content similarity ({overall_similarity:.2f}) suggests different files")
                analysis_details["content_difference"] = "Low overall similarity"
        
        # Send enhanced notification if files appear to be different
        if is_different:
            try:
                from notification_module import notify_different_file_detection_enhanced
                notify_different_file_detection_enhanced(
                    file_path_a, 
                    file_path_b,
                    overall_similarity,
                    analysis_details
                )
            except ImportError:
                # Fall back to basic notification or logging
                logger.warning("notification_module not available for enhanced notifications")
                from notification_module import notify_same_name_different_files
                notify_same_name_different_files(file_path_a, overall_similarity)
            except Exception as e:
                logger.error(f"Error sending notification: {str(e)}")
        
        return is_different
        
    except Exception as e:
        logger.error(f"Error comparing files: {str(e)}")
        return False

def notify_other_users(message, file_paths=None, notification_type=None, details=None):
    """
    Send notifications to other users about Git operations and conflict resolutions
    using the notification_module.
    
    Args:
        message: The message to send
        file_paths: Optional list of affected files
        notification_type: Type of notification for routing (e.g., "conflict", "rename")
        details: Additional structured details about the notification
        
    Returns:
        bool: True if notification was successfully sent
    """
    logger.info(f"NOTIFICATION: {message}")
    if file_paths:
        logger.info(f"Affected files: {', '.join(file_paths)}")
    
    try:
        # Try to import notification module
        from notification_module import send_notification, notify_merge_conflict_resolved
        
        if notification_type == "merge_conflicts_resolved" and file_paths:
            # Safe handling of details
            stats = {}
            commit_id = None
            if details is not None:
                if "stats" in details:
                    stats = details["stats"]
                if "commit_id" in details:
                    commit_id = details["commit_id"]
            return notify_merge_conflict_resolved(file_paths, stats, commit_id)
        else:
            # Safe construction of metadata dictionary
            metadata = {}
            if file_paths:
                metadata["files"] = file_paths
            if details is not None:
                for key, value in details.items():
                    metadata[key] = value
            return send_notification(message, notification_type or "git_operation", metadata)
    except ImportError:
        logger.warning("notification_module not available. Using local logging only.")
        return True
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

def process_webhook_payload(payload_file):
    """Process a webhook payload file"""
    logger.info(f"Processing webhook payload from {payload_file}")
    
    try:
        with open(payload_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        logger.error(f"Error reading webhook payload: {str(e)}")
        return False
        
    # Extract changed files from payload
    changed_files = []
    
    # Process all commits in the payload
    for commit in payload.get('commits', []):
        changed_files.extend(commit.get('added', []))
        changed_files.extend(commit.get('modified', []))
        changed_files.extend(commit.get('removed', []))
        
    # Remove duplicates
    changed_files = list(set(changed_files))
    
    if changed_files:
        logger.info(f"Detected {len(changed_files)} changed files in webhook payload")
        # Execute stash-pull workflow
        return git_stash_pull_workflow()
    else:
        logger.info("No changed files detected in webhook payload")
        return True

def collect_resolution_stats(file_paths):
    """
    Collect statistics about how conflicts were resolved in each file
    for reporting purposes
    
    Args:
        file_paths: List of files where conflicts were resolved
        
    Returns:
        dict: Statistics about resolution methods used
    """
    stats = {
        "identical_content": 0,
        "line_based_merge": 0,
        "syntax_aware_merge": 0, 
        "json_merge": 0,
        "high_similarity": 0,
        "preference_based": 0,
        "critical_files": 0,
        "python_files": 0,
        "config_files": 0
    }
    
    for file_path in file_paths:
        # Count by file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.py':
            stats["python_files"] += 1
        elif file_ext in ['.json', '.yml', '.yaml', '.xml', '.ini', '.conf']:
            stats["config_files"] += 1
            
        # Count critical files
        is_critical = any(name in file_path for name in ['config', 'settings', 'credentials', 'password', 'key'])
        if is_critical:
            stats["critical_files"] += 1
        
        # We don't have exact stats on resolution methods without modifying the core functions,
        # but we can make a reasonable guess based on file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
                if 'def ' in content and 'class ' in content:
                    stats["syntax_aware_merge"] += 1
                elif '{' in content and '}' in content and ('"' in content or "'" in content):
                    stats["json_merge"] += 1
                else:
                    stats["line_based_merge"] += 1
        except Exception:
            pass
            
    return stats

def main():
    parser = argparse.ArgumentParser(description='Merge Conflict Handler for Git workflows')
    parser.add_argument('--pull', action='store_true', help='Pull changes using stash workflow')
    parser.add_argument('--resolve', action='store_true', help='Attempt to auto-resolve conflicts')
    parser.add_argument('--auto-commit', action='store_true', help='Auto-commit resolved conflicts')
    parser.add_argument('--remote', default=DEFAULT_REMOTE, help='Remote name (default: origin)')
    parser.add_argument('--branch', default=DEFAULT_BRANCH, help='Branch name (default: main)')
    parser.add_argument('--process-webhook', metavar='FILE', help='Process a webhook payload file')
    parser.add_argument('--push', action='store_true', help='Push changes after successful operations')
    parser.add_argument('--favor-remote', action='store_true', help='Favor remote changes when resolving conflicts')
    parser.add_argument('--skip-credentials-check', action='store_true', help='Skip Git credentials check')
    parser.add_argument('--notify', action='store_true', help='Send notifications about resolved conflicts')
    
    args = parser.parse_args()
    
    # Get the repository root directory
    repo_root = get_repo_root()
    if not repo_root:
        logger.error("Not in a Git repository")
        return 1
    
    # Check Git credentials unless explicitly skipped
    if not args.skip_credentials_check and TASK_MANAGER_AVAILABLE:
        credentials = check_credentials()
        if not credentials:
            logger.warning("Git credentials not available. Some operations may fail.")
    
    if args.process_webhook:
        logger.info("Processing webhook payload")
        success = process_webhook_payload(args.process_webhook)
        return 0 if success else 1
    
    # Track overall success for return code    
    overall_success = True
    resolved_files = []
    unresolved_files = []
    commit_error = None
    push_error = None
        
    if args.pull:
        logger.info(f"Pulling changes from {args.remote}/{args.branch}")
        pull_success = git_stash_pull_workflow(args.remote, args.branch)
        overall_success = overall_success and pull_success
        
        # If conflicts occurred and --resolve was specified, attempt to resolve them
        if not pull_success and args.resolve:
            logger.info("Pull resulted in conflicts, attempting auto-resolution")
            conflict_files, _ = run_command("git diff --name-only --diff-filter=U")
            if conflict_files:
                conflicts = [f for f in conflict_files.split('\n') if f.strip()]
                logger.info(f"Detected {len(conflicts)} files with conflicts")
                
                # Determine favor_local based on args
                favor_local = not args.favor_remote
                resolved = auto_resolve_conflicts(conflicts, favor_local=favor_local)
                resolved_files.extend(resolved)
                
                # Track unresolved files and their reasons
                unresolved = set(conflicts) - set(resolved_files)
                if unresolved:
                    for file in unresolved:
                        unresolved_files.append((file, "Conflict resolution failed"))
                
                # Update success status if we resolved all conflicts
                if len(resolved) == len(conflicts) and conflicts:
                    logger.info("Successfully resolved all conflicts")
                    overall_success = True
        
    elif args.resolve:
        logger.info("Resolving existing conflicts")
        conflict_files, _ = run_command("git diff --name-only --diff-filter=U")
        if conflict_files:
            conflicts = [f for f in conflict_files.split('\n') if f.strip()]
            logger.info(f"Found {len(conflicts)} files with conflicts")
            
            # Determine favor_local based on args
            favor_local = not args.favor_remote
            resolved = auto_resolve_conflicts(conflicts, favor_local=favor_local)
            resolved_files.extend(resolved)
            
            # Track unresolved files and their reasons
            unresolved = set(conflicts) - set(resolved_files)
            if unresolved:
                for file in unresolved:
                    unresolved_files.append((file, "Conflict resolution failed"))
            
            overall_success = len(resolved) > 0
        else:
            logger.info("No conflict files found")
    
    commit_id = None
    
    # Handle auto-commit if specified and we have resolved files
    if args.auto_commit and resolved_files:
        logger.info(f"Auto-committing {len(resolved_files)} resolved files")
        commit_msg = f"Auto-resolved merge conflicts in {len(resolved_files)} files"
        commit_output, commit_error = run_command(f'git commit -m "{commit_msg}"')
        
        if commit_error:
            logger.error(f"Error auto-committing: {commit_error}")
            overall_success = False
        else:
            logger.info("Successfully committed resolved conflicts")
            # Get the commit ID for notifications
            commit_id = get_commit_id()
            
            # Push if requested
            if args.push:
                logger.info(f"Pushing changes to {args.remote}/{args.branch}")
                push_output, push_error = run_command(f"git push {args.remote} {args.branch}")
                
                if push_error:
                    logger.error(f"Error pushing changes: {push_error}")
                    overall_success = False
                      # Register push failure as a task with notification
                    register_task_with_notification(
                        task_type="push_failed",
                        description=f"Failed to push resolved conflicts to {args.remote}/{args.branch}",
                        details={
                            "error": push_error,
                            "resolved_files": resolved_files,
                            "requires_action": "git push retry or credential check"
                        },
                        priority="high",
                        auto_solve=False
                    )
                else:
                    logger.info("Successfully pushed changes")
    
    # Send enhanced notifications if requested
    if args.notify:
        if resolved_files or unresolved_files:
            logger.info("Sending enhanced notifications about conflict resolution results")
            
            # Process unresolved files into format expected by notification system
            unresolved_dict = {}
            for file_path, reason in unresolved_files:
                unresolved_dict[file_path] = reason
            
            # Try to import notification module for special notification types
            try:
                from notification_module import notify_merge_conflict_resolved, notify_unresolved_conflicts
                
                # Send notification about resolved files
                if resolved_files:
                    resolution_stats = collect_resolution_stats(resolved_files)
                    notify_merge_conflict_resolved(resolved_files, resolution_stats, commit_id)
                    
                # Send notification about unresolved files
                if unresolved_files:
                    notify_unresolved_conflicts([u[0] for u in unresolved_files], unresolved_dict)
                    
            except ImportError:
                # Fallback to basic notification if specialized functions aren't available
                send_enhanced_notification(
                    resolved_files=resolved_files,
                    unresolved_files=[u[0] for u in unresolved_files],
                    commit_id=commit_id,
                    auto_committed=args.auto_commit and not commit_error,
                    pushed=args.push and args.auto_commit and not push_error
                )
    
    # If no actions specified, print help
    if not (args.pull or args.resolve or args.process_webhook):
        parser.print_help()
    
    return 0 if overall_success else 1

def get_commit_id():
    """Get the current commit ID"""
    commit_id, _ = run_command("git rev-parse HEAD")
    return commit_id

# Enhanced function to send notifications after conflict resolution
def send_enhanced_notification(resolved_files, unresolved_files=None, commit_id=None, auto_committed=False, pushed=False):
    """
    Send comprehensive notification about conflict resolution results
    
    Args:
        resolved_files: List of files that were successfully resolved
        unresolved_files: List of files that couldn't be resolved
        commit_id: Optional commit ID if changes were committed
        auto_committed: Whether changes were automatically committed
        pushed: Whether changes were pushed
        
    Returns:
        bool: True if notification was sent successfully
    """
    if not resolved_files and not unresolved_files:
        return False
        
    # Collect resolution statistics for reporting
    resolution_stats = collect_resolution_stats(resolved_files)
    
    # Build notification details
    details = {
        "stats": resolution_stats,
        "commit_id": commit_id,
        "auto_committed": auto_committed,
        "pushed": pushed,
        "resolved_count": len(resolved_files),
        "unresolved_count": len(unresolved_files) if unresolved_files else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Send the notification
    return notify_other_users(
        f"Auto-resolved {len(resolved_files)} merge conflicts" + 
        (f" ({len(unresolved_files)} remaining)" if unresolved_files else ""),
        resolved_files,
        "merge_conflicts_resolved",
        details
    )

def register_task_with_notification(task_type, description, details, priority="medium", auto_solve=False):
    """
    Register a task with the Git task manager and send a notification
    
    Args:
        task_type: Type of task to create
        description: Human-readable description
        details: Dict with task details
        priority: Task priority (low, medium, high, critical)
        auto_solve: Whether AI system should attempt to solve automatically
        
    Returns:
        str or None: Task ID if successful, None otherwise
    """
    if not TASK_MANAGER_AVAILABLE:
        logger.warning("Task manager not available - can't register task")
        return None
        
    # Register the task
    task_id = register_git_task(
        task_type=task_type,
        description=description,
        details=details,
        priority=priority,
        auto_solve=auto_solve
    )
    
    if not task_id:
        logger.error("Failed to register task")
        return None
        
    logger.info(f"Registered task {task_id} ({task_type})")
    
    # Send notification about the task
    try:
        from notification_module import notify_ai_workflow_task
        notify_ai_workflow_task(task_id, task_type, description)
    except ImportError:
        logger.warning("notification_module not available - can't send task notification")
    except Exception as e:
        logger.error(f"Error sending task notification: {str(e)}")
        
    return task_id

def create_merge_conflict_report(resolved_files, unresolved_files=None, stats=None, commit_id=None):
    """
    Create a detailed report for merge conflict resolution results
    that can be used for GUI display or notification emails
    
    Args:
        resolved_files: List of files that were successfully resolved
        unresolved_files: List of files that couldn't be resolved (with reasons)
        stats: Resolution statistics
        commit_id: Optional commit ID if changes were committed
        
    Returns:
        dict: Structured report data
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_conflicts": len(resolved_files) + (len(unresolved_files) if unresolved_files else 0),
            "resolved_count": len(resolved_files),
            "unresolved_count": len(unresolved_files) if unresolved_files else 0,
            "success_rate": 0
        },
        "resolved_files": resolved_files,
        "unresolved_files": [f[0] for f in unresolved_files] if unresolved_files else [],
        "failure_reasons": {},
        "stats": stats or {},
        "commit_id": commit_id
    }
    
    # Calculate success rate
    if report["summary"]["total_conflicts"] > 0:
        report["summary"]["success_rate"] = round(
            (report["summary"]["resolved_count"] / report["summary"]["total_conflicts"]) * 100, 1
        )
        
    # Extract failure reasons
    if unresolved_files:
        reasons = {}
        for file_path, reason in unresolved_files:
            if reason not in reasons:
                reasons[reason] = []
            reasons[reason].append(file_path)
        report["failure_reasons"] = reasons
    
    return report

def gui_notify_conflicts(report):
    """
    Display a notification in the GUI about merge conflict resolution
    
    Args:
        report: Merge conflict resolution report from create_merge_conflict_report
        
    Returns:
        bool: True if notification was displayed
    """
    try:
        # Here you would integrate with your GUI notification system
        # For now, we'll just log that we would show a GUI notification
        
        success_rate = report["summary"]["success_rate"]
        resolved = report["summary"]["resolved_count"]
        total = report["summary"]["total_conflicts"]
        
        logger.info(f"GUI NOTIFICATION: Resolved {resolved}/{total} conflicts ({success_rate}%)")
        
        # You could try to import your GUI components here:
        # try:
        #     from ggg_gui_styles import show_notification
        #     show_notification(
        #         title="Merge Conflicts Resolved", 
        #         message=f"Resolved {resolved}/{total} conflicts ({success_rate}%)",
        #         notification_type="success" if success_rate == 100 else "warning",
        #         data=report
        #     )
        # except ImportError:
        #     logger.warning("GUI notification components not available")
        
        return True
    except Exception as e:
        logger.error(f"Error showing GUI notification: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(main())
