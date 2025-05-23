#!/usr/bin/env python3
"""
Open3D Visualization Module

This module provides 3D visualization capabilities for GlowingGoldenGlobe using Open3D.
It integrates with the model description viewer and provides preliminary visualization
before models are refined in Blender and simulated in O3DE.

Uses lazy loading and provides fallback mechanisms when Open3D is not available.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Use lazy loading to check for Open3D
try:
    import check_open3d
except ImportError:
    # Create minimal stub
    class check_open3d:
        @staticmethod
        def is_open3d_available():
            return False
        @staticmethod
        def has_visualization_capability():
            return False

# Global state
_o3d = None
_has_visualization = False
_initialized = False

def initialize():
    """Initialize Open3D - only called when needed"""
    global _o3d, _has_visualization, _initialized
    
    if _initialized:
        return _has_visualization
    
    _initialized = True
    
    # Check if Open3D is available
    if not check_open3d.is_open3d_available():
        print("Open3D is not available. Using fallback visualization.")
        return False
    
    # Check visualization capability
    _has_visualization = check_open3d.has_visualization_capability()
    
    # Import Open3D if available
    try:
        import open3d as o3d
        _o3d = o3d
        return _has_visualization
    except ImportError:
        print("Failed to import Open3D. Using fallback visualization.")
        return False

def load_mesh_from_json(json_path):
    """
    Load a mesh from a JSON model description file
    
    Args:
        json_path: Path to JSON model description
        
    Returns:
        mesh or None: Open3D mesh if successful, None otherwise
    """
    if not initialize():
        print("Cannot load mesh: Open3D not available")
        return None
    
    try:
        # Load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Create a base mesh
        mesh = _o3d.geometry.TriangleMesh.create_sphere(radius=0.01)
        mesh.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray
        
        # Parse model properties
        if 'model_name' in data:
            model_name = data['model_name']
        else:
            model_name = os.path.basename(json_path).replace('.json', '')
        
        # Get size info
        size = 1.0
        if 'base_size' in data:
            size = float(data['base_size'])
        elif 'physical_properties' in data and 'base_size' in data['physical_properties']:
            size = float(data['physical_properties']['base_size'])
        
        # Create basic geometric primitives based on model data
        primitives = []
        
        # Check for parts
        if 'parts' in data:
            parts = data['parts']
            
            for part_name, part_info in parts.items():
                part_mesh = None
                
                # Get position (default to origin)
                pos = [0, 0, 0]
                if 'position' in part_info:
                    pos = part_info['position']
                
                # Get part type/shape
                shape = part_info.get('shape', 'box')
                
                if shape == 'sphere':
                    # Get radius
                    radius = part_info.get('radius', size * 0.1)
                    part_mesh = _o3d.geometry.TriangleMesh.create_sphere(radius=radius)
                    
                elif shape == 'cylinder':
                    # Get height and radius
                    radius = part_info.get('radius', size * 0.05)
                    height = part_info.get('height', size * 0.2)
                    part_mesh = _o3d.geometry.TriangleMesh.create_cylinder(radius=radius, height=height)
                    
                elif shape == 'box' or shape == 'cube':
                    # Get dimensions
                    width = part_info.get('width', size * 0.1)
                    height = part_info.get('height', size * 0.1)
                    depth = part_info.get('depth', size * 0.1)
                    part_mesh = _o3d.geometry.TriangleMesh.create_box(width=width, height=height, depth=depth)
                
                else:
                    # Default to a small sphere for unknown shapes
                    part_mesh = _o3d.geometry.TriangleMesh.create_sphere(radius=size * 0.05)
                
                # Get color (default to random color)
                color = [np.random.random() * 0.5 + 0.5 for _ in range(3)]
                if 'color' in part_info:
                    color = part_info['color']
                elif 'material' in part_info:
                    # Generate color based on material
                    material = part_info['material'].lower()
                    if 'steel' in material or 'metal' in material:
                        color = [0.7, 0.7, 0.7]  # Silver
                    elif 'plastic' in material:
                        color = [0.9, 0.9, 1.0]  # White/light blue
                    elif 'rubber' in material:
                        color = [0.1, 0.1, 0.1]  # Black
                    elif 'copper' in material:
                        color = [0.85, 0.55, 0.35]  # Copper
                    elif 'gold' in material:
                        color = [1.0, 0.85, 0.35]  # Gold
                    # Add more material colors as needed
                
                if part_mesh:
                    # Apply color
                    part_mesh.paint_uniform_color(color)
                    
                    # Apply position
                    part_mesh.translate(pos)
                    
                    # Add to primitives list
                    primitives.append(part_mesh)
        
        # If no parts defined, create a basic representation
        if not primitives:
            # Basic representation based on parameters
            if 'parameters' in data:
                params = data['parameters']
                
                # Check for movement capabilities
                if 'movement_capabilities' in params:
                    capabilities = params['movement_capabilities']
                    
                    # Add wheels if "rolling" is a capability
                    if 'rolling' in capabilities:
                        wheel_radius = size * 0.15
                        wheel = _o3d.geometry.TriangleMesh.create_cylinder(radius=wheel_radius, height=wheel_radius * 0.5)
                        wheel.paint_uniform_color([0.1, 0.1, 0.1])  # Black
                        
                        # Position wheels
                        wheel1 = wheel.clone()
                        wheel1.translate([size * 0.3, -size * 0.3, size * 0.15])
                        
                        wheel2 = wheel.clone()
                        wheel2.translate([size * 0.3, size * 0.3, size * 0.15])
                        
                        wheel3 = wheel.clone()
                        wheel3.translate([-size * 0.3, -size * 0.3, size * 0.15])
                        
                        wheel4 = wheel.clone()
                        wheel4.translate([-size * 0.3, size * 0.3, size * 0.15])
                        
                        primitives.extend([wheel1, wheel2, wheel3, wheel4])
                
                # Create basic body
                if 'wall_height' in params:
                    height = float(params['wall_height'])
                else:
                    height = size * 0.3
                
                body = _o3d.geometry.TriangleMesh.create_box(width=size, height=size, depth=height)
                body.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray
                body.translate([0, 0, height/2])
                
                primitives.append(body)
            
            # If still no primitives, create a simple ball
            if not primitives:
                sphere = _o3d.geometry.TriangleMesh.create_sphere(radius=size * 0.5)
                sphere.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray
                primitives.append(sphere)
        
        # Combine all primitives into one mesh
        combined_mesh = primitives[0]
        for primitive in primitives[1:]:
            combined_mesh += primitive
        
        # Compute normals for proper lighting
        combined_mesh.compute_vertex_normals()
        
        # Add text label with model name
        # Note: Open3D doesn't support text directly, so this is a placeholder
        # In the future, we could use a 3D text geometry library
        
        return combined_mesh
        
    except Exception as e:
        print(f"Error loading mesh from JSON: {str(e)}")
        return None

def load_mesh_from_file(file_path):
    """
    Load mesh from a 3D model file (obj, stl, ply, etc.)
    
    Args:
        file_path: Path to 3D model file
        
    Returns:
        mesh or None: Open3D mesh if successful, None otherwise
    """
    if not initialize():
        print("Cannot load mesh: Open3D not available")
        return None
    
    try:
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.obj', '.stl', '.ply', '.off']:
            mesh = _o3d.io.read_triangle_mesh(file_path)
            
            # If the mesh has no vertex colors, add a default color
            if not mesh.has_vertex_colors():
                mesh.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray
            
            # Compute normals if not present
            if not mesh.has_vertex_normals():
                mesh.compute_vertex_normals()
                
            return mesh
        else:
            print(f"Unsupported file format: {ext}")
            return None
            
    except Exception as e:
        print(f"Error loading mesh from file: {str(e)}")
        return None

def visualize_mesh(mesh, window_name="GlowingGoldenGlobe Model Viewer"):
    """
    Visualize a mesh using Open3D
    
    Args:
        mesh: Open3D mesh to visualize
        window_name: Title for the visualization window
        
    Returns:
        bool: True if visualization successful, False otherwise
    """
    if not initialize():
        print("Cannot visualize: Open3D not available")
        return False
    
    if mesh is None:
        print("Cannot visualize: No mesh provided")
        return False
    
    try:
        # Create visualization with custom settings
        vis = _o3d.visualization.Visualizer()
        vis.create_window(window_name=window_name, width=800, height=600)
        
        # Add the mesh
        vis.add_geometry(mesh)
        
        # Improve rendering
        opt = vis.get_render_option()
        opt.background_color = [0.3, 0.3, 0.3]  # Dark gray background
        opt.point_size = 5.0
        opt.line_width = 2.0
        opt.light_on = True
        
        # Set default camera view
        view_control = vis.get_view_control()
        view_control.set_zoom(0.8)
        
        # Run the visualization
        vis.run()
        vis.destroy_window()
        
        return True
        
    except Exception as e:
        print(f"Error visualizing mesh: {str(e)}")
        return False

def save_mesh_screenshot(mesh, output_path, width=800, height=600):
    """
    Save a screenshot of the mesh without showing a window
    
    Args:
        mesh: Open3D mesh to visualize
        output_path: Path to save the screenshot
        width, height: Image dimensions
        
    Returns:
        bool: True if screenshot saved successfully, False otherwise
    """
    if not initialize():
        print("Cannot save screenshot: Open3D not available")
        return False
    
    if mesh is None:
        print("Cannot save screenshot: No mesh provided")
        return False
    
    try:
        # Create offscreen visualizer
        vis = _o3d.visualization.Visualizer()
        vis.create_window(visible=False, width=width, height=height)
        
        # Add the mesh
        vis.add_geometry(mesh)
        
        # Improve rendering
        opt = vis.get_render_option()
        opt.background_color = [0.3, 0.3, 0.3]  # Dark gray background
        opt.point_size = 5.0
        opt.light_on = True
        
        # Set default camera view
        view_control = vis.get_view_control()
        view_control.set_zoom(0.8)
        
        # Update renderer
        vis.poll_events()
        vis.update_renderer()
        
        # Capture image
        vis.capture_screen_image(output_path)
        vis.destroy_window()
        
        print(f"Screenshot saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error saving screenshot: {str(e)}")
        return False

def generate_multi_view(mesh, output_dir, base_name="model_view", views=4):
    """
    Generate multiple views of the mesh from different angles
    
    Args:
        mesh: Open3D mesh to visualize
        output_dir: Directory to save the screenshots
        base_name: Base filename for screenshots
        views: Number of views to generate
        
    Returns:
        list: Paths to generated screenshots, or empty list on failure
    """
    if not initialize():
        print("Cannot generate views: Open3D not available")
        return []
    
    if mesh is None:
        print("Cannot generate views: No mesh provided")
        return []
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    screenshots = []
    
    try:
        # Create offscreen visualizer
        vis = _o3d.visualization.Visualizer()
        vis.create_window(visible=False, width=800, height=600)
        
        # Add the mesh
        vis.add_geometry(mesh)
        
        # Improve rendering
        opt = vis.get_render_option()
        opt.background_color = [0.3, 0.3, 0.3]  # Dark gray background
        opt.point_size = 5.0
        opt.light_on = True
        
        # Get view control
        view_control = vis.get_view_control()
        
        # Generate views from different angles
        for i in range(views):
            # Calculate rotation angle
            angle = i * (360.0 / views)
            
            # Set camera position based on angle
            radius = 1.5
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            z = 0.5
            
            # Position camera
            cam = view_control.convert_to_pinhole_camera_parameters()
            cam.extrinsic = np.array([
                [1, 0, 0, -x],
                [0, 1, 0, -y],
                [0, 0, 1, -z],
                [0, 0, 0, 1]
            ])
            view_control.convert_from_pinhole_camera_parameters(cam)
            
            # Update renderer
            vis.poll_events()
            vis.update_renderer()
            
            # Save screenshot
            output_path = os.path.join(output_dir, f"{base_name}_angle{i}.png")
            vis.capture_screen_image(output_path)
            screenshots.append(output_path)
        
        vis.destroy_window()
        
        return screenshots
        
    except Exception as e:
        print(f"Error generating multiple views: {str(e)}")
        return []

def analyze_mesh(mesh):
    """
    Analyze mesh properties
    
    Args:
        mesh: Open3D mesh to analyze
        
    Returns:
        dict: Dictionary of mesh properties or None on failure
    """
    if not initialize():
        print("Cannot analyze mesh: Open3D not available")
        return None
    
    if mesh is None:
        print("Cannot analyze mesh: No mesh provided")
        return None
    
    try:
        # Compute basic properties
        result = {
            "vertex_count": len(mesh.vertices),
            "triangle_count": len(mesh.triangles),
            "has_vertex_normals": mesh.has_vertex_normals(),
            "has_vertex_colors": mesh.has_vertex_colors(),
            "volume": mesh.get_volume(),
            "surface_area": mesh.get_surface_area(),
            "is_watertight": mesh.is_watertight(),
            "is_self_intersecting": mesh.is_self_intersecting(),
            "bbox_min": mesh.get_min_bound().tolist(),
            "bbox_max": mesh.get_max_bound().tolist()
        }
        
        # Compute center of mass
        center = mesh.get_center().tolist()
        result["center"] = center
        
        # Try to compute mesh quality metrics
        try:
            # Check triangle quality (all triangles should have non-zero area)
            triangles = np.asarray(mesh.triangles)
            vertices = np.asarray(mesh.vertices)
            
            # Calculate triangle areas
            v0 = vertices[triangles[:, 0], :]
            v1 = vertices[triangles[:, 1], :]
            v2 = vertices[triangles[:, 2], :]
            
            # Cross product for area calculation
            cross = np.cross(v1 - v0, v2 - v0)
            areas = 0.5 * np.sqrt(np.sum(cross * cross, axis=1))
            
            result["min_triangle_area"] = float(np.min(areas))
            result["max_triangle_area"] = float(np.max(areas))
            result["mean_triangle_area"] = float(np.mean(areas))
            result["zero_area_triangles"] = int(np.sum(areas < 1e-10))
            
        except Exception as e:
            print(f"Error computing mesh quality metrics: {str(e)}")
        
        return result
        
    except Exception as e:
        print(f"Error analyzing mesh: {str(e)}")
        return None

def mesh_to_pointcloud(mesh, points_per_triangle=10):
    """
    Convert a mesh to a point cloud
    
    Args:
        mesh: Open3D mesh to convert
        points_per_triangle: Density of point sampling
        
    Returns:
        PointCloud or None: Resulting point cloud or None on failure
    """
    if not initialize():
        print("Cannot convert mesh: Open3D not available")
        return None
    
    if mesh is None:
        print("Cannot convert mesh: No mesh provided")
        return None
    
    try:
        pcd = mesh.sample_points_poisson_disk(
            number_of_points=len(mesh.triangles) * points_per_triangle
        )
        return pcd
        
    except Exception as e:
        print(f"Error converting mesh to point cloud: {str(e)}")
        return None

# Fallback visualization using ASCII
def ascii_visualize(size=10):
    """Simple ASCII visualization when Open3D isn't available"""
    print("\nASCII Visualization (Open3D not available)\n")
    print("   Model Preview  ")
    print("  " + "-" * size)
    
    for i in range(size):
        line = "| "
        for j in range(size):
            # Create a simple sphere pattern
            dist = ((i - size//2)**2 + (j - size//2)**2)**0.5
            if dist < size//3:
                line += "##"
            elif dist < size//2:
                line += "oo"
            else:
                line += "  "
        line += " |"
        print(line)
    
    print("  " + "-" * size)
    print("\nOpen3D not available. Install with: pip install open3d")

# Command line interface
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Open3D Visualization Tool")
    parser.add_argument("file", help="Path to 3D model file or JSON description")
    parser.add_argument("--screenshot", help="Save screenshot to the specified path")
    parser.add_argument("--analyze", action="store_true", help="Analyze mesh properties")
    parser.add_argument("--views", type=int, default=0, 
                      help="Generate multiple views (specify number of views)")
    parser.add_argument("--output-dir", default="./views", 
                      help="Output directory for generated views")
    
    args = parser.parse_args()
    
    # Check if Open3D is available
    if not initialize():
        print("Open3D is not available. Using fallback visualization.")
        ascii_visualize()
        sys.exit(1)
    
    # Load the mesh based on file extension
    ext = os.path.splitext(args.file)[1].lower()
    
    if ext == '.json':
        mesh = load_mesh_from_json(args.file)
    else:
        mesh = load_mesh_from_file(args.file)
    
    if mesh is None:
        print(f"Failed to load mesh from {args.file}")
        sys.exit(1)
    
    # Analyze mesh if requested
    if args.analyze:
        analysis = analyze_mesh(mesh)
        print("\nMesh Analysis:")
        for key, value in analysis.items():
            print(f"  {key}: {value}")
    
    # Generate multiple views if requested
    if args.views > 0:
        print(f"Generating {args.views} views...")
        screenshots = generate_multi_view(mesh, args.output_dir, views=args.views)
        print(f"Generated {len(screenshots)} views:")
        for screenshot in screenshots:
            print(f"  {screenshot}")
    
    # Save screenshot if requested
    if args.screenshot:
        print(f"Saving screenshot to {args.screenshot}...")
        save_mesh_screenshot(mesh, args.screenshot)
    
    # Visualize if no other output options were selected
    if not args.screenshot and not args.views:
        visualize_mesh(mesh)