"""
Organization Context Module
Provides organization-scoped context extraction from request headers.
"""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.session import get_db


@dataclass
class OrganizationContext:
    """Lightweight organisation context carried on every org-scoped request."""

    org_id: str
    org_name: str


async def get_organization_context(
    x_organization_id: str = Header(..., alias="X-Organization-Id"),
    db: AsyncSession = Depends(get_db),
) -> OrganizationContext:
    """
    Extract the organisation header and look up the organisation in the DB.

    Returns 404 when the header is missing, blank, or the organisation does
    not exist.
    """
    if not x_organization_id or not x_organization_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-Id header is required",
        )

    org_id = x_organization_id.strip()

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{org_id}' not found",
        )

    return OrganizationContext(
        org_id=org.id,
        org_name=org.name,
    )


async def require_org_access(
    current_user: User = Depends(get_current_user),
    org_context: OrganizationContext = Depends(get_organization_context),
) -> tuple[User, OrganizationContext]:
    """
    Return the authenticated user together with the organisation context.

    Full membership / RBAC checks are deferred to a future issue.
    """
    return current_user, org_context
