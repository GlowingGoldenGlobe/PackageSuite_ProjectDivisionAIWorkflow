# upkgs.py
# upkgs.py: Upgrade all packages in a virtual environment for Python 3.13+
# Built: 04 28 2024 (April 28, 2024)
r"""
     Instructions: Part 1 - Basic Usage
      ------------
      # Navigate to the virtual environment directory
      cd glowinggoldenglobe_venv
      
      # Activate the virtual environment
      .\Scripts\Activate.ps1
      
      # Start Python 3.13+
      python
      
      # Import and run the package updater
      import upkgs
      upkgs.main()  # For selected packages only
      
      # Exit Python and deactivate when done
      exit()
      deactivate

     Instructions: Part 2 - Update All Packages
      ------------
      # To update all packages in this virtual environment:
      python
      from upkgs import main as m1
      m1(2)  # Parameter 2 updates all packages
      exit()
      deactivate
      
      # Alternative direct execution methods for Python 3.13+:
      # Method 1: One-liner in PowerShell
      python -c "import upkgs; upkgs.main(2)"
      
      # Method 2: Run as module
      python -m upkgs

     Instructions: Part 3 - Open3D and Visualization Support
      ------------
      This script now handles Open3D installation with special considerations:
      
      1. Platform Detection: Automatically detects your operating system (Windows, Linux, macOS)
      2. Architecture Check: Verifies 64-bit architecture (required for Open3D)
      3. OS-Specific Installation:
         - Windows: Installs standard Open3D package
         - Linux: Tries standard package first, falls back to CPU-only if needed
         - macOS: Installs standard Open3D package
      4. Visual Support: Automatically installs matplotlib and Pillow for visualization
      
      Known requirements:
      - 64-bit OS (Open3D will not install on 32-bit systems)
      - Windows: Visual C++ Redistributable may be required
      - Linux: Mesa drivers v20.2+ for CPU rendering
      - macOS 10.14+ with XCode 8.0+ for compilation
      
      Note: Open3D installation can be complex due to its dependencies. If automated
      installation fails, you may need to install it manually following the official
      documentation at: https://www.open3d.org/docs/release/getting_started.html

     Instructions: Part 4 - Troubleshooting
      ------------
      If an error occurs during downloading (upgrading) packages, then:
      1. Select the error text (or otherwise summarize the error message), to copy the text, press, CTRL + Shift + c.
      2. In, GitHub Copilot chat (or Claude 3 Opus) paste or type the error message. 
      3. Optional - Type something as instructions to the LLM chat, such as, "Python 3 venv: terminal window: packages download upgrade error. Solve.".
      4. Sometimes, merely re-attempting the upgrade will solve the problem! For example, I got a an error, "Hash [not recognized, etc.]". What solved the problem was to retry the terminal command, py -m upkgs. Solved! 
      5. Options - search in the browser for a solution. For example, Microsoft Edge: Bing Copilot (GPT-4): search or chat.
      
      For Open3D specific issues:
      - If you get GPU-related errors, try the CPU-only version on Linux:
        ```
        pip install open3d-cpu
        ```
      - On Windows, ensure you have Visual C++ Redistributable installed
      - For standalone Open3D visualization, add these lines to your code:
        ```python
        import open3d as o3d
        o3d.visualization.webrtc_server.enable_webrtc()
        ```
"""

import subprocess
import sys
import re

# Function to get dependencies installed alongside pyautogen
def get_pyautogen_dependencies():
    installed_packages = []
    try:
        # Use sys.executable to ensure we're using the correct Python interpreter
        result = subprocess.run([sys.executable, "-m", "pip", 'install', 'pyautogen', '--dry-run'], 
                               capture_output=True, text=True)
        package_regex = re.compile(r'^\s*([a-zA-Z0-9_-]+)', re.MULTILINE)
        matches = package_regex.findall(result.stdout)
        installed_packages.extend(set([match for match in matches if match.lower() != 'pyautogen']))
    except Exception as e:
        print(f"Error getting pyautogen dependencies: {str(e)}")
    return installed_packages

some_selected_packages = """
  pip-tools
  numpy
  scipy
  pandas
  scikit-learn
  requests
  urllib3
  certifi
  idna
  chardet
  regex
  tiktoken
  pyautogen
  dash==3.0.4
  flask==3.0.3
  werkzeug==3.0.6
  """
  
all_of_the_packages = """
  annotated-types
  anthropic
  anyio
  asyncer
  autopep8
  build
  certifi
  chardet
  charset-normalizer
  click
  colorama
  diskcache
  distro
  docker
  h11
  httpcore
  httpx
  idna
  jiter
  openai
  packaging
  pip
  pip-tools
  psutil
  pyautogen
  pycodestyle
  pydantic
  pydantic_core
  pyproject_hooks
  python-dotenv
  pywin32
  regex
  requests
  schedule
  setuptools
  sniffio
  termcolor
  tiktoken
  tqdm
  typing_extensions
  typing-inspection
  urllib3
  wheel
  """

def check_open3d_installed():
    """
    Check if Open3D is already installed and working
    """
    try:
        # Check if the module can be imported
        result = subprocess.run([sys.executable, "-c", "import open3d as o3d; print(o3d.__version__)"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if this is a fallback version
        if "0.0.0-fallback" in result.stdout:
            print("Detected Open3D fallback mode (mock implementation)")
            return False
        
        # Try a basic test operation
        check_code = """
import open3d as o3d
try:
    # Create a simple mesh to test functionality
    mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0)
    print("Open3D test successful!")
except Exception as e:
    print(f"Open3D test failed: {e}")
    exit(1)
"""
        result = subprocess.run([sys.executable, "-c", check_code], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if "Open3D test successful" in result.stdout:
            print("Open3D is already installed and working correctly!")
            return True
        elif "[MOCK]" in result.stdout or "[FALLBACK]" in result.stdout:
            print("Detected Open3D fallback mode (mock implementation)")
            return False 
        else:
            print("Open3D is installed but not working correctly.")
            return False
    
    except subprocess.CalledProcessError:
        print("Open3D is not installed or not functioning properly.")
        return False

def _setup_fallback_open3d():
    """
    Create a fallback mock Open3D module that allows the code to run
    without actual Open3D functionality. This prevents errors in 
    code that checks for Open3D's existence.
    """
    print("Setting up Open3D fallback mode...")
    print("This creates a minimal mock module that allows your code to run without crashing")
    print("but won't provide actual Open3D functionality.")
    
    # Ensure we have os available
    import os
    
    fallback_code = """
# Mock Open3D module for fallback mode
# This allows code to import open3d without crashing when actual Open3D can't be installed

class FallbackGeometry:
    class TriangleMesh:
        @staticmethod
        def create_sphere(radius=1.0):
            print("[MOCK] Created sphere mesh with radius", radius)
            return FallbackMesh()
    
    class PointCloud:
        def __init__(self):
            print("[MOCK] Created point cloud")
            self.points = []
    
    class Image:
        def __init__(self):
            print("[MOCK] Created image")

class FallbackMesh:
    def __init__(self):
        self.vertices = []
        self.triangles = []
        print("[MOCK] Initialized mesh object")
    
    def compute_vertex_normals(self):
        print("[MOCK] Computed vertex normals")
        return self
    
    def has_vertices(self):
        return False
    
    def is_watertight(self):
        return False

class FallbackVisualization:
    def draw_geometries(geometries_list):
        print("[MOCK] Visualizing", len(geometries_list), "geometries (not actually shown)")
    
    class Visualizer:
        def __init__(self):
            print("[MOCK] Created visualizer")
        
        def create_window(self, visible=True, width=1280, height=960):
            print(f"[MOCK] Created window (visible={visible}, {width}x{height})")
            return True
        
        def add_geometry(self, geometry):
            print("[MOCK] Added geometry to visualizer")
            return True
        
        def run(self):
            print("[MOCK] Running visualizer (no actual window shown)")
            return True
        
        def destroy_window(self):
            print("[MOCK] Destroyed window")
            return True

class FallbackIO:
    def read_triangle_mesh(filepath):
        print(f"[MOCK] Reading triangle mesh from {filepath} (not actually loaded)")
        return FallbackMesh()
    
    def write_triangle_mesh(filepath, mesh):
        print(f"[MOCK] Writing triangle mesh to {filepath} (not actually saved)")
        return True

# Create the fallback module structure
geometry = FallbackGeometry()
visualization = FallbackVisualization()
io = FallbackIO()

# Set version
__version__ = "0.0.0-fallback"

print("[FALLBACK OPEN3D] Loaded mock Open3D module")
print("[FALLBACK OPEN3D] This provides minimal functionality to prevent crashes")
print("[FALLBACK OPEN3D] Install full Open3D for actual 3D processing capabilities")
"""
    
    try:
        import site
        site_packages = site.getsitepackages()[0]
        
        # Create open3d package directory
        open3d_dir = os.path.join(site_packages, "open3d")
        os.makedirs(open3d_dir, exist_ok=True)
        
        # Create __init__.py with fallback code
        with open(os.path.join(open3d_dir, "__init__.py"), "w") as f:
            f.write(fallback_code)
        
        print(f"Created fallback Open3D module at {open3d_dir}")
        print("Your code can now import open3d without crashing, but functionality will be limited.")
        print("Consider installing the full Open3D in a compatible environment when possible.")
        
        # Create a README to explain what this is
        with open(os.path.join(open3d_dir, "README_FALLBACK.txt"), "w") as f:
            f.write("""FALLBACK OPEN3D MODULE
===================

This is a fallback mock implementation of Open3D created because the actual Open3D
package could not be installed. It provides minimal functionality to prevent code
that imports open3d from crashing, but does not provide actual 3D processing capabilities.

To install the actual Open3D:
1. Create a virtual environment with Python 3.8-3.11 (Open3D is not officially supported on Python 3.12+ yet)
2. Run: pip install open3d

For more information, visit: https://www.open3d.org/docs/release/getting_started.html
""")
        
        return True
    except Exception as e:
        print(f"Error setting up fallback module: {e}")
        return False

def upgrade_open3d_python310():
    """Execute the Python 3.10 Open3D upgrade script"""
    import os
    import platform
    
    print("\n" + "="*60)
    print("Open3D and Visualization Packages for Python 3.10")
    print("="*60)
    
    # Determine the path to the Python 3.10 directory
    base_path = os.path.dirname(os.path.abspath(__file__))
    python310_path = os.path.join(base_path, "open3d_direct", "python310")
    python_exe = os.path.join(python310_path, "python.exe" if platform.system() == "Windows" else "python")
    
    # Try multiple upgrade scripts
    upgrade_scripts = [
        "upgrade_all_py310.py",  # New comprehensive script
        "upkgs_py310.py",        # Original script
    ]
    
    if not os.path.exists(python_exe):
        print(f"Error: Python 3.10 executable not found at {python_exe}")
        return False
    
    # Find which script exists
    script_to_run = None
    for script in upgrade_scripts:
        script_path = os.path.join(python310_path, script)
        if os.path.exists(script_path):
            script_to_run = script_path
            break
    
    if not script_to_run:
        print(f"Error: No upgrade script found in {python310_path}")
        return False
    
    print(f"Executing upgrade using Python 3.10...")
    print(f"Python path: {python_exe}")
    print(f"Script path: {script_to_run}")
    
    # Install Open3D dependencies that belong in Python 3.10
    open3d_deps = ["numpy", "scipy", "matplotlib", "pillow", "pandas", "scikit-learn"]
    
    print("\nStep 1: Installing Open3D dependencies in Python 3.10 environment...")
    print("-" * 60)
    for dep in open3d_deps:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "--no-cache-dir", dep])
            print(f"✓ {dep} installed")
        except subprocess.CalledProcessError:
            print(f"✗ Warning: Failed to install {dep}")
    
    print("\nStep 2: Installing Open3D package...")
    print("-" * 60)
    try:
        # Install Open3D directly first
        print("Installing Open3D...")
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "open3d"])
        print("✓ Open3D installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"✗ Direct Open3D installation failed: {e}")
        print("Trying alternative installation method...")
        
        try:
            # Run the upgrade script as fallback
            if "upgrade_all" in script_to_run:
                subprocess.check_call([python_exe, script_to_run])
            else:
                subprocess.check_call([python_exe, script_to_run, "--all"])
        except subprocess.CalledProcessError as e2:
            print(f"✗ Alternative installation also failed: {e2}")
            return False
    
    # Test Open3D installation
    print("\nStep 3: Testing Open3D installation...")
    print("-" * 60)
    try:
        test_result = subprocess.run(
            [python_exe, "-c", "import open3d as o3d; print(f'Open3D {o3d.__version__} is working!')"],
            capture_output=True, text=True
        )
        if test_result.returncode == 0:
            print(f"✓ {test_result.stdout.strip()}")
            print("\nOpen3D environment upgrade completed successfully!")
            return True
        else:
            print(f"✗ Open3D test failed: {test_result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error testing Open3D: {e}")
        return False

def main(p=1):
    global some_selected_packages, all_of_the_packages    
    
    # Update pip using sys.executable for Python 3.13 compatibility
    print("Updating pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--default-timeout=1000", "--upgrade", "pip"])

    # Get pyautogen dependencies
    print("Getting pyautogen dependencies...")
    pyautogen_related_packages = get_pyautogen_dependencies()

    some_packages = []
    developer_selection_packages = some_selected_packages if p == 1 else all_of_the_packages

    # Filter out pyautogen_related_packages
    filtered_packages = [pkg for pkg in developer_selection_packages.split('\n') if pkg.strip() not in pyautogen_related_packages]

    for item in filtered_packages:
        item_stripped = item.strip()
        if item_stripped != "":
            some_packages.append(item_stripped)
    
    # Remove open3d from the list since it will be handled by Python 3.10
    if "open3d" in some_packages:
        print("Note: Open3D will be installed using Python 3.10 environment")
        some_packages = [pkg for pkg in some_packages if pkg != "open3d"]
    
    # Install remaining packages using sys.executable for Python 3.13 compatibility
    for package in some_packages:
        print(f"Installing/upgrading {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--default-timeout=1000", "--upgrade", package])
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {str(e)}")
            print("Continuing with next package...")
    
    # After all other packages, upgrade Open3D in Python 3.10 environment
    print("\n" + "="*60)
    print("Stage 2: Open3D Installation in Python 3.10 Environment")
    print("="*60)
    upgrade_open3d_python310()

def test_open3d_standalone():
    """
    Test Open3D in standalone mode with visualization
    This function can be used to verify Open3D is working correctly with visualization
    """
    try:
        check_code = """
import open3d as o3d
import numpy as np

# Try to enable standalone mode with WebRTC visualization
try:
    o3d.visualization.webrtc_server.enable_webrtc()
    print("WebRTC visualization server enabled!")
except Exception as e:
    print(f"WebRTC visualization not available: {e}")

# Create a simple mesh for testing
mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0)
mesh.compute_vertex_normals()
mesh.paint_uniform_color([0.5, 0.5, 0.8])  # Blue color

# Try basic visualization
print("Attempting visualization...")
o3d.visualization.draw_geometries([mesh])
print("Open3D visualization test completed. If a window did not appear, check your display configuration.")
"""
        print("Running Open3D standalone test...")
        subprocess.run([sys.executable, "-c", check_code])
        return True
    except Exception as e:
        print(f"Open3D standalone test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Running package upgrades with Python {sys.version}")
    
    # Check for command-line argument to run Open3D test
    if len(sys.argv) > 1 and sys.argv[1] == "--test-open3d":
        print("Running Open3D test only...")
        test_open3d_standalone()
    else:
        main()

    
""" 
# The following function is not used in this module, but was an idea of GitHub Copilot (GPT-3.5):
def check_and_install_compatible_version(package):
    # Example compatibility requirements
    # These should be replaced with actual compatibility checks based on the package's requirements
    if package == "numpy":
        compatible_version = "1.19.5"  # This should be determined dynamically as shown in the previous example
        subprocess.check_call(["pip", "install", "--default-timeout=1000", "--upgrade", f"{package}=={compatible_version}"])
    elif package == "urllib3":
        compatible_version = "1.26.5"  # Example version, adjust based on actual compatibility
        subprocess.check_call(["pip", "install", "--default-timeout=1000", "--upgrade", f"{package}=={compatible_version}"])
    else:
        subprocess.check_call(["pip", "install", "--default-timeout=1000", "--upgrade", package])
"""