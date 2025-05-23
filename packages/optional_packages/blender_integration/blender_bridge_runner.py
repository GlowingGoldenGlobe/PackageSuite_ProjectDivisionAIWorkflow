"""
blender_bridge_runner.py - A bridge script to run Agent1_Part1.py functionality in Blender
This script creates a simplified version of the agent that works within Blender's environment
without requiring external dependencies like autogen.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def get_blender_path():
    """Get the path to Blender executable"""
    try:
        result = subprocess.run(
            ["where", "blender"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        blender_paths = result.stdout.strip().split('\n')
        if blender_paths:
            return blender_paths[0]
    except subprocess.CalledProcessError:
        pass
    
    possible_paths = [
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def create_blender_execution_script():
    """Create a script that will be executed by Blender"""
    script_content = """
import bpy
import os
import sys
import json
import time

def setup_environment():
    \"\"\"Setup the Blender environment\"\"\"
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Create output directories
    current_dir = os.path.dirname(bpy.data.filepath)
    if not current_dir:
        current_dir = os.getcwd()
        
    output_dir = os.path.join(current_dir, "agent_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Environment setup complete. Output directory: {output_dir}")
    return output_dir

def create_micro_robot_composite_part(data):
    # Create a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=1)
    cube = bpy.context.active_object
    cube.name = "MicroRobotPart"
    
    # Apply dimensions from data
    dimensions = data.get("dimensions", {"length": 10, "width": 5, "height": 3})
    cube.scale = (
        dimensions.get("length", 10) * 0.1, 
        dimensions.get("width", 5) * 0.1, 
        dimensions.get("height", 3) * 0.1
    )
    
    # Setup physics properties
    try:
        bpy.ops.rigidbody.object_add()
        cube.rigid_body.mass = 0.01
        cube.rigid_body.friction = 0.7
    cube.rigid_body.restitution = 0.3  # Bounciness
    
    # Create a simple material based on the first material in the data
    materials = data.get("materials", ["aluminum"])
    if materials:
        mat = bpy.data.materials.new(name=materials[0])
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # Set color based on material type
        if "aluminum" in materials[0].lower():
            nodes["Principled BSDF"].inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)  # Silver
        elif "plastic" in materials[0].lower():
            nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.2, 0.8, 1.0)  # Blue plastic
        elif "copper" in materials[0].lower():
            nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.5, 0.2, 1.0)  # Copper
        else:
            nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)  # Default gray
        
        # Assign material to cube
        if cube.data.materials:
            cube.data.materials[0] = mat
        else:
            cube.data.materials.append(mat)
    
    print(f"Created MicroRobotPart with dimensions: {dimensions}")
    return cube

def setup_camera_and_lighting():
    """Setup camera and lighting for rendering"""
    # Add a camera
    bpy.ops.object.camera_add(location=(0, -20, 10))
    camera = bpy.context.active_object
    camera.rotation_euler = (0.7, 0, 0)  # Point at the center
    bpy.context.scene.camera = camera
    
    # Add lighting - a sun and two area lights
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
    area1 = bpy.context.active_object
    area1.data.energy = 30.0
    
    bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
    area2 = bpy.context.active_object
    area2.data.energy = 30.0
    
    print("Camera and lighting setup complete")

def setup_physics_environment():
    """Setup physics environment for testing"""
    # Create a ground plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -2))
    plane = bpy.context.active_object
    plane.name = "Ground"
    
    # Add physics to the plane
    bpy.ops.rigidbody.object_add()
    plane.rigid_body.type = 'PASSIVE'  # Non-moving collision object
    plane.rigid_body.friction = 0.5
    
    # Enable rigid body world
    bpy.ops.rigidbody.world_add()
    bpy.context.scene.rigidbody_world.time_scale = 1.0
    
    print("Physics environment setup complete")

def run_physics_simulation(frames=250):
    """Run the physics simulation"""
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frames
    
    # Keyframe the initial state
    bpy.context.scene.frame_set(1)
    for obj in bpy.data.objects:
        if obj.rigid_body:
            obj.keyframe_insert(data_path="location")
            obj.keyframe_insert(data_path="rotation_euler")
    
    # Run the simulation by advancing frames
    print("Running physics simulation...")
    for frame in range(1, frames + 1):
        bpy.context.scene.frame_set(frame)
        if frame % 50 == 0:
            print(f"Simulating frame {frame}/{frames}")
    
    print("Physics simulation completed")
    
    # Bake the simulation if needed
    # bpy.ops.ptcache.bake_all(bake=True)
    # print("Physics simulation baked")

def save_outputs(output_dir, version=1):
    """Save the rendered images and model files"""
    # Setup rendering
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.samples = 32  # Lower for faster rendering
    
    # Render from different angles
    angles = [(0, 0), (0, 90), (0, 180), (0, 270)]  # (rotation_z, rotation_x)
    camera = bpy.context.scene.camera
    
    for i, (rot_z, rot_x) in enumerate(angles):
        # Position camera
        camera.rotation_euler = (rot_x * 3.14159 / 180, 0, rot_z * 3.14159 / 180)
        camera.location = (0, -15, 10)
        
        # Render
        render_path = os.path.join(output_dir, f"micro_robot_part_v{version}_angle{i}.png")
        bpy.context.scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered view {i+1} to {render_path}")
    
    # Save the blend file
    blend_file = os.path.join(output_dir, f"micro_robot_composite_part_v{version}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_file)
    print(f"Saved blend file to {blend_file}")
      # Export to various formats - check and enable addons if needed
    try:
        # Try to enable necessary add-ons for export
        bpy.ops.preferences.addon_enable(module="io_scene_fbx")
        bpy.ops.preferences.addon_enable(module="io_scene_obj")
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
        bpy.ops.preferences.addon_enable(module="io_mesh_ply")
    except Exception as e:
        print(f"Note: Could not enable export add-ons: {str(e)}")
        
    export_formats = [
        {"format": "fbx", "operator": bpy.ops.export_scene.fbx},
        {"format": "obj", "operator": bpy.ops.export_scene.obj},
        {"format": "stl", "operator": bpy.ops.export_mesh.stl},
        {"format": "ply", "operator": bpy.ops.export_mesh.ply}
    ]
    
    # Select the robot part for export
    bpy.ops.object.select_all(action='DESELECT')
    robot_part = bpy.data.objects.get("MicroRobotPart")
    if robot_part:
        robot_part.select_set(True)
        bpy.context.view_layer.objects.active = robot_part
        
        for export_info in export_formats:
            file_format = export_info["format"]
            try:
                export_path = os.path.join(output_dir, f"micro_robot_composite_part_v{version}.{file_format}")
                if hasattr(export_info["operator"], "__call__"):
                    export_info["operator"](filepath=export_path)
                    print(f"Exported {file_format} to {export_path}")
            except Exception as e:
                print(f"Failed to export {file_format}: {str(e)}")

def main():
    """Main entry point for the Blender script"""
    print("Starting micro-robot-composite part generation in Blender...")
    
    # Setup the environment
    output_dir = setup_environment()
    
    # Load model data
    model_data = {}
    try:        current_dir = os.path.dirname(bpy.data.filepath)
        if not current_dir:
            current_dir = os.getcwd()
            
        data_file = os.path.join(current_dir, "agent_outputs", "micro_robot_composite_part_v1.json")
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                model_data = json.load(f)
                print(f"Loaded model data from {data_file}")
        else:
            # Default data if file not found
            model_data = {
                "dimensions": {
                    "length": 10,
                    "width": 5,
                    "height": 3
                },
                "materials": [
                    "aluminum",
                    "plastic",
                    "copper"
                ]
            }
            print(f"Using default model data (file not found: {data_file})")
    except Exception as e:
        print(f"Error loading model data: {str(e)}")
        model_data = {
            "dimensions": {
                "length": 10,
                "width": 5,
                "height": 3
            },
            "materials": [
                "aluminum"
            ]
        }
    
    # Create the parts
    robot_part = create_micro_robot_composite_part(model_data)
    
    # Setup camera and lighting
    setup_camera_and_lighting()
    
    # Setup physics environment
    setup_physics_environment()
    
    # Run physics simulation
    run_physics_simulation(frames=100)  # Reduced for faster execution
    
    # Save outputs
    save_outputs(output_dir, version=1)
    
    print("Blender execution completed successfully")

# Run the main function
main()
"""
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_execution_script.py")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    print(f"Created Blender execution script at: {script_path}")
    return script_path

def run_blender_bridge():
    """Run the Agent1_Part1.py functionality using Blender"""
    print("Starting Blender bridge runner...")
    
    # Get Blender path
    blender_path = get_blender_path()
    if not blender_path:
        print("Error: Blender executable not found.")
        return False
    
    print(f"Found Blender at: {blender_path}")
    
    # Create the Blender execution script
    execution_script = create_blender_execution_script()
      # Create or update the JSON data file for the model
    model_data = {
        "dimensions": {
            "length": 10,
            "width": 5,
            "height": 3
        },
        "materials": [
            "aluminum",
            "plastic",
            "copper"
        ],
        "design_principles": {
            "stress_capacity": 100,
            "weight_capacity": 50
        },
        "motion_capabilities": {
            "speed": 5,
            "degrees_of_freedom": 3
        },
        "energy_source": {
            "type": "wireless",
            "power_capacity": 500,
            "current_capacity": 100
        },
        "control_mechanism": "ROS2 API"
    }
    
    # Create agent_outputs directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON to agent_outputs directory instead of root
    json_path = os.path.join(output_dir, "micro_robot_composite_part_v1.json")
    with open(json_path, "w") as f:
        json.dump(model_data, f, indent=4)
    
    print(f"Created model data JSON at: {json_path}")
    
    # Run Blender with the execution script
    cmd = [blender_path, "--background", "--python", execution_script]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            
            if output == '' and error == '' and process.poll() is not None:
                break
                
            if output:
                print(output.strip())
            if error:
                print(f"ERROR: {error.strip()}", file=sys.stderr)
                
        # Get the return code
        return_code = process.poll()
        
        if return_code == 0:
            print("\nBlender execution completed successfully.")
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_outputs")
            print(f"Check {output_dir} for rendered images and exported models.")
            return True
        else:
            print(f"\nBlender execution failed with return code {return_code}")
            return False
            
    except Exception as e:
        print(f"Error running Blender: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if run_blender_bridge() else 1)
