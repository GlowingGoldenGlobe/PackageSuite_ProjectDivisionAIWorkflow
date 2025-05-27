# Git Setup File Placement Guide

## File Locations

When installing this package, place files in the following locations:

1. **`.gitignore`**
   - Location: Project root directory
   - Purpose: Defines files/folders to exclude from git tracking

2. **`scheduled_git_cleanup_task.py`**
   - Location: `ai_managers/` folder
   - Purpose: Scheduled task for automatic git cleanup

3. **`nested_git_handler.py`**
   - Location: `utils/` folder  
   - Purpose: Utility for handling nested git repositories

4. **`NESTED_GIT_CLEANUP_SYSTEM.md`**
   - Location: `docs/` folder
   - Purpose: Documentation for the cleanup system

## Required Folder Structure
```
project_root/
├── .gitignore
├── ai_managers/
│   └── scheduled_git_cleanup_task.py
├── utils/
│   └── nested_git_handler.py
└── docs/
    └── NESTED_GIT_CLEANUP_SYSTEM.md
```

## Note
These folders must exist in your project before placing the files. The git cleanup system helps manage nested git repositories that can cause issues in the main project.