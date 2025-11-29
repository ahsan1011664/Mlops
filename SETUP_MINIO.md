# MinIO Setup Guide (Step 2.3)

MinIO is an S3-compatible object storage server, perfect for local testing and development.

## Option 1: Use MinIO with Docker (Recommended for Local Testing)

### Quick Start

MinIO is already configured in `docker-compose.yml`. Just start it:

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
docker-compose up -d minio
```

### Access MinIO Console

1. Open browser: **http://localhost:9001**
2. Login:
   - Username: `minioadmin`
   - Password: `minioadmin`

### Default Configuration

- **Endpoint**: `http://localhost:9000`
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin`
- **Bucket**: `lahore-weather-data` (will be created automatically)

## Option 2: Use AWS S3

### Setup

1. Get AWS credentials:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region (e.g., `us-east-1`)

2. Set environment variables:
```powershell
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:S3_BUCKET_NAME = "lahore-weather-data"
# Leave S3_ENDPOINT_URL unset (or set to $null)
```

3. Create S3 bucket (via AWS Console or CLI):
```powershell
aws s3 mb s3://lahore-weather-data --region us-east-1
```

## Option 3: Use Azure Blob Storage

For Azure Blob Storage, you'll need to use the Azure SDK instead of boto3. This requires additional setup.

## Configuration in Airflow DAG

The DAG reads configuration from environment variables:

```python
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'lahore-weather-data')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', None)  # None for AWS, URL for MinIO
S3_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
S3_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('MINIO_SECRET_KEY', 'minioadmin')
```

## Testing the Upload

After running the DAG, check:

1. **MinIO Console**: http://localhost:9001
   - Navigate to `lahore-weather-data` bucket
   - Check `processed_data/` folder

2. **AWS S3 Console**: 
   - Navigate to your bucket
   - Check `processed_data/` prefix

3. **Via CLI**:
```powershell
# MinIO
aws s3 ls s3://lahore-weather-data/processed_data/ --endpoint-url http://localhost:9000

# AWS S3
aws s3 ls s3://lahore-weather-data/processed_data/
```

## Troubleshooting

### Connection Errors

- **MinIO not running**: Start with `docker-compose up -d minio`
- **Wrong endpoint**: Check `S3_ENDPOINT_URL` is `http://localhost:9000` for MinIO
- **Wrong credentials**: Verify access key and secret key

### Permission Errors

- **Bucket doesn't exist**: The script will create it automatically
- **Access denied**: Check credentials and bucket policies

### Network Issues

- **Can't reach MinIO**: Ensure MinIO container is running and port 9000 is accessible
- **Timeout**: Check firewall settings

