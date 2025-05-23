#!/usr/bin/env python3
"""
Creates Windows executable for the division installer
Uses PyInstaller to bundle the installer into a standalone exe
"""
import subprocess
import sys
from pathlib import Path


def create_exe():
    """Create installer executable"""
    installer_path = Path(__file__).parent / "installer.py"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable
        "--windowed",                   # No console window
        "--name", "GGG_Division_Installer",
        "--icon", "installer/icons/ggg_installer.ico",  # Custom icon if available
        "--add-data", "packages_manifest.json;.",       # Include manifest
        "--add-data", "packages;packages",              # Include packages
        "--add-data", "dependencies;dependencies",      # Include dependencies
        "--hidden-import", "tkinter",
        "--hidden-import", "win32com.client",
        str(installer_path)
    ]
    
    print("Creating installer executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Executable created successfully!")
        print("  Location: dist/GGG_Division_Installer.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to create executable: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Install with: pip install pyinstaller")
        return False
        
    return True


def create_autorun():
    """Create autorun.inf for USB"""
    autorun_content = """[autorun]
icon=installer\\icons\\ggg_installer.ico
label=GGG Division Installer
open=GGG_Division_Installer.exe
action=Install GlowingGoldenGlobe Division
"""
    
    autorun_path = Path(__file__).parent / "autorun.inf"
    autorun_path.write_text(autorun_content)
    print("✓ Created autorun.inf")


if __name__ == "__main__":
    if create_exe():
        create_autorun()
        print("\nPackage suite executable ready for USB deployment!")