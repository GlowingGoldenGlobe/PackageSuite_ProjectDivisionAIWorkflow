#!/usr/bin/env python3
"""
Toggle Claude Code Settings between Auto and Manual modes
Preserves both states and allows easy switching
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

class ClaudeSettingsToggle:
    def __init__(self):
        self.claude_dir = Path("/mnt/c/Users/yerbr/glowinggoldenglobe_venv/.claude")
        self.settings_file = self.claude_dir / "settings.local.json"
        self.settings_auto = self.claude_dir / "settings_auto.json"
        self.settings_manual = self.claude_dir / "settings_manual.json"
        self.state_file = self.claude_dir / "settings_state.json"
        self.backup_dir = self.claude_dir / "backups"
        
    def ensure_backup_dir(self):
        """Ensure backup directory exists"""
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_current_settings(self):
        """Backup current settings before switching"""
        if self.settings_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"settings_backup_{timestamp}.json"
            shutil.copy2(self.settings_file, backup_file)
            print(f"✓ Backed up current settings to: {backup_file.name}")
            
    def load_state(self):
        """Load current state information"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return None
        
    def save_state(self, state):
        """Save state information"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
            
    def get_current_mode(self):
        """Determine current mode"""
        state = self.load_state()
        if state:
            return state.get('current_mode', 'unknown')
        return 'unknown'
        
    def toggle(self, target_mode=None):
        """Toggle between auto and manual modes"""
        self.ensure_backup_dir()
        
        # Load current state
        state = self.load_state()
        if not state:
            print("⚠️  No state file found. Creating initial state...")
            state = self.create_initial_state()
            
        current_mode = state['current_mode']
        
        # Determine target mode
        if target_mode:
            if target_mode not in ['auto', 'manual']:
                print(f"❌ Invalid mode: {target_mode}. Use 'auto' or 'manual'")
                return False
            new_mode = target_mode
        else:
            # Toggle to opposite mode
            new_mode = 'manual' if current_mode == 'auto' else 'auto'
            
        if current_mode == new_mode:
            print(f"ℹ️  Already in {new_mode} mode")
            return True
            
        # Backup current settings
        self.backup_current_settings()
        
        # Get source file for new mode
        if new_mode == 'auto':
            source_file = self.settings_auto
        else:
            source_file = self.settings_manual
            
        if not source_file.exists():
            print(f"❌ Settings file not found: {source_file}")
            return False
            
        # Copy new settings
        try:
            shutil.copy2(source_file, self.settings_file)
            print(f"✓ Switched to {new_mode} mode")
            
            # Update state
            state['current_mode'] = new_mode
            state['last_toggle'] = datetime.now().isoformat()
            
            # Add to history
            if 'toggle_history' not in state:
                state['toggle_history'] = []
                
            state['toggle_history'].append({
                'from': current_mode,
                'to': new_mode,
                'timestamp': datetime.now().isoformat(),
                'reason': f"Manual toggle to {new_mode} mode"
            })
            
            # Keep only last 10 history entries
            state['toggle_history'] = state['toggle_history'][-10:]
            
            self.save_state(state)
            
            # Show mode features
            self.show_mode_info(new_mode, state)
            
            return True
            
        except Exception as e:
            print(f"❌ Error switching modes: {e}")
            return False
            
    def create_initial_state(self):
        """Create initial state file"""
        state = {
            "current_mode": "auto",
            "last_toggle": datetime.now().isoformat(),
            "modes": {
                "auto": {
                    "description": "Autonomous operation with 5 parallel terminals",
                    "file": "settings_auto.json",
                    "features": [
                        "No permission prompts for authorized commands",
                        "Up to 5 parallel terminal instances",
                        "Automatic script execution",
                        "Process management capabilities"
                    ]
                },
                "manual": {
                    "description": "Manual permission mode - original settings",
                    "file": "settings_manual.json",
                    "features": [
                        "Permission required for most operations",
                        "Limited automation capabilities",
                        "Basic file and git operations only"
                    ]
                }
            },
            "toggle_history": []
        }
        self.save_state(state)
        return state
        
    def show_mode_info(self, mode, state):
        """Display information about the current mode"""
        mode_info = state['modes'].get(mode, {})
        print(f"\n📋 {mode.upper()} Mode Active")
        print(f"   {mode_info.get('description', '')}")
        print("\n   Features:")
        for feature in mode_info.get('features', []):
            print(f"   • {feature}")
        print()
        
    def status(self):
        """Show current status"""
        state = self.load_state()
        if not state:
            print("⚠️  No state information available")
            return
            
        current_mode = state['current_mode']
        print(f"\n🔧 Claude Code Settings Status")
        print(f"   Current Mode: {current_mode.upper()}")
        print(f"   Last Toggle: {state.get('last_toggle', 'Unknown')}")
        
        self.show_mode_info(current_mode, state)
        
        # Show recent history
        history = state.get('toggle_history', [])
        if history:
            print("📜 Recent Toggle History:")
            for entry in history[-5:]:
                timestamp = entry['timestamp'].split('T')[0]
                print(f"   • {timestamp}: {entry['from']} → {entry['to']}")
        
    def verify_files(self):
        """Verify all required files exist"""
        print("\n🔍 Verifying settings files...")
        
        files_to_check = [
            (self.settings_file, "Current settings"),
            (self.settings_auto, "Auto mode settings"),
            (self.settings_manual, "Manual mode settings"),
            (self.state_file, "State tracker")
        ]
        
        all_good = True
        for file_path, description in files_to_check:
            if file_path.exists():
                print(f"   ✓ {description}: {file_path.name}")
            else:
                print(f"   ❌ {description}: Missing!")
                all_good = False
                
        return all_good


def main():
    """Main entry point"""
    toggle = ClaudeSettingsToggle()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            toggle.status()
        elif command == 'verify':
            toggle.verify_files()
        elif command in ['auto', 'manual']:
            toggle.toggle(target_mode=command)
        elif command == 'toggle':
            toggle.toggle()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python toggle_claude_settings.py [command]")
            print("\nCommands:")
            print("  status  - Show current mode and settings")
            print("  toggle  - Switch to opposite mode")
            print("  auto    - Switch to auto mode")
            print("  manual  - Switch to manual mode")
            print("  verify  - Verify all settings files exist")
    else:
        # Default action: show status
        toggle.status()
        print("\nTo toggle modes, run: python toggle_claude_settings.py toggle")


if __name__ == "__main__":
    main()