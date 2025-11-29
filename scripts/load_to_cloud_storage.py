"""
Data Loading to Cloud Storage (Step 2.3)
Uploads processed datasets to cloud storage (MinIO/S3/Azure Blob Storage).
"""

import os
import boto3
from pathlib import Path
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_s3_client(endpoint_url=None, access_key=None, secret_key=None, region='us-east-1'):
    """
    Create and return an S3 client (works with MinIO, AWS S3, or S3-compatible storage).
    
    Args:
        endpoint_url: Custom endpoint URL (for MinIO, e.g., 'http://localhost:9000')
        access_key: Access key ID
        secret_key: Secret access key
        region: AWS region (default: us-east-1)
    
    Returns:
        boto3 S3 client
    """
    # Get credentials from environment or parameters
    access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    endpoint_url = endpoint_url or os.getenv('S3_ENDPOINT_URL') or os.getenv('MINIO_ENDPOINT_URL')
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,  # None for AWS S3, URL for MinIO
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    
    return s3_client


def ensure_bucket_exists(s3_client, bucket_name):
    """
    Ensure the S3 bucket exists, create it if it doesn't.
    
    Args:
        s3_client: boto3 S3 client
        bucket_name: Name of the bucket
    """
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket doesn't exist, create it
            try:
                if s3_client.meta.endpoint_url:
                    # MinIO or S3-compatible
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    # AWS S3 (requires region)
                    region = s3_client.meta.region_name or 'us-east-1'
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                logger.info(f"Created bucket '{bucket_name}'")
            except ClientError as create_error:
                logger.error(f"Failed to create bucket '{bucket_name}': {create_error}")
                raise
        else:
            logger.error(f"Error checking bucket '{bucket_name}': {e}")
            raise


def upload_file_to_s3(s3_client, local_file_path, bucket_name, s3_key=None):
    """
    Upload a file to S3/MinIO.
    
    Args:
        s3_client: boto3 S3 client
        local_file_path: Path to local file
        bucket_name: S3 bucket name
        s3_key: S3 object key (path in bucket). If None, uses filename.
    
    Returns:
        S3 URL of uploaded file
    """
    local_path = Path(local_file_path)
    
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_file_path}")
    
    # Use filename if s3_key not provided
    if s3_key is None:
        s3_key = local_path.name
    
    try:
        logger.info(f"Uploading {local_path.name} to s3://{bucket_name}/{s3_key}")
        
        # Upload file
        s3_client.upload_file(
            str(local_path),
            bucket_name,
            s3_key,
            ExtraArgs={'Metadata': {
                'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                'original_filename': local_path.name
            }}
        )
        
        # Construct S3 URL
        if s3_client.meta.endpoint_url:
            # MinIO or custom endpoint
            s3_url = f"{s3_client.meta.endpoint_url}/{bucket_name}/{s3_key}"
        else:
            # AWS S3
            s3_url = f"s3://{bucket_name}/{s3_key}"
        
        logger.info(f"✓ Successfully uploaded to {s3_url}")
        
        return s3_url
        
    except ClientError as e:
        logger.error(f"Failed to upload file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise


def upload_processed_data(processed_data_path, bucket_name, s3_prefix='processed_data', 
                         endpoint_url=None, access_key=None, secret_key=None):
    """
    Upload processed dataset to cloud storage.
    
    Args:
        processed_data_path: Path to processed data file (CSV or Parquet)
        bucket_name: S3 bucket name
        s3_prefix: Prefix for S3 object key (default: 'processed_data')
        endpoint_url: Custom endpoint URL (for MinIO)
        access_key: Access key ID
        secret_key: Secret access key
    
    Returns:
        Dictionary with upload information
    """
    print(f"\n{'='*60}")
    print("LOADING DATA TO CLOUD STORAGE (Step 2.3)")
    print(f"{'='*60}\n")
    
    processed_path = Path(processed_data_path)
    
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_data_path}")
    
    # Get S3 client
    try:
        s3_client = get_s3_client(endpoint_url, access_key, secret_key)
        print(f"✓ Connected to cloud storage")
        if endpoint_url:
            print(f"  Endpoint: {endpoint_url}")
        else:
            print(f"  Using AWS S3")
    except Exception as e:
        raise Exception(f"Failed to connect to cloud storage: {e}")
    
    # Ensure bucket exists
    try:
        ensure_bucket_exists(s3_client, bucket_name)
    except Exception as e:
        raise Exception(f"Failed to ensure bucket exists: {e}")
    
    # Upload file
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    s3_key = f"{s3_prefix}/{processed_path.name}"
    
    try:
        s3_url = upload_file_to_s3(s3_client, processed_path, bucket_name, s3_key)
        
        # Get file size
        file_size_mb = processed_path.stat().st_size / (1024 * 1024)
        
        result = {
            'local_path': str(processed_path),
            's3_url': s3_url,
            'bucket': bucket_name,
            's3_key': s3_key,
            'file_size_mb': round(file_size_mb, 2),
            'upload_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n{'='*60}")
        print("DATA LOADING COMPLETE")
        print(f"{'='*60}")
        print(f"  Local file: {processed_path.name}")
        print(f"  S3 URL: {s3_url}")
        print(f"  File size: {file_size_mb:.2f} MB")
        print(f"  Bucket: {bucket_name}")
        print(f"  S3 Key: {s3_key}")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        raise Exception(f"Failed to upload processed data: {e}")


def list_uploaded_files(s3_client, bucket_name, prefix='processed_data'):
    """
    List all files in the bucket with the given prefix.
    
    Args:
        s3_client: boto3 S3 client
        bucket_name: S3 bucket name
        prefix: Prefix to filter files
    
    Returns:
        List of file keys
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except ClientError as e:
        logger.error(f"Failed to list files: {e}")
        return []

