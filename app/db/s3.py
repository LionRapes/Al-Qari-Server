"""Yandex S3 Object Storage implementation."""

import json

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import STORAGE_SETTINGS
from app.core.interfaces import StorageInterface


class YandexS3Storage(StorageInterface):
    """Storage client for interacting with Yandex Object Storage (S3)."""

    def __init__(self):
        """Initialize the S3 client with configuration settings."""
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=STORAGE_SETTINGS.s3_endpoint,
            aws_access_key_id=STORAGE_SETTINGS.aws_access_key,
            aws_secret_access_key=STORAGE_SETTINGS.aws_secret_key,
            region_name=STORAGE_SETTINGS.region,
        )
        self.bucket = STORAGE_SETTINGS.bucket_name

    def fetch_json(self, file_path: str) -> str:
        """Fetch and parse a JSON file from the S3 bucket."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            raw_data = response["Body"].read().decode("utf-8")
            return json.loads(raw_data)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File '{file_path}' not found.") from e
            raise RuntimeError(f"Cloud storage error: {e!s}") from e
        except json.JSONDecodeError as exc:
            raise ValueError(f"File '{file_path}' is not valid JSON.") from exc

    async def create_presigned_url(self, key: str, expires_in: int = 900) -> str:
        """Generate a pre-signed URL for temporary file access."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except (BotoCoreError, ClientError):
            return None

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload raw byte data to the S3 bucket."""
        try:
            self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        except ClientError as e:
            raise RuntimeError(f"Failed to upload file '{key}' to S3: {e!s}") from e
