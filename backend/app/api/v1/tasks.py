"""
Task Management API
Provides endpoints for managing tasks and comments within projects
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Project,
    Task,
    TaskStatus,
    TaskComment,
    WorkspaceMember,
)
from app.schemas.project import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatusUpdate,
    TaskAssigneeUpdate,
    TaskWithCommentsResponse,
    TaskCommentCreate,
    TaskCommentUpdate,
    TaskCommentResponse,
)
from app.core.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_project_access(
    project_id: int,
    user: User,
    db: AsyncSession
) -> Project:
    """
    Check if user has access to the project via workspace membership.
    Returns the project or raises 403/404.
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check workspace membership
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == project.workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )

    return project


async def get_task_with_access_check(
    task_id: int,
    user: User,
    db: AsyncSession
) -> Task:
    """
    Get task and verify user has project/workspace access.
    Returns the task or raises 404/403.
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check project access (which checks workspace membership)
    await check_project_access(task.project_id, user, db)

    return task


# ============================================
# Task Endpoints
# ============================================
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task in a project.
    User must have access to the project's workspace.
    """
    # Check project access
    project = await check_project_access(task_data.project_id, current_user, db)

    # If assignee_id provided, verify they're a workspace member
    if task_data.assignee_id:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == task_data.assignee_id
        )
        result = await db.execute(stmt)
        assignee_membership = result.scalar_one_or_none()

        if not assignee_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a workspace member"
            )

    # Get max position for new task
    max_position_stmt = select(func.max(Task.position)).where(
        Task.project_id == task_data.project_id
    )
    result = await db.execute(max_position_stmt)
    max_position = result.scalar() or 0

    # Create task
    new_task = Task(
        project_id=task_data.project_id,
        assignee_id=task_data.assignee_id,
        created_by_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status.value,
        priority=task_data.priority.value,
        position=max_position + 1,
        due_date=task_data.due_date
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Load related data for response
    stmt = (
        select(Task)
        .options(selectinload(Task.assignee), selectinload(Task.created_by))
        .where(Task.id == new_task.id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        created_by_id=task.created_by_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_email=task.assignee.email if task.assignee else None,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by_email=task.created_by.email if task.created_by else None,
        created_by_name=task.created_by.full_name if task.created_by else None,
        comment_count=0
    )


@router.get("/project/{project_id}", response_model=TaskListResponse)
async def list_project_tasks(
    project_id: int,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    assignee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tasks in a project.
    User must have access to the project.
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # Build query
    stmt = (
        select(Task)
        .options(selectinload(Task.assignee), selectinload(Task.created_by))
        .where(Task.project_id == project_id)
    )

    # Apply filters
    if status_filter:
        stmt = stmt.where(Task.status == status_filter.value)

    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)

    stmt = stmt.order_by(Task.position.asc())

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Build task responses with comment counts
    task_responses = []
    for task in tasks:
        # Count comments
        comment_count_stmt = select(func.count(TaskComment.id)).where(
            TaskComment.task_id == task.id
        )
        comment_count_result = await db.execute(comment_count_stmt)
        comment_count = comment_count_result.scalar()

        task_response = TaskResponse(
            id=task.id,
            project_id=task.project_id,
            assignee_id=task.assignee_id,
            created_by_id=task.created_by_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            position=task.position,
            due_date=task.due_date,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            assignee_email=task.assignee.email if task.assignee else None,
            assignee_name=task.assignee.full_name if task.assignee else None,
            created_by_email=task.created_by.email if task.created_by else None,
            created_by_name=task.created_by.full_name if task.created_by else None,
            comment_count=comment_count
        )
        task_responses.append(task_response)

    return TaskListResponse(tasks=task_responses, total=len(task_responses))


@router.get("/{task_id}", response_model=TaskWithCommentsResponse)
async def get_task_details(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get task details with comments.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    # Load related data
    stmt = (
        select(Task)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.created_by),
            selectinload(Task.comments).selectinload(TaskComment.author)
        )
        .where(Task.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()

    # Build comment responses
    comment_responses = [
        TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            author_id=comment.author_id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author_email=comment.author.email if comment.author else None,
            author_name=comment.author.full_name if comment.author else None,
            author_avatar_url=comment.author.avatar_url if comment.author else None,
        )
        for comment in task.comments
    ]

    return TaskWithCommentsResponse(
        id=task.id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        created_by_id=task.created_by_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_email=task.assignee.email if task.assignee else None,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by_email=task.created_by.email if task.created_by else None,
        created_by_name=task.created_by.full_name if task.created_by else None,
        comment_count=len(comment_responses),
        comments=comment_responses
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update task information.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    # Get project for workspace check
    stmt = select(Project).where(Project.id == task.project_id)
    result = await db.execute(stmt)
    project = result.scalar_one()

    # If assignee_id is being updated, verify they're a workspace member
    if task_update.assignee_id is not None and task_update.assignee_id != task.assignee_id:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == task_update.assignee_id
        )
        result = await db.execute(stmt)
        assignee_membership = result.scalar_one_or_none()

        if not assignee_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a workspace member"
            )

    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["status", "priority"] and value:
            setattr(task, field, value.value)
        else:
            setattr(task, field, value)

    # If status changed to DONE, set completed_at
    if task_update.status and task_update.status == TaskStatus.DONE and not task.completed_at:
        task.completed_at = datetime.utcnow()
    # If status changed from DONE to something else, clear completed_at
    elif task_update.status and task_update.status != TaskStatus.DONE and task.completed_at:
        task.completed_at = None

    await db.commit()
    await db.refresh(task)

    # Load related data for response
    stmt = (
        select(Task)
        .options(selectinload(Task.assignee), selectinload(Task.created_by))
        .where(Task.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()

    # Count comments
    comment_count_stmt = select(func.count(TaskComment.id)).where(TaskComment.task_id == task.id)
    comment_count_result = await db.execute(comment_count_stmt)
    comment_count = comment_count_result.scalar()

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        created_by_id=task.created_by_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_email=task.assignee.email if task.assignee else None,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by_email=task.created_by.email if task.created_by else None,
        created_by_name=task.created_by.full_name if task.created_by else None,
        comment_count=comment_count
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task and all its comments.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    # Delete task (cascade will delete comments)
    await db.delete(task)
    await db.commit()


@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update task status.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    task.status = status_update.status.value

    # Set completed_at if moving to DONE
    if status_update.status == TaskStatus.DONE and not task.completed_at:
        task.completed_at = datetime.utcnow()
    # Clear completed_at if moving from DONE
    elif status_update.status != TaskStatus.DONE and task.completed_at:
        task.completed_at = None

    await db.commit()
    await db.refresh(task)

    # Load related data for response
    stmt = (
        select(Task)
        .options(selectinload(Task.assignee), selectinload(Task.created_by))
        .where(Task.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()

    # Count comments
    comment_count_stmt = select(func.count(TaskComment.id)).where(TaskComment.task_id == task.id)
    comment_count_result = await db.execute(comment_count_stmt)
    comment_count = comment_count_result.scalar()

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        created_by_id=task.created_by_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_email=task.assignee.email if task.assignee else None,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by_email=task.created_by.email if task.created_by else None,
        created_by_name=task.created_by.full_name if task.created_by else None,
        comment_count=comment_count
    )


@router.put("/{task_id}/assignee", response_model=TaskResponse)
async def update_task_assignee(
    task_id: int,
    assignee_update: TaskAssigneeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign or unassign a task.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    # Get project for workspace check
    stmt = select(Project).where(Project.id == task.project_id)
    result = await db.execute(stmt)
    project = result.scalar_one()

    # If assignee_id provided, verify they're a workspace member
    if assignee_update.assignee_id:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == assignee_update.assignee_id
        )
        result = await db.execute(stmt)
        assignee_membership = result.scalar_one_or_none()

        if not assignee_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a workspace member"
            )

    task.assignee_id = assignee_update.assignee_id
    await db.commit()
    await db.refresh(task)

    # Load related data for response
    stmt = (
        select(Task)
        .options(selectinload(Task.assignee), selectinload(Task.created_by))
        .where(Task.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()

    # Count comments
    comment_count_stmt = select(func.count(TaskComment.id)).where(TaskComment.task_id == task.id)
    comment_count_result = await db.execute(comment_count_stmt)
    comment_count = comment_count_result.scalar()

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        created_by_id=task.created_by_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_email=task.assignee.email if task.assignee else None,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_by_email=task.created_by.email if task.created_by else None,
        created_by_name=task.created_by.full_name if task.created_by else None,
        comment_count=comment_count
    )


# ============================================
# Task Comment Endpoints
# ============================================
@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_task_comment(
    task_id: int,
    comment_data: TaskCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to a task.
    User must have access to the project.
    """
    task = await get_task_with_access_check(task_id, current_user, db)

    # Create comment
    new_comment = TaskComment(
        task_id=task_id,
        author_id=current_user.id,
        content=comment_data.content
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    # Load author data
    stmt = (
        select(TaskComment)
        .options(selectinload(TaskComment.author))
        .where(TaskComment.id == new_comment.id)
    )
    result = await db.execute(stmt)
    comment = result.scalar_one()

    return TaskCommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        author_id=comment.author_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author_email=comment.author.email if comment.author else None,
        author_name=comment.author.full_name if comment.author else None,
        author_avatar_url=comment.author.avatar_url if comment.author else None,
    )


@router.put("/{task_id}/comments/{comment_id}", response_model=TaskCommentResponse)
async def update_task_comment(
    task_id: int,
    comment_id: int,
    comment_update: TaskCommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a task comment.
    User must be the comment author.
    """
    # Check task access
    await get_task_with_access_check(task_id, current_user, db)

    # Get comment
    stmt = select(TaskComment).where(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id
    )
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check if user is the author
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )

    # Update comment
    comment.content = comment_update.content
    await db.commit()
    await db.refresh(comment)

    # Load author data
    stmt = (
        select(TaskComment)
        .options(selectinload(TaskComment.author))
        .where(TaskComment.id == comment_id)
    )
    result = await db.execute(stmt)
    comment = result.scalar_one()

    return TaskCommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        author_id=comment.author_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author_email=comment.author.email if comment.author else None,
        author_name=comment.author.full_name if comment.author else None,
        author_avatar_url=comment.author.avatar_url if comment.author else None,
    )


@router.delete("/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_comment(
    task_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task comment.
    User must be the comment author.
    """
    # Check task access
    await get_task_with_access_check(task_id, current_user, db)

    # Get comment
    stmt = select(TaskComment).where(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id
    )
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check if user is the author
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    # Delete comment
    await db.delete(comment)
    await db.commit()
