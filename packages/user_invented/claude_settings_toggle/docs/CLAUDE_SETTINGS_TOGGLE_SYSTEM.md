# Claude Code Settings Toggle System

## Overview

The Claude Settings Toggle System allows you to switch between two modes of Claude Code operation:

1. **AUTO Mode**: Full automation with up to 5 parallel terminals, no permission prompts
2. **MANUAL Mode**: Original settings requiring user permission for most operations

## Files Created

### Settings Files
- `.claude/settings_auto.json` - Full automation settings
- `.claude/settings_manual.json` - Manual permission settings
- `.claude/settings_state.json` - Tracks current mode and history
- `.claude/settings.local.json` - Active settings (modified by toggle)

### Toggle Scripts
- `toggle_claude_settings.py` - Main Python toggle script
- `Toggle_Claude_Settings.bat` - Windows batch file interface
- `Toggle-ClaudeSettings.ps1` - PowerShell GUI-like interface

### Backup Directory
- `.claude/backups/` - Automatic backups before each toggle

## Usage

### Method 1: Command Line (Python)
```bash
# Show current status
python toggle_claude_settings.py status

# Toggle to opposite mode
python toggle_claude_settings.py toggle

# Switch to specific mode
python toggle_claude_settings.py auto
python toggle_claude_settings.py manual

# Verify all files exist
python toggle_claude_settings.py verify
```

### Method 2: Batch File (Windows)
Double-click `Toggle_Claude_Settings.bat` or run from command prompt:
```cmd
Toggle_Claude_Settings.bat
```

### Method 3: PowerShell (Recommended)
```powershell
# Interactive menu
.\Toggle-ClaudeSettings.ps1

# Direct commands
.\Toggle-ClaudeSettings.ps1 -Action toggle
.\Toggle-ClaudeSettings.ps1 -Action auto
.\Toggle-ClaudeSettings.ps1 -Action manual
```

## Mode Differences

### AUTO Mode Features
- No permission prompts for authorized commands
- Up to 5 parallel terminal instances
- Automatic script execution
- Process management capabilities
- Terminal launch commands enabled
- Full automation configuration

### MANUAL Mode Features
- Permission required for most operations
- Limited automation capabilities
- Basic file and git operations only
- Original Claude Code behavior
- Safer for sensitive operations

## Important Notes

1. **Restart Required**: You must restart Claude Code after toggling for changes to take effect

2. **Automatic Backups**: The system automatically backs up current settings before each toggle

3. **State Tracking**: Toggle history is maintained in `settings_state.json`

4. **Modified Files**: The toggle system modifies:
   - `.claude/settings.local.json` (primary settings file)
   - `.claude/settings_state.json` (state tracking)

## Troubleshooting

### Settings Not Taking Effect
- Ensure Claude Code is completely closed before toggling
- Verify the toggle completed successfully using `verify` command
- Check that `.claude/settings.local.json` was updated

### Missing Files
Run the verify command to check all required files:
```bash
python toggle_claude_settings.py verify
```

### Restore from Backup
Backups are stored in `.claude/backups/` with timestamps. To restore:
```bash
cp .claude/backups/settings_backup_YYYYMMDD_HHMMSS.json .claude/settings.local.json
```

## Integration with Project

The toggle system integrates with:
- Claude Parallel execution system
- Task automation workflows
- Terminal lifecycle management
- GUI automation controls

## Security Considerations

- AUTO mode grants extensive permissions - use with caution
- MANUAL mode is safer for sensitive operations
- Review permissions in each mode before toggling
- Backups allow recovery from unwanted changes

## Quick Reference

| Action | Command | Effect |
|--------|---------|--------|
| Check status | `python toggle_claude_settings.py status` | Shows current mode |
| Toggle mode | `python toggle_claude_settings.py toggle` | Switches modes |
| Set AUTO | `python toggle_claude_settings.py auto` | Enables automation |
| Set MANUAL | `python toggle_claude_settings.py manual` | Requires permissions |
| Verify files | `python toggle_claude_settings.py verify` | Checks all files |

## Desktop Shortcut

To create a desktop shortcut for easy access:
```powershell
.\Toggle-ClaudeSettings.ps1
# Select option 7 from the menu
```

This creates a "Toggle Claude Settings" shortcut on your desktop for quick access to the toggle system.