"""
Workspace Schemas
Pydantic models for workspace-related requests and responses
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse


class WorkspaceCreate(BaseModel):
    """Schema for creating a workspace"""
    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    slug: str = Field(..., min_length=1, max_length=255, description="URL-friendly identifier")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is URL-friendly"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only letters, numbers, hyphens, and underscores")
        return v.lower()


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    logo_url: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Schema for workspace responses"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class WorkspaceMemberResponse(BaseModel):
    """Schema for workspace member responses"""
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None

    model_config = {
        "from_attributes": True
    }


class WorkspaceWithMembersResponse(WorkspaceResponse):
    """Schema for workspace with members"""
    members: List[WorkspaceMemberResponse] = []


class WorkspaceInviteRequest(BaseModel):
    """Schema for inviting a user to workspace"""
    email: str = Field(..., description="Email of user to invite")
    role: str = Field(default="member", description="Role to assign (owner, admin, member, guest)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values"""
        allowed_roles = ["owner", "admin", "member", "guest"]
        if v.lower() not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v.lower()


class WorkspaceRoleUpdate(BaseModel):
    """Schema for updating a member's role"""
    role: str = Field(..., description="New role (owner, admin, member, guest)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values"""
        allowed_roles = ["owner", "admin", "member", "guest"]
        if v.lower() not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v.lower()
