import os

from dotenv import load_dotenv

load_dotenv()

class S3StorageSettings:
    BUCKET_NAME = os.getenv("YANDEX_BUCKET_NAME", "al-qari")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_ENDPOINT = "https://storage.yandexcloud.net"
    REGION = "ru-central1"

    
class YDBSettings:
    YDB_DATABASE = os.getenv("YDB_DATABASE")
    YDB_ENDPOINT = "grpcs://ydb.serverless.yandexcloud.net:2135"
    
class MailSettings:
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FRONTEND_URL = os.getenv("FRONTEND_URL")
    SMTP_HOST = "smtp.mail.ru"
    SMTP_PORT = 465
    
class JWTSettings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"


storageSettings = S3StorageSettings()
ydbSettings = YDBSettings()
mailSettings = MailSettings()
jwtSettings = JWTSettings()