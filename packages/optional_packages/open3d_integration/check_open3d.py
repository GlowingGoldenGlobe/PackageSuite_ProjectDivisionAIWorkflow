#!/usr/bin/env python3
"""
Open3D Availability Checker
==========================

This script checks if Open3D is available and working correctly.
It provides functions to:
1. Check if Open3D is installed
2. Verify if it has visualization capabilities
3. Test basic functionality
4. Handle fallbacks gracefully

Usage:
    import check_open3d
    is_available = check_open3d.is_open3d_available()
    has_visualization = check_open3d.has_visualization_capability()
    mesh = check_open3d.get_test_mesh()  # Returns a mesh or None if unavailable
"""

import importlib
import sys
import platform
import subprocess
from pathlib import Path

# Cache results to avoid repeated checks
_OPEN3D_AVAILABLE = None
_OPEN3D_VISUALIZATION = None
_OPEN3D_VERSION = None
_IS_FALLBACK = None

def is_open3d_available():
    """
    Check if Open3D is available and properly installed.
    
    Returns:
        bool: True if Open3D is available and working, False otherwise
    """
    global _OPEN3D_AVAILABLE, _OPEN3D_VERSION, _IS_FALLBACK
    
    if _OPEN3D_AVAILABLE is not None:
        return _OPEN3D_AVAILABLE
    
    try:
        import open3d as o3d
        _OPEN3D_VERSION = o3d.__version__
        
        # Check if this is a fallback implementation
        if _OPEN3D_VERSION == "0.0.0-fallback" or hasattr(o3d, "_IS_FALLBACK_MODULE"):
            print("Detected Open3D fallback mode (minimal implementation)")
            _IS_FALLBACK = True
            _OPEN3D_AVAILABLE = False
            return False
        
        # Test basic functionality by creating a simple mesh
        try:
            mesh = o3d.geometry.TriangleMesh.create_sphere()
            if not hasattr(mesh, 'vertices') or not hasattr(mesh, 'triangles'):
                print("Open3D seems to be partially working but missing expected attributes")
                _OPEN3D_AVAILABLE = False
                return False
                
            _OPEN3D_AVAILABLE = True
            _IS_FALLBACK = False
            return True
        except Exception as e:
            print(f"Open3D is installed but not functioning correctly: {str(e)}")
            _OPEN3D_AVAILABLE = False
            return False
            
    except ImportError:
        print("Open3D is not installed")
        _OPEN3D_AVAILABLE = False
        return False
    except Exception as e:
        print(f"Unexpected error checking Open3D: {str(e)}")
        _OPEN3D_AVAILABLE = False
        return False

def has_visualization_capability():
    """
    Check if Open3D's visualization capabilities are available.
    
    Returns:
        bool: True if Open3D visualization is available, False otherwise
    """
    global _OPEN3D_VISUALIZATION
    
    if _OPEN3D_VISUALIZATION is not None:
        return _OPEN3D_VISUALIZATION
    
    if not is_open3d_available():
        _OPEN3D_VISUALIZATION = False
        return False
    
    try:
        import open3d as o3d
        
        # Check for visualization module
        if not hasattr(o3d, 'visualization'):
            print("Open3D visualization module is not available")
            _OPEN3D_VISUALIZATION = False
            return False
        
        # Check if we're in a headless environment
        is_headless = False
        if platform.system() == 'Linux':
            # Check for display on Linux
            try:
                import os
                if 'DISPLAY' not in os.environ:
                    is_headless = True
            except:
                pass
                
        # If in headless environment, check for offscreen rendering capability
        if is_headless:
            # Just having the o3d.visualization module is enough for headless rendering
            _OPEN3D_VISUALIZATION = True
            return True
        
        # For non-headless, further check visualization functionality
        try:
            if hasattr(o3d.visualization, 'Visualizer'):
                # Check if creating a visualizer works (but don't create window)
                vis = o3d.visualization.Visualizer()
                _OPEN3D_VISUALIZATION = True
                return True
            else:
                print("Open3D Visualizer class is not available")
                _OPEN3D_VISUALIZATION = False
                return False
        except Exception as e:
            print(f"Error testing Open3D visualization: {str(e)}")
            _OPEN3D_VISUALIZATION = False
            return False
            
    except Exception as e:
        print(f"Error checking Open3D visualization capability: {str(e)}")
        _OPEN3D_VISUALIZATION = False
        return False

def get_test_mesh():
    """
    Create and return a test mesh to verify Open3D functionality.
    
    Returns:
        object or None: An Open3D mesh object if available, or None if unavailable
    """
    if not is_open3d_available():
        return None
    
    try:
        import open3d as o3d
        mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0)
        mesh.compute_vertex_normals()
        return mesh
    except Exception as e:
        print(f"Error creating test mesh: {str(e)}")
        return None

def get_version_info():
    """
    Get detailed information about the Open3D installation.
    
    Returns:
        dict: Dictionary with Open3D version information
    """
    info = {
        'available': is_open3d_available(),
        'version': _OPEN3D_VERSION,
        'is_fallback': _IS_FALLBACK,
        'has_visualization': has_visualization_capability(),
        'platform': platform.system(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    
    # Add specific platform information
    if platform.system() == 'Windows':
        try:
            import ctypes
            info['is_64bit'] = platform.architecture()[0] == '64bit'
            info['has_opengl'] = ctypes.windll.opengl32 is not None
        except:
            pass
    elif platform.system() == 'Linux':
        try:
            import os
            info['has_display'] = 'DISPLAY' in os.environ
            # Check for Mesa
            try:
                glxinfo = subprocess.check_output(['glxinfo'], stderr=subprocess.DEVNULL).decode('utf-8')
                if 'Mesa' in glxinfo:
                    info['renderer'] = 'Mesa'
            except:
                pass
        except:
            pass
            
    return info

def render_test_image(output_path=None, show_window=False):
    """
    Render a test image to verify Open3D rendering capabilities.
    
    Args:
        output_path (str, optional): Path to save the rendered image
        show_window (bool, optional): Whether to show a window during rendering
        
    Returns:
        bool: True if rendering succeeded, False otherwise
    """
    if not is_open3d_available() or not has_visualization_capability():
        return False
    
    if output_path is None:
        output_path = "open3d_test_render.png"
    
    try:
        import open3d as o3d
        mesh = get_test_mesh()
        
        if show_window:
            # Interactive window rendering
            o3d.visualization.draw_geometries([mesh])
            return True
        else:
            # Offscreen rendering
            vis = o3d.visualization.Visualizer()
            vis.create_window(visible=False)
            vis.add_geometry(mesh)
            vis.update_geometry(mesh)
            vis.poll_events()
            vis.update_renderer()
            vis.capture_screen_image(output_path)
            vis.destroy_window()
            
            # Check if file was created
            if Path(output_path).exists():
                print(f"Test image saved to {output_path}")
                return True
            else:
                print("Failed to create test image")
                return False
                
    except Exception as e:
        print(f"Error during rendering test: {str(e)}")
        return False

def recommended_installation_method():
    """
    Recommend the best installation method based on the current system.
    
    Returns:
        str: Recommended installation instructions
    """
    system = platform.system()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    if is_open3d_available():
        return "Open3D is already installed and working correctly."
    
    if system == 'Windows':
        if float(python_version) > 3.11:
            return (
                "On Windows with Python {python_version}:\n"
                "1. Consider creating a Python 3.10 or 3.11 virtual environment for Open3D\n"
                "2. Or use the build_open3d_direct.bat script for a custom build"
            )
        else:
            return (
                f"On Windows with Python {python_version}:\n"
                "pip install open3d"
            )
    elif system == 'Linux':
        if float(python_version) > 3.11:
            return (
                f"On Linux with Python {python_version}:\n"
                "1. Try installing with: pip install open3d\n"
                "2. If that fails, try: pip install open3d-cpu\n"
                "3. For advanced users: Use build_open3d.sh script"
            )
        else:
            return (
                f"On Linux with Python {python_version}:\n"
                "pip install open3d\n"
                "# If that fails, try: pip install open3d-cpu"
            )
    elif system == 'Darwin':  # macOS
        if float(python_version) > 3.11:
            return (
                f"On macOS with Python {python_version}:\n"
                "1. Try installing with: pip install open3d\n"
                "2. If that fails, consider creating a Python 3.10 or 3.11 environment"
            )
        else:
            return (
                f"On macOS with Python {python_version}:\n"
                "pip install open3d"
            )
    else:
        return (
            "For your platform, please check the Open3D documentation at:\n"
            "https://www.open3d.org/docs/release/getting_started.html"
        )

if __name__ == "__main__":
    print("=" * 50)
    print("Open3D Availability Checker")
    print("=" * 50)
    
    print(f"System: {platform.system()} {platform.version()}")
    print(f"Python: {sys.version}")
    print()
    
    if is_open3d_available():
        import open3d as o3d
        print(f"Open3D version: {o3d.__version__}")
        print("Open3D is available and basic functionality is working!")
        
        if has_visualization_capability():
            print("Visualization capabilities are available")
            
            # Ask if user wants to render a test image
            try:
                choice = input("Would you like to render a test image? (y/n): ").strip().lower()
                if choice.startswith('y'):
                    interactive = input("Show interactive window? (y/n): ").strip().lower().startswith('y')
                    render_test_image(show_window=interactive)
            except:
                # Handle keyboard interrupt or other issues
                pass
        else:
            print("Visualization capabilities are NOT available")
    else:
        print("Open3D is NOT available or not functioning correctly")
        print("\nRecommended installation method:")
        print(recommended_installation_method())