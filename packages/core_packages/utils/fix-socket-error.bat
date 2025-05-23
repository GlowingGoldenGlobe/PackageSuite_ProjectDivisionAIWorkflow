@echo off
echo === Socket Hang Up Error Fixer ===
echo.
echo Choose an option:
echo 1. Run PowerShell fix (Recommended)
echo 2. Run Python troubleshooter
echo 3. Quick WSL restart only
echo 4. Exit
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo Starting PowerShell network fix...
    PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Fix-SocketHangUp.ps1"
    pause
) else if "%choice%"=="2" (
    echo Starting Python troubleshooter...
    python "%~dp0network_troubleshooter.py"
    pause
) else if "%choice%"=="3" (
    echo Restarting WSL...
    wsl --shutdown
    echo WSL shutdown complete
    pause
) else if "%choice%"=="4" (
    exit
) else (
    echo Invalid choice
    pause
)