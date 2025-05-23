"""
Cloud Storage Module for GlowingGoldenGlobe Model Components

This module provides functionality for storing, retrieving, and managing model
components in various cloud storage services including AWS S3 and Azure Blob Storage.
"""

import os
import json
import logging
import tempfile
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

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

# Constants
MAX_WORKERS = 5
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
MAX_UPLOAD_RETRIES = 3
RETRY_DELAY = 2  # seconds

@dataclass
class CloudStorageConfig:
    """Configuration for cloud storage providers"""
    provider: str
    credentials_file: str = None
    region: str = None
    bucket_name: str = None
    container_name: str = None
    prefix: str = "model_components"
    encryption: bool = True
    public_access: bool = False
    max_workers: int = MAX_WORKERS


class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider"""
        pass
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to cloud storage"""
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from cloud storage"""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = None) -> List[str]:
        """List files in cloud storage"""
        pass
    
    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from cloud storage"""
        pass
    
    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in cloud storage"""
        pass
    
    @abstractmethod
    def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a file in cloud storage"""
        pass


class MockCloudStorageProvider(CloudStorageProvider):
    """Mock implementation for testing without actual cloud services"""
    
    def __init__(self, config: CloudStorageConfig):
        self.config = config
        self.storage_dir = os.path.join(tempfile.gettempdir(), "mock_cloud_storage")
        self.authenticated = False
        
        # Create mock storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Mock cloud storage initialized at {self.storage_dir}")
    
    def authenticate(self) -> bool:
        """Mock authentication"""
        self.authenticated = True
        logger.info("Mock authentication successful")
        return True
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Mock file upload by copying to temp directory"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        try:
            target_path = os.path.join(self.storage_dir, remote_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            with open(local_path, 'rb') as src_file, open(target_path, 'wb') as dst_file:
                dst_file.write(src_file.read())
            
            logger.info(f"Mock uploaded {local_path} to {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Mock upload failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Mock file download by copying from temp directory"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        try:
            source_path = os.path.join(self.storage_dir, remote_path)
            
            if not os.path.exists(source_path):
                logger.error(f"File does not exist in mock storage: {remote_path}")
                return False
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(source_path, 'rb') as src_file, open(local_path, 'wb') as dst_file:
                dst_file.write(src_file.read())
            
            logger.info(f"Mock downloaded {remote_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Mock download failed: {e}")
            return False
    
    def list_files(self, prefix: str = None) -> List[str]:
        """Mock listing files in temporary directory"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return []
        
        try:
            result = []
            base_len = len(self.storage_dir) + 1
            
            for root, _, files in os.walk(self.storage_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = full_path[base_len:]
                    
                    if not prefix or rel_path.startswith(prefix):
                        result.append(rel_path)
            
            return result
        except Exception as e:
            logger.error(f"Mock list failed: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """Mock file deletion"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        try:
            target_path = os.path.join(self.storage_dir, remote_path)
            
            if not os.path.exists(target_path):
                logger.error(f"File does not exist in mock storage: {remote_path}")
                return False
            
            os.remove(target_path)
            logger.info(f"Mock deleted {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Mock deletion failed: {e}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in mock storage"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        target_path = os.path.join(self.storage_dir, remote_path)
        return os.path.exists(target_path)
    
    def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a file in mock storage"""
        if not self.authenticated:
            logger.error("Not authenticated")
            return {}
        
        target_path = os.path.join(self.storage_dir, remote_path)
        
        if not os.path.exists(target_path):
            logger.error(f"File does not exist in mock storage: {remote_path}")
            return {}
        
        try:
            stats = os.stat(target_path)
            return {
                "size": stats.st_size,
                "last_modified": time.ctime(stats.st_mtime),
                "created": time.ctime(stats.st_ctime)
            }
        except Exception as e:
            logger.error(f"Error getting mock file metadata: {e}")
            return {}


class CloudStorageManager:
    """
    Main class for managing cloud storage operations.
    Acts as a facade for different cloud providers.
    """
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize with configuration"""
        self.config = config
        self.provider = self._initialize_provider()
        
        # Initialize ThreadPoolExecutor for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        
        # Cache for file metadata
        self.metadata_cache = {}
        
        # Track operations
        self.operation_log = []
    
    def _initialize_provider(self) -> CloudStorageProvider:
        """Initialize the appropriate cloud storage provider"""
        if self.config.provider.lower() == "mock":
            return MockCloudStorageProvider(self.config)
        elif self.config.provider.lower() == "aws":
            # This will be implemented when adding AWS support
            # return AWSStorageProvider(self.config)
            raise NotImplementedError("AWS provider not yet implemented")
        elif self.config.provider.lower() == "azure":
            # This will be implemented when adding Azure support
            # return AzureStorageProvider(self.config)
            raise NotImplementedError("Azure provider not yet implemented")
        else:
            raise ValueError(f"Unsupported cloud provider: {self.config.provider}")
    
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider"""
        return self.provider.authenticate()
    
    def upload_component(self, component_path: str, component_id: str = None) -> bool:
        """
        Upload a model component to cloud storage.
        
        Args:
            component_path: Local path to the component file
            component_id: Optional ID to use for the component (defaults to filename)
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not os.path.exists(component_path):
            logger.error(f"Component file not found: {component_path}")
            return False
        
        # Use filename as component_id if not provided
        if component_id is None:
            component_id = os.path.basename(component_path)
        
        # Determine remote path
        remote_path = f"{self.config.prefix}/{component_id}"
        
        # Upload file
        success = self.provider.upload_file(component_path, remote_path)
        
        if success:
            # Log the operation
            self.operation_log.append({
                "operation": "upload",
                "component_id": component_id,
                "local_path": component_path,
                "remote_path": remote_path,
                "timestamp": time.time()
            })
            
            # Clear metadata cache for this file
            if remote_path in self.metadata_cache:
                del self.metadata_cache[remote_path]
        
        return success
    
    def download_component(self, component_id: str, destination_path: str = None) -> bool:
        """
        Download a model component from cloud storage.
        
        Args:
            component_id: ID of the component to download
            destination_path: Local path to save the component (defaults to component_id)
            
        Returns:
            bool: True if download successful, False otherwise
        """
        # Determine remote path
        remote_path = f"{self.config.prefix}/{component_id}"
        
        # Default destination path to component_id if not provided
        if destination_path is None:
            destination_path = os.path.join("downloads", component_id)
        
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Download file
        success = self.provider.download_file(remote_path, destination_path)
        
        if success:
            # Log the operation
            self.operation_log.append({
                "operation": "download",
                "component_id": component_id,
                "remote_path": remote_path,
                "local_path": destination_path,
                "timestamp": time.time()
            })
        
        return success
    
    def list_components(self) -> List[str]:
        """
        List all model components in cloud storage.
        
        Returns:
            List[str]: List of component IDs
        """
        # List files with prefix
        files = self.provider.list_files(self.config.prefix)
        
        # Extract component IDs from paths
        prefix_len = len(self.config.prefix) + 1
        component_ids = [f[prefix_len:] for f in files if f.startswith(self.config.prefix + "/")]
        
        return component_ids
    
    def delete_component(self, component_id: str) -> bool:
        """
        Delete a model component from cloud storage.
        
        Args:
            component_id: ID of the component to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        # Determine remote path
        remote_path = f"{self.config.prefix}/{component_id}"
        
        # Delete file
        success = self.provider.delete_file(remote_path)
        
        if success:
            # Log the operation
            self.operation_log.append({
                "operation": "delete",
                "component_id": component_id,
                "remote_path": remote_path,
                "timestamp": time.time()
            })
            
            # Clear metadata cache for this file
            if remote_path in self.metadata_cache:
                del self.metadata_cache[remote_path]
        
        return success
    
    def component_exists(self, component_id: str) -> bool:
        """
        Check if a component exists in cloud storage.
        
        Args:
            component_id: ID of the component to check
            
        Returns:
            bool: True if component exists, False otherwise
        """
        # Determine remote path
        remote_path = f"{self.config.prefix}/{component_id}"
        
        # Check if file exists
        return self.provider.file_exists(remote_path)
    
    def get_component_metadata(self, component_id: str) -> Dict[str, Any]:
        """
        Get metadata for a component in cloud storage.
        
        Args:
            component_id: ID of the component to get metadata for
            
        Returns:
            Dict[str, Any]: Component metadata
        """
        # Determine remote path
        remote_path = f"{self.config.prefix}/{component_id}"
        
        # Check cache first
        if remote_path in self.metadata_cache:
            return self.metadata_cache[remote_path]
        
        # Get metadata from provider
        metadata = self.provider.get_file_metadata(remote_path)
        
        # Cache metadata
        if metadata:
            self.metadata_cache[remote_path] = metadata
        
        return metadata
    
    def batch_upload_components(self, component_paths: List[str], component_ids: List[str] = None) -> Dict[str, bool]:
        """
        Upload multiple components in parallel.
        
        Args:
            component_paths: List of local paths to component files
            component_ids: Optional list of component IDs (defaults to filenames)
            
        Returns:
            Dict[str, bool]: Dictionary mapping component IDs to upload results
        """
        if component_ids is None:
            component_ids = [os.path.basename(path) for path in component_paths]
        
        if len(component_paths) != len(component_ids):
            logger.error("component_paths and component_ids must have the same length")
            return {}
        
        # Submit upload tasks to executor
        future_to_id = {}
        for path, component_id in zip(component_paths, component_ids):
            future = self.executor.submit(self.upload_component, path, component_id)
            future_to_id[future] = component_id
        
        # Collect results
        results = {}
        for future in future_to_id:
            component_id = future_to_id[future]
            try:
                results[component_id] = future.result()
            except Exception as e:
                logger.error(f"Error uploading component {component_id}: {e}")
                results[component_id] = False
        
        return results
    
    def batch_download_components(self, component_ids: List[str], destination_dir: str = "downloads") -> Dict[str, bool]:
        """
        Download multiple components in parallel.
        
        Args:
            component_ids: List of component IDs to download
            destination_dir: Directory to save downloaded components
            
        Returns:
            Dict[str, bool]: Dictionary mapping component IDs to download results
        """
        # Ensure destination directory exists
        os.makedirs(destination_dir, exist_ok=True)
        
        # Submit download tasks to executor
        future_to_id = {}
        for component_id in component_ids:
            destination_path = os.path.join(destination_dir, component_id)
            future = self.executor.submit(self.download_component, component_id, destination_path)
            future_to_id[future] = component_id
        
        # Collect results
        results = {}
        for future in future_to_id:
            component_id = future_to_id[future]
            try:
                results[component_id] = future.result()
            except Exception as e:
                logger.error(f"Error downloading component {component_id}: {e}")
                results[component_id] = False
        
        return results
    
    def get_operation_log(self) -> List[Dict[str, Any]]:
        """Get the operation log"""
        return self.operation_log
    
    def __del__(self):
        """Clean up resources"""
        self.executor.shutdown()


# Factory function to create a CloudStorageManager with default testing configuration
def create_test_manager() -> CloudStorageManager:
    """Create a CloudStorageManager with default test configuration"""
    config = CloudStorageConfig(
        provider="mock",
        prefix="test_components"
    )
    manager = CloudStorageManager(config)
    manager.authenticate()
    return manager