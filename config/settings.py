"""Centralized Environment Settings for ARA v1.0 using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # General App Settings
    APP_NAME: str = "AI Research Assistant (ARA)"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development, staging, production, test")
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "ara_super_secret_jwt_key_sprint_1_infrastructure"

    # PostgreSQL Database Settings
    POSTGRES_USER: str = "ara"
    POSTGRES_PASSWORD: str = "ara_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ara_db"
    DATABASE_URL: Optional[str] = None
    ASYNC_DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis Cache Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    REDIS_TTL_SECONDS: int = 3600
    REDIS_MAX_CONNECTIONS: int = 50

    # MinIO Object Storage Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "us-east-1"
    
    # MinIO Buckets
    MINIO_BUCKET_UPLOADS: str = "ara-uploads"
    MINIO_BUCKET_REPORTS: str = "ara-reports"
    MINIO_BUCKET_DATASETS: str = "ara-datasets"
    MINIO_BUCKET_SCREENSHOTS: str = "ara-screenshots"
    MINIO_BUCKET_BROWSER_DOWNLOADS: str = "ara-browser-downloads"
    MINIO_BUCKET_BROWSER_UPLOADS: str = "ara-browser-uploads"
    MINIO_BUCKET_GENERATED_FILES: str = "ara-generated-files"
    MINIO_BUCKET_TEMP_ASSETS: str = "ara-temp-assets"

    # Vector Embedding Settings (pgvector)
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    VECTOR_EMBEDDING_DIM: int = 1536
    VECTOR_DISTANCE_METRIC: str = "cosine"  # cosine, l2, inner_product

    # External APIs
    OPENALEX_API_KEY: Optional[str] = "I3EAeilCze3Ua9d5UyzKsf"
    CROSSREF_API_URL: str = "https://api.crossref.org/works/"

    # Authentication & JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_async_database_url(self) -> str:
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Singleton Settings Instance
settings = AppSettings()