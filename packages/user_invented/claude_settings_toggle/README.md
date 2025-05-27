# Claude Settings Toggle Package

## Overview

This package provides a toggle system for switching Claude Code between two operational modes:

1. **AUTO Mode**: Full automation with up to 5 parallel terminals, no permission prompts
2. **MANUAL Mode**: Original settings requiring user permission for most operations

## Package Contents

- `toggle_claude_settings.py` - Main Python toggle script
- `Toggle_Claude_Settings.bat` - Windows batch file interface
- `Toggle-ClaudeSettings.ps1` - PowerShell GUI-like interface
- `.claude/settings_auto.json` - Auto mode configuration
- `.claude/settings_manual.json` - Manual mode configuration
- `.claude/settings_state.json` - State tracking file
- `docs/CLAUDE_SETTINGS_TOGGLE_SYSTEM.md` - Full documentation

## Installation

When installing this package:

1. All files will be copied to your project root
2. The `.claude` folder will be created/updated with settings files
3. Scripts will be available in the project root for easy access

## Usage

### Quick Toggle
```bash
python toggle_claude_settings.py toggle
```

### Windows Interface
Double-click `Toggle_Claude_Settings.bat`

### PowerShell GUI
```powershell
.\Toggle-ClaudeSettings.ps1
```

## Features

- **Easy Switching**: Toggle between modes without editing JSON files
- **Automatic Backups**: Creates timestamped backups before each toggle
- **State Tracking**: Maintains history of all mode changes
- **Multiple Interfaces**: Command line, batch, and PowerShell options

## Important Notes

- **Restart Required**: Claude Code must be restarted after toggling
- **Security**: AUTO mode grants extensive permissions - use with caution
- **Backups**: Stored in `.claude/backups/` with timestamps

## Integration

This toggle system integrates with:
- Claude Parallel execution system
- Task automation workflows
- Terminal lifecycle management
- GUI automation controls

## Author

Richard Isaac Craddock

## Version

1.0.0 - Initial release with auto/manual toggle functionality