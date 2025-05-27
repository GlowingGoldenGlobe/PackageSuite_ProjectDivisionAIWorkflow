# Nested Git Repository Cleanup System

## Overview

This system automatically detects and handles nested `.git` directories in third-party folders that can cause VSCode to show thousands of untracked files.

## Problem It Solves

When third-party software (like `open3d_direct`) is added to the project with its own `.git` folder:
- VSCode shows "10k+ pending changes" in Source Control
- The main repository correctly ignores these via `.gitignore`
- But VSCode still displays them as a separate repository
- This clutters the interface and causes confusion

## Components

### 1. Nested Git Handler (`/utils/nested_git_handler.py`)

**Purpose**: Core utility for detecting and cleaning nested git repositories

**Features**:
- Automatically finds all `.git` directories in the project
- Identifies which ones are in ignored/third-party directories
- Analyzes each repository (size, remotes, likelihood of being third-party)
- Safely removes `.git` folders that are clearly third-party
- Maintains a log of all actions

**Usage**:
```bash
# Check for nested repositories
python utils/nested_git_handler.py --check-only

# Automatically clean safe repositories
python utils/nested_git_handler.py --auto-clean

# Dry run to see what would be done
python utils/nested_git_handler.py --auto-clean --dry-run
```

### 2. Scheduled Cleanup Task (`/ai_managers/scheduled_git_cleanup_task.py`)

**Purpose**: Integrates with the scheduled tasks system for automatic weekly cleanup

**Features**:
- Runs weekly (168 hours)
- Automatically detects and cleans nested git repos
- Logs all actions to `git_cleanup_log.json`
- Only removes repositories that are:
  - In third-party directories
  - Have no remote connections
  - Are clearly not part of the main project

### 3. Integration with Scheduled Tasks

Added to `parallel_execution_tasks.json`:
```json
"nested_git_cleanup": {
  "enabled": true,
  "interval_hours": 168,
  "description": "Clean nested .git directories from third-party folders",
  "priority": "medium"
}
```

## How It Works

1. **Detection Phase**:
   - Scans project directory for `.git` folders
   - Checks against `.gitignore` patterns
   - Identifies third-party patterns (open3d_direct, vendor, node_modules, etc.)

2. **Analysis Phase**:
   - Calculates repository size
   - Checks for remote connections
   - Determines if it's likely third-party software

3. **Cleanup Phase**:
   - Only removes `.git` folders that are:
     - In ignored directories
     - Match third-party patterns
     - Have no remote repositories configured
   - Logs all actions for audit trail

## Safety Features

- **Never removes the main project's `.git`**
- **Checks for remotes** - Won't remove repos with configured remotes
- **Pattern matching** - Only targets known third-party directories
- **Dry run mode** - Test what would happen before doing it
- **Logging** - All actions are logged for review

## Manual Usage

If you encounter the "10k+ pending changes" issue:

1. Run the check:
   ```bash
   python utils/nested_git_handler.py --check-only
   ```

2. Review what would be cleaned:
   ```bash
   python utils/nested_git_handler.py --auto-clean --dry-run
   ```

3. Execute the cleanup:
   ```bash
   python utils/nested_git_handler.py --auto-clean
   ```

## Automatic Operation

The system runs automatically:
- **Weekly** via the scheduled tasks manager
- **Logs** to `ai_managers/git_cleanup_log.json`
- **Safe** - only removes obvious third-party repos

## Benefits

1. **Clean VSCode Interface** - No more "10k+ pending changes"
2. **Automatic** - Runs weekly without intervention
3. **Safe** - Multiple checks before removing anything
4. **Logged** - Full audit trail of actions
5. **Configurable** - Can adjust patterns and rules as needed
