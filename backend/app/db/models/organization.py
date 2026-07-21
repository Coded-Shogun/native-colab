"""
Organization Model
Represents top-level organisations used for multi-tenant RBAC.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from app.db.session import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Organization(Base):
    """
    Organisation that owns workspaces and members.

    Attributes:
        id: UUID primary key
        name: Human-readable organisation name
        slug: URL-friendly unique identifier
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        is_active: Whether the organisation is active
    """

    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"
