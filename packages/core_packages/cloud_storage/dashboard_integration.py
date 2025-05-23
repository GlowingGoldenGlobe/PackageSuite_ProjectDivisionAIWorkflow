"""
Cloud Storage Dashboard Integration

This module integrates the cloud storage functionality with the main dashboard.
"""

import os
import logging
import tkinter as tk
from tkinter import ttk

from cloud_storage.dashboard_cloud_integration import create_cloud_storage_tab
from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig

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


def integrate_cloud_storage(dashboard_app, notebook):
    """
    Integrate cloud storage with the dashboard application.
    
    Args:
        dashboard_app: The main dashboard application
        notebook: The notebook widget to add the cloud storage tab to
        
    Returns:
        object: The cloud storage integration object
    """
    logger.info("Integrating cloud storage with dashboard")
    
    # Create the cloud storage tab
    cloud_integration = create_cloud_storage_tab(notebook, dashboard_app)
    
    # Register the cloud storage integration with the dashboard
    if hasattr(dashboard_app, 'register_module'):
        dashboard_app.register_module("cloud_storage", cloud_integration)
    
    return cloud_integration


def add_cloud_storage_to_menu(dashboard_app, menu_bar):
    """
    Add cloud storage options to the dashboard menu.
    
    Args:
        dashboard_app: The main dashboard application
        menu_bar: The menu bar to add the cloud storage menu to
    """
    # Create cloud storage menu
    cloud_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Cloud Storage", menu=cloud_menu)
    
    # Add menu items
    cloud_menu.add_command(label="Configure AWS S3...", command=lambda: _show_provider_settings(dashboard_app, "aws"))
    cloud_menu.add_command(label="Configure Azure Blob...", command=lambda: _show_provider_settings(dashboard_app, "azure"))
    cloud_menu.add_separator()
    cloud_menu.add_command(label="Connect to Cloud...", command=lambda: _connect_to_cloud(dashboard_app))
    cloud_menu.add_command(label="Synchronize...", command=lambda: _show_sync_dialog(dashboard_app))
    cloud_menu.add_separator()
    cloud_menu.add_command(label="Cloud Storage Help", command=_show_cloud_help)


def _show_provider_settings(dashboard_app, provider):
    """Show provider settings dialog"""
    # Get cloud integration
    cloud_integration = getattr(dashboard_app, "cloud_storage", None)
    
    if cloud_integration:
        # Set provider
        cloud_integration.provider_var.set(provider)
        
        # Show settings
        cloud_integration.show_settings()
    else:
        # Show error
        tk.messagebox.showerror(
            "Cloud Storage Not Available",
            "Cloud storage integration is not available in the dashboard."
        )


def _connect_to_cloud(dashboard_app):
    """Connect to cloud storage"""
    # Get cloud integration
    cloud_integration = getattr(dashboard_app, "cloud_storage", None)
    
    if cloud_integration:
        # Connect
        cloud_integration.connect_to_cloud()
    else:
        # Show error
        tk.messagebox.showerror(
            "Cloud Storage Not Available",
            "Cloud storage integration is not available in the dashboard."
        )


def _show_sync_dialog(dashboard_app):
    """Show synchronization dialog"""
    # Get cloud integration
    cloud_integration = getattr(dashboard_app, "cloud_storage", None)
    
    if cloud_integration:
        # Show sync dialog
        cloud_integration.synchronize_components()
    else:
        # Show error
        tk.messagebox.showerror(
            "Cloud Storage Not Available",
            "Cloud storage integration is not available in the dashboard."
        )


def _show_cloud_help():
    """Show cloud storage help"""
    # Try to open README with system viewer
    readme_path = os.path.join(os.path.dirname(__file__), "CLOUD_STORAGE_README.md")
    
    if os.path.exists(readme_path):
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(readme_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', readme_path])
            else:  # Linux
                subprocess.call(['xdg-open', readme_path])
        except Exception as e:
            # Show error
            tk.messagebox.showerror(
                "Error Opening Help",
                f"Could not open help file: {e}\n\nThe file is located at: {readme_path}"
            )
    else:
        # Show error
        tk.messagebox.showerror(
            "Help Not Found",
            f"Could not find help file at: {readme_path}"
        )


# Test function to create a standalone cloud storage application
def create_standalone_app():
    """Create a standalone cloud storage application for testing"""
    # Create root window
    root = tk.Tk()
    root.title("Cloud Storage Test App")
    root.geometry("800x600")
    
    # Create frame
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Create notebook
    notebook = ttk.Notebook(frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create cloud storage tab
    cloud_integration = create_cloud_storage_tab(notebook)
    
    # Start main loop
    root.mainloop()
    
    # Clean up
    if hasattr(cloud_integration, 'shutdown'):
        cloud_integration.shutdown()


if __name__ == "__main__":
    # Run standalone app
    create_standalone_app()