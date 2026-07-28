"""Configuration Loader reading environment variables and .env files."""

import os
from typing import Optional
from core.config.settings import AppConfig, EventConfig, SessionConfig
from core.exceptions.base import ConfigError
from core.exceptions.codes import ErrorCode


class ConfigLoader:
    """Loads configuration values from environment variables and environment files."""

    @staticmethod
    def load_from_env(env_file: Optional[str] = None) -> AppConfig:
        """Load configuration from environment variables and optional .env file.

        Args:
            env_file: Path to optional .env file to load beforehand.

        Returns:
            AppConfig instance initialized with typed settings.
        """
        if env_file and os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            os.environ.setdefault(key.strip(), val.strip())
            except Exception as e:
                raise ConfigError(
                    f"Failed to read env file '{env_file}'",
                    code=ErrorCode.CONFIG_INVALID,
                    cause=e,
                )

        env_name = os.getenv("APP_ENV", "development")
        debug = os.getenv("APP_DEBUG", "false").lower() in ("true", "1", "yes")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Load event bus settings
        max_q = int(os.getenv("EVENT_MAX_QUEUE_SIZE", "1000"))
        disp_tout = float(os.getenv("EVENT_DISPATCH_TIMEOUT", "30.0"))
        async_exec = os.getenv("EVENT_ENABLE_ASYNC", "true").lower() in ("true", "1", "yes")
        event_cfg = EventConfig(
            max_queue_size=max_q,
            dispatch_timeout_seconds=disp_tout,
            enable_async_execution=async_exec,
        )

        # Load session settings
        sess_tout = float(os.getenv("SESSION_DEFAULT_TIMEOUT", "3600.0"))
        max_sess = int(os.getenv("SESSION_MAX_CONCURRENT", "50"))
        sess_cfg = SessionConfig(
            default_timeout_seconds=sess_tout,
            max_concurrent_sessions=max_sess,
        )

        return AppConfig(
            environment=env_name,
            debug=debug,
            log_level=log_level,
            events=event_cfg,
            session=sess_cfg,
        )
