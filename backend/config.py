# config.py
"""
Centralized configuration management for the AFCARE platform.
All settings are loaded from environment variables with secure defaults.
"""
import os
import secrets
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AFCARE API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = os.getenv(
        "SQLALCHEMY_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite:///./afcare.db")
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["*"]  # Restrict in production
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # AWS S3
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Blockchain (Phase 2)
    blockchain_node: Optional[str] = os.getenv("BLOCKCHAIN_NODE")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "your-secret-key" or len(v) < 32:
            # Generate a secure key if placeholder or too short
            return secrets.token_urlsafe(32)
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance for convenience
settings = get_settings()
