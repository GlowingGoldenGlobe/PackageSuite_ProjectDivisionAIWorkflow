"""
Network troubleshooting utility for WSL2/VS Code.

For comprehensive repair (including DNS, .wslconfig, and VS Code settings), see:
- fix_network_connections.ps1 (project root)

Do not run the PowerShell script while WSL2/Claude Code tasks are active.
"""

"""
Network Troubleshooter Utility
Handles socket hang up and other network connectivity issues

Run as Administrator for full functionality
"""

import os
import sys
import subprocess
import platform

def is_admin():
    """Check if script is running with admin privileges"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    return os.getuid() == 0  # Unix/Linux

def reset_network_winsock():
    """Reset Windows network stack - requires admin"""
    if platform.system() != 'Windows':
        print("This function is for Windows only")
        return False
    
    print("Resetting Windows network stack...")
    try:
        # Reset winsock
        result = subprocess.run(['netsh', 'winsock', 'reset'], 
                              capture_output=True, text=True)
        print(f"Winsock reset: {result.stdout}")
        
        # Flush DNS
        result = subprocess.run(['ipconfig', '/flushdns'], 
                              capture_output=True, text=True)
        print(f"DNS flush: {result.stdout}")
        
        # Reset TCP/IP stack
        result = subprocess.run(['netsh', 'int', 'ip', 'reset'], 
                              capture_output=True, text=True)
        print(f"TCP/IP reset: {result.stdout}")
        
        print("\nNetwork reset complete. Please restart your computer.")
        return True
        
    except Exception as e:
        print(f"Error resetting network: {e}")
        return False

def restart_wsl():
    """Restart WSL to apply network settings"""
    if platform.system() != 'Windows':
        print("WSL is only available on Windows")
        return False
    
    print("Restarting WSL...")
    try:
        result = subprocess.run(['wsl', '--shutdown'], 
                              capture_output=True, text=True)
        print("WSL shutdown complete")
        return True
    except Exception as e:
        print(f"Error restarting WSL: {e}")
        return False

def test_connectivity():
    """Test network connectivity"""
    test_sites = [
        "https://github.com",
        "https://api.anthropic.com",
        "https://www.google.com"
    ]
    
    print("Testing network connectivity...")
    for site in test_sites:
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['curl', '-I', site], 
                                      capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(['curl', '-I', site], 
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ {site} - Reachable")
            else:
                print(f"✗ {site} - Not reachable")
        except Exception as e:
            print(f"✗ {site} - Error: {e}")

def fix_socket_hang_up():
    """Main function to fix socket hang up errors"""
    print("=== Network Socket Hang Up Troubleshooter ===\n")
    
    # Check if running as admin
    if not is_admin():
        print("WARNING: Not running as administrator.")
        print("Some functions may not work properly.")
        print("Please run this script as administrator for full functionality.\n")
    
    # 1. Restart WSL
    print("Step 1: Restarting WSL...")
    restart_wsl()
    
    # 2. Test connectivity
    print("\nStep 2: Testing network connectivity...")
    test_connectivity()
    
    # 3. Reset network if admin
    if is_admin():
        print("\nStep 3: Resetting network stack (admin only)...")
        response = input("Reset Windows network stack? This requires a restart. (y/n): ")
        if response.lower() == 'y':
            reset_network_winsock()
    else:
        print("\nStep 3: Network reset skipped (requires admin)")
        print("To reset network stack, run as administrator")
    
    print("\n=== Troubleshooting Complete ===")
    print("\nAdditional steps:")
    print("1. Restart VS Code")
    print("2. Check VS Code settings.json has network config")
    print("3. Check ~/.wslconfig has network optimization")
    print("4. If issues persist, wait for network conditions to improve")
    print("   (Recent solar activity may affect connectivity)")

if __name__ == "__main__":
    fix_socket_hang_up()