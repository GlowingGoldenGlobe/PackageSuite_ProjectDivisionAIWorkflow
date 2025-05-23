"""
AWS S3 Storage Provider for GlowingGoldenGlobe Model Components

This module implements the AWS S3 cloud storage provider for the CloudStorageManager.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional

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


class AWSS3StorageProvider(CloudStorageProvider):
    """AWS S3 implementation of the cloud storage provider"""
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize with S3 configuration"""
        self.config = config
        self.s3_client = None
        self.authenticated = False
        
        # Validate configuration
        if not config.bucket_name:
            raise ValueError("Bucket name is required for AWS S3 provider")
    
    def authenticate(self) -> bool:
        """Authenticate with AWS S3"""
        try:
            # Import boto3 only when needed to allow the module to be used without boto3 installed
            import boto3
            from botocore.exceptions import ClientError
            
            # Load credentials from file if provided
            if self.config.credentials_file and os.path.exists(self.config.credentials_file):
                with open(self.config.credentials_file, 'r') as f:
                    credentials = json.load(f)
                
                # Create S3 client with credentials
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.config.region or credentials.get('region'),
                    aws_access_key_id=credentials.get('aws_access_key_id'),
                    aws_secret_access_key=credentials.get('aws_secret_access_key')
                )
            else:
                # Use default credentials from environment variables or IAM role
                self.s3_client = boto3.client('s3', region_name=self.config.region)
            
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == '404':
                    logger.error(f"Bucket {self.config.bucket_name} does not exist")
                    return False
                elif error_code == '403':
                    logger.error(f"Access denied to bucket {self.config.bucket_name}")
                    return False
                else:
                    raise
            
            self.authenticated = True
            logger.info(f"Successfully authenticated with AWS S3 and verified bucket {self.config.bucket_name}")
            return True
            
        except ImportError:
            logger.error("boto3 is required for AWS S3 provider. Install with 'pip install boto3'")
            return False
        except Exception as e:
            logger.error(f"AWS S3 authentication failed: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to S3"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return False
        
        try:
            # Import boto3 error types here to handle retries
            from botocore.exceptions import ClientError
            
            # Configure extra args for upload
            extra_args = {}
            
            # Set encryption if enabled
            if self.config.encryption:
                extra_args['ServerSideEncryption'] = 'AES256'
            
            # Set public access if enabled
            if self.config.public_access:
                extra_args['ACL'] = 'public-read'
            
            # Retry logic
            retries = 0
            while retries < MAX_UPLOAD_RETRIES:
                try:
                    self.s3_client.upload_file(
                        local_path,
                        self.config.bucket_name,
                        remote_path,
                        ExtraArgs=extra_args
                    )
                    logger.info(f"Successfully uploaded {local_path} to S3://{self.config.bucket_name}/{remote_path}")
                    return True
                except ClientError as e:
                    retries += 1
                    if retries >= MAX_UPLOAD_RETRIES:
                        logger.error(f"Upload failed after {MAX_UPLOAD_RETRIES} retries: {e}")
                        return False
                    
                    logger.warning(f"Upload attempt {retries} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
            
            return False
            
        except Exception as e:
            logger.error(f"Upload to S3 failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from S3"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return False
        
        try:
            # Import boto3 error types
            from botocore.exceptions import ClientError
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Retry logic
            retries = 0
            while retries < MAX_UPLOAD_RETRIES:
                try:
                    self.s3_client.download_file(
                        self.config.bucket_name,
                        remote_path,
                        local_path
                    )
                    logger.info(f"Successfully downloaded S3://{self.config.bucket_name}/{remote_path} to {local_path}")
                    return True
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code')
                    if error_code == 'NoSuchKey':
                        logger.error(f"File not found in S3: {remote_path}")
                        return False
                    
                    retries += 1
                    if retries >= MAX_UPLOAD_RETRIES:
                        logger.error(f"Download failed after {MAX_UPLOAD_RETRIES} retries: {e}")
                        return False
                    
                    logger.warning(f"Download attempt {retries} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
            
            return False
            
        except Exception as e:
            logger.error(f"Download from S3 failed: {e}")
            return False
    
    def list_files(self, prefix: str = None) -> List[str]:
        """List files in S3 bucket"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return []
        
        try:
            # If prefix is provided, append it to the configured prefix
            s3_prefix = prefix or ""
            
            # List objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.config.bucket_name, Prefix=s3_prefix)
            
            # Collect file paths
            result = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        result.append(obj['Key'])
            
            return result
            
        except Exception as e:
            logger.error(f"List files in S3 failed: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from S3"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return False
        
        try:
            # Delete object
            self.s3_client.delete_object(
                Bucket=self.config.bucket_name,
                Key=remote_path
            )
            
            logger.info(f"Successfully deleted S3://{self.config.bucket_name}/{remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Delete from S3 failed: {e}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in S3"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return False
        
        try:
            # Check if object exists
            self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=remote_path
            )
            
            return True
            
        except Exception:
            return False
    
    def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a file in S3"""
        if not self.authenticated:
            logger.error("Not authenticated with AWS S3")
            return {}
        
        try:
            # Get object metadata
            response = self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=remote_path
            )
            
            # Extract metadata
            metadata = {
                "size": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified', '').isoformat() if response.get('LastModified') else '',
                "etag": response.get('ETag', '').strip('"'),
                "content_type": response.get('ContentType', ''),
                "storage_class": response.get('StorageClass', '')
            }
            
            # Add user-defined metadata
            if 'Metadata' in response:
                metadata.update(response['Metadata'])
            
            return metadata
            
        except Exception as e:
            logger.error(f"Get metadata from S3 failed: {e}")
            return {}