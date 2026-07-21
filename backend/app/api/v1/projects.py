"""
Project Management API
Provides endpoints for managing projects within workspaces
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Project,
    ProjectStatus,
    Task,
    TaskStatus,
    Workspace,
    WorkspaceMember,
    Team,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> WorkspaceMember:
    """
    Check if user has access to the workspace.
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
            detail="You don't have access to this workspace"
        )

    return membership


async def get_project_with_access_check(
    project_id: int,
    user: User,
    db: AsyncSession
) -> Project:
    """
    Get project and verify user has workspace access.
    Returns the project or raises 404/403.
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check workspace access
    await check_workspace_access(project.workspace_id, user, db)

    return project


# ============================================
# Project Endpoints
# ============================================
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project in a workspace.
    User must be a member of the workspace.
    """
    # Check workspace access
    await check_workspace_access(project_data.workspace_id, current_user, db)

    # Verify workspace exists
    stmt = select(Workspace).where(Workspace.id == project_data.workspace_id)
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # If team_id provided, verify it belongs to the workspace
    if project_data.team_id:
        stmt = select(Team).where(
            Team.id == project_data.team_id,
            Team.workspace_id == project_data.workspace_id
        )
        result = await db.execute(stmt)
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team not found or doesn't belong to this workspace"
            )

    # Create project
    new_project = Project(
        workspace_id=project_data.workspace_id,
        team_id=project_data.team_id,
        owner_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        status=project_data.status.value,
        start_date=project_data.start_date,
        due_date=project_data.due_date
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return new_project


@router.get("/workspace/{workspace_id}", response_model=ProjectListResponse)
async def list_workspace_projects(
    workspace_id: int,
    status_filter: Optional[ProjectStatus] = Query(None, alias="status"),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects in a workspace.
    User must be a member of the workspace.
    """
    # Check workspace access
    await check_workspace_access(workspace_id, current_user, db)

    # Build query
    stmt = select(Project).where(Project.workspace_id == workspace_id)

    # Apply filters
    if status_filter:
        stmt = stmt.where(Project.status == status_filter.value)

    if not include_archived:
        stmt = stmt.where(Project.is_archived == False)

    stmt = stmt.order_by(Project.created_at.desc())

    result = await db.execute(stmt)
    projects = result.scalars().all()

    # Get task counts for each project
    project_responses = []
    for project in projects:
        # Count total tasks
        task_count_stmt = select(func.count(Task.id)).where(Task.project_id == project.id)
        task_count_result = await db.execute(task_count_stmt)
        task_count = task_count_result.scalar()

        # Count completed tasks
        completed_count_stmt = select(func.count(Task.id)).where(
            Task.project_id == project.id,
            Task.status == TaskStatus.DONE.value
        )
        completed_count_result = await db.execute(completed_count_stmt)
        completed_count = completed_count_result.scalar()

        project_response = ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            team_id=project.team_id,
            owner_id=project.owner_id,
            name=project.name,
            description=project.description,
            status=project.status,
            start_date=project.start_date,
            due_date=project.due_date,
            is_archived=project.is_archived,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=task_count,
            completed_task_count=completed_count
        )
        project_responses.append(project_response)

    return ProjectListResponse(projects=project_responses, total=len(project_responses))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_details(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project details.
    User must have access to the workspace.
    """
    project = await get_project_with_access_check(project_id, current_user, db)

    # Get task counts
    task_count_stmt = select(func.count(Task.id)).where(Task.project_id == project.id)
    task_count_result = await db.execute(task_count_stmt)
    task_count = task_count_result.scalar()

    completed_count_stmt = select(func.count(Task.id)).where(
        Task.project_id == project.id,
        Task.status == TaskStatus.DONE.value
    )
    completed_count_result = await db.execute(completed_count_stmt)
    completed_count = completed_count_result.scalar()

    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        team_id=project.team_id,
        owner_id=project.owner_id,
        name=project.name,
        description=project.description,
        status=project.status,
        start_date=project.start_date,
        due_date=project.due_date,
        is_archived=project.is_archived,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        completed_task_count=completed_count
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update project information.
    User must have access to the workspace.
    """
    project = await get_project_with_access_check(project_id, current_user, db)

    # If team_id is being updated, verify it belongs to the workspace
    if project_update.team_id is not None:
        if project_update.team_id != project.team_id:
            stmt = select(Team).where(
                Team.id == project_update.team_id,
                Team.workspace_id == project.workspace_id
            )
            result = await db.execute(stmt)
            team = result.scalar_one_or_none()

            if not team:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team not found or doesn't belong to this workspace"
                )

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(project, field, value.value)
        else:
            setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a project and all its tasks.
    User must have access to the workspace.
    """
    project = await get_project_with_access_check(project_id, current_user, db)

    # Delete project (cascade will delete tasks and comments)
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a project.
    User must have access to the workspace.
    """
    project = await get_project_with_access_check(project_id, current_user, db)

    project.is_archived = True
    await db.commit()
    await db.refresh(project)

    return project


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
async def unarchive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unarchive a project.
    User must have access to the workspace.
    """
    project = await get_project_with_access_check(project_id, current_user, db)

    project.is_archived = False
    await db.commit()
    await db.refresh(project)

    return project
