"""Generic BaseRepository implementation with CRUD, filtering, pagination, and soft delete."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy import func
from sqlalchemy.orm import Session
from infrastructure.database.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository providing clean Data Access Layer abstractions over ORM models."""

    def __init__(self, model_cls: Type[T], session: Session):
        self.model_cls = model_cls
        self.session = session

    def get_by_id(self, entity_id: str, include_soft_deleted: bool = False) -> Optional[T]:
        """Fetch a single record by primary key."""
        query = self.session.query(self.model_cls).filter(self.model_cls.id == entity_id)
        if hasattr(self.model_cls, "is_deleted") and not include_soft_deleted:
            query = query.filter(self.model_cls.is_deleted.is_(False))
        return query.first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = True,
        include_soft_deleted: bool = False,
    ) -> List[T]:
        """Retrieve paginated records matching optional filters."""
        query = self.session.query(self.model_cls)
        
        if hasattr(self.model_cls, "is_deleted") and not include_soft_deleted:
            query = query.filter(self.model_cls.is_deleted.is_(False))

        if filters:
            for field, val in filters.items():
                if hasattr(self.model_cls, field):
                    query = query.filter(getattr(self.model_cls, field) == val)

        if order_by and hasattr(self.model_cls, order_by):
            col = getattr(self.model_cls, order_by)
            query = query.order_by(col.desc() if descending else col.asc())
        elif hasattr(self.model_cls, "created_at"):
            col = getattr(self.model_cls, "created_at")
            query = query.order_by(col.desc() if descending else col.asc())

        return query.offset(skip).limit(limit).all()

    def count(self, filters: Optional[Dict[str, Any]] = None, include_soft_deleted: bool = False) -> int:
        """Count total records matching optional criteria."""
        query = self.session.query(func.count(self.model_cls.id))
        
        if hasattr(self.model_cls, "is_deleted") and not include_soft_deleted:
            query = query.filter(self.model_cls.is_deleted.is_(False))

        if filters:
            for field, val in filters.items():
                if hasattr(self.model_cls, field):
                    query = query.filter(getattr(self.model_cls, field) == val)

        return query.scalar() or 0

    def create(self, attributes: Dict[str, Any]) -> T:
        """Instantiate and persist a new model instance."""
        entity = self.model_cls(**attributes)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity_id: str, attributes: Dict[str, Any]) -> Optional[T]:
        """Update an existing record attributes."""
        entity = self.get_by_id(entity_id, include_soft_deleted=True)
        if not entity:
            return None
        
        for key, val in attributes.items():
            if hasattr(entity, key):
                setattr(entity, key, val)

        self.session.flush()
        return entity

    def delete(self, entity_id: str, hard_delete: bool = False) -> bool:
        """Delete or soft-delete a record."""
        entity = self.get_by_id(entity_id, include_soft_deleted=True)
        if not entity:
            return False

        if hard_delete or not hasattr(entity, "soft_delete"):
            self.session.delete(entity)
        else:
            entity.soft_delete()

        self.session.flush()
        return True

    def bulk_create(self, attributes_list: List[Dict[str, Any]]) -> List[T]:
        """Bulk insert multiple records."""
        entities = [self.model_cls(**attrs) for attrs in attributes_list]
        self.session.add_all(entities)
        self.session.flush()
        return entities
