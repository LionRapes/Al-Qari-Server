"""Application configuration module for handling environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class S3StorageSettings:
    """Settings for Yandex S3 Object Storage connection."""

    BUCKET_NAME = os.getenv("YANDEX_BUCKET_NAME", "al-qari")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_ENDPOINT = "https://storage.yandexcloud.net"
    REGION = "ru-central1"


class YDBSettings:
    """Settings for Yandex Database (YDB) connection."""

    YDB_DATABASE = os.getenv("YDB_DATABASE", "").strip()
    YDB_ENDPOINT = "grpcs://ydb.serverless.yandexcloud.net:2135"


class MailSettings:
    """Settings for SMTP email configuration and mailing."""

    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")
    SMTP_HOST = "smtp.mail.ru"
    SMTP_PORT = 465


class JWTSettings:
    """Settings for JSON Web Token (JWT) authentication and hashing."""

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"


STORAGE_SETTINGS = S3StorageSettings()
YDB_SETTINGS = YDBSettings()
MAIL_SETTINGS = MailSettings()
JWT_SETTINGS = JWTSettings()
