@echo off
REM Toggle Claude Code Settings between Auto and Manual modes
title Claude Settings Toggle

echo ========================================
echo Claude Code Settings Toggle System
echo ========================================
echo.

if "%1"=="" (
    echo Current Status:
    python "%~dp0toggle_claude_settings.py" status
    echo.
    echo Options:
    echo   1. Toggle modes (switch between auto/manual)
    echo   2. Set to AUTO mode
    echo   3. Set to MANUAL mode
    echo   4. Verify files
    echo   5. Exit
    echo.
    set /p choice="Enter your choice (1-5): "
    
    if "!choice!"=="1" python "%~dp0toggle_claude_settings.py" toggle
    if "!choice!"=="2" python "%~dp0toggle_claude_settings.py" auto
    if "!choice!"=="3" python "%~dp0toggle_claude_settings.py" manual
    if "!choice!"=="4" python "%~dp0toggle_claude_settings.py" verify
    if "!choice!"=="5" exit
) else (
    python "%~dp0toggle_claude_settings.py" %1
)

echo.
echo Press any key to exit...
pause >nul