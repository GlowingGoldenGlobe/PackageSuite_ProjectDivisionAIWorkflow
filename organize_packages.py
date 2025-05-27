#!/usr/bin/env python3
"""
Organizes project packages into the pkg-suite structure for division portability
"""
import shutil
import json
from pathlib import Path
from datetime import datetime


class PackageOrganizer:
    def __init__(self):
        self.project_root = Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv")
        self.pkg_suite_root = self.project_root / "pkg-suite"
        self.packages_dir = self.pkg_suite_root / "packages"
        
    def organize_user_invented_packages(self):
        """Organize the 8 user-invented packages"""
        user_packages = {
            "code_pre_api_compiler": {
                "description": "In-application code pre-API-input compiler",
                "files": [
                    # This package needs to be created based on user's specification
                    "code_pre_api_compiler.py"
                ]
            },
            "error_handler": {
                "description": "Error handler package with simple_error_reporter",
                "files": [
                    "Div_AI_Agent_Focus_1/simple_error_reporter.py",
                    "Div_AI_Agent_Focus_2/simple_error_reporter.py", 
                    "Div_AI_Agent_Focus_3/simple_error_reporter.py",
                    "Div_AI_Agent_Focus_4/simple_error_reporter.py",
                    "Div_AI_Agent_Focus_5/simple_error_reporter.py"
                ]
            },
            "ai_automated_workflow": {
                "description": "AI Automated Workflow main package",
                "files": [
                    "ai_workflow_integration.py",
                    "ai_workflow_status.py",
                    "ai_workflow_status.json",
                    "ai_managers/workflow_integrity_manager.py",
                    "workflow_pause.py"
                ]
            },
            "task_scheduler": {
                "description": "Tasks scheduler plus to-do list package",
                "files": [
                    "claude_task_scheduler.py",
                    "ai_managers/scheduled_tasks_manager.py",
                    "ai_managers/task_manager.py",
                    "ai_managers/git_task_manager.py",
                    "ai_managers/interleaving_task_manager.py",
                    "task_manager_integration.py"
                ]
            },
            "project_ai_managers": {
                "description": "Project AI managers package",
                "files": [
                    "ai_managers/project_ai_manager.py",
                    "ai_managers/enhanced_project_ai_manager.py",
                    "ai_managers/enhanced_project_ai_manager_v2.py",
                    "ai_managers/ai_manager_context_builder.py",
                    "ai_managers/project_resource_manager.py"
                ]
            },
            "hardware_monitor": {
                "description": "Hardware monitor package",
                "files": [
                    "hardware_monitor.py",
                    "windows_resource_monitor.py",
                    "claude_resource_monitor.py",
                    "hardware_monitor_config.json"
                ]
            },
            "gui_parallel_workflow": {
                "description": "GUI parallel workflow AI automation manager",
                "files": [
                    "parallel_execution_gui.py",
                    "parallel_gui_integration.py",
                    "gui/claude_parallel_gui.py",
                    "ai_managers/parallel_execution_manager.py",
                    "claude_parallel_manager.py",
                    "parallel_execution_integration.py"
                ]
            },
            "config_ai_agent_memory": {
                "description": "Config AI Agent Memory with Restricted Automation Mode",
                "files": [
                    "claude_memory.py",
                    "CLAUDE.md",
                    "ai_managers/auto_conflict_handler.py",
                    "ai_managers/manual_override_emailer.py",
                    "ai_managers/restricted_automation_schema.json"
                ]
            },
            "parallel_agents_conflict_prevention": {
                "description": "Parallel AI Agents Conflict Prevention package",
                "files": [
                    "merge_conflict_handler.py",
                    "gui/session_conflict_manager.py",
                    "ai_managers/session_detector.py"
                ]
            },
            "llm_memory_cpuo_system": {
                "description": "LLM Memory CPUO (Contents-Procedure-Utils-Options) System",
                "files": [
                    "utils/project_improvement_procedure.py",
                    "utils/cross_reference_manager.py"
                ]
            }
        }
        
        # Create user_invented directory
        user_dir = self.packages_dir / "user_invented"
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy packages
        for pkg_name, pkg_info in user_packages.items():
            pkg_dir = user_dir / pkg_name
            pkg_dir.mkdir(exist_ok=True)
            
            # Create package README
            readme_content = f"""# {pkg_name.replace('_', ' ').title()}

{pkg_info['description']}

## Files Included:
"""
            
            # Copy files
            for file_path in pkg_info['files']:
                src = self.project_root / file_path
                if src.exists():
                    # Preserve directory structure for multi-file packages
                    if '/' in file_path:
                        sub_dir = pkg_dir / Path(file_path).parent
                        sub_dir.mkdir(parents=True, exist_ok=True)
                        dst = pkg_dir / file_path
                    else:
                        dst = pkg_dir / Path(file_path).name
                    
                    shutil.copy2(src, dst)
                    readme_content += f"- {file_path}\n"
                    print(f"  ✓ Copied {file_path}")
                else:
                    print(f"  ✗ Missing {file_path}")
                    
            # Write README
            (pkg_dir / "README.md").write_text(readme_content)
            
    def organize_core_packages(self):
        """Organize core project packages"""
        core_packages = {
            "gui_system": {
                "description": "Complete GUI implementation system",
                "source": "gui"
            },
            "ai_managers": {
                "description": "AI management and coordination system",
                "source": "ai_managers"
            },
            "utils": {
                "description": "Utility scripts and helpers",
                "source": "utils"
            },
            "cloud_storage": {
                "description": "Cloud storage integration",
                "source": "cloud_storage"
            },
            "templates": {
                "description": "Pro-forma templates for consistency",
                "source": "templates"
            }
        }
        
        # Create core_packages directory
        core_dir = self.packages_dir / "core_packages"
        core_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy entire directories
        for pkg_name, pkg_info in core_packages.items():
            src_dir = self.project_root / pkg_info['source']
            if src_dir.exists() and src_dir.is_dir():
                dst_dir = core_dir / pkg_name
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
                print(f"✓ Copied {pkg_info['source']} -> {pkg_name}")
                
                # Create package info
                info = {
                    "name": pkg_name,
                    "description": pkg_info['description'],
                    "source": pkg_info['source'],
                    "copied_date": datetime.now().isoformat()
                }
                (dst_dir / "package_info.json").write_text(json.dumps(info, indent=2))
                
    def organize_optional_packages(self):
        """Organize optional enhancement packages"""
        optional_packages = {
            "ros2_integration": {
                "description": "ROS2 integration for robotics",
                "source": "ros2_integration"
            },
            "blender_integration": {
                "description": "Blender 3D modeling integration",
                "files": [
                    "blender_bridge.py",
                    "blender_bridge_runner.py",
                    "blender_execution_script.py"
                ]
            },
            "open3d_integration": {
                "description": "Open3D visualization tools",
                "files": [
                    "open3d_viewer.py",
                    "open3d_gui_integration.py",
                    "check_open3d.py"
                ]
            }
        }
        
        # Create optional_packages directory
        opt_dir = self.packages_dir / "optional_packages"
        opt_dir.mkdir(parents=True, exist_ok=True)
        
        for pkg_name, pkg_info in optional_packages.items():
            pkg_dir = opt_dir / pkg_name
            pkg_dir.mkdir(exist_ok=True)
            
            if 'source' in pkg_info:
                # Copy entire directory
                src_dir = self.project_root / pkg_info['source']
                if src_dir.exists():
                    shutil.copytree(src_dir, pkg_dir, dirs_exist_ok=True)
                    print(f"✓ Copied {pkg_info['source']} -> {pkg_name}")
            elif 'files' in pkg_info:
                # Copy individual files
                for file_path in pkg_info['files']:
                    src = self.project_root / file_path
                    if src.exists():
                        dst = pkg_dir / Path(file_path).name
                        shutil.copy2(src, dst)
                        print(f"  ✓ Copied {file_path}")
                        
    def create_integration_script(self):
        """Create script for integrating packages into new division"""
        integration_script = '''#!/usr/bin/env python3
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
        "Div_AI_Agent_Focus_1", "Div_AI_Agent_Focus_2", "Div_AI_Agent_Focus_3", "Div_AI_Agent_Focus_4", "Div_AI_Agent_Focus_5",
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
    
    print("\\n✓ Package integration complete!")
    print(f"  Division ready at: {division_path}")
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python integrate.py <division_path>")
        sys.exit(1)
    
    integrate_packages(sys.argv[1])
'''
        
        integration_path = self.pkg_suite_root / "integrate.py"
        integration_path.write_text(integration_script)
        integration_path.chmod(0o755)
        print("✓ Created integration script")
        
    def run(self):
        """Run the package organization"""
        print("Organizing packages for division portability...")
        print("=" * 60)
        
        print("\n1. Organizing user-invented packages:")
        self.organize_user_invented_packages()
        
        print("\n2. Organizing core packages:")
        self.organize_core_packages()
        
        print("\n3. Organizing optional packages:")
        self.organize_optional_packages()
        
        print("\n4. Creating integration script:")
        self.create_integration_script()
        
        print("\n✓ Package organization complete!")
        print(f"  Location: {self.pkg_suite_root}")


if __name__ == "__main__":
    organizer = PackageOrganizer()
    organizer.run()