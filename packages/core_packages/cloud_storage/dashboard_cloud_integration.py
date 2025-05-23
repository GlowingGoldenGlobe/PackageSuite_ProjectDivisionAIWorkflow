"""
Dashboard Integration for Cloud Storage

This module integrates the cloud storage functionality with the visualization dashboard.
"""

import os
import json
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional, Callable
import threading
import queue
from datetime import datetime

from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig
from cloud_storage.aws_storage_provider import AWSS3StorageProvider
from cloud_storage.azure_storage_provider import AzureBlobStorageProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_storage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CloudDashboardIntegration:
    """
    Class for integrating cloud storage with the visualization dashboard.
    """
    
    def __init__(self, parent_frame, dashboard=None, status_callback=None):
        """
        Initialize the cloud storage dashboard integration.
        
        Args:
            parent_frame: The tkinter frame to add the cloud storage UI to
            dashboard: Optional reference to the main dashboard
            status_callback: Optional callback for status updates
        """
        self.parent = parent_frame
        self.dashboard = dashboard
        self.status_callback = status_callback
        
        # Cloud storage manager
        self.storage_manager = None
        
        # UI elements
        self.cloud_frame = None
        self.provider_var = tk.StringVar(value="aws")
        self.component_listbox = None
        self.status_label = None
        
        # Task queue for background operations
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.running = True
        
        # Initialize the UI
        self.setup_ui()
        
        # Start background worker
        self.start_worker_thread()
    
    def setup_ui(self):
        """Set up the cloud storage UI"""
        # Create main frame
        self.cloud_frame = ttk.LabelFrame(self.parent, text="Cloud Storage")
        self.cloud_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top frame for provider selection and connect button
        top_frame = ttk.Frame(self.cloud_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Provider selection
        ttk.Label(top_frame, text="Provider:").pack(side=tk.LEFT, padx=5)
        provider_combobox = ttk.Combobox(
            top_frame, 
            textvariable=self.provider_var,
            values=["aws", "azure", "mock"],
            state="readonly",
            width=10
        )
        provider_combobox.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        ttk.Button(
            top_frame, 
            text="Settings", 
            command=self.show_settings
        ).pack(side=tk.LEFT, padx=5)
        
        # Connect button
        ttk.Button(
            top_frame, 
            text="Connect", 
            command=self.connect_to_cloud
        ).pack(side=tk.LEFT, padx=5)
        
        # Create middle frame for component list and operations
        middle_frame = ttk.Frame(self.cloud_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Component list
        list_frame = ttk.LabelFrame(middle_frame, text="Components in Cloud")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame for the listbox and scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox with scrollbar
        self.component_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set
        )
        self.component_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.component_listbox.yview)
        
        # Refresh button under listbox
        ttk.Button(
            list_frame, 
            text="Refresh List", 
            command=self.refresh_component_list
        ).pack(side=tk.BOTTOM, pady=5)
        
        # Operations frame
        operations_frame = ttk.LabelFrame(middle_frame, text="Operations")
        operations_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Upload button
        ttk.Button(
            operations_frame, 
            text="Upload Component",
            command=self.upload_component
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Upload selected button 
        ttk.Button(
            operations_frame, 
            text="Upload Selected", 
            command=self.upload_selected_components
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Download button
        ttk.Button(
            operations_frame, 
            text="Download Selected",
            command=self.download_selected_components
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # View metadata button
        ttk.Button(
            operations_frame, 
            text="View Metadata",
            command=self.view_metadata
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Delete button
        ttk.Button(
            operations_frame, 
            text="Delete Selected",
            command=self.delete_selected_components
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Batch operations button
        ttk.Button(
            operations_frame, 
            text="Batch Operations",
            command=self.show_batch_operations
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Synchronize button
        ttk.Button(
            operations_frame, 
            text="Synchronize",
            command=self.synchronize_components
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Status frame at the bottom
        status_frame = ttk.Frame(self.cloud_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def update_status(self, message: str):
        """Update the status label with a message"""
        if self.status_label:
            self.status_label.config(text=message)
        
        if self.status_callback:
            self.status_callback(message)
        
        logger.info(message)
    
    def show_settings(self):
        """Show cloud provider settings dialog"""
        # Create settings dialog
        settings_dialog = tk.Toplevel(self.parent)
        settings_dialog.title(f"{self.provider_var.get().upper()} Settings")
        settings_dialog.geometry("500x400")
        settings_dialog.resizable(True, True)
        
        # Make dialog modal
        settings_dialog.transient(self.parent)
        settings_dialog.grab_set()
        
        # Create settings frame
        settings_frame = ttk.Frame(settings_dialog, padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Provider label
        provider_name = self.provider_var.get().upper()
        ttk.Label(
            settings_frame, 
            text=f"{provider_name} Configuration",
            font=("Helvetica", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Load existing settings if available
        config_file = f"cloud_storage_{self.provider_var.get()}_config.json"
        config = {}
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Common settings
        row = 1
        
        # Credentials file
        ttk.Label(settings_frame, text="Credentials File:").grid(row=row, column=0, sticky=tk.W, pady=2)
        credentials_var = tk.StringVar(value=config.get("credentials_file", ""))
        credentials_entry = ttk.Entry(settings_frame, textvariable=credentials_var, width=40)
        credentials_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        ttk.Button(
            settings_frame, 
            text="Browse...",
            command=lambda: credentials_var.set(filedialog.askopenfilename())
        ).grid(row=row, column=2, pady=2)
        
        row += 1
        
        # Provider-specific settings
        if self.provider_var.get() == "aws":
            # Region
            ttk.Label(settings_frame, text="Region:").grid(row=row, column=0, sticky=tk.W, pady=2)
            region_var = tk.StringVar(value=config.get("region", "us-east-1"))
            ttk.Entry(settings_frame, textvariable=region_var).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
            
            # Bucket name
            ttk.Label(settings_frame, text="Bucket Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
            bucket_var = tk.StringVar(value=config.get("bucket_name", ""))
            ttk.Entry(settings_frame, textvariable=bucket_var).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
        
        elif self.provider_var.get() == "azure":
            # Container name
            ttk.Label(settings_frame, text="Container Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
            container_var = tk.StringVar(value=config.get("container_name", ""))
            ttk.Entry(settings_frame, textvariable=container_var).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
        
        # Common settings continued
        # Prefix
        ttk.Label(settings_frame, text="Prefix:").grid(row=row, column=0, sticky=tk.W, pady=2)
        prefix_var = tk.StringVar(value=config.get("prefix", "model_components"))
        ttk.Entry(settings_frame, textvariable=prefix_var).grid(row=row, column=1, sticky=tk.W, pady=2)
        
        row += 1
        
        # Encryption
        encryption_var = tk.BooleanVar(value=config.get("encryption", True))
        ttk.Checkbutton(
            settings_frame, 
            text="Enable Encryption", 
            variable=encryption_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        row += 1
        
        # Public access
        public_access_var = tk.BooleanVar(value=config.get("public_access", False))
        ttk.Checkbutton(
            settings_frame, 
            text="Allow Public Access", 
            variable=public_access_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        row += 1
        
        # Save and Cancel buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_settings(
                settings_dialog,
                {
                    "provider": self.provider_var.get(),
                    "credentials_file": credentials_var.get(),
                    "region": region_var.get() if self.provider_var.get() == "aws" else None,
                    "bucket_name": bucket_var.get() if self.provider_var.get() == "aws" else None,
                    "container_name": container_var.get() if self.provider_var.get() == "azure" else None,
                    "prefix": prefix_var.get(),
                    "encryption": encryption_var.get(),
                    "public_access": public_access_var.get()
                }
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=settings_dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Wait for the dialog to be closed
        settings_dialog.wait_window()
    
    def save_settings(self, dialog, settings):
        """Save cloud provider settings"""
        try:
            # Remove None values
            settings = {k: v for k, v in settings.items() if v is not None}
            
            # Save to file
            config_file = f"cloud_storage_{settings['provider']}_config.json"
            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.update_status(f"Settings saved to {config_file}")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            logger.error(f"Failed to save settings: {e}")
    
    def connect_to_cloud(self):
        """Connect to the selected cloud provider"""
        provider = self.provider_var.get()
        
        # Load configuration
        config_file = f"cloud_storage_{provider}_config.json"
        
        if not os.path.exists(config_file) and provider != "mock":
            messagebox.showinfo("Configuration Required", f"Please configure {provider.upper()} settings first.")
            self.show_settings()
            return
        
        # Load configuration if not mock
        if provider != "mock":
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
                logger.error(f"Failed to load configuration: {e}")
                return
        else:
            # Mock configuration
            config_data = {
                "provider": "mock",
                "prefix": "model_components",
                "encryption": False,
                "public_access": False
            }
        
        # Create CloudStorageConfig
        config = CloudStorageConfig(
            provider=config_data["provider"],
            credentials_file=config_data.get("credentials_file"),
            region=config_data.get("region"),
            bucket_name=config_data.get("bucket_name"),
            container_name=config_data.get("container_name"),
            prefix=config_data.get("prefix", "model_components"),
            encryption=config_data.get("encryption", True),
            public_access=config_data.get("public_access", False)
        )
        
        # Connect in background to avoid UI freeze
        self.update_status(f"Connecting to {provider.upper()}...")
        self.add_task(self._connect_task, config)
    
    def _connect_task(self, config):
        """Background task for connecting to cloud provider"""
        try:
            # Create storage manager
            self.storage_manager = CloudStorageManager(config)
            
            # Authenticate
            if self.storage_manager.authenticate():
                # Update UI
                self.parent.after(0, lambda: self.update_status(f"Connected to {config.provider.upper()}"))
                self.parent.after(0, self.refresh_component_list)
            else:
                # Show error
                self.parent.after(0, lambda: messagebox.showerror(
                    "Connection Failed", 
                    f"Failed to authenticate with {config.provider.upper()}. Check logs for details."
                ))
                self.parent.after(0, lambda: self.update_status("Connection failed"))
        except Exception as e:
            # Show error
            error_msg = f"Error connecting to {config.provider.upper()}: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Connection error"))
            logger.error(error_msg)
    
    def refresh_component_list(self):
        """Refresh the list of components in cloud storage"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Clear listbox
        self.component_listbox.delete(0, tk.END)
        
        # Update status
        self.update_status("Refreshing component list...")
        
        # Get components in background
        self.add_task(self._refresh_list_task)
    
    def _refresh_list_task(self):
        """Background task for refreshing component list"""
        try:
            # Get component list
            components = self.storage_manager.list_components()
            
            # Update UI
            self.parent.after(0, lambda: self._update_component_list(components))
            self.parent.after(0, lambda: self.update_status(f"Found {len(components)} components"))
        except Exception as e:
            # Show error
            error_msg = f"Error refreshing component list: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Refresh Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Refresh error"))
            logger.error(error_msg)
    
    def _update_component_list(self, components):
        """Update the component listbox with retrieved components"""
        # Clear listbox
        self.component_listbox.delete(0, tk.END)
        
        # Add components to listbox
        for component in components:
            self.component_listbox.insert(tk.END, component)
    
    def upload_component(self):
        """Upload a component to cloud storage"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Get files to upload
        file_paths = filedialog.askopenfilenames(
            title="Select Components to Upload",
            filetypes=[
                ("All Files", "*.*"),
                ("JSON Files", "*.json"),
                ("Blend Files", "*.blend"),
                ("FBX Files", "*.fbx"),
                ("STL Files", "*.stl"),
                ("GLTF Files", "*.gltf")
            ]
        )
        
        if not file_paths:
            return
        
        # Upload files in background
        self.update_status(f"Uploading {len(file_paths)} component(s)...")
        self.add_task(self._upload_components_task, file_paths)
    
    def _upload_components_task(self, file_paths):
        """Background task for uploading components"""
        try:
            # Upload files
            results = self.storage_manager.batch_upload_components(file_paths)
            
            # Count successes and failures
            successes = sum(1 for success in results.values() if success)
            failures = sum(1 for success in results.values() if not success)
            
            # Update UI
            self.parent.after(0, lambda: self.update_status(f"Uploaded {successes} component(s), {failures} failed"))
            self.parent.after(0, self.refresh_component_list)
        except Exception as e:
            # Show error
            error_msg = f"Error uploading components: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Upload Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Upload error"))
            logger.error(error_msg)
    
    def upload_selected_components(self):
        """Upload selected components from the visualization dashboard"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        if not self.dashboard:
            messagebox.showinfo("No Dashboard", "Visualization dashboard not available.")
            return
        
        # TODO: Get selected components from dashboard
        # This is a placeholder; implement according to dashboard API
        try:
            selected_components = self.dashboard.get_selected_components()
            
            if not selected_components:
                messagebox.showinfo("No Selection", "Please select components in the dashboard first.")
                return
            
            # Upload components in background
            self.update_status(f"Uploading {len(selected_components)} component(s)...")
            self.add_task(self._upload_selected_task, selected_components)
        except AttributeError:
            messagebox.showinfo("Not Implemented", "This feature requires dashboard integration.")
    
    def _upload_selected_task(self, selected_components):
        """Background task for uploading selected components"""
        try:
            # Upload components
            results = self.storage_manager.batch_upload_components(
                [component["path"] for component in selected_components],
                [component["id"] for component in selected_components]
            )
            
            # Count successes and failures
            successes = sum(1 for success in results.values() if success)
            failures = sum(1 for success in results.values() if not success)
            
            # Update UI
            self.parent.after(0, lambda: self.update_status(f"Uploaded {successes} component(s), {failures} failed"))
            self.parent.after(0, self.refresh_component_list)
        except Exception as e:
            # Show error
            error_msg = f"Error uploading selected components: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Upload Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Upload error"))
            logger.error(error_msg)
    
    def download_selected_components(self):
        """Download selected components from cloud storage"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Get selected components
        selected_indices = self.component_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select components to download.")
            return
        
        # Get selected component IDs
        selected_components = [self.component_listbox.get(i) for i in selected_indices]
        
        # Get download directory
        download_dir = filedialog.askdirectory(title="Select Download Directory")
        
        if not download_dir:
            return
        
        # Download components in background
        self.update_status(f"Downloading {len(selected_components)} component(s)...")
        self.add_task(self._download_components_task, selected_components, download_dir)
    
    def _download_components_task(self, selected_components, download_dir):
        """Background task for downloading components"""
        try:
            # Download components
            results = self.storage_manager.batch_download_components(selected_components, download_dir)
            
            # Count successes and failures
            successes = sum(1 for success in results.values() if success)
            failures = sum(1 for success in results.values() if not success)
            
            # Update UI
            self.parent.after(0, lambda: self.update_status(f"Downloaded {successes} component(s), {failures} failed"))
            
            # Open download directory if at least one component was downloaded successfully
            if successes > 0:
                self.parent.after(0, lambda: os.startfile(download_dir) if os.name == 'nt' else None)
        except Exception as e:
            # Show error
            error_msg = f"Error downloading components: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Download Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Download error"))
            logger.error(error_msg)
    
    def view_metadata(self):
        """View metadata for selected component"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Get selected component
        selected_indices = self.component_listbox.curselection()
        
        if not selected_indices or len(selected_indices) > 1:
            messagebox.showinfo("Invalid Selection", "Please select a single component.")
            return
        
        # Get selected component ID
        component_id = self.component_listbox.get(selected_indices[0])
        
        # Get metadata in background
        self.update_status(f"Getting metadata for {component_id}...")
        self.add_task(self._get_metadata_task, component_id)
    
    def _get_metadata_task(self, component_id):
        """Background task for getting component metadata"""
        try:
            # Get metadata
            metadata = self.storage_manager.get_component_metadata(component_id)
            
            # Update UI
            self.parent.after(0, lambda: self._show_metadata_dialog(component_id, metadata))
            self.parent.after(0, lambda: self.update_status("Metadata retrieved"))
        except Exception as e:
            # Show error
            error_msg = f"Error getting metadata: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Metadata Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Metadata error"))
            logger.error(error_msg)
    
    def _show_metadata_dialog(self, component_id, metadata):
        """Show metadata dialog"""
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Metadata: {component_id}")
        dialog.geometry("400x300")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Component ID
        ttk.Label(
            frame, 
            text=f"Component: {component_id}",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Create text widget for metadata
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, width=50, height=15)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Insert metadata
        text_widget.insert(tk.END, json.dumps(metadata, indent=4))
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=dialog.destroy
        ).pack(pady=(10, 0))
    
    def delete_selected_components(self):
        """Delete selected components from cloud storage"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Get selected components
        selected_indices = self.component_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select components to delete.")
            return
        
        # Get selected component IDs
        selected_components = [self.component_listbox.get(i) for i in selected_indices]
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_components)} component(s)?\n\nThis action cannot be undone."
        ):
            return
        
        # Delete components in background
        self.update_status(f"Deleting {len(selected_components)} component(s)...")
        self.add_task(self._delete_components_task, selected_components)
    
    def _delete_components_task(self, selected_components):
        """Background task for deleting components"""
        try:
            # Delete components
            results = {}
            for component_id in selected_components:
                results[component_id] = self.storage_manager.delete_component(component_id)
            
            # Count successes and failures
            successes = sum(1 for success in results.values() if success)
            failures = sum(1 for success in results.values() if not success)
            
            # Update UI
            self.parent.after(0, lambda: self.update_status(f"Deleted {successes} component(s), {failures} failed"))
            self.parent.after(0, self.refresh_component_list)
        except Exception as e:
            # Show error
            error_msg = f"Error deleting components: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Delete Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Delete error"))
            logger.error(error_msg)
    
    def show_batch_operations(self):
        """Show batch operations dialog"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Batch Operations")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            frame, 
            text="Batch Operations",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Batch upload section
        upload_frame = ttk.LabelFrame(frame, text="Batch Upload")
        upload_frame.pack(fill=tk.X, pady=5)
        
        # Upload directory
        upload_dir_frame = ttk.Frame(upload_frame)
        upload_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(upload_dir_frame, text="Directory:").pack(side=tk.LEFT, padx=5)
        
        upload_dir_var = tk.StringVar()
        upload_dir_entry = ttk.Entry(upload_dir_frame, textvariable=upload_dir_var, width=30)
        upload_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            upload_dir_frame,
            text="Browse...",
            command=lambda: upload_dir_var.set(filedialog.askdirectory(title="Select Upload Directory"))
        ).pack(side=tk.LEFT, padx=5)
        
        # File pattern
        pattern_frame = ttk.Frame(upload_frame)
        pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="File Pattern:").pack(side=tk.LEFT, padx=5)
        
        pattern_var = tk.StringVar(value="*.blend *.fbx *.stl *.gltf *.json")
        pattern_entry = ttk.Entry(pattern_frame, textvariable=pattern_var, width=30)
        pattern_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Upload button
        ttk.Button(
            upload_frame,
            text="Upload Files",
            command=lambda: self._batch_upload(upload_dir_var.get(), pattern_var.get(), dialog)
        ).pack(padx=5, pady=5)
        
        # Batch download section
        download_frame = ttk.LabelFrame(frame, text="Batch Download")
        download_frame.pack(fill=tk.X, pady=5)
        
        # Download pattern
        download_pattern_frame = ttk.Frame(download_frame)
        download_pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(download_pattern_frame, text="Component Pattern:").pack(side=tk.LEFT, padx=5)
        
        download_pattern_var = tk.StringVar()
        download_pattern_entry = ttk.Entry(download_pattern_frame, textvariable=download_pattern_var, width=30)
        download_pattern_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Download directory
        download_dir_frame = ttk.Frame(download_frame)
        download_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(download_dir_frame, text="Download To:").pack(side=tk.LEFT, padx=5)
        
        download_dir_var = tk.StringVar(value="downloads")
        download_dir_entry = ttk.Entry(download_dir_frame, textvariable=download_dir_var, width=30)
        download_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            download_dir_frame,
            text="Browse...",
            command=lambda: download_dir_var.set(filedialog.askdirectory(title="Select Download Directory"))
        ).pack(side=tk.LEFT, padx=5)
        
        # Download button
        ttk.Button(
            download_frame,
            text="Download Components",
            command=lambda: self._batch_download(download_pattern_var.get(), download_dir_var.get(), dialog)
        ).pack(padx=5, pady=5)
        
        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=dialog.destroy
        ).pack(pady=(10, 0))
    
    def _batch_upload(self, directory, pattern, dialog=None):
        """Perform batch upload of files"""
        if not directory:
            messagebox.showerror("Error", "Please select a directory.")
            return
        
        # Parse pattern
        patterns = pattern.split() if pattern else ["*"]
        
        # Find matching files
        file_paths = []
        for pattern in patterns:
            import glob
            for file_path in glob.glob(os.path.join(directory, pattern)):
                if os.path.isfile(file_path):
                    file_paths.append(file_path)
        
        if not file_paths:
            messagebox.showinfo("No Files", f"No files matching pattern '{pattern}' found in {directory}.")
            return
        
        # Confirm upload
        if not messagebox.askyesno(
            "Confirm Upload",
            f"Upload {len(file_paths)} file(s) to cloud storage?"
        ):
            return
        
        # Close dialog if provided
        if dialog:
            dialog.destroy()
        
        # Upload files in background
        self.update_status(f"Uploading {len(file_paths)} file(s)...")
        self.add_task(self._upload_components_task, file_paths)
    
    def _batch_download(self, pattern, directory, dialog=None):
        """Perform batch download of components"""
        if not directory:
            messagebox.showerror("Error", "Please select a download directory.")
            return
        
        # List components
        all_components = self.storage_manager.list_components()
        
        # Filter by pattern
        if pattern:
            import fnmatch
            components = [c for c in all_components if fnmatch.fnmatch(c, pattern)]
        else:
            components = all_components
        
        if not components:
            messagebox.showinfo("No Components", f"No components matching pattern '{pattern}' found.")
            return
        
        # Confirm download
        if not messagebox.askyesno(
            "Confirm Download",
            f"Download {len(components)} component(s) to {directory}?"
        ):
            return
        
        # Close dialog if provided
        if dialog:
            dialog.destroy()
        
        # Download components in background
        self.update_status(f"Downloading {len(components)} component(s)...")
        self.add_task(self._download_components_task, components, directory)
    
    def synchronize_components(self):
        """Synchronize components between local and cloud storage"""
        if not self.storage_manager:
            messagebox.showinfo("Not Connected", "Please connect to a cloud provider first.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Synchronize Components")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            frame, 
            text="Synchronize Components",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Local directory
        dir_frame = ttk.Frame(frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dir_frame, text="Local Directory:").pack(side=tk.LEFT, padx=5)
        
        dir_var = tk.StringVar(value="agent_outputs")
        dir_entry = ttk.Entry(dir_frame, textvariable=dir_var, width=30)
        dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            dir_frame,
            text="Browse...",
            command=lambda: dir_var.set(filedialog.askdirectory(title="Select Local Directory"))
        ).pack(side=tk.LEFT, padx=5)
        
        # Sync direction
        direction_frame = ttk.LabelFrame(frame, text="Sync Direction")
        direction_frame.pack(fill=tk.X, padx=5, pady=5)
        
        direction_var = tk.StringVar(value="both")
        
        ttk.Radiobutton(
            direction_frame,
            text="Both Directions (Two-way sync)",
            variable=direction_var,
            value="both"
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            direction_frame,
            text="Local to Cloud (Upload missing/newer files)",
            variable=direction_var,
            value="upload"
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            direction_frame,
            text="Cloud to Local (Download missing/newer files)",
            variable=direction_var,
            value="download"
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Options
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        delete_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Delete files that don't exist in source",
            variable=delete_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Overwrite existing files",
            variable=overwrite_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Sync button
        ttk.Button(
            frame,
            text="Start Synchronization",
            command=lambda: self._start_sync(
                dir_var.get(),
                direction_var.get(),
                delete_var.get(),
                overwrite_var.get(),
                dialog
            )
        ).pack(pady=10)
        
        # Close button
        ttk.Button(
            frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(pady=5)
    
    def _start_sync(self, local_dir, direction, delete_files, overwrite, dialog=None):
        """Start synchronization process"""
        if not local_dir:
            messagebox.showerror("Error", "Please select a local directory.")
            return
        
        # Create the directory if it doesn't exist
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        # Close dialog if provided
        if dialog:
            dialog.destroy()
        
        # Start sync in background
        self.update_status("Starting synchronization...")
        self.add_task(
            self._sync_task,
            local_dir,
            direction,
            delete_files,
            overwrite
        )
    
    def _sync_task(self, local_dir, direction, delete_files, overwrite):
        """Background task for synchronization"""
        try:
            # This is a placeholder implementation
            # In a real implementation, we would compare local and cloud files,
            # check timestamps, and perform the necessary operations
            
            # For demonstration purposes, just display the sync options
            result = f"Sync options: Direction={direction}, Delete={delete_files}, Overwrite={overwrite}"
            self.parent.after(0, lambda: self.update_status(result))
            
            # TODO: Implement actual synchronization logic
            # This would involve listing local files, listing cloud files,
            # comparing timestamps, and uploading/downloading as needed
            
            # Refresh component list
            self.parent.after(0, self.refresh_component_list)
        except Exception as e:
            # Show error
            error_msg = f"Error during synchronization: {e}"
            self.parent.after(0, lambda: messagebox.showerror("Sync Error", error_msg))
            self.parent.after(0, lambda: self.update_status("Sync error"))
            logger.error(error_msg)
    
    def start_worker_thread(self):
        """Start background worker thread"""
        self.worker_thread = threading.Thread(target=self._worker_thread)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def _worker_thread(self):
        """Background worker thread function"""
        while self.running:
            try:
                # Get a task from the queue (blocking)
                task = self.task_queue.get(timeout=1.0)
                
                # Execute the task
                func, args = task[0], task[1:]
                func(*args)
                
                # Mark task as done
                self.task_queue.task_done()
            except queue.Empty:
                # No tasks available, just continue
                continue
            except Exception as e:
                # Log the error
                logger.error(f"Error in worker thread: {e}")
                
                # Show error on UI
                error_msg = f"An error occurred: {e}"
                self.parent.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
                self.parent.after(0, lambda: self.update_status("Error occurred"))
                
                # Mark task as done
                self.task_queue.task_done()
    
    def add_task(self, func, *args):
        """Add a task to the background queue"""
        self.task_queue.put((func,) + args)
    
    def shutdown(self):
        """Shut down the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)


# Helper function to create and integrate the cloud storage tab with the dashboard
def create_cloud_storage_tab(notebook, dashboard=None):
    """
    Create a cloud storage tab in the given notebook and return the integration object.
    
    Args:
        notebook: Tkinter notebook widget
        dashboard: Optional reference to the main dashboard
        
    Returns:
        CloudDashboardIntegration: The cloud storage integration object
    """
    # Create a frame for the cloud storage tab
    cloud_frame = ttk.Frame(notebook)
    
    # Add the frame to the notebook
    notebook.add(cloud_frame, text="Cloud Storage")
    
    # Create the cloud storage integration
    cloud_integration = CloudDashboardIntegration(cloud_frame, dashboard)
    
    return cloud_integration