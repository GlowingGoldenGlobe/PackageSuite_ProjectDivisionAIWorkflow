"""
Synchronization Module for Cloud Storage

This module implements the synchronization functionality between local and cloud storage.
"""

import os
import logging
import time
import json
import fnmatch
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from cloud_storage.cloud_storage_module import CloudStorageManager

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


class SyncConfig:
    """Configuration for synchronization"""
    
    def __init__(
        self,
        local_dir: str,
        direction: str = "both",
        delete_files: bool = False,
        overwrite: bool = True,
        file_patterns: List[str] = None,
        max_workers: int = MAX_WORKERS
    ):
        """
        Initialize synchronization configuration.
        
        Args:
            local_dir: Local directory for synchronization
            direction: Sync direction ("both", "upload", "download")
            delete_files: Whether to delete files that don't exist in source
            overwrite: Whether to overwrite existing files
            file_patterns: File patterns to include (e.g. ["*.blend", "*.fbx"])
            max_workers: Maximum number of worker threads for parallel operations
        """
        self.local_dir = local_dir
        self.direction = direction
        self.delete_files = delete_files
        self.overwrite = overwrite
        self.file_patterns = file_patterns or ["*"]
        self.max_workers = max_workers


class SyncResult:
    """Results of a synchronization operation"""
    
    def __init__(self):
        """Initialize sync results"""
        self.uploaded_files = []
        self.downloaded_files = []
        self.deleted_local_files = []
        self.deleted_cloud_files = []
        self.failed_uploads = []
        self.failed_downloads = []
        self.failed_deletions = []
        self.skipped_files = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary"""
        return {
            "uploaded_files": self.uploaded_files,
            "downloaded_files": self.downloaded_files,
            "deleted_local_files": self.deleted_local_files,
            "deleted_cloud_files": self.deleted_cloud_files,
            "failed_uploads": self.failed_uploads,
            "failed_downloads": self.failed_downloads,
            "failed_deletions": self.failed_deletions,
            "skipped_files": self.skipped_files
        }
    
    def to_json(self) -> str:
        """Convert results to JSON string"""
        return json.dumps(self.to_dict(), indent=4)
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary counts"""
        return {
            "uploaded": len(self.uploaded_files),
            "downloaded": len(self.downloaded_files),
            "deleted_local": len(self.deleted_local_files),
            "deleted_cloud": len(self.deleted_cloud_files),
            "failed_uploads": len(self.failed_uploads),
            "failed_downloads": len(self.failed_downloads),
            "failed_deletions": len(self.failed_deletions),
            "skipped": len(self.skipped_files)
        }
    
    def get_summary_string(self) -> str:
        """Get summary as string"""
        summary = self.get_summary()
        return (
            f"Uploaded: {summary['uploaded']}, "
            f"Downloaded: {summary['downloaded']}, "
            f"Deleted local: {summary['deleted_local']}, "
            f"Deleted cloud: {summary['deleted_cloud']}, "
            f"Failed: {summary['failed_uploads'] + summary['failed_downloads'] + summary['failed_deletions']}, "
            f"Skipped: {summary['skipped']}"
        )


class FileInfo:
    """Information about a file for synchronization"""
    
    def __init__(self, path: str, size: int, last_modified: float):
        """
        Initialize file information.
        
        Args:
            path: File path (relative to base directory)
            size: File size in bytes
            last_modified: Last modified timestamp
        """
        self.path = path
        self.size = size
        self.last_modified = last_modified
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "size": self.size,
            "last_modified": self.last_modified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Create from dictionary"""
        return cls(
            path=data["path"],
            size=data["size"],
            last_modified=data["last_modified"]
        )


class StorageSynchronizer:
    """Class for synchronizing between local and cloud storage"""
    
    def __init__(self, storage_manager: CloudStorageManager, config: SyncConfig):
        """
        Initialize the synchronizer.
        
        Args:
            storage_manager: Cloud storage manager
            config: Synchronization configuration
        """
        self.storage_manager = storage_manager
        self.config = config
        
        # Ensure local directory exists
        os.makedirs(config.local_dir, exist_ok=True)
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        
        # Initialize result
        self.result = SyncResult()
        
        # Initialize sync state file path
        self.state_file = os.path.join(config.local_dir, ".cloud_sync_state.json")
    
    def synchronize(self, progress_callback=None) -> SyncResult:
        """
        Perform synchronization between local and cloud.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            SyncResult: Synchronization results
        """
        # Log start of synchronization
        logger.info(f"Starting synchronization with direction={self.config.direction}")
        
        # Update progress
        if progress_callback:
            progress_callback("Scanning local files...")
        
        # Get local files
        local_files = self._scan_local_files()
        
        # Update progress
        if progress_callback:
            progress_callback("Scanning cloud files...")
        
        # Get cloud files
        cloud_files = self._scan_cloud_files()
        
        # Load previous sync state
        prev_state = self._load_sync_state()
        
        # Determine files to upload, download, and delete
        to_upload, to_download, to_delete_local, to_delete_cloud = self._compare_files(
            local_files, cloud_files, prev_state
        )
        
        # Perform operations based on sync direction
        if self.config.direction in ["both", "upload"]:
            # Upload files
            if progress_callback:
                progress_callback(f"Uploading {len(to_upload)} file(s)...")
            
            self._upload_files(to_upload, progress_callback)
            
            # Delete cloud files
            if self.config.delete_files and to_delete_cloud:
                if progress_callback:
                    progress_callback(f"Deleting {len(to_delete_cloud)} cloud file(s)...")
                
                self._delete_cloud_files(to_delete_cloud, progress_callback)
        
        if self.config.direction in ["both", "download"]:
            # Download files
            if progress_callback:
                progress_callback(f"Downloading {len(to_download)} file(s)...")
            
            self._download_files(to_download, progress_callback)
            
            # Delete local files
            if self.config.delete_files and to_delete_local:
                if progress_callback:
                    progress_callback(f"Deleting {len(to_delete_local)} local file(s)...")
                
                self._delete_local_files(to_delete_local, progress_callback)
        
        # Save sync state
        self._save_sync_state(local_files, cloud_files)
        
        # Log completion
        logger.info(f"Synchronization completed: {self.result.get_summary_string()}")
        
        # Final progress update
        if progress_callback:
            progress_callback(f"Completed: {self.result.get_summary_string()}")
        
        return self.result
    
    def _scan_local_files(self) -> Dict[str, FileInfo]:
        """
        Scan local files.
        
        Returns:
            Dict[str, FileInfo]: Dictionary of file paths to FileInfo objects
        """
        local_files = {}
        
        for root, _, files in os.walk(self.config.local_dir):
            for file in files:
                # Skip the sync state file
                if file == ".cloud_sync_state.json":
                    continue
                
                # Check if file matches pattern
                if not any(fnmatch.fnmatch(file, pattern) for pattern in self.config.file_patterns):
                    continue
                
                # Get file path
                file_path = os.path.join(root, file)
                
                # Get relative path
                rel_path = os.path.relpath(file_path, self.config.local_dir)
                
                # Get file stats
                try:
                    stats = os.stat(file_path)
                    
                    # Create FileInfo
                    local_files[rel_path] = FileInfo(
                        path=rel_path,
                        size=stats.st_size,
                        last_modified=stats.st_mtime
                    )
                except Exception as e:
                    logger.error(f"Error scanning local file {file_path}: {e}")
        
        logger.info(f"Found {len(local_files)} local file(s)")
        return local_files
    
    def _scan_cloud_files(self) -> Dict[str, FileInfo]:
        """
        Scan cloud files.
        
        Returns:
            Dict[str, FileInfo]: Dictionary of file paths to FileInfo objects
        """
        cloud_files = {}
        
        # Get component list
        components = self.storage_manager.list_components()
        
        for component_id in components:
            # Check if file matches pattern
            if not any(fnmatch.fnmatch(component_id, pattern) for pattern in self.config.file_patterns):
                continue
            
            # Get metadata
            metadata = self.storage_manager.get_component_metadata(component_id)
            
            # Parse last modified timestamp
            last_modified = metadata.get("last_modified")
            if isinstance(last_modified, str):
                try:
                    # Try to parse ISO format
                    last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00')).timestamp()
                except ValueError:
                    # Try to parse ctime format
                    try:
                        last_modified = time.mktime(time.strptime(last_modified))
                    except ValueError:
                        # Default to current time
                        last_modified = time.time()
            else:
                # Default to current time
                last_modified = time.time()
            
            # Create FileInfo
            cloud_files[component_id] = FileInfo(
                path=component_id,
                size=metadata.get("size", 0),
                last_modified=last_modified
            )
        
        logger.info(f"Found {len(cloud_files)} cloud file(s)")
        return cloud_files
    
    def _load_sync_state(self) -> Dict[str, Dict[str, FileInfo]]:
        """
        Load previous sync state.
        
        Returns:
            Dict[str, Dict[str, FileInfo]]: Previous sync state
        """
        state = {
            "local": {},
            "cloud": {}
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Parse local files
                if "local" in data:
                    for path, file_data in data["local"].items():
                        state["local"][path] = FileInfo.from_dict(file_data)
                
                # Parse cloud files
                if "cloud" in data:
                    for path, file_data in data["cloud"].items():
                        state["cloud"][path] = FileInfo.from_dict(file_data)
                
                logger.info(f"Loaded sync state: {len(state['local'])} local, {len(state['cloud'])} cloud")
            except Exception as e:
                logger.error(f"Error loading sync state: {e}")
        
        return state
    
    def _save_sync_state(self, local_files: Dict[str, FileInfo], cloud_files: Dict[str, FileInfo]):
        """
        Save sync state.
        
        Args:
            local_files: Local files
            cloud_files: Cloud files
        """
        try:
            # Convert FileInfo objects to dictionaries
            state = {
                "local": {path: file_info.to_dict() for path, file_info in local_files.items()},
                "cloud": {path: file_info.to_dict() for path, file_info in cloud_files.items()},
                "timestamp": time.time(),
                "config": {
                    "direction": self.config.direction,
                    "delete_files": self.config.delete_files,
                    "overwrite": self.config.overwrite,
                    "file_patterns": self.config.file_patterns
                }
            }
            
            # Save to file
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
            
            logger.info("Saved sync state")
        except Exception as e:
            logger.error(f"Error saving sync state: {e}")
    
    def _compare_files(
        self,
        local_files: Dict[str, FileInfo],
        cloud_files: Dict[str, FileInfo],
        prev_state: Dict[str, Dict[str, FileInfo]]
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Compare files to determine which ones to upload, download, and delete.
        
        Args:
            local_files: Local files
            cloud_files: Cloud files
            prev_state: Previous sync state
            
        Returns:
            Tuple: Lists of files to upload, download, delete locally, and delete in cloud
        """
        to_upload = []
        to_download = []
        to_delete_local = []
        to_delete_cloud = []
        
        # Files in both local and cloud
        common_files = set(local_files.keys()) & set(cloud_files.keys())
        
        # Files only in local
        local_only = set(local_files.keys()) - set(cloud_files.keys())
        
        # Files only in cloud
        cloud_only = set(cloud_files.keys()) - set(local_files.keys())
        
        # Previous state for reference
        prev_local = prev_state.get("local", {})
        prev_cloud = prev_state.get("cloud", {})
        
        # Compare common files
        for path in common_files:
            local_file = local_files[path]
            cloud_file = cloud_files[path]
            
            # Skip if files are the same size and modified time
            if (local_file.size == cloud_file.size and
                abs(local_file.last_modified - cloud_file.last_modified) < 1):
                continue
            
            # Determine which file is newer
            if local_file.last_modified > cloud_file.last_modified:
                # Local file is newer
                if self.config.direction in ["both", "upload"]:
                    to_upload.append(path)
            else:
                # Cloud file is newer
                if self.config.direction in ["both", "download"]:
                    to_download.append(path)
        
        # Handle local-only files
        for path in local_only:
            if path in prev_cloud:
                # File was deleted in cloud
                if self.config.direction in ["both", "download"] and self.config.delete_files:
                    to_delete_local.append(path)
            else:
                # New local file
                if self.config.direction in ["both", "upload"]:
                    to_upload.append(path)
        
        # Handle cloud-only files
        for path in cloud_only:
            if path in prev_local:
                # File was deleted locally
                if self.config.direction in ["both", "upload"] and self.config.delete_files:
                    to_delete_cloud.append(path)
            else:
                # New cloud file
                if self.config.direction in ["both", "download"]:
                    to_download.append(path)
        
        logger.info(
            f"Comparison results: {len(to_upload)} to upload, {len(to_download)} to download, "
            f"{len(to_delete_local)} to delete locally, {len(to_delete_cloud)} to delete in cloud"
        )
        
        return to_upload, to_download, to_delete_local, to_delete_cloud
    
    def _upload_files(self, file_paths: List[str], progress_callback=None):
        """
        Upload files to cloud.
        
        Args:
            file_paths: List of file paths to upload
            progress_callback: Optional callback for progress updates
        """
        if not file_paths:
            return
        
        # Create a local copy to avoid modification during iteration
        files_to_upload = list(file_paths)
        
        # Process in batches
        batch_size = min(self.config.max_workers, len(files_to_upload))
        total_files = len(files_to_upload)
        processed = 0
        
        while files_to_upload:
            # Get next batch
            batch = files_to_upload[:batch_size]
            files_to_upload = files_to_upload[batch_size:]
            
            # Submit upload tasks
            future_to_path = {}
            for path in batch:
                local_path = os.path.join(self.config.local_dir, path)
                future = self.executor.submit(self._upload_file, path, local_path)
                future_to_path[future] = path
            
            # Process results
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    success = future.result()
                    
                    if success:
                        self.result.uploaded_files.append(path)
                    else:
                        self.result.failed_uploads.append(path)
                except Exception as e:
                    logger.error(f"Error uploading {path}: {e}")
                    self.result.failed_uploads.append(path)
            
            # Update progress
            processed += len(batch)
            if progress_callback:
                progress_callback(f"Uploaded {processed}/{total_files} file(s)...")
    
    def _upload_file(self, rel_path: str, local_path: str) -> bool:
        """
        Upload a single file.
        
        Args:
            rel_path: Relative path
            local_path: Local file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(local_path):
                logger.error(f"Local file not found: {local_path}")
                return False
            
            # Upload file
            success = self.storage_manager.upload_component(local_path, rel_path)
            
            if success:
                logger.info(f"Uploaded {rel_path}")
            else:
                logger.error(f"Failed to upload {rel_path}")
            
            return success
        except Exception as e:
            logger.error(f"Error uploading {rel_path}: {e}")
            return False
    
    def _download_files(self, file_paths: List[str], progress_callback=None):
        """
        Download files from cloud.
        
        Args:
            file_paths: List of file paths to download
            progress_callback: Optional callback for progress updates
        """
        if not file_paths:
            return
        
        # Create a local copy to avoid modification during iteration
        files_to_download = list(file_paths)
        
        # Process in batches
        batch_size = min(self.config.max_workers, len(files_to_download))
        total_files = len(files_to_download)
        processed = 0
        
        while files_to_download:
            # Get next batch
            batch = files_to_download[:batch_size]
            files_to_download = files_to_download[batch_size:]
            
            # Submit download tasks
            future_to_path = {}
            for path in batch:
                local_path = os.path.join(self.config.local_dir, path)
                future = self.executor.submit(self._download_file, path, local_path)
                future_to_path[future] = path
            
            # Process results
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    success = future.result()
                    
                    if success:
                        self.result.downloaded_files.append(path)
                    else:
                        self.result.failed_downloads.append(path)
                except Exception as e:
                    logger.error(f"Error downloading {path}: {e}")
                    self.result.failed_downloads.append(path)
            
            # Update progress
            processed += len(batch)
            if progress_callback:
                progress_callback(f"Downloaded {processed}/{total_files} file(s)...")
    
    def _download_file(self, component_id: str, local_path: str) -> bool:
        """
        Download a single file.
        
        Args:
            component_id: Component ID
            local_path: Local file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file already exists
            if os.path.exists(local_path) and not self.config.overwrite:
                logger.info(f"Skipping existing file: {local_path}")
                self.result.skipped_files.append(component_id)
                return True
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            success = self.storage_manager.download_component(component_id, local_path)
            
            if success:
                logger.info(f"Downloaded {component_id} to {local_path}")
            else:
                logger.error(f"Failed to download {component_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error downloading {component_id}: {e}")
            return False
    
    def _delete_local_files(self, file_paths: List[str], progress_callback=None):
        """
        Delete local files.
        
        Args:
            file_paths: List of file paths to delete
            progress_callback: Optional callback for progress updates
        """
        if not file_paths:
            return
        
        # Create a local copy to avoid modification during iteration
        files_to_delete = list(file_paths)
        
        # Process in batches
        batch_size = min(self.config.max_workers, len(files_to_delete))
        total_files = len(files_to_delete)
        processed = 0
        
        while files_to_delete:
            # Get next batch
            batch = files_to_delete[:batch_size]
            files_to_delete = files_to_delete[batch_size:]
            
            # Submit delete tasks
            future_to_path = {}
            for path in batch:
                local_path = os.path.join(self.config.local_dir, path)
                future = self.executor.submit(self._delete_local_file, path, local_path)
                future_to_path[future] = path
            
            # Process results
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    success = future.result()
                    
                    if success:
                        self.result.deleted_local_files.append(path)
                    else:
                        self.result.failed_deletions.append(path)
                except Exception as e:
                    logger.error(f"Error deleting local file {path}: {e}")
                    self.result.failed_deletions.append(path)
            
            # Update progress
            processed += len(batch)
            if progress_callback:
                progress_callback(f"Deleted {processed}/{total_files} local file(s)...")
    
    def _delete_local_file(self, rel_path: str, local_path: str) -> bool:
        """
        Delete a local file.
        
        Args:
            rel_path: Relative path
            local_path: Local file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(local_path):
                logger.info(f"Local file already deleted: {local_path}")
                return True
            
            # Delete file
            os.remove(local_path)
            logger.info(f"Deleted local file: {local_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting local file {local_path}: {e}")
            return False
    
    def _delete_cloud_files(self, file_paths: List[str], progress_callback=None):
        """
        Delete cloud files.
        
        Args:
            file_paths: List of file paths to delete
            progress_callback: Optional callback for progress updates
        """
        if not file_paths:
            return
        
        # Create a local copy to avoid modification during iteration
        files_to_delete = list(file_paths)
        
        # Process in batches
        batch_size = min(self.config.max_workers, len(files_to_delete))
        total_files = len(files_to_delete)
        processed = 0
        
        while files_to_delete:
            # Get next batch
            batch = files_to_delete[:batch_size]
            files_to_delete = files_to_delete[batch_size:]
            
            # Submit delete tasks
            future_to_path = {}
            for path in batch:
                future = self.executor.submit(self._delete_cloud_file, path)
                future_to_path[future] = path
            
            # Process results
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    success = future.result()
                    
                    if success:
                        self.result.deleted_cloud_files.append(path)
                    else:
                        self.result.failed_deletions.append(path)
                except Exception as e:
                    logger.error(f"Error deleting cloud file {path}: {e}")
                    self.result.failed_deletions.append(path)
            
            # Update progress
            processed += len(batch)
            if progress_callback:
                progress_callback(f"Deleted {processed}/{total_files} cloud file(s)...")
    
    def _delete_cloud_file(self, component_id: str) -> bool:
        """
        Delete a cloud file.
        
        Args:
            component_id: Component ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete file
            success = self.storage_manager.delete_component(component_id)
            
            if success:
                logger.info(f"Deleted cloud file: {component_id}")
            else:
                logger.error(f"Failed to delete cloud file: {component_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting cloud file {component_id}: {e}")
            return False