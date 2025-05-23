# Create a desktop shortcut for the GlowingGoldenGlobe Fixed Layout GUI
# This script creates a shortcut that launches the improved GUI with fixed layout

# Get the desktop path
$desktopPath = [Environment]::GetFolderPath("Desktop")

# Create a WScript.Shell object
$WshShell = New-Object -ComObject WScript.Shell

# Define the shortcut path
$ShortcutPath = "$desktopPath\GlowingGoldenGlobe - Fixed Layout GUI.lnk"

# Define the target path (the batch file)
$TargetPath = Join-Path $PSScriptRoot "Run_Fixed_Layout.bat"

# Create the shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "GlowingGoldenGlobe GUI with Improved Fixed Layout"
$Shortcut.IconLocation = Join-Path $PSScriptRoot "gui\gui_icons\default_icon.ppm"
$Shortcut.Save()

# Write to error log txt file instead of creating a separate log file
$LogPath = Join-Path $PSScriptRoot "gui\gui_launcher_error_log.txt"
Add-Content -Path $LogPath -Value "$(Get-Date) - Desktop shortcut created at: $ShortcutPath"

Write-Host "Desktop shortcut created successfully at: $ShortcutPath"
Write-Host ""
Write-Host "The shortcut will launch the GlowingGoldenGlobe GUI with the improved fixed layout."
Write-Host "This layout has better spacing, correct tab content, and maintains 50% screen width."
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")