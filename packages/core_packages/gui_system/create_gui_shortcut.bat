@echo off
:: Create-WorkingGUIShortcut.bat
:: Creates a desktop shortcut to the GlowingGoldenGlobe Working GUI
:: This version is located in the /gui/ folder

echo Creating desktop shortcut for GlowingGoldenGlobe GUI with Claude Parallel...
echo.

:: Get current directory (gui folder)
set "GUI_DIR=%~dp0"

:: Get parent directory (project root)
for %%a in ("%GUI_DIR%..") do set "PROJECT_DIR=%%~fa"

:: Set batch file path (in gui folder)
set "BATCH_FILE=%GUI_DIR%gui_launch.bat"

:: Check if the batch file exists
if not exist "%BATCH_FILE%" (
    echo Error: gui_launch.bat not found at %BATCH_FILE%
    echo Please make sure the batch file exists in the project root.
    pause
    exit /b 1
)

:: Get the current user's desktop path
for /f "tokens=2* delims= " %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Desktop"') do set "DESKTOP_PATH=%%b"

:: Create the shortcut using VBScript
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP_PATH%\GlowingGoldenGlobe GUI.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%BATCH_FILE%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%PROJECT_DIR%" >> "%TEMP%\CreateShortcut.vbs"

:: Try to set custom icon if available
if exist "%GUI_DIR%gui_icons\ggg_icon.ico" (
    echo oLink.IconLocation = "%GUI_DIR%gui_icons\ggg_icon.ico, 0" >> "%TEMP%\CreateShortcut.vbs"
) else (
    echo oLink.IconLocation = "%SystemRoot%\System32\shell32.dll, 0" >> "%TEMP%\CreateShortcut.vbs"
)

echo oLink.Description = "Launch GlowingGoldenGlobe GUI with Claude Parallel Integration" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

:: Execute the VBScript to create the shortcut
cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo Desktop shortcut created successfully!
echo The shortcut has been placed on your desktop as "GlowingGoldenGlobe GUI"
echo.
echo The shortcut will launch: %BATCH_FILE%
echo.
pause