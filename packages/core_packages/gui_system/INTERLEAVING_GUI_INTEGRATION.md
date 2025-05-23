# Interleaving GUI Integration Guide

## Overview

The Claude interleaving functionality has been integrated with GUI controls that allow both user and AI workflow control.

## Components Added

### 1. Interleaving Configuration Manager (`/interleaving_config_manager.py`)
- Manages global and per-agent interleaving settings
- Supports locking to prevent unwanted changes
- Tracks task-specific overrides
- Logs session history

### 2. GUI Tab (`/gui/interleaving_config_tab.py`)
- Provides visual controls for all settings
- Shows real-time status for each agent
- Allows locking settings to prevent AI changes
- Displays session history

### 3. AI Manager Integration (`/ai_managers/interleaving_task_manager.py`)
- Automatically evaluates tasks to determine if interleaving is beneficial
- Respects user locks
- Makes recommendations based on task complexity and type

## How to Add the Tab to Your GUI

In your main GUI file where you create the notebook/tabs, add:

```python
# Import the interleaving config tab
from interleaving_config_tab import add_interleaving_config_tab

# After creating your notebook widget
notebook = ttk.Notebook(parent)

# Add other tabs...

# Add the interleaving config tab
interleaving_tab = add_interleaving_config_tab(notebook)
```

## Usage

### For Users:
1. Open the "Interleaving Config" tab in the GUI
2. Toggle global setting to enable/disable for all agents
3. Configure individual agents as needed
4. Use lock checkboxes to prevent AI from changing settings

### For AI Workflow:
The system automatically:
- Evaluates each task to determine if interleaving would help
- Respects locked settings
- Falls back to PyAutoGen when interleaving is disabled
- Logs all decisions for review

## Features

### Session Control (Option 1)
- Global on/off switch affects entire session
- Can be locked by user

### Agent/Task Control (Option 2)
- Per-agent settings
- Task-specific overrides
- AI manager recommendations
- Automatic optimization based on task type

## Benefits

1. **Better Performance**: Complex tasks use interleaving for enhanced reasoning
2. **User Control**: Lock settings to maintain preferences
3. **Automatic Optimization**: AI managers choose the best mode per task
4. **Transparency**: View all decisions in session history

## Technical Details

Settings are stored in `interleaving_config.json` and include:
- Global enable/disable with lock option
- Per-agent settings with individual locks
- Task-specific overrides
- Session event history

The AI workflow can only change unlocked settings when confidence is high (>80%) that interleaving would significantly improve results.