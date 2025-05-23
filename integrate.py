#!/usr/bin/env python3
"""
Integration script for GGG package suite
Automatically integrates packages into new division structure
"""
import os
import sys
import json
import shutil
from pathlib import Path


def integrate_packages(division_path):
    """Integrate packages into new division"""
    division_path = Path(division_path)
    pkg_suite_path = Path(__file__).parent
    
    print(f"Integrating GGG packages into: {division_path}")
    
    # Create division structure if needed
    required_dirs = [
        "AI_Agent_1", "AI_Agent_2", "AI_Agent_3", "AI_Agent_4", "AI_Agent_5",
        "ai_managers", "gui", "utils", "cloud_storage", "templates"
    ]
    
    for dir_name in required_dirs:
        (division_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Copy user invented packages
    user_src = pkg_suite_path / "packages" / "user_invented"
    for pkg_dir in user_src.iterdir():
        if pkg_dir.is_dir():
            print(f"Installing {pkg_dir.name}...")
            
            # Special handling for multi-agent packages
            if pkg_dir.name == "error_handler":
                # Copy to each AI_Agent folder
                for i in range(1, 6):
                    agent_dir = division_path / f"AI_Agent_{i}"
                    for file in pkg_dir.glob("**/simple_error_reporter.py"):
                        shutil.copy2(file, agent_dir / "simple_error_reporter.py")
            else:
                # Copy package files to appropriate locations
                for file in pkg_dir.rglob("*"):
                    if file.is_file() and file.name != "README.md":
                        # Determine destination based on file path
                        rel_path = file.relative_to(pkg_dir)
                        if "ai_managers" in str(rel_path):
                            dst = division_path / rel_path
                        elif "gui" in str(rel_path):
                            dst = division_path / rel_path
                        elif "utils" in str(rel_path):
                            dst = division_path / rel_path
                        else:
                            dst = division_path / rel_path
                        
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, dst)
    
    # Copy core packages
    core_src = pkg_suite_path / "packages" / "core_packages"
    for pkg_dir in core_src.iterdir():
        if pkg_dir.is_dir():
            dst_dir = division_path / pkg_dir.name
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(pkg_dir, dst_dir)
            print(f"✓ Installed core package: {pkg_dir.name}")
    
    # Create division config
    config = {
        "division_type": "GGG_Division",
        "packages_integrated": True,
        "ggg_objectives_url": "https://glowinggoldenglobe.com",
        "ai_workspace_url": "https://glowinggoldenglobe.w3spaces.com/ai",
        "integration_date": str(Path.cwd())
    }
    
    (division_path / "division_config.json").write_text(json.dumps(config, indent=2))
    
    print("\n✓ Package integration complete!")
    print(f"  Division ready at: {division_path}")
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python integrate.py <division_path>")
        sys.exit(1)
    
    integrate_packages(sys.argv[1])
