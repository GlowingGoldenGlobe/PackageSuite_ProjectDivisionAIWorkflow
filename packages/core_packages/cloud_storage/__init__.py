"""
Cloud Storage Module for GlowingGoldenGlobe Model Components

This package provides functionality for storing, retrieving, and managing model
components in various cloud storage services including AWS S3 and Azure Blob Storage.
"""

from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig
from cloud_storage.sync_module import StorageSynchronizer, SyncConfig
from cloud_storage.dashboard_integration import integrate_cloud_storage, add_cloud_storage_to_menu

__version__ = '1.0.0'