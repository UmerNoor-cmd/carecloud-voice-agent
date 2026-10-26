import os
from pydantic_settings import BaseSettings if False else object

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./patients.db")
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PHONE_NUMBER_ID: str = os.getenv("VAPI_PHONE_NUMBER_ID", "")
    VAPI_ASSISTANT_ID: str = os.getenv("VAPI_ASSISTANT_ID", "")
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "carecloud-secret-demo-key")

settings = Settings()
