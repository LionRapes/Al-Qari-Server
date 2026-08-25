import json
import boto3
from botocore.exceptions import ClientError
from app.interfaces import StorageInterface
from app.config import settings

class YandexS3Storage(StorageInterface):
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.REGION,
        )
        self.bucket = settings.BUCKET_NAME

    def fetch_json(self, file_path: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            raw_data = response["Body"].read().decode("utf-8")
            return json.loads(raw_data)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File '{file_path}' not found.")
            raise RuntimeError(f"Cloud storage error: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError(f"File '{file_path}' is not valid JSON.")
        
    
    async def create_presigned_url(self, key: str, expires_in: int = 900) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except Exception:
            return None