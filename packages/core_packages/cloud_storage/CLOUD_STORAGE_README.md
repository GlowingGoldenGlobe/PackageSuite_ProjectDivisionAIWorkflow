# Cloud Storage for Model Components

This module provides functionality for storing, retrieving, and managing model components in various cloud storage services including AWS S3 and Azure Blob Storage.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
   - [Basic Usage](#basic-usage)
   - [Dashboard Integration](#dashboard-integration)
   - [Synchronization](#synchronization)
6. [Providers](#providers)
   - [AWS S3](#aws-s3)
   - [Azure Blob Storage](#azure-blob-storage)
   - [Mock Provider](#mock-provider)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

The Cloud Storage module allows you to store and manage your GlowingGoldenGlobe model components in the cloud, providing:

- Backup and disaster recovery
- Collaboration and sharing
- Version control
- Centralized management
- Synchronization between local and cloud storage

The module is integrated with the visualization dashboard, providing a user-friendly interface for cloud operations.

## Features

- **Multiple Cloud Providers**: Support for AWS S3, Azure Blob Storage, and a mock provider for testing
- **Component Management**: Upload, download, list, and delete components
- **Batch Operations**: Efficiently process multiple components at once
- **Synchronization**: Two-way sync between local and cloud storage
- **Metadata**: View component metadata like size, creation date, and modification time
- **Dashboard Integration**: User-friendly interface for cloud operations
- **Parallel Processing**: Improved performance with concurrent operations
- **Error Handling**: Robust error handling and retry logic

## Installation

The Cloud Storage module is included in the GlowingGoldenGlobe project. To use the AWS S3 or Azure Blob Storage providers, you need to install the respective SDKs:

For AWS S3:
```bash
pip install boto3
```

For Azure Blob Storage:
```bash
pip install azure-storage-blob
```

## Configuration

### AWS S3 Configuration

To configure AWS S3, create a credentials file with the following format:

```json
{
    "aws_access_key_id": "YOUR_ACCESS_KEY",
    "aws_secret_access_key": "YOUR_SECRET_KEY",
    "region": "us-east-1"
}
```

Or set environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`

### Azure Blob Storage Configuration

To configure Azure Blob Storage, create a credentials file with the following format:

```json
{
    "connection_string": "YOUR_CONNECTION_STRING"
}
```

Or with account name and key:

```json
{
    "account_name": "YOUR_ACCOUNT_NAME",
    "account_key": "YOUR_ACCOUNT_KEY"
}
```

Or set environment variables:
- `AZURE_STORAGE_CONNECTION_STRING`

### Configuration Files

Provider-specific configuration files are created automatically when you configure the provider through the dashboard. They are stored as:

- `cloud_storage_aws_config.json`
- `cloud_storage_azure_config.json`

## Usage

### Basic Usage

```python
from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig

# Create configuration
config = CloudStorageConfig(
    provider="aws",
    credentials_file="aws_credentials.json",
    bucket_name="model-components",
    prefix="models",
    encryption=True,
    public_access=False
)

# Create manager
manager = CloudStorageManager(config)

# Authenticate
if manager.authenticate():
    # Upload a component
    manager.upload_component("path/to/component.blend", "component_id")
    
    # List components
    components = manager.list_components()
    print(f"Found {len(components)} components")
    
    # Download a component
    manager.download_component("component_id", "download/path.blend")
    
    # Delete a component
    manager.delete_component("component_id")
```

### Dashboard Integration

The cloud storage functionality is integrated with the visualization dashboard. To access it:

1. Open the visualization dashboard
2. Go to the "Cloud Storage" tab
3. Configure your preferred cloud provider
4. Use the interface to upload, download, list, and manage components

### Synchronization

The synchronization feature allows you to keep local and cloud storage in sync:

```python
from cloud_storage.cloud_storage_module import CloudStorageManager, CloudStorageConfig
from cloud_storage.sync_module import StorageSynchronizer, SyncConfig

# Create storage manager
config = CloudStorageConfig(
    provider="aws",
    credentials_file="aws_credentials.json",
    bucket_name="model-components"
)
manager = CloudStorageManager(config)
manager.authenticate()

# Create sync configuration
sync_config = SyncConfig(
    local_dir="agent_outputs",
    direction="both",
    delete_files=True,
    overwrite=True,
    file_patterns=["*.blend", "*.fbx", "*.stl", "*.gltf"]
)

# Create synchronizer
synchronizer = StorageSynchronizer(manager, sync_config)

# Perform synchronization
def progress_callback(message):
    print(message)

result = synchronizer.synchronize(progress_callback)
print(result.get_summary_string())
```

## Providers

### AWS S3

The AWS S3 provider uses the [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library to interact with Amazon S3.

Features:
- Server-side encryption
- Public/private access control
- Region selection
- Bucket management
- Retry logic for reliable operations

### Azure Blob Storage

The Azure Blob Storage provider uses the [azure-storage-blob](https://pypi.org/project/azure-storage-blob/) library to interact with Azure Blob Storage.

Features:
- Container creation and management
- Blob storage tiers
- Access control
- Retry logic for reliable operations

### Mock Provider

The Mock provider simulates cloud storage using the local filesystem. It's useful for testing and development without real cloud resources.

Features:
- No external dependencies
- Simulated latency and errors
- Local storage for testing

## Best Practices

1. **Organize Components**: Use a consistent naming convention for your components to make them easier to find and manage.

2. **Batch Operations**: Use batch operations for uploading or downloading multiple components to improve performance.

3. **Regular Synchronization**: Set up regular synchronization to keep your local and cloud storage in sync.

4. **Security**: Use encryption and avoid public access unless necessary.

5. **Error Handling**: Handle errors and retries, especially for large uploads and downloads.

6. **Metadata**: Use metadata to store additional information about your components.

7. **Clean Up**: Regularly clean up unused components to reduce storage costs.

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Check your credentials
   - Verify that your account has the necessary permissions
   - Make sure your credentials file is in the correct format

2. **Upload/Download Failures**:
   - Check your network connection
   - Verify that the file exists and is accessible
   - Check for sufficient disk space

3. **Synchronization Issues**:
   - Check the sync direction
   - Verify that the local directory exists
   - Look for conflicts in file modifications

### Logs

The cloud storage module logs operations to `cloud_storage.log`. Check this file for detailed information about errors and operations.

### Getting Help

If you encounter issues not covered in this documentation, please check the logs and report the issue with details about the operation that failed.