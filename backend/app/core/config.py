from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Accounting System API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = ""

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS - comma-separated list of allowed origins
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = ""  # Additional origins, comma-separated

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # Email (for invites)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "Accounting System"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
