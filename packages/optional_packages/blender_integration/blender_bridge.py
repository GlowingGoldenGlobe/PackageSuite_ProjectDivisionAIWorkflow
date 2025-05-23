
import bpy
import os
import json
import sys

# Ensure the current directory is in the path
current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir)

print("Blender bridge script starting...")

# Load the task data from the temp file
task_file = os.path.join(current_dir, "temp_task_data.json")
with open(task_file, "r") as f:
    task_data = json.load(f)

print("Task data loaded:")
print(task_data)

# Create a new scene
bpy.ops.object.delete() if bpy.context.object else None

# Create a new cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "micro_robot_composite_part"

# Apply dimensions from task data
cube.scale = (
    task_data["dimensions"]["length"] * 0.1,
    task_data["dimensions"]["width"] * 0.1,
    task_data["dimensions"]["height"] * 0.1
)

# Add physics properties
bpy.ops.rigidbody.object_add({'object': cube})
cube.rigid_body.mass = 0.01
cube.rigid_body.friction = 0.7
cube.rigid_body.restitution = 0.3

# Add materials
for material_name in task_data["materials"]:
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    cube.data.materials.append(material)

# Add custom properties
cube["weight_capacity"] = task_data["design_principles"]["weight_capacity"]
cube["speed"] = task_data["motion_capabilities"]["speed"]
cube["degrees_of_freedom"] = task_data["motion_capabilities"]["degrees_of_freedom"]
cube["energy_type"] = task_data["energy_source"]["type"]
cube["power_capacity"] = task_data["energy_source"]["power_capacity"]

print("Object created and properties set")

# Set up a simulation environment
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -2))
plane = bpy.context.active_object
plane.name = "ground"

# Add physics to ground
bpy.ops.rigidbody.object_add({'object': plane})
plane.rigid_body.type = 'PASSIVE'

# Ensure physics world exists
if not bpy.context.scene.rigidbody_world:
    bpy.ops.rigidbody.world_add()

# Set up physics world
bpy.context.scene.rigidbody_world.time_scale = 1.0
bpy.context.scene.rigidbody_world.steps_per_second = 60

# Create output directory
output_dir = os.path.join(current_dir, "agent_outputs")
os.makedirs(output_dir, exist_ok=True)

# Set up rendering
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.engine = 'CYCLES'  # Use Cycles for better quality

# Create a camera
bpy.ops.object.camera_add(location=(15, -15, 10))
camera = bpy.context.active_object
camera.rotation_euler = (0.9, 0.0, 0.8)
scene.camera = camera

# Add a light
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
light = bpy.context.active_object
light.data.energy = 5.0

# Take a snapshot
def save_snapshot(name):
    filepath = os.path.join(output_dir, f"{name}.png")
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    print(f"Snapshot saved: {filepath}")

# Save initial snapshot
save_snapshot("initial_model")

# Run a short physics simulation
for frame in range(1, 101):
    scene.frame_set(frame)
    if frame % 25 == 0:
        save_snapshot(f"simulation_frame_{frame}")

# Save the model as a .blend file
blend_path = os.path.join(output_dir, "micro_robot_composite_part_v1.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Export as PLY
ply_path = os.path.join(output_dir, "micro_robot_composite_part_v1.ply")
bpy.ops.export_mesh.ply(filepath=ply_path, use_selection=True)

# Export as OBJ
obj_path = os.path.join(output_dir, "micro_robot_composite_part_v1.obj")
bpy.ops.export_scene.obj(filepath=obj_path)

print("Simulation complete.")
print(f"Blend file saved: {blend_path}")
print(f"PLY file exported: {ply_path}")
print(f"OBJ file exported: {obj_path}")
print("Blender bridge script completed.")
