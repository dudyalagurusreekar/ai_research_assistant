"""Database Manager & Session Factory with Sync and Async context managers."""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from infrastructure.database.config import db_config
from utils.logger import get_logger

logger = get_logger("DatabaseManager")


class DatabaseManager:
    """Production database manager providing engines, sessions, and transaction management."""

    def __init__(self, database_url: Optional[str] = None):
        self._url = database_url or db_config.url
        self._is_sqlite = self._url.startswith("sqlite")
        
        # Configure engine options based on dialect
        if self._is_sqlite:
            from sqlalchemy.pool import StaticPool
            engine_kwargs = {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        else:
            engine_kwargs = db_config.engine_kwargs
        
        self.engine = create_engine(self._url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_all_tables(self, base_class: type) -> None:
        """Create all registered ORM tables in database."""
        logger.info(f"Creating all database tables for URL: {self._url}")
        base_class.metadata.create_all(bind=self.engine)

    def drop_all_tables(self, base_class: type) -> None:
        """Drop all ORM tables (used for testing resets)."""
        logger.warning(f"Dropping all database tables for URL: {self._url}")
        base_class.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional session scope for database operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error(f"Database session error, rolling back transaction: {exc}")
            raise
        finally:
            session.close()

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """Context manager explicitly managing database transactions."""
        session = self.SessionLocal()
        try:
            session.begin()
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error(f"Transaction failed, rolled back: {exc}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check database connection connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            return False


# Global default DatabaseManager instance
db_manager = DatabaseManager()
