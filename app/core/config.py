"""Application configuration module for handling environment variables."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

environment = os.getenv("APP_ENV", "development")

if environment == "production":
    active_env_files = (".env", ".env.production")
else:
    active_env_files = (".env")

class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=active_env_files,
        env_file_encoding="utf-8",
        extra="ignore"
    )


class CoreSettings(BaseConfig):
    """Settings for Yandex S3 Object Storage connection."""
    
    cors_origins: str
    frontend_base_url: str


class S3StorageSettings(BaseConfig):
    """Settings for Yandex S3 Object Storage connection."""
    
    bucket_name: str = Field(alias="YANDEX_BUCKET_NAME")
    aws_access_key: str = Field(alias="AWS_ACCESS_KEY_ID")
    aws_secret_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")
    s3_endpoint: str = "https://storage.yandexcloud.net"
    region: str = "ru-central1"


class YDBSettings(BaseConfig):
    """Settings for Yandex Database (YDB) connection."""
    
    ydb_database: str = ""
    ydb_endpoint: str = "grpcs://ydb.serverless.yandexcloud.net:2135"
    ydb_service_account_key_file: str = 'secrets/keys/authorized_key.json'


class MailSettings(BaseConfig):
    """Settings for SMTP email configuration and mailing."""
    
    smtp_user: str
    smtp_password: str
    smtp_host: str = "smtp.mail.ru"
    smtp_port: int = 465


class JWTSettings(BaseConfig):
    """Settings for JSON Web Token (JWT) authentication and hashing."""
    
    jwt_secret_key: str
    algorithm: str = "HS256"


CORE_SETTINGS = CoreSettings()
STORAGE_SETTINGS = S3StorageSettings()
YDB_SETTINGS = YDBSettings()
MAIL_SETTINGS = MailSettings()
JWT_SETTINGS = JWTSettings()