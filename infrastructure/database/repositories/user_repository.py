"""User, Role, and API Key repository implementations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from infrastructure.database.models.auth import APIKey, Role, User, UserRole
from infrastructure.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Specialized repository for User entity operations."""

    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch active user by email address."""
        return (
            self.session.query(User)
            .filter(User.email == email, User.is_deleted.is_(False))
            .first()
        )

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Fetch all assigned roles for a user."""
        return (
            self.session.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )

    def assign_role(self, user_id: str, role_id: str) -> UserRole:
        """Assign a role to a user."""
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        self.session.flush()
        return user_role

    def get_active_api_key(self, key_hash: str) -> Optional[APIKey]:
        """Validate and fetch active API Key."""
        return (
            self.session.query(APIKey)
            .filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active.is_(True),
                APIKey.is_deleted.is_(False),
            )
            .first()
        )
