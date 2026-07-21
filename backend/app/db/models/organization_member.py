"""
Organization Member Model
Join table linking users to organisations with a role.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.db.session import Base


def _utcnow():
    return datetime.now(timezone.utc)


class OrganizationMember(Base):
    """
    Organisation membership linking users to organisations.

    Attributes:
        id: UUID primary key
        organization_id: Foreign key to Organization
        user_id: Foreign key to User
        role: Member's role (owner, admin, member, viewer)
        created_at: Timestamp of when membership was created
    """

    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member", nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_organization_user"),
    )

    def __repr__(self):
        return (
            f"<OrganizationMember(organization_id={self.organization_id}, "
            f"user_id={self.user_id}, role='{self.role}')>"
        )
