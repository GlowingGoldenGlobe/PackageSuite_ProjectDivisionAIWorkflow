#!/usr/bin/env python
# open3d_gui_integration.py - Integrates Open3D mesh processing with GlowingGoldenGlobe GUI
"""
This module provides GUI integration for the improved Open3D mesh processing capabilities.
It adds a dedicated tab to the GUI for visualizing, analyzing and improving 3D models
using the enhanced Open3D utilities.

Features:
- Model quality analysis with visual feedback
- Mesh repair and optimization
- Advanced visualization generation
- Integration with the existing version control system
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
import tempfile
from datetime import datetime
from pathlib import Path
import glob
import subprocess
import platform
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

# Add the parent directory to sys.path to make sure we can find the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Try to import the required modules
try:
    # Import our custom Open3D utilities
    from Div_AI_Agent_Focus_1.open3d_utils import (
        MeshQualityMetrics,
        MeshProcessing,
        MeshVisualization,
        MeshExportImport,
        OPEN3D_AVAILABLE
    )
    
    # Import refinement modules
    from Div_AI_Agent_Focus_1.refinement_3d_sequence import Model3DRefinementSequence
    
    # Import other utilities as needed
    from model_notification_system import get_notification_system, ModelNotification
    
    # Import physics-related modules if available
    try:
        from Div_AI_Agent_Focus_1.advanced_physics_simulation import (
            MaterialType,
            MaterialProperties,
            MATERIAL_LIBRARY
        )
        PHYSICS_MODULE_AVAILABLE = True
    except ImportError:
        PHYSICS_MODULE_AVAILABLE = False
except ImportError as e:
    print(f"Error importing modules: {e}")
    OPEN3D_AVAILABLE = False


class Open3DGUIIntegration:
    """Integrates Open3D utilities with the GlowingGoldenGlobe GUI"""
    
    def __init__(self, parent, config_path="agent_mode_config.json"):
        """
        Initialize the Open3D GUI integration.
        
        Args:
            parent: The parent GUI instance
            config_path: Path to configuration file
        """
        self.parent = parent
        self.config_path = config_path
        
        # Status of required components
        self.open3d_available = OPEN3D_AVAILABLE
        self.physics_available = PHYSICS_MODULE_AVAILABLE
        
        # UI variables
        self.progress_bar = None
        self.status_label = None
        self.model_listbox = None
        self.image_label = None
        self.image_window = None
        self.quality_report_text = None
        
        # Repair settings
        self.fill_holes_var = tk.BooleanVar(value=True)
        self.remove_isolated_var = tk.BooleanVar(value=True)
        self.simplify_mesh_var = tk.BooleanVar(value=True)
        self.target_triangles_var = tk.StringVar(value="5000")
        self.preserve_features_var = tk.BooleanVar(value=True)
        
        # Material selection for export
        self.material_var = tk.StringVar(value="aluminum_6061")
        
        # Set up notification system
        try:
            self.notification_system = get_notification_system()
        except:
            self.notification_system = None
    
    def setup_ui(self, notebook):
        """Set up the Open3D tab in the notebook"""
        if not notebook:
            return
            
        # Create tab
        self.open3d_tab = ttk.Frame(notebook)
        notebook.add(self.open3d_tab, text="Open3D Processing")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.open3d_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="3D Model Analysis & Refinement", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Model selection frame
        model_frame = ttk.LabelFrame(
            main_frame, 
            text="Available Models",
            padding="10"
        )
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model listbox with scrollbar
        models_frame = ttk.Frame(model_frame)
        models_frame.pack(fill=tk.X, expand=True)
        
        self.model_listbox = tk.Listbox(models_frame, height=5)
        self.model_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=self.model_listbox.yview)
        self.model_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button to refresh model list
        button_frame = ttk.Frame(model_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Refresh Models",
            command=self.refresh_model_list
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Import Model",
            command=self.import_model
        ).pack(side=tk.LEFT, padx=5)
        
        # Create a frame for options and actions
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        # Split into left and right panes
        left_pane = ttk.Frame(options_frame)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_pane = ttk.Frame(options_frame)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Left pane: Repair options
        repair_frame = ttk.LabelFrame(left_pane, text="Mesh Repair Options", padding="10")
        repair_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            repair_frame,
            text="Fill holes",
            variable=self.fill_holes_var
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            repair_frame,
            text="Remove isolated components",
            variable=self.remove_isolated_var
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            repair_frame,
            text="Simplify mesh",
            variable=self.simplify_mesh_var
        ).pack(anchor=tk.W, pady=2)
        
        target_frame = ttk.Frame(repair_frame)
        target_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(target_frame, text="Target triangles:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(
            target_frame,
            textvariable=self.target_triangles_var,
            width=8
        ).pack(side=tk.LEFT)
        
        ttk.Checkbutton(
            repair_frame,
            text="Preserve features",
            variable=self.preserve_features_var
        ).pack(anchor=tk.W, pady=2)
        
        # Material selection
        if self.physics_available:
            material_frame = ttk.LabelFrame(left_pane, text="Material Properties", padding="10")
            material_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(material_frame, text="Material:").pack(anchor=tk.W, pady=2)
            
            material_names = []
            try:
                # Get material names from MaterialType enum
                material_names = [mt.value for mt in MaterialType]
            except:
                material_names = ["aluminum_6061", "abs_plastic", "pla_plastic", "copper_c110"]
            
            material_combo = ttk.Combobox(
                material_frame,
                textvariable=self.material_var,
                values=material_names,
                state="readonly"
            )
            material_combo.pack(fill=tk.X, pady=2)
        
        # Right pane: Actions
        action_frame = ttk.LabelFrame(right_pane, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            action_frame,
            text="Analyze Quality",
            command=self.analyze_model_quality
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            action_frame,
            text="Repair Model",
            command=self.repair_model
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            action_frame,
            text="Run Full Refinement",
            command=self.run_refinement_sequence
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            action_frame,
            text="Export Model",
            command=self.export_model
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            action_frame,
            text="View in Blender",
            command=self.view_in_blender
        ).pack(fill=tk.X, pady=2)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        results_notebook = ttk.Notebook(results_frame)
        results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Results tabs
        preview_tab = ttk.Frame(results_notebook)
        report_tab = ttk.Frame(results_notebook)
        
        results_notebook.add(preview_tab, text="Preview")
        results_notebook.add(report_tab, text="Quality Report")
        
        # Preview tab: Image preview
        preview_frame = ttk.Frame(preview_tab, padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_label = ttk.Label(preview_frame, text="No preview available")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Report tab: Quality report text
        report_frame = ttk.Frame(report_tab, padding="10")
        report_frame.pack(fill=tk.BOTH, expand=True)
        
        self.quality_report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD)
        self.quality_report_text.pack(fill=tk.BOTH, expand=True)
        
        # Initialize model list
        self.refresh_model_list()
        
        # Check for Open3D and show warning if not available
        if not self.open3d_available:
            messagebox.showwarning(
                "Open3D Not Available",
                "Open3D is not installed or couldn't be loaded. Some features will be disabled.\n\n"
                "To install Open3D, run:\n"
                "pip install open3d"
            )
    
    def refresh_model_list(self):
        """Refresh the list of available 3D models"""
        if not hasattr(self, 'model_listbox') or not self.model_listbox:
            return
            
        # Clear current list
        self.model_listbox.delete(0, tk.END)
        
        # Find 3D model files
        model_files = []
        
        # Search for models in agent_outputs and related directories
        search_paths = [
            "./agent_outputs/**/*.blend",
            "./Div_AI_Agent_Focus_1/**/*.blend",
            "./agent_outputs/**/*.obj",
            "./agent_outputs/**/*.ply",
            "./agent_outputs/**/*.stl",
            "./Div_AI_Agent_Focus_1/**/*.obj",
            "./Div_AI_Agent_Focus_1/**/*.ply",
            "./Div_AI_Agent_Focus_1/**/*.stl",
            "./Div_AI_Agent_Focus_1/agent_outputs/**/*.blend",
            "./Div_AI_Agent_Focus_1/agent_outputs/**/*.obj",
            "./Div_AI_Agent_Focus_1/agent_outputs/**/*.ply",
            "./Div_AI_Agent_Focus_1/agent_outputs/**/*.stl"
        ]
        
        for path in search_paths:
            model_files.extend(glob.glob(path, recursive=True))
        
        # Deduplicate and sort
        model_files = sorted(list(set(model_files)))
        
        # Add to listbox
        for file_path in model_files:
            display_name = f"{os.path.basename(file_path)} ({os.path.getsize(file_path) // 1024} KB)"
            self.model_listbox.insert(tk.END, display_name)
            # Store actual path as listbox item data (not supported in tk.Listbox)
            # We'll use a parallel list or dictionary to store this mapping
        
        # Store the mapping of display names to file paths
        self.model_paths = {self.model_listbox.get(i): model_files[i] for i in range(len(model_files))}
        
        # Update status
        self.update_status(f"Found {len(model_files)} model files")
    
    def get_selected_model_path(self):
        """Get the file path of the selected model"""
        selection = self.model_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model file")
            return None
            
        selected_text = self.model_listbox.get(selection[0])
        return self.model_paths.get(selected_text)
    
    def update_status(self, message, progress=None):
        """Update status message and progress bar"""
        if self.status_label:
            self.status_label.config(text=message)
            
        if progress is not None and self.progress_bar:
            if progress < 0:
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start()
            else:
                self.progress_bar.config(mode='determinate')
                self.progress_bar.stop()
                self.progress_bar['value'] = progress
    
    def import_model(self):
        """Import a 3D model file"""
        file_path = filedialog.askopenfilename(
            title="Select 3D Model File",
            filetypes=[
                ("3D Models", "*.obj *.ply *.stl *.blend *.fbx *.glb *.gltf"),
                ("OBJ Files", "*.obj"),
                ("PLY Files", "*.ply"),
                ("STL Files", "*.stl"),
                ("Blender Files", "*.blend"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        # Copy file to agent_outputs directory
        try:
            output_dir = os.path.join("agent_outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Get base filename without path
            filename = os.path.basename(file_path)
            
            # Create destination path
            dest_path = os.path.join(output_dir, filename)
            
            # Copy the file
            import shutil
            shutil.copy2(file_path, dest_path)
            
            # Update model list
            self.refresh_model_list()
            
            # Select the newly imported model
            for i, item in enumerate(self.model_listbox.get(0, tk.END)):
                if filename in item:
                    self.model_listbox.selection_clear(0, tk.END)
                    self.model_listbox.selection_set(i)
                    self.model_listbox.see(i)
                    break
            
            # Update status
            self.update_status(f"Imported {filename}", 100)
            
            # Show confirmation
            messagebox.showinfo("Import Successful", f"Model imported: {filename}")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import model: {str(e)}")
    
    def analyze_model_quality(self):
        """Analyze the quality of the selected model"""
        if not self.open3d_available:
            messagebox.showwarning("Open3D Not Available", "Open3D is required for model analysis")
            return
            
        # Get selected model
        model_path = self.get_selected_model_path()
        if not model_path:
            return
            
        # Start progress indicator
        self.update_status("Analyzing model quality...", -1)
        
        # Run analysis in background thread
        threading.Thread(target=self._run_quality_analysis, args=(model_path,), daemon=True).start()
    
    def _run_quality_analysis(self, model_path):
        """Run quality analysis in background thread"""
        try:
            # Import Open3D here to avoid module import errors in the main thread
            import open3d as o3d
            
            # Import our analysis tools
            from Div_AI_Agent_Focus_1.open3d_utils import MeshQualityMetrics, MeshVisualization
            
            # Load the mesh
            mesh = o3d.io.read_triangle_mesh(model_path)
            
            if not mesh.has_vertices():
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Could not load mesh from file: {model_path}\n"
                    "The file may be corrupted or in an unsupported format."
                ))
                self.root.after(0, lambda: self.update_status("Analysis failed", 0))
                return
                
            # Ensure we have vertex normals
            if not mesh.has_vertex_normals():
                mesh.compute_vertex_normals()
                
            # Generate quality report
            report = MeshQualityMetrics.generate_quality_report(mesh)
            
            # Generate visualizations
            viz_outputs = MeshVisualization.visualize_quality_analysis(mesh)
            
            # Update UI in main thread
            self.parent.root.after(0, lambda: self._update_quality_ui(report, viz_outputs))
            
        except Exception as e:
            print(f"Error in quality analysis: {e}")
            import traceback
            traceback.print_exc()
            
            self.parent.root.after(0, lambda: messagebox.showerror(
                "Analysis Error",
                f"Failed to analyze model: {str(e)}"
            ))
            self.parent.root.after(0, lambda: self.update_status("Analysis failed", 0))
    
    def _update_quality_ui(self, report, viz_outputs):
        """Update UI with quality analysis results"""
        # Update progress
        self.update_status("Analysis complete", 100)
        
        # Update quality report text
        if self.quality_report_text:
            self.quality_report_text.delete(1.0, tk.END)
            
            # Create a formatted report
            report_text = "# 3D Model Quality Analysis\n\n"
            
            # Add overall quality
            quality_rating = report.get("quality_summary", "Unknown")
            report_text += f"## Overall Quality: {quality_rating}\n\n"
            
            # Add overall score
            if "metrics" in report and "simulation_quality_score" in report["metrics"]:
                score = report["metrics"]["simulation_quality_score"]
                report_text += f"Quality Score: {score}/100\n\n"
            
            # Add basic metrics
            if "metrics" in report:
                metrics = report["metrics"]
                report_text += "## Basic Metrics\n\n"
                report_text += f"- Vertices: {metrics.get('vertex_count', 'N/A')}\n"
                report_text += f"- Triangles: {metrics.get('triangle_count', 'N/A')}\n"
                report_text += f"- Watertight: {metrics.get('is_watertight', False)}\n"
                report_text += f"- Manifold: {metrics.get('is_edge_manifold', False)}\n"
                report_text += f"- Self-Intersecting: {metrics.get('is_self_intersecting', False)}\n"
                
                if "surface_area" in metrics:
                    report_text += f"- Surface Area: {metrics['surface_area']:.6f} sq units\n"
                
                if "volume" in metrics and metrics["volume"] is not None:
                    report_text += f"- Volume: {metrics['volume']:.6f} cubic units\n"
                
                report_text += "\n"
            
            # Add triangle quality metrics
            if "metrics" in report and "aspect_ratio" in report["metrics"]:
                aspect = report["metrics"]["aspect_ratio"]
                report_text += "## Triangle Quality\n\n"
                report_text += f"- Mean Aspect Ratio: {aspect.get('mean', 'N/A'):.2f}\n"
                report_text += f"- Min Aspect Ratio: {aspect.get('min', 'N/A'):.2f}\n"
                report_text += f"- Max Aspect Ratio: {aspect.get('max', 'N/A'):.2f}\n\n"
            
            # Add recommendations
            if "recommendations" in report and report["recommendations"]:
                report_text += "## Recommendations\n\n"
                for rec in report["recommendations"]:
                    report_text += f"- {rec}\n"
                report_text += "\n"
            
            # Insert the report text
            self.quality_report_text.insert(1.0, report_text)
        
        # Update preview image if available
        if viz_outputs and "aspect_ratio" in viz_outputs:
            try:
                from PIL import Image, ImageTk
                
                # Load the image
                image_path = viz_outputs["aspect_ratio"]
                image = Image.open(image_path)
                
                # Resize to fit the preview area (maintaining aspect ratio)
                max_width = 400
                max_height = 300
                
                if image.width > max_width or image.height > max_height:
                    ratio = min(max_width / image.width, max_height / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Update image label
                if self.image_label:
                    self.image_label.config(image=photo)
                    self.image_label.image = photo  # Keep a reference to prevent garbage collection
                
                # Add button to view full images
                self._add_view_image_button(viz_outputs)
                
            except Exception as img_error:
                print(f"Error displaying image: {img_error}")
    
    def _add_view_image_button(self, viz_outputs):
        """Add a button to view full-size images"""
        # Create a button if it doesn't exist
        parent = self.image_label.master
        
        # Remove existing buttons
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.Button) and widget.winfo_name() == "view_images_button":
                widget.destroy()
        
        # Create new button
        view_button = ttk.Button(
            parent,
            text="View All Images",
            command=lambda: self._show_all_images(viz_outputs),
            name="view_images_button"
        )
        view_button.pack(pady=(5, 0))
    
    def _show_all_images(self, viz_outputs):
        """Show all visualization images in a new window"""
        if not viz_outputs:
            return
            
        # Create a new window for images
        img_window = tk.Toplevel(self.parent.root)
        img_window.title("Model Visualizations")
        img_window.geometry("800x600")
        
        # Create a notebook for different visualizations
        img_notebook = ttk.Notebook(img_window)
        img_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            from PIL import Image, ImageTk
            
            # Add each visualization as a tab
            for viz_name, img_path in viz_outputs.items():
                if viz_name == "report" or not os.path.exists(img_path):
                    continue
                    
                # Create tab
                tab = ttk.Frame(img_notebook)
                img_notebook.add(tab, text=viz_name.replace("_", " ").title())
                
                # Load image
                image = Image.open(img_path)
                
                # Create a canvas to display the image
                canvas = tk.Canvas(tab, bg="white")
                canvas.pack(fill=tk.BOTH, expand=True)
                
                # Add scrollbars
                h_scrollbar = ttk.Scrollbar(tab, orient=tk.HORIZONTAL, command=canvas.xview)
                v_scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
                canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
                
                h_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)
                v_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Add to canvas
                canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                canvas.image = photo  # Keep reference
                
                # Configure canvas scrolling region
                canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            
            # Add a close button
            ttk.Button(
                img_window,
                text="Close",
                command=img_window.destroy
            ).pack(pady=10)
            
        except Exception as e:
            print(f"Error showing images: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to display images: {str(e)}")
    
    def repair_model(self):
        """Repair the selected model"""
        if not self.open3d_available:
            messagebox.showwarning("Open3D Not Available", "Open3D is required for model repair")
            return
            
        # Get selected model
        model_path = self.get_selected_model_path()
        if not model_path:
            return
            
        # Get repair options
        options = {
            "fill_holes": self.fill_holes_var.get(),
            "remove_isolated_components": self.remove_isolated_var.get(),
            "max_hole_size": 0.05  # 5% of model size
        }
        
        # Start progress indicator
        self.update_status("Repairing model...", -1)
        
        # Run repair in background thread
        threading.Thread(target=self._run_model_repair, args=(model_path, options), daemon=True).start()
    
    def _run_model_repair(self, model_path, options):
        """Run model repair in background thread"""
        try:
            # Import Open3D and utilities
            import open3d as o3d
            from Div_AI_Agent_Focus_1.open3d_utils import MeshProcessing, MeshQualityMetrics
            
            # Load the mesh
            mesh = o3d.io.read_triangle_mesh(model_path)
            
            if not mesh.has_vertices():
                self.parent.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Could not load mesh from file: {model_path}"
                ))
                self.parent.root.after(0, lambda: self.update_status("Repair failed", 0))
                return
            
            # Run repair process
            repaired_mesh, repair_report = MeshProcessing.repair_mesh(mesh, options)
            
            # Run simplification if selected
            if self.simplify_mesh_var.get():
                try:
                    target_triangles = int(self.target_triangles_var.get())
                    simplified_mesh, simplify_report = MeshProcessing.simplify_for_physics(
                        repaired_mesh,
                        target_triangle_count=target_triangles,
                        preserve_features=self.preserve_features_var.get()
                    )
                    
                    # Update mesh and report
                    repaired_mesh = simplified_mesh
                    repair_report["simplification"] = simplify_report
                    
                except ValueError:
                    self.parent.root.after(0, lambda: messagebox.showwarning(
                        "Invalid Value",
                        "Target triangles must be a valid number. Using the default repair only."
                    ))
            
            # Generate quality report for the repaired mesh
            quality_report = MeshQualityMetrics.generate_quality_report(repaired_mesh)
            
            # Create output path for repaired mesh
            base_path = os.path.splitext(model_path)[0]
            output_path = f"{base_path}_repaired.ply"
            
            # Save repaired mesh
            o3d.io.write_triangle_mesh(output_path, repaired_mesh)
            
            # Also save in OBJ format for better compatibility
            obj_path = f"{base_path}_repaired.obj"
            o3d.io.write_triangle_mesh(obj_path, repaired_mesh)
            
            # Generate visualization
            viz_output = self._generate_before_after_visualization(mesh, repaired_mesh, base_path)
            
            # Update UI in main thread
            self.parent.root.after(0, lambda: self._update_repair_ui(
                output_path, obj_path, repair_report, quality_report, viz_output
            ))
            
        except Exception as e:
            print(f"Error in model repair: {e}")
            import traceback
            traceback.print_exc()
            
            self.parent.root.after(0, lambda: messagebox.showerror(
                "Repair Error",
                f"Failed to repair model: {str(e)}"
            ))
            self.parent.root.after(0, lambda: self.update_status("Repair failed", 0))
    
    def _generate_before_after_visualization(self, original_mesh, repaired_mesh, base_path):
        """Generate visualization showing before and after repair"""
        viz_path = f"{base_path}_repair_comparison.png"
        
        try:
            import open3d as o3d
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # Create visualizers for both meshes
            vis_orig = o3d.visualization.Visualizer()
            vis_orig.create_window(visible=False, width=800, height=600)
            vis_orig.add_geometry(original_mesh)
            vis_orig.update_geometry(original_mesh)
            
            # Get a good viewpoint
            view_control = vis_orig.get_view_control()
            view_control.set_zoom(0.7)
            
            # Capture original mesh
            vis_orig.poll_events()
            vis_orig.update_renderer()
            orig_img_path = f"{base_path}_orig_temp.png"
            vis_orig.capture_screen_image(orig_img_path)
            vis_orig.destroy_window()
            
            # Visualize repaired mesh
            vis_repaired = o3d.visualization.Visualizer()
            vis_repaired.create_window(visible=False, width=800, height=600)
            vis_repaired.add_geometry(repaired_mesh)
            vis_repaired.update_geometry(repaired_mesh)
            
            # Use same viewpoint
            view_control = vis_repaired.get_view_control()
            view_control.set_zoom(0.7)
            
            # Capture repaired mesh
            vis_repaired.poll_events()
            vis_repaired.update_renderer()
            repaired_img_path = f"{base_path}_repaired_temp.png"
            vis_repaired.capture_screen_image(repaired_img_path)
            vis_repaired.destroy_window()
            
            # Create side-by-side comparison
            orig_img = Image.open(orig_img_path)
            repaired_img = Image.open(repaired_img_path)
            
            # Resize if needed
            width, height = orig_img.size
            
            # Create combined image
            combined_width = width * 2 + 20  # 20px padding between images
            combined_height = height + 60  # Space for title
            combined_img = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))
            
            # Add title
            draw = ImageDraw.Draw(combined_img)
            draw.text((10, 10), "Before Repair", fill=(0, 0, 0))
            draw.text((width + 30, 10), "After Repair", fill=(0, 0, 0))
            
            # Paste images
            combined_img.paste(orig_img, (0, 40))
            combined_img.paste(repaired_img, (width + 20, 40))
            
            # Save combined image
            combined_img.save(viz_path)
            
            # Clean up temp files
            os.remove(orig_img_path)
            os.remove(repaired_img_path)
            
            return viz_path
            
        except Exception as e:
            print(f"Error generating comparison: {e}")
            return None
    
    def _update_repair_ui(self, ply_path, obj_path, repair_report, quality_report, viz_path):
        """Update UI after model repair"""
        # Update progress
        self.update_status("Repair complete", 100)
        
        # Update quality report text
        if self.quality_report_text:
            self.quality_report_text.delete(1.0, tk.END)
            
            # Create repair report
            report_text = "# Model Repair Report\n\n"
            
            # Add repair operations
            if "operations_applied" in repair_report:
                report_text += "## Repair Operations\n\n"
                for op in repair_report["operations_applied"]:
                    report_text += f"- {op.replace('_', ' ').title()}\n"
                report_text += "\n"
            
            # Add vertex/triangle changes
            report_text += "## Changes Made\n\n"
            
            if "vertex_count_change" in repair_report:
                count_change = repair_report["vertex_count_change"]
                if count_change > 0:
                    report_text += f"- Added {count_change} vertices\n"
                elif count_change < 0:
                    report_text += f"- Removed {abs(count_change)} vertices\n"
                else:
                    report_text += "- No change in vertex count\n"
            
            if "triangle_count_change" in repair_report:
                count_change = repair_report["triangle_count_change"]
                if count_change > 0:
                    report_text += f"- Added {count_change} triangles\n"
                elif count_change < 0:
                    report_text += f"- Removed {abs(count_change)} triangles\n"
                else:
                    report_text += "- No change in triangle count\n"
            
            # Add watertight status change
            if ("initial_metrics" in repair_report and "final_metrics" in repair_report and
                "is_watertight" in repair_report["initial_metrics"] and
                "is_watertight" in repair_report["final_metrics"]):
                
                initial_watertight = repair_report["initial_metrics"]["is_watertight"]
                final_watertight = repair_report["final_metrics"]["is_watertight"]
                
                if not initial_watertight and final_watertight:
                    report_text += "- Made the mesh watertight\n"
                elif initial_watertight and not final_watertight:
                    report_text += "- Warning: Mesh is no longer watertight\n"
                elif initial_watertight and final_watertight:
                    report_text += "- Preserved watertight mesh\n"
                else:
                    report_text += "- Could not make mesh watertight\n"
            
            # Add simplification results if available
            if "simplification" in repair_report:
                simplify = repair_report["simplification"]
                report_text += "\n## Simplification Results\n\n"
                
                if "status" in simplify:
                    if simplify["status"] == "success":
                        report_text += f"- Successfully simplified mesh\n"
                        
                        if "initial_triangles" in simplify and "final_triangles" in simplify:
                            initial = simplify["initial_triangles"]
                            final = simplify["final_triangles"]
                            reduction = simplify.get("reduction_percentage", 0)
                            report_text += f"- Reduced from {initial} to {final} triangles ({reduction:.1f}% reduction)\n"
                    else:
                        report_text += f"- {simplify['status']}\n"
            
            # Add file info
            report_text += "\n## Output Files\n\n"
            report_text += f"- PLY: {os.path.basename(ply_path)}\n"
            report_text += f"- OBJ: {os.path.basename(obj_path)}\n"
            
            # Insert the report text
            self.quality_report_text.insert(1.0, report_text)
        
        # Update preview image if available
        if viz_path and os.path.exists(viz_path):
            try:
                from PIL import Image, ImageTk
                
                # Load the image
                image = Image.open(viz_path)
                
                # Resize to fit the preview area
                max_width = 600
                max_height = 400
                
                if image.width > max_width or image.height > max_height:
                    ratio = min(max_width / image.width, max_height / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Update image label
                if self.image_label:
                    self.image_label.config(image=photo)
                    self.image_label.image = photo  # Keep a reference
                
            except Exception as img_error:
                print(f"Error displaying image: {img_error}")
        
        # Refresh model list
        self.refresh_model_list()
        
        # Show success message
        messagebox.showinfo(
            "Repair Complete",
            f"Model repaired successfully.\n"
            f"Output files saved to:\n"
            f"- {ply_path}\n"
            f"- {obj_path}"
        )
    
    def run_refinement_sequence(self):
        """Run the complete 3D refinement sequence on the selected model"""
        if not self.open3d_available:
            messagebox.showwarning("Open3D Not Available", "Open3D is required for the refinement sequence")
            return
            
        # Get selected model
        model_path = self.get_selected_model_path()
        if not model_path:
            return
            
        # Start progress indicator
        self.update_status("Running refinement sequence...", -1)
        
        # Run in background thread
        threading.Thread(target=self._run_refinement_sequence, args=(model_path,), daemon=True).start()
    
    def _run_refinement_sequence(self, model_path):
        """Run full refinement sequence in background thread"""
        try:
            # Import the refinement sequence module
            from Div_AI_Agent_Focus_1.refinement_3d_sequence import Model3DRefinementSequence
            
            # Initialize refiner
            refiner = Model3DRefinementSequence()
            
            # Execute full sequence
            results = refiner.execute_full_sequence(model_path)
            
            # Update UI in main thread
            self.parent.root.after(0, lambda: self._update_refinement_ui(results))
            
        except Exception as e:
            print(f"Error in refinement sequence: {e}")
            import traceback
            traceback.print_exc()
            
            self.parent.root.after(0, lambda: messagebox.showerror(
                "Refinement Error",
                f"Failed to run refinement sequence: {str(e)}"
            ))
            self.parent.root.after(0, lambda: self.update_status("Refinement failed", 0))
    
    def _update_refinement_ui(self, results):
        """Update UI after refinement sequence"""
        # Update progress
        self.update_status("Refinement sequence complete", 100)
        
        # Check if refinement was successful
        if not results.get("final_model"):
            messagebox.showerror(
                "Refinement Failed",
                "The refinement sequence did not produce a valid output model."
            )
            return
            
        # Update quality report text
        if self.quality_report_text:
            self.quality_report_text.delete(1.0, tk.END)
            
            # Create refinement report
            report_text = "# 3D Refinement Sequence Report\n\n"
            
            # Add sequence overview
            report_text += "## Refinement Sequence\n\n"
            report_text += f"- **Input Model**: {os.path.basename(results.get('input_model', 'Unknown'))}\n"
            report_text += f"- **Final Model**: {os.path.basename(results.get('final_model', 'Unknown'))}\n"
            report_text += f"- **Sequence Start**: {results.get('sequence_start', 'Unknown')}\n"
            report_text += f"- **Sequence End**: {results.get('sequence_end', 'Unknown')}\n\n"
            
            # Add stage results
            stages = results.get("stages", {})
            report_text += "## Stage Results\n\n"
            
            # Open3D stage
            if "open3d" in stages:
                open3d_stage = stages["open3d"]
                report_text += "### Open3D Stage\n\n"
                
                if open3d_stage.get("success", False):
                    report_text += "- Status: ✅ Success\n"
                    
                    # Add improvement metrics
                    if "improvement_metrics" in open3d_stage:
                        metrics = open3d_stage["improvement_metrics"]
                        
                        if "vertex_reduction" in metrics:
                            report_text += f"- Vertex Reduction: {metrics['vertex_reduction']:.1f}%\n"
                            
                        if "triangle_reduction" in metrics:
                            report_text += f"- Triangle Reduction: {metrics['triangle_reduction']:.1f}%\n"
                            
                        if "is_watertight" in metrics:
                            report_text += f"- Watertight: {metrics['is_watertight']}\n"
                        
                        # Add operations applied
                        if "refinements_applied" in metrics:
                            report_text += "\n**Operations Applied:**\n\n"
                            for op in metrics["refinements_applied"]:
                                report_text += f"- {op}\n"
                else:
                    report_text += "- Status: ❌ Failed\n"
                    if "error" in open3d_stage:
                        report_text += f"- Error: {open3d_stage['error']}\n"
                
                report_text += "\n"
            
            # Blender stage
            if "blender" in stages:
                blender_stage = stages["blender"]
                report_text += "### Blender Stage\n\n"
                
                if blender_stage.get("success", False):
                    report_text += "- Status: ✅ Success\n"
                    
                    # Add enhancements
                    if "enhancements_applied" in blender_stage:
                        report_text += "\n**Enhancements Applied:**\n\n"
                        for enh in blender_stage["enhancements_applied"]:
                            report_text += f"- {enh}\n"
                else:
                    report_text += "- Status: ❌ Failed\n"
                    if "error" in blender_stage:
                        report_text += f"- Error: {blender_stage['error']}\n"
                
                report_text += "\n"
            
            # O3DE stage
            if "o3de" in stages:
                o3de_stage = stages["o3de"]
                report_text += "### O3DE Stage\n\n"
                
                if o3de_stage.get("success", False):
                    report_text += "- Status: ✅ Success\n"
                    
                    # Add validation scores
                    if "validation_score" in o3de_stage:
                        report_text += f"- Validation Score: {o3de_stage['validation_score']:.1f}%\n"
                    
                    if "functional_score" in o3de_stage:
                        report_text += f"- Functional Score: {o3de_stage['functional_score']:.1f}%\n"
                    
                    if "combined_score" in o3de_stage:
                        report_text += f"- Combined Score: {o3de_stage['combined_score']:.1f}%\n"
                    
                    if "physics_ready" in o3de_stage:
                        status = "Yes" if o3de_stage["physics_ready"] else "No"
                        report_text += f"- Physics Ready: {status}\n"
                    
                    # Add validation results
                    if "validation_results" in o3de_stage:
                        report_text += "\n**Validation Tests:**\n\n"
                        for test in o3de_stage["validation_results"]:
                            passed = "✅ Pass" if test.get("passed", False) else "❌ Fail"
                            report_text += f"- {test.get('name', 'Unknown')}: {passed}\n"
                else:
                    report_text += "- Status: ❌ Failed\n"
                    if "error" in o3de_stage:
                        report_text += f"- Error: {o3de_stage['error']}\n"
                    elif "note" in o3de_stage:
                        report_text += f"- Note: {o3de_stage['note']}\n"
                
                report_text += "\n"
            
            # Final metrics
            if "metrics" in results:
                metrics = results["metrics"]
                report_text += "## Performance Metrics\n\n"
                
                # Add final performance metrics
                report_text += "### Final Metrics\n\n"
                
                if "performance_metrics" in metrics:
                    perf = metrics["performance_metrics"]
                    for metric, value in perf.items():
                        report_text += f"- {metric.replace('_', ' ').title()}: {value}\n"
                
                report_text += "\n"
            
            # Insert the report text
            self.quality_report_text.insert(1.0, report_text)
        
        # Try to display visualizations
        try:
            # Look for visualization images
            viz_outputs = {}
            
            # Open3D visualizations
            if ("stages" in results and "open3d" in results["stages"] and
                "visualization_paths" in results["stages"]["open3d"]):
                
                paths = results["stages"]["open3d"]["visualization_paths"]
                for i, path in enumerate(paths):
                    if os.path.exists(path):
                        viz_outputs[f"open3d_view_{i}"] = path
            
            # Update preview
            if viz_outputs:
                self._show_all_images(viz_outputs)
                
        except Exception as img_error:
            print(f"Error handling visualizations: {img_error}")
        
        # Refresh model list
        self.refresh_model_list()
        
        # Show success message
        messagebox.showinfo(
            "Refinement Complete",
            f"Refinement sequence completed successfully.\n"
            f"Final model: {os.path.basename(results.get('final_model', 'Unknown'))}"
        )
    
    def export_model(self):
        """Export the selected model with material properties"""
        if not self.open3d_available:
            messagebox.showwarning("Open3D Not Available", "Open3D is required for model export")
            return
            
        # Get selected model
        model_path = self.get_selected_model_path()
        if not model_path:
            return
            
        # Choose export format and destination
        formats = [
            ("PLY Files", "*.ply"),
            ("OBJ Files", "*.obj"),
            ("STL Files", "*.stl")
        ]
        
        export_path = filedialog.asksaveasfilename(
            title="Export Model As",
            filetypes=formats,
            defaultextension=".ply",
            initialfile=os.path.basename(model_path).replace(
                os.path.splitext(model_path)[1], 
                "_exported.ply"
            )
        )
        
        if not export_path:
            return
            
        # Get material type
        material_type = None
        if self.physics_available:
            material_name = self.material_var.get()
            for mt in MaterialType:
                if mt.value == material_name:
                    material_type = mt
                    break
        
        # Start export
        self.update_status(f"Exporting model to {os.path.basename(export_path)}...", -1)
        
        # Run in background thread
        threading.Thread(
            target=self._run_model_export, 
            args=(model_path, export_path, material_type),
            daemon=True
        ).start()
    
    def _run_model_export(self, model_path, export_path, material_type):
        """Run model export in background thread"""
        try:
            # Import Open3D and export utility
            import open3d as o3d
            from Div_AI_Agent_Focus_1.open3d_utils import MeshExportImport
            
            # Load mesh
            mesh = o3d.io.read_triangle_mesh(model_path)
            
            if not mesh.has_vertices():
                self.parent.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Could not load mesh from file: {model_path}"
                ))
                self.parent.root.after(0, lambda: self.update_status("Export failed", 0))
                return
            
            # Add custom properties
            custom_props = {
                "exported_by": "GlowingGoldenGlobe GUI",
                "export_date": datetime.now().isoformat(),
                "source_file": os.path.basename(model_path)
            }
            
            # Export with material properties
            result = MeshExportImport.export_mesh_with_materials(
                mesh, export_path, material_type, custom_props
            )
            
            # Update UI in main thread
            self.parent.root.after(0, lambda: self._update_export_ui(result))
            
        except Exception as e:
            print(f"Error in model export: {e}")
            import traceback
            traceback.print_exc()
            
            self.parent.root.after(0, lambda: messagebox.showerror(
                "Export Error",
                f"Failed to export model: {str(e)}"
            ))
            self.parent.root.after(0, lambda: self.update_status("Export failed", 0))
    
    def _update_export_ui(self, result):
        """Update UI after model export"""
        # Update progress
        self.update_status("Export complete", 100)
        
        # Check for error
        if "error" in result:
            messagebox.showerror("Export Error", f"Failed to export model: {result['error']}")
            return
            
        # Show success message
        messagebox.showinfo(
            "Export Complete",
            f"Model exported successfully.\n"
            f"File: {result.get('file_path', 'Unknown')}\n"
            f"Metadata: {result.get('metadata_path', 'None')}"
        )
    
    def view_in_blender(self):
        """Open the selected model in Blender"""
        # Get selected model
        model_path = self.get_selected_model_path()
        if not model_path:
            return
            
        try:
            if platform.system() == "Windows":
                # Try to find Blender in common locations
                blender_paths = [
                    r"C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
                    r"C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",
                    r"C:\\Program Files\\Blender Foundation\\Blender 3.5\\blender.exe"
                ]
                
                blender_exe = None
                for path in blender_paths:
                    if os.path.exists(path):
                        blender_exe = path
                        break
                        
                if blender_exe:
                    subprocess.Popen([blender_exe, model_path])
                else:
                    # Try to use system association
                    os.startfile(model_path)
            else:
                # On Linux/Mac, try to use blender command
                subprocess.Popen(["blender", model_path])
                
            # Update status
            self.update_status(f"Opened {os.path.basename(model_path)} in Blender", 100)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open model in Blender: {str(e)}"
            )


def setup_open3d_tab(gui_instance):
    """Set up the Open3D tab in the GUI"""
    if not hasattr(gui_instance, 'notebook'):
        return None
        
    # Create and setup the Open3D integration
    open3d_integration = Open3DGUIIntegration(gui_instance)
    open3d_integration.setup_ui(gui_instance.notebook)
    
    return open3d_integration


# Main function for testing in standalone mode
if __name__ == "__main__":
    # Test if Open3D is available
    if not OPEN3D_AVAILABLE:
        print("Open3D is not available. Please install it with 'pip install open3d'")
        sys.exit(1)
        
    # Create a simple root window for testing
    root = tk.Tk()
    root.title("Open3D Integration Test")
    root.geometry("800x600")
    
    # Add a notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create mock parent with required attributes
    class MockParent:
        def __init__(self, root):
            self.root = root
            self.notebook = notebook
    
    parent = MockParent(root)
    
    # Create and setup the Open3D integration
    integration = Open3DGUIIntegration(parent)
    integration.setup_ui(notebook)
    
    # Start main loop
    root.mainloop()