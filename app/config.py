import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BUCKET_NAME = os.getenv("YANDEX_BUCKET_NAME", "al-qari")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_ENDPOINT = "https://storage.yandexcloud.net"
    REGION = "ru-central1"

settings = Settings()