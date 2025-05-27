#!/usr/bin/env python3
"""
Package Suite Installer for GlowingGoldenGlobe Project Divisions
Shows dependencies and sets up new division environments
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


class DivisionInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GGG Division Setup - Package Suite Installer")
        self.root.geometry("800x600")
        
        # Load manifest
        self.manifest_path = Path(__file__).parent / "packages_manifest.json"
        self.load_manifest()
        
        # Setup UI
        self.setup_ui()
        
    def load_manifest(self):
        """Load package manifest"""
        try:
            with open(self.manifest_path, 'r') as f:
                self.manifest = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load manifest: {e}")
            sys.exit(1)
            
    def setup_ui(self):
        """Create installer UI"""
        # Title
        title = ttk.Label(self.root, text="GlowingGoldenGlobe Division Setup", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Dependencies tab
        self.deps_frame = ttk.Frame(notebook)
        notebook.add(self.deps_frame, text="Dependencies")
        self.setup_dependencies_tab()
        
        # Packages tab
        self.pkg_frame = ttk.Frame(notebook)
        notebook.add(self.pkg_frame, text="Packages")
        self.setup_packages_tab()
        
        # Configuration tab
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="Configuration")
        self.setup_config_tab()
        
        # Install button
        install_btn = ttk.Button(self.root, text="Install Division", 
                                command=self.install_division,
                                style='Accent.TButton')
        install_btn.pack(pady=10)
        
    def setup_dependencies_tab(self):
        """Show all dependencies"""
        # Create scrollable frame
        canvas = tk.Canvas(self.deps_frame)
        scrollbar = ttk.Scrollbar(self.deps_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add dependencies
        deps = self.manifest.get('dependencies', {})
        
        # Python packages
        if 'python_packages' in deps:
            py_label = ttk.Label(scrollable_frame, text="Python Packages:", 
                                font=('Arial', 12, 'bold'))
            py_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            
            for i, pkg in enumerate(deps['python_packages'], 1):
                pkg_text = f"• {pkg['name']} {pkg['version']}"
                if pkg.get('purpose'):
                    pkg_text += f" - {pkg['purpose']}"
                label = ttk.Label(scrollable_frame, text=pkg_text)
                label.grid(row=i, column=0, sticky='w', padx=20, pady=2)
        
        # System requirements
        if 'system_requirements' in deps:
            sys_label = ttk.Label(scrollable_frame, text="\nSystem Requirements:", 
                                 font=('Arial', 12, 'bold'))
            sys_label.grid(row=20, column=0, sticky='w', padx=5, pady=5)
            
            for req, value in deps['system_requirements'].items():
                req_text = f"• {req}: {value}"
                label = ttk.Label(scrollable_frame, text=req_text)
                label.grid(row=21, column=0, sticky='w', padx=20, pady=2)
        
        # External tools
        if 'external_tools' in deps:
            tools_label = ttk.Label(scrollable_frame, text="\nExternal Tools:", 
                                   font=('Arial', 12, 'bold'))
            tools_label.grid(row=30, column=0, sticky='w', padx=5, pady=5)
            
            for i, tool in enumerate(deps['external_tools'], 31):
                tool_text = f"• {tool['name']} - {tool['purpose']}"
                label = ttk.Label(scrollable_frame, text=tool_text)
                label.grid(row=i, column=0, sticky='w', padx=20, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_packages_tab(self):
        """Show installable packages"""
        # Create treeview
        tree = ttk.Treeview(self.pkg_frame, columns=('Type', 'Description'), 
                           show='tree headings')
        tree.heading('#0', text='Package')
        tree.heading('Type', text='Type')
        tree.heading('Description', text='Description')
        
        # Add packages
        packages = self.manifest.get('packages', {})
        
        # User invented packages
        if 'user_invented' in packages:
            user_parent = tree.insert('', 'end', text='User Invented Packages', 
                                     values=('Category', ''))
            for pkg_id, pkg_info in packages['user_invented'].items():
                tree.insert(user_parent, 'end', text=pkg_info['name'],
                           values=(pkg_info['type'], pkg_info['description']))
        
        # Project packages
        if 'project_packages' in packages:
            proj_parent = tree.insert('', 'end', text='Project Core Packages', 
                                     values=('Category', ''))
            for pkg_id, pkg_info in packages['project_packages'].items():
                tree.insert(proj_parent, 'end', text=pkg_info['name'],
                           values=(pkg_info['type'], pkg_info['description']))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
    def setup_config_tab(self):
        """Division configuration options"""
        # Division name
        name_label = ttk.Label(self.config_frame, text="Division Name:")
        name_label.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        self.division_name = tk.StringVar(value="NewDivision")
        name_entry = ttk.Entry(self.config_frame, textvariable=self.division_name, 
                              width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Install location
        loc_label = ttk.Label(self.config_frame, text="Install Location:")
        loc_label.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        self.install_path = tk.StringVar()
        loc_entry = ttk.Entry(self.config_frame, textvariable=self.install_path, 
                             width=30)
        loc_entry.grid(row=1, column=1, padx=10, pady=5)
        
        browse_btn = ttk.Button(self.config_frame, text="Browse", 
                               command=self.browse_location)
        browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Options
        options_frame = ttk.LabelFrame(self.config_frame, text="Installation Options")
        options_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=20, 
                          sticky='ew')
        
        self.create_venv = tk.BooleanVar(value=True)
        venv_check = ttk.Checkbutton(options_frame, text="Create virtual environment",
                                     variable=self.create_venv)
        venv_check.pack(anchor='w', padx=10, pady=5)
        
        self.install_deps = tk.BooleanVar(value=True)
        deps_check = ttk.Checkbutton(options_frame, text="Install dependencies",
                                     variable=self.install_deps)
        deps_check.pack(anchor='w', padx=10, pady=5)
        
        self.create_shortcuts = tk.BooleanVar(value=True)
        shortcuts_check = ttk.Checkbutton(options_frame, text="Create desktop shortcuts",
                                         variable=self.create_shortcuts)
        shortcuts_check.pack(anchor='w', padx=10, pady=5)
        
    def browse_location(self):
        """Browse for install location"""
        path = filedialog.askdirectory(title="Select Installation Directory")
        if path:
            self.install_path.set(path)
            
    def install_division(self):
        """Install new division"""
        if not self.install_path.get():
            messagebox.showerror("Error", "Please select installation location")
            return
            
        try:
            # Create progress window
            progress = tk.Toplevel(self.root)
            progress.title("Installing Division")
            progress.geometry("400x200")
            
            progress_label = ttk.Label(progress, text="Installing...", 
                                      font=('Arial', 12))
            progress_label.pack(pady=20)
            
            progress_bar = ttk.Progressbar(progress, length=300, mode='indeterminate')
            progress_bar.pack(pady=10)
            progress_bar.start()
            
            status_label = ttk.Label(progress, text="Creating directory structure...")
            status_label.pack(pady=10)
            
            # Perform installation
            division_path = Path(self.install_path.get()) / self.division_name.get()
            
            # Create directory structure
            self.create_division_structure(division_path)
            status_label.config(text="Copying packages...")
            
            # Copy packages
            self.copy_packages(division_path)
            status_label.config(text="Setting up configuration...")
            
            # Setup configuration
            self.setup_division_config(division_path)
            
            if self.create_venv.get():
                status_label.config(text="Creating virtual environment...")
                self.create_virtual_environment(division_path)
                
            if self.install_deps.get():
                status_label.config(text="Installing dependencies...")
                self.install_dependencies(division_path)
                
            if self.create_shortcuts.get():
                status_label.config(text="Creating shortcuts...")
                self.create_division_shortcuts(division_path)
            
            progress_bar.stop()
            progress.destroy()
            
            messagebox.showinfo("Success", 
                              f"Division '{self.division_name.get()}' installed successfully!")
            
        except Exception as e:
            messagebox.showerror("Installation Failed", str(e))
            
    def create_division_structure(self, division_path: Path):
        """Create division directory structure"""
        # Main directories
        directories = [
            'Div_AI_Agent_Focus_1', 'Div_AI_Agent_Focus_2', 'Div_AI_Agent_Focus_3', 'Div_AI_Agent_Focus_4', 'Div_AI_Agent_Focus_5',
            'ai_managers', 'gui', 'utils', 'docs', 'cloud_storage',
            'logs', 'agent_outputs', 'templates', 'Scripts'
        ]
        
        for dir_name in directories:
            (division_path / dir_name).mkdir(parents=True, exist_ok=True)
            
    def copy_packages(self, division_path: Path):
        """Copy packages to division"""
        source_root = Path(__file__).parent.parent
        
        # Copy core files
        core_files = [
            'main.py', 'setup.py', 'requirements.txt',
            'README.md', 'CLAUDE.md'
        ]
        
        for file in core_files:
            src = source_root / file
            if src.exists():
                shutil.copy2(src, division_path / file)
                
        # Copy package directories
        package_dirs = ['ai_managers', 'gui', 'utils', 'cloud_storage']
        
        for pkg_dir in package_dirs:
            src_dir = source_root / pkg_dir
            if src_dir.exists():
                shutil.copytree(src_dir, division_path / pkg_dir, 
                               dirs_exist_ok=True)
                               
    def setup_division_config(self, division_path: Path):
        """Setup division configuration"""
        config = {
            'division_name': self.division_name.get(),
            'created_date': datetime.now().isoformat(),
            'packages': self.manifest.get('packages', {}),
            'settings': {
                'ai_workflow_enabled': True,
                'parallel_execution': True,
                'auto_conflict_handling': True
            }
        }
        
        with open(division_path / 'division_config.json', 'w') as f:
            json.dump(config, f, indent=2)
            
    def create_virtual_environment(self, division_path: Path):
        """Create virtual environment"""
        venv_path = division_path / 'venv'
        subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
        
    def install_dependencies(self, division_path: Path):
        """Install Python dependencies"""
        req_file = division_path / 'requirements.txt'
        if req_file.exists():
            venv_pip = division_path / 'venv' / 'Scripts' / 'pip.exe'
            if venv_pip.exists():
                subprocess.run([str(venv_pip), 'install', '-r', str(req_file)], 
                             check=True)
                             
    def create_division_shortcuts(self, division_path: Path):
        """Create desktop shortcuts"""
        desktop = Path.home() / 'Desktop'
        
        # Create launcher batch file
        launcher = division_path / 'launch_division.bat'
        launcher_content = f"""@echo off
cd /d "{division_path}"
call venv\\Scripts\\activate
python gui\\run_ggg_gui.py
pause
"""
        launcher.write_text(launcher_content)
        
        # Create shortcut (Windows)
        if sys.platform == 'win32':
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(
                str(desktop / f"{self.division_name.get()}.lnk")
            )
            shortcut.Targetpath = str(launcher)
            shortcut.WorkingDirectory = str(division_path)
            shortcut.IconLocation = str(division_path / 'gui' / 'gui_icons' / 'default_icon.ico')
            shortcut.save()
            
    def run(self):
        """Run installer"""
        self.root.mainloop()


if __name__ == "__main__":
    installer = DivisionInstaller()
    installer.run()