#!/usr/bin/env python3
"""Deployment checker for hardware health optimization package

Ensures package only installs on appropriate local systems.
"""

import os
import sys
import platform

def is_local_deployment() -> bool:
    """Check if running on local hardware (not cloud)"""
    # Check for cloud environment variables
    cloud_indicators = [
        "AWS_EXECUTION_ENV",
        "AWS_LAMBDA_FUNCTION_NAME",
        "AZURE_FUNCTIONS_ENVIRONMENT",
        "WEBSITE_INSTANCE_ID",  # Azure App Service
        "GCP_PROJECT",
        "GOOGLE_CLOUD_PROJECT",
        "KUBERNETES_SERVICE_HOST",
        "ECS_CONTAINER_METADATA_URI",
        "DYNO",  # Heroku
        "VCAP_APPLICATION"  # Cloud Foundry
    ]
    
    if any(os.environ.get(var) for var in cloud_indicators):
        return False
    
    # Check for virtualization/containerization
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read() or 'lxc' in f.read():
                return False
    except:
        pass
    
    # Check hostname patterns
    hostname = platform.node().lower()
    cloud_patterns = ['ec2', 'compute', 'vm-', 'instance-', 'gke-', 'aks-']
    if any(pattern in hostname for pattern in cloud_patterns):
        return False
        
    return True

def check_gpu_memory() -> bool:
    """Check if system has minimum GPU memory"""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        
        # Check for 4GB minimum (in bytes)
        return mem_info.total >= 4 * 1024 * 1024 * 1024
    except:
        # No NVIDIA GPU or pynvml not available
        return False

def main():
    """Run deployment checks"""
    print("Hardware Health Optimization - Deployment Check")
    print("=" * 50)
    
    # Check if local deployment
    if not is_local_deployment():
        print("❌ Cloud environment detected - package not suitable for cloud deployments")
        print("   Cloud providers manage their own hardware optimization")
        sys.exit(1)
    
    print("✓ Local deployment confirmed")
    
    # Check GPU
    if check_gpu_memory():
        print("✓ GPU with sufficient memory detected")
    else:
        print("⚠ No suitable GPU found - thermal optimization will be CPU-only")
    
    # Check OS
    os_name = platform.system()
    if os_name in ['Windows', 'Linux']:
        print(f"✓ Supported OS: {os_name}")
    else:
        print(f"⚠ Untested OS: {os_name} - some features may not work")
    
    print("\n✅ Deployment checks passed - package can be installed")
    return 0

if __name__ == "__main__":
    sys.exit(main())