"""Database Configuration Settings."""

from typing import Any, Dict
from config.settings import settings


class DatabaseConfig:
    """Database configuration options derived from global settings."""

    @property
    def url(self) -> str:
        return settings.get_database_url()

    @property
    def async_url(self) -> str:
        return settings.get_async_database_url()

    @property
    def engine_kwargs(self) -> Dict[str, Any]:
        return {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "echo": settings.DB_ECHO,
        }


db_config = DatabaseConfig()
