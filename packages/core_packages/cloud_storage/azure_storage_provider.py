"""
Azure Blob Storage Provider for GlowingGoldenGlobe Model Components

This module implements the Azure Blob Storage provider for the CloudStorageManager.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from cloud_storage.cloud_storage_module import CloudStorageProvider, CloudStorageConfig

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
MAX_UPLOAD_RETRIES = 3
RETRY_DELAY = 2  # seconds


class AzureBlobStorageProvider(CloudStorageProvider):
    """Azure Blob Storage implementation of the cloud storage provider"""
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize with Azure configuration"""
        self.config = config
        self.blob_service_client = None
        self.container_client = None
        self.authenticated = False
        
        # Validate configuration
        if not config.container_name:
            raise ValueError("Container name is required for Azure Blob Storage provider")
    
    def authenticate(self) -> bool:
        """Authenticate with Azure Blob Storage"""
        try:
            # Import Azure SDK only when needed to allow the module to be used without the Azure SDK installed
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
            
            # Load credentials from file if provided
            if self.config.credentials_file and os.path.exists(self.config.credentials_file):
                with open(self.config.credentials_file, 'r') as f:
                    credentials = json.load(f)
                
                # Create Blob Service client with connection string
                connection_string = credentials.get('connection_string')
                if connection_string:
                    self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                else:
                    # Use account name and key
                    account_name = credentials.get('account_name')
                    account_key = credentials.get('account_key')
                    
                    if not account_name or not account_key:
                        logger.error("Azure credentials must include connection_string or account_name and account_key")
                        return False
                    
                    self.blob_service_client = BlobServiceClient(
                        account_url=f"https://{account_name}.blob.core.windows.net",
                        credential=account_key
                    )
            else:
                # Use default credentials from environment variables
                connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
                if connection_string:
                    self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                else:
                    logger.error("Azure credentials not found in file or environment variables")
                    return False
            
            # Get container client
            self.container_client = self.blob_service_client.get_container_client(self.config.container_name)
            
            # Check if container exists
            try:
                container_properties = self.container_client.get_container_properties()
                logger.info(f"Connected to existing container: {self.config.container_name}")
            except ResourceNotFoundError:
                # Create container if it doesn't exist
                logger.info(f"Container {self.config.container_name} not found, creating...")
                
                try:
                    # Set public access if enabled
                    public_access = "container" if self.config.public_access else None
                    self.container_client.create_container(public_access=public_access)
                    logger.info(f"Created container: {self.config.container_name}")
                except ResourceExistsError:
                    # Container was created in the meantime (race condition)
                    logger.info(f"Container already created: {self.config.container_name}")
                except Exception as e:
                    logger.error(f"Failed to create container {self.config.container_name}: {e}")
                    return False
            
            self.authenticated = True
            logger.info(f"Successfully authenticated with Azure Blob Storage and verified container {self.config.container_name}")
            return True
            
        except ImportError:
            logger.error("azure-storage-blob is required for Azure Blob Storage provider. Install with 'pip install azure-storage-blob'")
            return False
        except Exception as e:
            logger.error(f"Azure Blob Storage authentication failed: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to Azure Blob Storage"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return False
        
        try:
            # Import Azure exceptions
            from azure.core.exceptions import ServiceError
            
            # Get blob client
            blob_client = self.container_client.get_blob_client(remote_path)
            
            # Retry logic
            retries = 0
            while retries < MAX_UPLOAD_RETRIES:
                try:
                    # Upload file
                    with open(local_path, "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                    
                    logger.info(f"Successfully uploaded {local_path} to Azure Blob Storage: {remote_path}")
                    return True
                except ServiceError as e:
                    retries += 1
                    if retries >= MAX_UPLOAD_RETRIES:
                        logger.error(f"Upload failed after {MAX_UPLOAD_RETRIES} retries: {e}")
                        return False
                    
                    logger.warning(f"Upload attempt {retries} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
            
            return False
            
        except Exception as e:
            logger.error(f"Upload to Azure Blob Storage failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from Azure Blob Storage"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return False
        
        try:
            # Import Azure exceptions
            from azure.core.exceptions import ResourceNotFoundError, ServiceError
            
            # Get blob client
            blob_client = self.container_client.get_blob_client(remote_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Retry logic
            retries = 0
            while retries < MAX_UPLOAD_RETRIES:
                try:
                    # Download file
                    with open(local_path, "wb") as download_file:
                        download_file.write(blob_client.download_blob().readall())
                    
                    logger.info(f"Successfully downloaded Azure Blob Storage: {remote_path} to {local_path}")
                    return True
                except ResourceNotFoundError:
                    logger.error(f"Blob not found in Azure Storage: {remote_path}")
                    return False
                except ServiceError as e:
                    retries += 1
                    if retries >= MAX_UPLOAD_RETRIES:
                        logger.error(f"Download failed after {MAX_UPLOAD_RETRIES} retries: {e}")
                        return False
                    
                    logger.warning(f"Download attempt {retries} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
            
            return False
            
        except Exception as e:
            logger.error(f"Download from Azure Blob Storage failed: {e}")
            return False
    
    def list_files(self, prefix: str = None) -> List[str]:
        """List blobs in Azure Blob Storage container"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return []
        
        try:
            # If prefix is provided, use it
            name_starts_with = prefix if prefix else None
            
            # List blobs
            blob_list = self.container_client.list_blobs(name_starts_with=name_starts_with)
            
            # Collect blob names
            result = [blob.name for blob in blob_list]
            
            return result
            
        except Exception as e:
            logger.error(f"List blobs in Azure Blob Storage failed: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a blob from Azure Blob Storage"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return False
        
        try:
            # Get blob client
            blob_client = self.container_client.get_blob_client(remote_path)
            
            # Delete blob
            blob_client.delete_blob()
            
            logger.info(f"Successfully deleted Azure Blob Storage: {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Delete from Azure Blob Storage failed: {e}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a blob exists in Azure Blob Storage"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return False
        
        try:
            # Get blob client
            blob_client = self.container_client.get_blob_client(remote_path)
            
            # Check if blob exists
            properties = blob_client.get_blob_properties()
            return True
            
        except Exception:
            return False
    
    def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a blob in Azure Blob Storage"""
        if not self.authenticated:
            logger.error("Not authenticated with Azure Blob Storage")
            return {}
        
        try:
            # Get blob client
            blob_client = self.container_client.get_blob_client(remote_path)
            
            # Get blob properties
            properties = blob_client.get_blob_properties()
            
            # Extract metadata
            metadata = {
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else '',
                "created": properties.creation_time.isoformat() if properties.creation_time else '',
                "blob_type": properties.blob_type,
                "lease_state": properties.lease.state
            }
            
            # Add user-defined metadata
            if properties.metadata:
                metadata.update(properties.metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Get metadata from Azure Blob Storage failed: {e}")
            return {}