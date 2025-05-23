"""
Test Script for Cloud Storage Module

This script tests the cloud storage functionality using the mock provider.
"""

import os
import sys
import logging
import time
import json
from typing import List, Dict, Any

from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig
from cloud_storage.sync_module import StorageSynchronizer, SyncConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_storage_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_test_files(directory: str, count: int = 5) -> List[str]:
    """
    Create test files for upload.
    
    Args:
        directory: Directory to create files in
        count: Number of files to create
        
    Returns:
        List[str]: List of created file paths
    """
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Create files
    file_paths = []
    for i in range(count):
        file_path = os.path.join(directory, f"test_file_{i}.json")
        
        # Create test data
        data = {
            "id": f"test_file_{i}",
            "name": f"Test File {i}",
            "description": f"This is test file {i}",
            "created": time.time(),
            "version": 1.0,
            "metadata": {
                "author": "Test Script",
                "timestamp": time.time()
            }
        }
        
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        file_paths.append(file_path)
        logger.info(f"Created test file: {file_path}")
    
    return file_paths


def test_basic_operations():
    """Test basic cloud storage operations"""
    print("\n=== Testing Basic Operations ===")
    
    # Create test directory
    test_dir = "cloud_storage_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test files
    file_paths = create_test_files(test_dir)
    
    # Create storage manager with mock provider
    config = CloudStorageConfig(
        provider="mock",
        prefix="test_components"
    )
    manager = CloudStorageManager(config)
    
    # Authenticate
    print("Authenticating with mock provider...")
    if not manager.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Upload files
    print("\nUploading files...")
    for file_path in file_paths:
        component_id = os.path.basename(file_path)
        if manager.upload_component(file_path, component_id):
            print(f"✅ Uploaded {component_id}")
        else:
            print(f"❌ Failed to upload {component_id}")
            return False
    
    # List components
    print("\nListing components...")
    components = manager.list_components()
    if len(components) != len(file_paths):
        print(f"❌ Expected {len(file_paths)} components, got {len(components)}")
        return False
    
    print(f"✅ Found {len(components)} components:")
    for component in components:
        print(f"  - {component}")
    
    # Get component metadata
    print("\nGetting metadata...")
    component_id = os.path.basename(file_paths[0])
    metadata = manager.get_component_metadata(component_id)
    if not metadata:
        print(f"❌ Failed to get metadata for {component_id}")
        return False
    
    print(f"✅ Got metadata for {component_id}:")
    for key, value in metadata.items():
        print(f"  - {key}: {value}")
    
    # Download components
    print("\nDownloading components...")
    download_dir = os.path.join(test_dir, "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    for component in components:
        download_path = os.path.join(download_dir, component)
        if manager.download_component(component, download_path):
            print(f"✅ Downloaded {component}")
        else:
            print(f"❌ Failed to download {component}")
            return False
    
    # Verify downloaded files
    print("\nVerifying downloaded files...")
    for component in components:
        download_path = os.path.join(download_dir, component)
        if not os.path.exists(download_path):
            print(f"❌ Downloaded file not found: {download_path}")
            return False
    
    print("✅ All files downloaded successfully")
    
    # Delete components
    print("\nDeleting components...")
    for component in components:
        if manager.delete_component(component):
            print(f"✅ Deleted {component}")
        else:
            print(f"❌ Failed to delete {component}")
            return False
    
    # Verify deletion
    remaining = manager.list_components()
    if remaining:
        print(f"❌ Expected 0 components, got {len(remaining)}")
        return False
    
    print("✅ All components deleted successfully")
    
    return True


def test_batch_operations():
    """Test batch operations"""
    print("\n=== Testing Batch Operations ===")
    
    # Create test directory
    test_dir = "cloud_storage_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test files
    file_paths = create_test_files(test_dir, count=10)
    
    # Create storage manager with mock provider
    config = CloudStorageConfig(
        provider="mock",
        prefix="test_components"
    )
    manager = CloudStorageManager(config)
    
    # Authenticate
    print("Authenticating with mock provider...")
    if not manager.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Batch upload
    print("\nBatch uploading files...")
    component_ids = [os.path.basename(path) for path in file_paths]
    results = manager.batch_upload_components(file_paths, component_ids)
    
    successes = sum(1 for success in results.values() if success)
    failures = sum(1 for success in results.values() if not success)
    
    if failures > 0:
        print(f"❌ {failures} out of {len(file_paths)} uploads failed")
        return False
    
    print(f"✅ Uploaded {successes} files successfully")
    
    # Verify uploads
    components = manager.list_components()
    if len(components) != len(file_paths):
        print(f"❌ Expected {len(file_paths)} components, got {len(components)}")
        return False
    
    print(f"✅ Found {len(components)} components")
    
    # Batch download
    print("\nBatch downloading files...")
    download_dir = os.path.join(test_dir, "batch_downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    results = manager.batch_download_components(components, download_dir)
    
    successes = sum(1 for success in results.values() if success)
    failures = sum(1 for success in results.values() if not success)
    
    if failures > 0:
        print(f"❌ {failures} out of {len(components)} downloads failed")
        return False
    
    print(f"✅ Downloaded {successes} files successfully")
    
    # Verify downloads
    for component in components:
        download_path = os.path.join(download_dir, component)
        if not os.path.exists(download_path):
            print(f"❌ Downloaded file not found: {download_path}")
            return False
    
    print("✅ All files downloaded successfully")
    
    return True


def test_synchronization():
    """Test synchronization"""
    print("\n=== Testing Synchronization ===")
    
    # Create test directory
    test_dir = "cloud_storage_test"
    sync_dir = os.path.join(test_dir, "sync")
    os.makedirs(sync_dir, exist_ok=True)
    
    # Create test files
    file_paths = create_test_files(sync_dir, count=5)
    
    # Create storage manager with mock provider
    config = CloudStorageConfig(
        provider="mock",
        prefix="test_components"
    )
    manager = CloudStorageManager(config)
    
    # Authenticate
    print("Authenticating with mock provider...")
    if not manager.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Create sync configuration
    sync_config = SyncConfig(
        local_dir=sync_dir,
        direction="both",
        delete_files=True,
        overwrite=True,
        file_patterns=["*.json"]
    )
    
    # Create synchronizer
    synchronizer = StorageSynchronizer(manager, sync_config)
    
    # Define progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    # Perform initial synchronization
    print("\nPerforming initial synchronization...")
    result = synchronizer.synchronize(progress_callback)
    
    print("\nInitial sync results:")
    print(f"  {result.get_summary_string()}")
    
    if len(result.uploaded_files) != len(file_paths):
        print(f"❌ Expected {len(file_paths)} uploads, got {len(result.uploaded_files)}")
        return False
    
    print("✅ Initial synchronization successful")
    
    # Create new local file
    print("\nCreating new local file...")
    new_file = os.path.join(sync_dir, "new_file.json")
    with open(new_file, 'w') as f:
        json.dump({"name": "New File", "created": time.time()}, f)
    
    # Create new cloud file
    print("\nCreating new cloud file...")
    cloud_file_content = json.dumps({"name": "Cloud File", "created": time.time()})
    cloud_file_path = os.path.join(test_dir, "cloud_file.json")
    with open(cloud_file_path, 'w') as f:
        f.write(cloud_file_content)
    
    manager.upload_component(cloud_file_path, "cloud_file.json")
    
    # Modify an existing file
    print("\nModifying existing file...")
    existing_file = file_paths[0]
    with open(existing_file, 'r') as f:
        data = json.load(f)
    
    data["modified"] = True
    data["modification_time"] = time.time()
    
    with open(existing_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Delete a file
    print("\nDeleting a local file...")
    os.remove(file_paths[1])
    
    # Perform second synchronization
    print("\nPerforming second synchronization...")
    result = synchronizer.synchronize(progress_callback)
    
    print("\nSecond sync results:")
    print(f"  {result.get_summary_string()}")
    
    # Check if new cloud file was downloaded
    if not os.path.exists(os.path.join(sync_dir, "cloud_file.json")):
        print("❌ New cloud file was not downloaded")
        return False
    
    # Check if new local file was uploaded
    components = manager.list_components()
    if "new_file.json" not in components:
        print("❌ New local file was not uploaded")
        return False
    
    # Check if deleted local file was deleted from cloud
    if os.path.basename(file_paths[1]) in components:
        print("❌ Deleted local file was not deleted from cloud")
        return False
    
    print("✅ Second synchronization successful")
    
    return True


def run_all_tests():
    """Run all tests"""
    tests = [
        ("Basic Operations", test_basic_operations),
        ("Batch Operations", test_batch_operations),
        ("Synchronization", test_synchronization)
    ]
    
    success = True
    results = []
    
    print("=== Cloud Storage Tests ===\n")
    
    for name, test_func in tests:
        print(f"\n=== Running Test: {name} ===")
        try:
            test_success = test_func()
            results.append((name, test_success))
            if not test_success:
                success = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((name, False))
            success = False
    
    print("\n=== Test Results ===")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)