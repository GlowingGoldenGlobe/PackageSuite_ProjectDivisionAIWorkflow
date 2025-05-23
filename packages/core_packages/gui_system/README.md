# GlowingGoldenGlobe GUI System

This directory contains the GUI components for the GlowingGoldenGlobe project, organized according to improved naming conventions and folder structure.

## File Organization

All GUI files now follow a standardized naming convention with the `gui_` prefix and are located in this dedicated `gui` folder:

- `gui_launcher.py`: The main entry point that selects and launches the appropriate GUI version
- `gui_main.py`: The basic GUI implementation (previously agent_mode_gui.py)
- `gui_fixed.py`: Improved GUI with bugfixes (previously fixed_agent_mode_gui.py)
- `gui_enhanced.py`: Extended GUI with additional features (previously agent_mode_gui_enhanced.py)
- `gui_implementation.py`: Helper classes and functions (previously agent_mode_gui_implementation.py)
- `gui_styles.py`: Style definitions for GUI components (previously ggg_gui_styles.py)
- `gui_create_shortcut.ps1`: Script to create desktop shortcuts (previously Create-ParallelAgentModeShortcut.ps1)
- `gui_icons/`: Directory containing icons used by the GUI

## Getting Started

To launch the GUI application:

### Method 1: Using Batch File (Windows)
```batch
# From project root
Launch_GUI.bat
```

### Method 2: Direct Python Launch
```bash
python gui/gui_launcher.py
```

### Method 3: Module Launch
```bash
python -m gui.gui_launcher
```

### Method 4: Create Desktop Shortcut
From the gui folder:
```batch
CREATE_DESKTOP_SHORTCUT.bat
```
Or run directly:
```batch
gui\CREATE_DESKTOP_SHORTCUT.bat
```

## GUI Versions

The system includes multiple GUI versions with different feature sets:

0. **Working Version (`gui_working.py`)**
   - Clean implementation with core functionality
   - Handles missing dependencies gracefully
   - Recommended for most users

1. **Fixed Version (`gui_fixed.py`)**
   - Recommended for most users
   - Includes all critical bugfixes
   - Stable operation for core functionality

2. **Enhanced Version (`gui_enhanced.py`)**
   - Includes additional advanced features
   - Enhanced status display and time limit options
   - Process monitoring improvements

3. **Base Version (`gui_main.py`)**
   - Updated implementation with comprehensive features
   - Includes all tabs: Main Control, Resource Monitor, Task Manager, Help System, Notifications, Auto Refiner
   - Full integration with all project modules

The launcher automatically selects the best available version based on your environment and dependencies.

## Key Features

1. **Development Mode Selection**
   - Refined Model Development
   - Versioned Model Development
   - Testing-Only Mode

2. **Enhanced Status Display**
   - Real-time process status in the status bar
   - Runtime and remaining time displayed during operations

3. **Time Limit Options**
   - Hours and minutes configuration
   - Input validation

4. **Model Version Management**
   - Related model parts identification
   - Other version discovery
   - Status tracking with timestamps

5. **Desktop Integration**
   - Desktop shortcut creation
   - Icons and application metadata

6. **Status Bar Updates**
   - Process timer showing elapsed time and remaining time
   - Dynamic status updates during operations
   - Color-coded status messages (green for success, red for errors, blue for information)

7. **Agent Mode vs PyAutoGen Selection**
   - Added ability to select between Agent Mode and PyAutoGen for parallel execution
   - Includes API key input field for PyAutoGen mode

8. **Resource Monitoring**
   - Real-time CPU, memory, and disk usage tracking
   - Historical usage charts
   - Alert thresholds

9. **Task Management**
   - Create, edit, and track development tasks
   - Priority levels and status tracking
   - Task completion notifications

10. **Help System**
    - Built-in documentation
    - Troubleshooting guides
    - Context-sensitive help

11. **Notifications**
    - System alerts
    - Model completion notifications
    - Error notifications

12. **Auto Refiner**
    - Automated model quality improvement
    - Configurable quality thresholds
    - Progress tracking

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- Pillow (for enhanced graphics)
- psutil (for resource monitoring)
- Other project dependencies (see root requirements.txt)

## Configuration

The GUI stores its configuration in `agent_mode_config.json`:

```json
{
    "time_limit_hours": "4",
    "time_limit_minutes": "0",
    "todo_file": "To Do_Daily.txt",
    "last_session": "2025-05-17T10:00:00"
}
```

## Troubleshooting

Common issues and solutions:

1. **GUI Not Launching**
   - Ensure the correct Python environment is activated
   - Check for error messages in `gui/gui_launcher_error.log`
   - Verify that all required dependencies are installed
   - Run test script: `python gui/test_gui_launch.py`

2. **Display Issues**
   - If UI elements appear misaligned, your Tkinter version may be incompatible
   - Try another GUI version through the launcher

3. **Geometry Manager Errors**
   - "Cannot use geometry manager pack inside frame configured with grid"
   - This occurs when mixing pack and grid managers in the same container
   - Report the specific error for assistance

4. **Import Errors**
   - If modules cannot be found, ensure you're running from the project root directory
   - The GUI needs access to parent directory modules

5. **Indentation Errors**
   - Recent fixes have addressed indentation issues in gui_main.py
   - If errors persist, use the fixed launcher: `python gui/gui_launcher_fixed.py`

## Development Guidelines

When modifying or extending the GUI:

1. **Naming Convention**: All GUI files should use the `gui_` prefix
2. **File Location**: Place all GUI-related files in the `gui/` directory
3. **Geometry Managers**: Within a container, use either all `pack()` or all `grid()`, never mix them
4. **Error Handling**: Catch and log exceptions, especially during initialization
5. **Documentation**: Update this README when adding new features or files
6. **Testing**: Run `test_gui_launch.py` after making changes
7. **Backups**: Keep backups in the `backups/` directory when making significant changes

## Recent Updates

- Fixed indentation error in gui_main.py at line 243
- Added comprehensive error handling in gui_launcher_fixed.py
- Created test script for verifying GUI functionality
- Added Launch_GUI.bat for easy Windows launching
- Improved import path handling for parent directory modules

## Future Enhancements

- [ ] Dark mode theme support
- [ ] Customizable layouts
- [ ] Export functionality for logs and reports
- [ ] Cloud service integration
- [ ] Advanced visualization charts

## Support

For issues or questions:
1. Check the built-in help system (Help tab in GUI)
2. Review troubleshooting section above
3. Check error logs in `gui/gui_launcher_error.log`
4. Test with `python gui/test_gui_launch.py`
5. Refer to project documentation