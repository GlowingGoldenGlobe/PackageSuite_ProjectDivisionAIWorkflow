#!/usr/bin/env python3
"""
Clipboard Workflow Utilities

Service module providing clipboard workflow operations for AI Agent file modifications.
Prevents file mess in working directories by managing temporary files in designated clipboard area.

Functions:
- backup_file_to_clipboard(): Create backup before modification
- create_working_copy(): Create working copy in clipboard for modifications
- safe_replace_file(): Replace original with working copy after verification
- cleanup_clipboard_session(): Remove temporary files after successful operation
- get_clipboard_session_files(): List files in clipboard for recovery

Usage:
    from utils.clipboard_workflow import backup_file_to_clipboard, create_working_copy
    
    # Before modifying any file
    backup_path = backup_file_to_clipboard("/gui/gui_main.py")
    working_path = create_working_copy("/gui/gui_main.py")
    
    # Modify working_path...
    # Test working_path...
    
    # Replace original only when confirmed working
    safe_replace_file(working_path, "/gui/gui_main.py")
"""

import os
import shutil
import datetime
from pathlib import Path
from typing import Optional, Dict, List

# Configuration
CLIPBOARD_DIR = Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv/ai_workflow_clipboard")
OPERATIONS_LOG = CLIPBOARD_DIR / "operations.log"

def ensure_clipboard_exists():
    """Ensure clipboard directory exists"""
    CLIPBOARD_DIR.mkdir(exist_ok=True)

def log_operation(message: str, operation_type: str = "INFO"):
    """Log clipboard operations with timestamp"""
    ensure_clipboard_exists()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{operation_type}] {message}\n"
    
    with open(OPERATIONS_LOG, "a") as f:
        f.write(log_entry)

def backup_file_to_clipboard(file_path: str) -> Path:
    """
    Create backup of file in clipboard before modification
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file in clipboard
    """
    ensure_clipboard_exists()
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    backup_path = CLIPBOARD_DIR / backup_name
    
    shutil.copy2(file_path, backup_path)
    log_operation(f"Backed up {file_path} to {backup_path}", "BACKUP")
    
    return backup_path

def create_working_copy(file_path: str) -> Path:
    """
    Create working copy of file in clipboard for modifications
    
    Args:
        file_path: Path to original file
        
    Returns:
        Path to working copy in clipboard
    """
    ensure_clipboard_exists()
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    working_name = f"{file_path.stem}_WORKING_{timestamp}{file_path.suffix}"
    working_path = CLIPBOARD_DIR / working_name
    
    shutil.copy2(file_path, working_path)
    log_operation(f"Created working copy {working_path} from {file_path}", "WORKING")
    
    return working_path

def safe_replace_file(working_file_path: str, target_file_path: str) -> bool:
    """
    Safely replace original file with working copy
    
    Args:
        working_file_path: Path to working file in clipboard
        target_file_path: Path to original file to replace
        
    Returns:
        True if replacement successful, False otherwise
    """
    working_file_path = Path(working_file_path)
    target_file_path = Path(target_file_path)
    
    if not working_file_path.exists():
        log_operation(f"Working file not found: {working_file_path}", "ERROR")
        return False
    
    if not target_file_path.exists():
        log_operation(f"Target file not found: {target_file_path}", "ERROR")
        return False
    
    try:
        # Create final backup before replacement
        final_backup = backup_file_to_clipboard(str(target_file_path))
        
        # Replace original with working copy
        shutil.copy2(working_file_path, target_file_path)
        log_operation(f"Replaced {target_file_path} with {working_file_path}", "REPLACE")
        
        # Remove working copy
        working_file_path.unlink()
        log_operation(f"Cleaned up working file {working_file_path}", "CLEANUP")
        
        return True
        
    except Exception as e:
        log_operation(f"Error replacing file: {str(e)}", "ERROR")
        return False

def create_session_backup(file_path: str) -> Dict[str, Path]:
    """
    Create comprehensive session backup for high-risk files
    
    Args:
        file_path: Path to file requiring session backup
        
    Returns:
        Dictionary with session information
    """
    ensure_clipboard_exists()
    
    file_path = Path(file_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create session directory
    session_dir = CLIPBOARD_DIR / f"session_{file_path.stem}_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    # Create multiple copies
    original_backup = session_dir / f"{file_path.stem}_original{file_path.suffix}"
    working_copy = session_dir / f"{file_path.stem}_WORKING{file_path.suffix}"
    
    shutil.copy2(file_path, original_backup)
    shutil.copy2(file_path, working_copy)
    
    log_operation(f"Created session backup in {session_dir}", "SESSION")
    
    return {
        "session_dir": session_dir,
        "original_backup": original_backup,
        "working_copy": working_copy,
        "timestamp": timestamp
    }

def cleanup_clipboard_session(session_dir: Optional[str] = None, assessment_based: bool = True):
    """
    Clean up clipboard session files using project-beneficial assessment
    
    Args:
        session_dir: Specific session directory to clean (optional)
        assessment_based: Use intelligent assessment vs simple cleanup
    """
    ensure_clipboard_exists()
    
    if session_dir:
        # Clean specific session
        session_path = Path(session_dir)
        if session_path.exists() and session_path.is_dir():
            shutil.rmtree(session_path)
            log_operation(f"Cleaned up session directory {session_path}", "CLEANUP")
    else:
        # Assessment-based cleanup
        if assessment_based:
            _assessment_based_cleanup()
        else:
            # Fallback: only clean obviously obsolete files
            _safe_cleanup()

def _assessment_based_cleanup():
    """
    Perform intelligent assessment-based cleanup that benefits the project
    """
    log_operation("Starting assessment-based clipboard cleanup", "ASSESSMENT")
    
    for item in CLIPBOARD_DIR.iterdir():
        if item.is_file() and item.name not in ["README.md", "operations.log"]:
            if _assess_file_for_cleanup(item):
                item.unlink()
                log_operation(f"Assessed and removed: {item}", "CLEANUP")
        elif item.is_dir():
            if _assess_session_for_cleanup(item):
                shutil.rmtree(item)
                log_operation(f"Assessed and removed session: {item}", "CLEANUP")

def _assess_file_for_cleanup(file_path: Path) -> bool:
    """
    Assess if file should be cleaned up based on project benefit
    
    Returns:
        True if file should be removed, False if it should be kept
    """
    # Check 1: Is it a duplicate of existing working files?
    if _is_duplicate_of_working_file(file_path):
        log_operation(f"File is duplicate of working file: {file_path}", "ASSESSMENT")
        return True
    
    # Check 2: Is it part of a completed workflow?
    if _is_completed_workflow_file(file_path):
        log_operation(f"File is from completed workflow: {file_path}", "ASSESSMENT")
        return True
    
    # Check 3: Is it corrupted or invalid?
    if _is_corrupted_file(file_path):
        log_operation(f"File is corrupted: {file_path}", "ASSESSMENT")
        return True
    
    # Check 4: Is it a temporary test file with no ongoing utility?
    if _is_obsolete_test_file(file_path):
        log_operation(f"File is obsolete test file: {file_path}", "ASSESSMENT")
        return True
    
    # Default: Keep file if uncertain
    log_operation(f"File retained for project utility: {file_path}", "ASSESSMENT")
    return False

def _assess_session_for_cleanup(session_dir: Path) -> bool:
    """
    Assess if session directory should be cleaned up
    
    Returns:
        True if session should be removed, False if it should be kept
    """
    # Check if session has active working files
    working_files = list(session_dir.glob("*_WORKING*"))
    if working_files:
        # Check if working files are still being used
        for working_file in working_files:
            if _is_active_working_file(working_file):
                log_operation(f"Session has active working files: {session_dir}", "ASSESSMENT")
                return False
    
    # Check if session has recent activity
    if _has_recent_activity(session_dir):
        log_operation(f"Session has recent activity: {session_dir}", "ASSESSMENT")
        return False
    
    # Check if session is part of ongoing workflow
    if _is_ongoing_workflow_session(session_dir):
        log_operation(f"Session is part of ongoing workflow: {session_dir}", "ASSESSMENT")
        return False
    
    # Session can be safely removed
    log_operation(f"Session assessed for removal: {session_dir}", "ASSESSMENT")
    return True

def _is_duplicate_of_working_file(file_path: Path) -> bool:
    """Check if file is duplicate of existing working file"""
    # Extract base filename without backup/working suffixes
    base_name = file_path.name.replace("_backup_", "_").replace("_WORKING_", "_")
    base_name = "_".join(base_name.split("_")[:-1]) + file_path.suffix
    
    # Check if working version exists in project
    potential_paths = [
        Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv") / base_name,
        Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv/gui") / base_name,
        Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv/ai_managers") / base_name
    ]
    
    return any(p.exists() for p in potential_paths)

def _is_completed_workflow_file(file_path: Path) -> bool:
    """Check if file is from completed workflow"""
    # Look for indicators of completed workflow
    if "_backup_" in file_path.name:
        # Check if corresponding working file exists
        working_name = file_path.name.replace("_backup_", "_WORKING_")
        working_path = file_path.parent / working_name
        if not working_path.exists():
            return True  # Backup without working file = completed workflow
    
    return False

def _is_corrupted_file(file_path: Path) -> bool:
    """Check if file is corrupted or invalid"""
    try:
        # Basic file integrity check
        if file_path.stat().st_size == 0:
            return True
        
        # For Python files, check basic syntax
        if file_path.suffix == ".py":
            with open(file_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    return True
                # Very basic syntax check
                if content.count('(') != content.count(')'):
                    return True
        
        return False
    except Exception:
        return True  # If we can't read it, it's corrupted

def _is_obsolete_test_file(file_path: Path) -> bool:
    """Check if file is obsolete test file"""
    # Files with test patterns that are clearly temporary
    test_patterns = ["_test_", "_temp_", "_tmp_", "_debug_"]
    return any(pattern in file_path.name.lower() for pattern in test_patterns)

def _is_active_working_file(file_path: Path) -> bool:
    """Check if working file is still being actively used"""
    # Check modification time - if modified recently, it's active
    mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
    recent_threshold = datetime.datetime.now() - datetime.timedelta(hours=2)
    return mod_time > recent_threshold

def _has_recent_activity(session_dir: Path) -> bool:
    """Check if session directory has recent activity"""
    # Check if any file in session was modified recently
    recent_threshold = datetime.datetime.now() - datetime.timedelta(hours=6)
    
    for item in session_dir.iterdir():
        if item.is_file():
            mod_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            if mod_time > recent_threshold:
                return True
    
    return False

def _is_ongoing_workflow_session(session_dir: Path) -> bool:
    """Check if session is part of ongoing workflow"""
    # Check if session has both original and working files (indicates active workflow)
    has_original = any("_original" in f.name for f in session_dir.iterdir())
    has_working = any("_WORKING" in f.name for f in session_dir.iterdir())
    
    return has_original and has_working

def _safe_cleanup():
    """
    Fallback cleanup that only removes obviously safe files
    """
    log_operation("Performing safe cleanup (non-assessment mode)", "CLEANUP")
    
    # Only remove files that are clearly temporary and safe to delete
    for item in CLIPBOARD_DIR.iterdir():
        if item.is_file() and item.name not in ["README.md", "operations.log"]:
            # Only remove obviously temporary files
            if any(pattern in item.name.lower() for pattern in ["_temp_", "_tmp_", "_debug_"]):
                if item.stat().st_size == 0:  # Empty files only
                    item.unlink()
                    log_operation(f"Safe cleanup removed empty temp file: {item}", "CLEANUP")

def get_clipboard_session_files() -> List[Dict[str, str]]:
    """
    Get list of files in clipboard for recovery purposes
    
    Returns:
        List of file information dictionaries
    """
    ensure_clipboard_exists()
    
    files = []
    for item in CLIPBOARD_DIR.iterdir():
        if item.is_file() and item.name not in ["README.md", "operations.log"]:
            files.append({
                "name": item.name,
                "path": str(item),
                "size": item.stat().st_size,
                "modified": datetime.datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return sorted(files, key=lambda x: x["modified"], reverse=True)

def recover_from_backup(backup_name: str, target_path: str) -> bool:
    """
    Recover original file from clipboard backup
    
    Args:
        backup_name: Name of backup file in clipboard
        target_path: Path where to restore the file
        
    Returns:
        True if recovery successful, False otherwise
    """
    backup_path = CLIPBOARD_DIR / backup_name
    
    if not backup_path.exists():
        log_operation(f"Backup file not found: {backup_path}", "ERROR")
        return False
    
    try:
        shutil.copy2(backup_path, target_path)
        log_operation(f"Recovered {target_path} from {backup_path}", "RECOVERY")
        return True
    except Exception as e:
        log_operation(f"Error recovering file: {str(e)}", "ERROR")
        return False

# Example usage functions for Claude Code integration
def claude_safe_modify_file(file_path: str):
    """
    Claude Code integration: Start safe file modification workflow
    
    Returns:
        Path to working copy for modifications
    """
    # Step 1: Create backup
    backup_path = backup_file_to_clipboard(file_path)
    
    # Step 2: Create working copy
    working_path = create_working_copy(file_path)
    
    log_operation(f"Started safe modification workflow for {file_path}", "WORKFLOW")
    return working_path

def claude_finalize_modification(working_path: str, original_path: str) -> bool:
    """
    Claude Code integration: Finalize file modification workflow
    
    Args:
        working_path: Path to modified working copy
        original_path: Path to original file
        
    Returns:
        True if finalization successful
    """
    success = safe_replace_file(working_path, original_path)
    
    if success:
        log_operation(f"Finalized modification workflow for {original_path}", "WORKFLOW")
        # Clean up old clipboard files
        cleanup_clipboard_session(older_than_hours=1)
    
    return success