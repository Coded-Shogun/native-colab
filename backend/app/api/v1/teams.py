"""
Team Management API
Provides endpoints for managing teams within workspaces
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import User, Team, TeamMember, Workspace, WorkspaceMember, TeamRole, WorkspaceRole
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamWithMembersResponse,
    TeamMemberResponse,
    TeamMemberAdd,
    TeamMemberRoleUpdate,
    TeamListResponse,
)
from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext

router = APIRouter(dependencies=[Depends(get_organization_context)])


# ============================================
# Helper Functions
# ============================================
async def check_workspace_membership(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> WorkspaceMember:
    """
    Check if user is a member of the workspace.
    Returns the workspace membership or raises 403.
    """
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    return membership


async def check_workspace_admin_permission(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> WorkspaceMember:
    """
    Check if user has admin or owner role in the workspace.
    Returns the workspace membership or raises 403.
    """
    membership = await check_workspace_membership(workspace_id, user, db)

    role_hierarchy = {
        WorkspaceRole.GUEST.value: 0,
        WorkspaceRole.MEMBER.value: 1,
        WorkspaceRole.ADMIN.value: 2,
        WorkspaceRole.OWNER.value: 3,
    }

    if role_hierarchy.get(membership.role, 0) < role_hierarchy[WorkspaceRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need admin or owner role to perform this action"
        )

    return membership


async def check_team_management_permission(
    team_id: int,
    user: User,
    db: AsyncSession
) -> tuple[Team, WorkspaceMember, TeamMember | None]:
    """
    Check if user can manage the team (workspace admin/owner or team lead).
    Returns the team, workspace membership, and team membership (if exists).
    """
    # Get team with workspace
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check workspace membership
    workspace_membership = await check_workspace_membership(team.workspace_id, user, db)

    # Check if user is workspace admin/owner
    role_hierarchy = {
        WorkspaceRole.GUEST.value: 0,
        WorkspaceRole.MEMBER.value: 1,
        WorkspaceRole.ADMIN.value: 2,
        WorkspaceRole.OWNER.value: 3,
    }

    is_workspace_admin = role_hierarchy.get(workspace_membership.role, 0) >= role_hierarchy[WorkspaceRole.ADMIN.value]

    # Check if user is team lead
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id
    )
    result = await db.execute(stmt)
    team_membership = result.scalar_one_or_none()

    is_team_lead = team_membership and team_membership.role == TeamRole.LEAD.value

    if not (is_workspace_admin or is_team_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need to be a workspace admin/owner or team lead to perform this action"
        )

    return team, workspace_membership, team_membership


# ============================================
# Team Endpoints
# ============================================
@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new team in a workspace.
    Only workspace admins and owners can create teams.
    """
    # Check workspace admin permission
    await check_workspace_admin_permission(team_data.workspace_id, current_user, db)

    # Check if workspace exists
    stmt = select(Workspace).where(Workspace.id == team_data.workspace_id)
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Create team
    new_team = Team(
        workspace_id=team_data.workspace_id,
        name=team_data.name,
        description=team_data.description
    )

    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team


@router.get("/workspace/{workspace_id}", response_model=TeamListResponse)
async def list_workspace_teams(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all teams in a workspace.
    Any workspace member can view teams.
    """
    # Check workspace membership
    await check_workspace_membership(workspace_id, current_user, db)

    # Get all teams in workspace
    stmt = select(Team).where(Team.workspace_id == workspace_id).order_by(Team.created_at.desc())
    result = await db.execute(stmt)
    teams = result.scalars().all()

    return TeamListResponse(teams=teams, total=len(teams))


@router.get("/{team_id}", response_model=TeamWithMembersResponse)
async def get_team_details(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team details with member list.
    Any workspace member can view team details.
    """
    # Get team
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check workspace membership
    await check_workspace_membership(team.workspace_id, current_user, db)

    # Get team members with user info
    stmt = (
        select(TeamMember)
        .options(selectinload(TeamMember.user))
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.joined_at.asc())
    )
    result = await db.execute(stmt)
    members = result.scalars().all()

    # Build member responses
    member_responses = [
        TeamMemberResponse(
            id=member.id,
            team_id=member.team_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            user_email=member.user.email if member.user else None,
            user_full_name=member.user.full_name if member.user else None,
            user_avatar_url=member.user.avatar_url if member.user else None,
        )
        for member in members
    ]

    return TeamWithMembersResponse(
        id=team.id,
        workspace_id=team.workspace_id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        members=member_responses
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update team information.
    Only workspace admins/owners or team leads can update teams.
    """
    team, _, _ = await check_team_management_permission(team_id, current_user, db)

    # Update fields
    update_data = team_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a team.
    Only workspace admins and owners can delete teams.
    """
    # Get team
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check workspace admin permission
    await check_workspace_admin_permission(team.workspace_id, current_user, db)

    # Delete team (cascade will delete team members)
    await db.delete(team)
    await db.commit()


# ============================================
# Team Member Endpoints
# ============================================
@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a member to a team.
    Only workspace admins/owners or team leads can add members.
    The user being added must be a workspace member.
    """
    team, _, _ = await check_team_management_permission(team_id, current_user, db)

    # Check if user being added is a workspace member
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == team.workspace_id,
        WorkspaceMember.user_id == member_data.user_id
    )
    result = await db.execute(stmt)
    workspace_membership = result.scalar_one_or_none()

    if not workspace_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a workspace member before being added to a team"
        )

    # Check if user is already a team member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == member_data.user_id
    )
    result = await db.execute(stmt)
    existing_member = result.scalar_one_or_none()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )

    # Get user for response
    stmt = select(User).where(User.id == member_data.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Add team member
    new_member = TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role.value
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return TeamMemberResponse(
        id=new_member.id,
        team_id=new_member.team_id,
        user_id=new_member.user_id,
        role=new_member.role,
        joined_at=new_member.joined_at,
        user_email=user.email,
        user_full_name=user.full_name,
        user_avatar_url=user.avatar_url,
    )


@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member_role(
    team_id: int,
    user_id: int,
    role_update: TeamMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a team member's role.
    Only workspace admins/owners or team leads can update roles.
    """
    team, _, _ = await check_team_management_permission(team_id, current_user, db)

    # Get team member
    stmt = (
        select(TeamMember)
        .options(selectinload(TeamMember.user))
        .where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    team_member = result.scalar_one_or_none()

    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )

    # Update role
    team_member.role = role_update.role.value
    await db.commit()
    await db.refresh(team_member)

    return TeamMemberResponse(
        id=team_member.id,
        team_id=team_member.team_id,
        user_id=team_member.user_id,
        role=team_member.role,
        joined_at=team_member.joined_at,
        user_email=team_member.user.email if team_member.user else None,
        user_full_name=team_member.user.full_name if team_member.user else None,
        user_avatar_url=team_member.user.avatar_url if team_member.user else None,
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from a team.
    Only workspace admins/owners or team leads can remove members.
    Users can also remove themselves from a team.
    """
    # Allow users to remove themselves
    if user_id != current_user.id:
        await check_team_management_permission(team_id, current_user, db)
    else:
        # Just check that team exists and user is in workspace
        stmt = select(Team).where(Team.id == team_id)
        result = await db.execute(stmt)
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        await check_workspace_membership(team.workspace_id, current_user, db)

    # Get team member
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    )
    result = await db.execute(stmt)
    team_member = result.scalar_one_or_none()

    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )

    # Remove team member
    await db.delete(team_member)
    await db.commit()
