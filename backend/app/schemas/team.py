"""
Team Schemas
Pydantic schemas for team validation and serialization
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.db.models.team import TeamRole


# ============================================
# Base Schemas
# ============================================
class TeamBase(BaseModel):
    """Base schema for team data"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


# ============================================
# Request Schemas (Input)
# ============================================
class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    workspace_id: int = Field(..., gt=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate team name"""
        if not v or not v.strip():
            raise ValueError('Team name cannot be empty')
        return v.strip()


class TeamUpdate(BaseModel):
    """Schema for updating team information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate team name if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError('Team name cannot be empty')
            return v.strip()
        return v


class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team"""
    user_id: int = Field(..., gt=0)
    role: TeamRole = Field(default=TeamRole.MEMBER)


class TeamMemberRoleUpdate(BaseModel):
    """Schema for updating a team member's role"""
    role: TeamRole = Field(...)


# ============================================
# Response Schemas (Output)
# ============================================
class TeamMemberResponse(BaseModel):
    """Schema for team member response"""
    id: int
    team_id: int
    user_id: int
    role: str
    joined_at: datetime

    # User information (nested)
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class TeamResponse(BaseModel):
    """Schema for team response"""
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class TeamWithMembersResponse(TeamResponse):
    """Schema for team response with members"""
    members: List[TeamMemberResponse] = []

    model_config = {
        "from_attributes": True
    }


class TeamListResponse(BaseModel):
    """Schema for list of teams in a workspace"""
    teams: List[TeamResponse]
    total: int

    model_config = {
        "from_attributes": True
    }
