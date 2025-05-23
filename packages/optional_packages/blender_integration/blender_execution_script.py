
import bpy
import os
import sys
import json
import time

def setup_environment():
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
    except Exception as e:
        print(f"Warning: Could not add rigid body physics: {str(e)}")
    
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
    # Create a ground plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -2))
    plane = bpy.context.active_object
    plane.name = "Ground"
    
    # Add physics to the plane
    try:
        bpy.ops.rigidbody.object_add()
        plane.rigid_body.type = 'PASSIVE'  # Non-moving collision object
        plane.rigid_body.friction = 0.5
        
        # Enable rigid body world if it doesn't exist yet
        if not bpy.context.scene.rigidbody_world:
            bpy.ops.rigidbody.world_add()
        
        bpy.context.scene.rigidbody_world.time_scale = 1.0
        print("Physics environment setup complete")
    except Exception as e:
        print(f"Warning: Could not set up physics environment: {str(e)}")

def run_physics_simulation(frames=250):
    try:
        # Make sure we have a rigidbody world
        if not bpy.context.scene.rigidbody_world:
            bpy.ops.rigidbody.world_add()
            
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = frames
        
        # Keyframe the initial state
        bpy.context.scene.frame_set(1)
        for obj in bpy.data.objects:
            if hasattr(obj, "rigid_body") and obj.rigid_body:
                obj.keyframe_insert(data_path="location")
                obj.keyframe_insert(data_path="rotation_euler")
        
        # Run the simulation by advancing frames
        print("Running physics simulation...")
        for frame in range(1, frames + 1):
            bpy.context.scene.frame_set(frame)
            if frame % 50 == 0:
                print(f"Simulating frame {frame}/{frames}")
        
        print("Physics simulation completed")
    except Exception as e:
        print(f"Warning: Physics simulation failed: {str(e)}")

def save_outputs(output_dir, version=1):
    # Setup rendering
    bpy.context.scene.render.engine = 'CYCLES'
    try:
        bpy.context.scene.cycles.device = 'GPU'
    except:
        print("Warning: GPU rendering not available, using CPU")
        bpy.context.scene.cycles.device = 'CPU'
    
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
    
    # Export to various formats
    export_formats = []
    
    # Check which export add-ons are available
    if hasattr(bpy.ops.export_scene, "fbx"):
        export_formats.append({"format": "fbx", "operator": bpy.ops.export_scene.fbx})
    
    if hasattr(bpy.ops.export_scene, "obj"):
        export_formats.append({"format": "obj", "operator": bpy.ops.export_scene.obj})
    
    if hasattr(bpy.ops.export_mesh, "stl"):
        export_formats.append({"format": "stl", "operator": bpy.ops.export_mesh.stl})
    
    if hasattr(bpy.ops.export_mesh, "ply"):
        export_formats.append({"format": "ply", "operator": bpy.ops.export_mesh.ply})
    else:
        # Try to enable PLY add-on if not available
        try:
            bpy.ops.preferences.addon_enable(module="io_mesh_ply")
            if hasattr(bpy.ops.export_mesh, "ply"):
                export_formats.append({"format": "ply", "operator": bpy.ops.export_mesh.ply})
        except:
            print("Warning: PLY export not available")
    
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
                if file_format == "fbx":
                    export_info["operator"](filepath=export_path, use_selection=True)
                elif file_format == "obj":
                    export_info["operator"](filepath=export_path, use_selection=True)
                elif file_format in ["stl", "ply"]:
                    export_info["operator"](filepath=export_path, use_selection=True)
                print(f"Exported {file_format} to {export_path}")
            except Exception as e:
                print(f"Failed to export {file_format}: {str(e)}")

def main():
    print("Starting micro-robot-composite part generation in Blender...")
    
    # Setup the environment
    output_dir = setup_environment()
    
    # Load model data
    model_data = {}
    try:        current_dir = os.path.dirname(bpy.data.filepath)
        if not current_dir:
            current_dir = os.getcwd()
            
        # Look for data file in agent_outputs directory
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
