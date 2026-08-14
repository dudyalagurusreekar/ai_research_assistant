"""Redis Cache Configuration provider."""

from config.settings import settings


class RedisConfig:
    """Redis connection and keyspace configuration options."""

    @property
    def url(self) -> str:
        return settings.get_redis_url()

    @property
    def ttl_seconds(self) -> int:
        return settings.REDIS_TTL_SECONDS

    @property
    def max_connections(self) -> int:
        return settings.REDIS_MAX_CONNECTIONS


redis_config = RedisConfig()
