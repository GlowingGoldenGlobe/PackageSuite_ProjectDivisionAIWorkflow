# Toggle Claude Code Settings PowerShell Script
# Provides GUI-like interface for settings management

param(
    [ValidateSet('toggle', 'auto', 'manual', 'status', 'verify', 'backup', 'restore')]
    [string]$Action = 'status'
)

$ErrorActionPreference = 'Stop'

# Define paths
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = Join-Path $ProjectRoot ".claude"
$ToggleScript = Join-Path $ProjectRoot "toggle_claude_settings.py"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

# Check if Claude is currently running
function Test-ClaudeRunning {
    $claudeProcesses = Get-Process | Where-Object { 
        $_.ProcessName -match "claude|code" -and 
        $_.MainWindowTitle -match "Claude"
    }
    return $claudeProcesses.Count -gt 0
}

# Create desktop shortcut for easy access
function New-DesktopShortcut {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $Desktop "Toggle Claude Settings.lnk"
    
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.IconLocation = "powershell.exe,0"
    $Shortcut.Description = "Toggle Claude Code automation settings"
    $Shortcut.Save()
    
    Write-Success "✓ Desktop shortcut created: $ShortcutPath"
}

# Main menu
function Show-Menu {
    Clear-Host
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      Claude Code Settings Toggle System      ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host
    
    # Check if Claude is running
    if (Test-ClaudeRunning) {
        Write-Warning "⚠️  Claude appears to be running. Restart Claude after changing settings."
        Write-Host
    }
    
    # Show current status
    & python $ToggleScript status
    
    Write-Host
    Write-Host "Available Actions:" -ForegroundColor White
    Write-Host "  [1] Toggle Mode (switch between auto/manual)" -ForegroundColor Green
    Write-Host "  [2] Set to AUTO mode (5 parallel terminals)" -ForegroundColor Yellow
    Write-Host "  [3] Set to MANUAL mode (permission prompts)" -ForegroundColor Yellow
    Write-Host "  [4] Verify all settings files" -ForegroundColor Cyan
    Write-Host "  [5] Create backup of current settings" -ForegroundColor Magenta
    Write-Host "  [6] View backups" -ForegroundColor Magenta
    Write-Host "  [7] Create desktop shortcut" -ForegroundColor Blue
    Write-Host "  [0] Exit" -ForegroundColor DarkGray
    Write-Host
    
    $choice = Read-Host "Select an action (0-7)"
    
    switch ($choice) {
        "1" { 
            & python $ToggleScript toggle
            Write-Host
            Write-Warning "Please restart Claude Code for changes to take effect."
        }
        "2" { 
            & python $ToggleScript auto
            Write-Host
            Write-Warning "Please restart Claude Code for changes to take effect."
        }
        "3" { 
            & python $ToggleScript manual
            Write-Host
            Write-Warning "Please restart Claude Code for changes to take effect."
        }
        "4" { & python $ToggleScript verify }
        "5" { 
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupPath = Join-Path $ClaudeDir "backups\settings_backup_$timestamp.json"
            $currentSettings = Join-Path $ClaudeDir "settings.local.json"
            
            if (Test-Path $currentSettings) {
                New-Item -ItemType Directory -Force -Path (Split-Path $backupPath) | Out-Null
                Copy-Item $currentSettings $backupPath
                Write-Success "✓ Backup created: $backupPath"
            } else {
                Write-Error "❌ No current settings file found"
            }
        }
        "6" {
            $backupDir = Join-Path $ClaudeDir "backups"
            if (Test-Path $backupDir) {
                Write-Info "`nAvailable backups:"
                Get-ChildItem $backupDir -Filter "*.json" | 
                    Sort-Object LastWriteTime -Descending |
                    Select-Object -First 10 |
                    ForEach-Object {
                        Write-Host "  • $($_.Name) - $($_.LastWriteTime)"
                    }
            } else {
                Write-Warning "No backups found"
            }
        }
        "7" { New-DesktopShortcut }
        "0" { return }
        default { Write-Warning "Invalid choice. Please try again." }
    }
    
    Write-Host
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-Menu
}

# Execute based on parameter or show menu
if ($Action -eq 'status') {
    Show-Menu
} else {
    & python $ToggleScript $Action
}