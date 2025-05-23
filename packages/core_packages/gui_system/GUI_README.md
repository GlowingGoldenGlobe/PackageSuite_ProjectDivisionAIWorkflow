# GlowingGoldenGlobe GUI Selection Guide

## Available GUI Versions

This project includes multiple GUI versions with different features. Choose the one that best fits your needs:

### 1. GUI with Claude Parallel Integration (Recommended)
**File:** `gui/gui_main.py`

This updated version includes Claude Parallel integration and essential features:
- Complete model version management
- Message field with sending capability
- Related files list with file opening
- Subtitle display
- Hardware monitoring
- Task management
- Claude Parallel integration
- Help system

**To launch:**
```
Launch_GUI_with_Parallel.bat
```
Or use the desktop shortcut created by `Create_GUI_Shortcut.ps1`

### 2. Improved GUI
**File:** `improved_agent_mode_gui.py`

This version includes many enhancements:
- Agent Mode and PyAutoGen selection
- Process status display with runtime
- Start/stop controls
- Minutes in time limit
- Model status display
- Related model parts
- Fixed task completion

**To launch:**
```powershell
python improved_agent_mode_gui.py
```
Or use the desktop shortcut created by `Create-ImprovedGUIShortcut.ps1`

### 3. Fixed GUI
**File:** `fixed_agent_mode_gui.py`

This version addresses the geometry manager conflicts:
- Consistent use of grid layout manager
- Basic process controls
- Time limit improvements

**To launch:**
```powershell
python fixed_agent_mode_gui.py
```

### 4. Standard GUI
**File:** `agent_mode_gui.py`

The original version with basic functionality.

**To launch:**
```powershell
python agent_mode_gui.py
```

### 5. Smart Launcher
**File:** `run_ggg_gui.py`

A smart launcher that automatically selects the best available GUI version.

**To launch:**
```powershell
python run_ggg_gui.py
```

## Integrated GUI Features

The new integrated GUI (`gui/gui_main.py`) combines the best features of previous versions plus Claude Parallel integration:

### Main Controls Tab
- Development mode selection (Refined Model, Versioned Model, Testing Only)
- Time limit settings with hours and minutes
- Auto-continue option
- Auto-save interval configuration
- Model version dropdown with refresh
- Model part selection
- Message & instructions field with send functionality
- Model versions & related files display
- Action buttons for common operations (Start New Session, Resume Session, etc.)

### Hardware Monitor Tab
- System information display
- Real-time CPU, memory, and disk usage monitoring
- Resource usage progress bars
- Manual refresh capability

### Tasks & Schedule Tab
- Task list with status, priority, and creation date
- Task management controls (Add, Complete, Remove)
- Scheduled tasks display
- Task refresh functionality

### Help Tab
- Topic selection for common help areas
- Detailed documentation for each topic
- Information about Claude Parallel Integration

### Claude Parallel Tab (if available)
- Claude Parallel task management
- Task queue configuration
- Execution status monitoring
- Resource allocation settings

## Troubleshooting

If you encounter issues with the GUI:

1. Try using the smart launcher (`run_ggg_gui.py`) which includes error handling
2. Check the `gui/gui_launcher_error.txt` file for error information
3. Make sure all required packages are installed:
   ```powershell
   pip install psutil
   ```
4. If geometry manager conflicts occur, use the Fixed or Improved GUI versions
5. Make sure the required support modules are available in the correct locations

## File Structure

- `gui/gui_main.py`: Integrated GUI implementation with all tabs and features
- `gui/gui_claude_integration.py`: Integration module for Claude Parallel
- `gui/claude_parallel_gui.py`: Implementation of Claude Parallel GUI tab
- `Launch_GUI_with_Parallel.bat`: Batch file to launch the integrated GUI
- `Create_GUI_Shortcut.ps1`: PowerShell script to create a desktop shortcut

## Requirements

- Python 3.8+
- tkinter
- psutil (for hardware monitoring)
- Other support modules as needed

## Reporting Issues

Please report any issues to the development team with:
1. Which GUI version you were using
2. Steps to reproduce the issue
3. Any error messages
4. Screenshots if available