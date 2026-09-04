import json

import boto3
import ydb
from botocore.exceptions import BotoCoreError, ClientError

from app.config import storageSettings, ydbSettings
from app.interfaces import StorageInterface, YdbInterface


class YandexS3Storage(StorageInterface):
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=storageSettings.S3_ENDPOINT,
            aws_access_key_id=storageSettings.AWS_ACCESS_KEY,
            aws_secret_access_key=storageSettings.AWS_SECRET_KEY,
            region_name=storageSettings.REGION,
        )
        self.bucket = storageSettings.BUCKET_NAME

    def fetch_json(self, file_path: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            raw_data = response["Body"].read().decode("utf-8")
            return json.loads(raw_data)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File '{file_path}' not found.")
            raise RuntimeError(f"Cloud storage error: {e!s}")
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
        except (BotoCoreError, ClientError):
            return None
        
    
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to upload file '{key}' to S3: {e!s}")
        

import os
import ydb

class YandexYdbStorage(YdbInterface):
    def __init__(self):
        endpoint = ydbSettings.YDB_ENDPOINT
        database = ydbSettings.YDB_DATABASE
        
        key_file = os.getenv("YDB_SERVICE_ACCOUNT_KEY_FILE")

        if key_file and os.path.exists(key_file):
            credentials = ydb.iam.ServiceAccountCredentials.from_file(key_file)
        else:
            credentials = ydb.iam.MetadataUrlCredentials()

        driver_config = ydb.DriverConfig(
            endpoint=endpoint,
            database=database,
            credentials=credentials
        )
        print(endpoint, database, credentials)
        self.driver = ydb.Driver(driver_config)
        
        try:
            self.driver.wait(timeout=5, fail_fast=True)
        except TimeoutError:
            raise RuntimeError("Error connecting YDB")

        self.pool = ydb.SessionPool(self.driver)

    def execute(self, query: str, parameters: dict | None = None) -> list:
        def callee(session: ydb.Session):
            prepared = session.prepare(query)
            
            result_sets = session.transaction().execute(
                prepared, 
                parameters,
                commit_tx=True
            )
            return result_sets

        result = self.pool.retry_operation_sync(callee)
        
        if result and len(result) > 0:
            return result[0].rows
        return []

    def close(self):
        self.pool.stop()
        self.driver.stop()