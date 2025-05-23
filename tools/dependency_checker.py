#!/usr/bin/env python3
"""
Dependency Checker Tool
Verifies all required dependencies are available for division installation
"""
import sys
import subprocess
import json
import platform
from pathlib import Path


class DependencyChecker:
    def __init__(self):
        self.manifest_path = Path(__file__).parent.parent / "packages_manifest.json"
        self.missing_deps = []
        self.available_deps = []
        
    def load_manifest(self):
        """Load package manifest"""
        with open(self.manifest_path, 'r') as f:
            return json.load(f)
            
    def check_python_version(self):
        """Check Python version meets requirements"""
        required = (3, 8)
        current = sys.version_info[:2]
        
        if current >= required:
            self.available_deps.append(f"Python {current[0]}.{current[1]}")
            return True
        else:
            self.missing_deps.append(f"Python >= {required[0]}.{required[1]} (found {current[0]}.{current[1]})")
            return False
            
    def check_python_packages(self, packages):
        """Check Python package availability"""
        for pkg in packages:
            try:
                __import__(pkg['name'].replace('-', '_'))
                self.available_deps.append(f"{pkg['name']} {pkg['version']}")
            except ImportError:
                # Check if wheel file exists in dependencies
                wheel_path = Path(__file__).parent.parent / "dependencies" / "python_packages"
                wheel_files = list(wheel_path.glob(f"{pkg['name']}*.whl"))
                
                if wheel_files:
                    self.available_deps.append(f"{pkg['name']} {pkg['version']} (wheel available)")
                else:
                    self.missing_deps.append(f"{pkg['name']} {pkg['version']}")
                    
    def check_external_tools(self, tools):
        """Check external tool availability"""
        for tool in tools:
            if tool['name'] == 'Blender':
                # Check if Blender is installed
                try:
                    result = subprocess.run(['blender', '--version'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        self.available_deps.append(f"Blender (installed)")
                    else:
                        raise Exception()
                except:
                    # Check for installer
                    installer_path = Path(__file__).parent.parent / "dependencies" / "installers"
                    if list(installer_path.glob("blender*.msi")):
                        self.available_deps.append(f"Blender (installer available)")
                    else:
                        self.missing_deps.append("Blender")
                        
    def check_system_requirements(self, requirements):
        """Check system requirements"""
        system = platform.system()
        
        if 'os' in requirements:
            if system.lower() in requirements['os'].lower():
                self.available_deps.append(f"OS: {system}")
            else:
                self.missing_deps.append(f"OS: {requirements['os']} (found {system})")
                
        # Check disk space
        if 'disk_space' in requirements:
            import shutil
            usage = shutil.disk_usage(Path.home())
            free_gb = usage.free / (1024**3)
            required_gb = int(requirements['disk_space'].replace('GB', ''))
            
            if free_gb >= required_gb:
                self.available_deps.append(f"Disk space: {free_gb:.1f}GB free")
            else:
                self.missing_deps.append(f"Disk space: need {required_gb}GB (have {free_gb:.1f}GB)")
                
    def generate_report(self):
        """Generate dependency report"""
        manifest = self.load_manifest()
        deps = manifest.get('dependencies', {})
        
        print("=" * 60)
        print("GGG Division Dependency Check Report")
        print("=" * 60)
        
        # Check all dependencies
        self.check_python_version()
        
        if 'python_packages' in deps:
            self.check_python_packages(deps['python_packages'])
            
        if 'external_tools' in deps:
            self.check_external_tools(deps['external_tools'])
            
        if 'system_requirements' in deps:
            self.check_system_requirements(deps['system_requirements'])
            
        # Print results
        print("\n✓ Available Dependencies:")
        for dep in self.available_deps:
            print(f"  • {dep}")
            
        if self.missing_deps:
            print("\n✗ Missing Dependencies:")
            for dep in self.missing_deps:
                print(f"  • {dep}")
                
            print("\nPlease install missing dependencies before proceeding.")
            return False
        else:
            print("\n✓ All dependencies satisfied!")
            return True
            
            
if __name__ == "__main__":
    checker = DependencyChecker()
    checker.generate_report()