"""
Notifications API
Endpoints for managing user notifications and preferences
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationPriority,
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkRead,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationPreferenceListResponse,
    BulkPreferenceUpdate,
    NotificationStats,
)
from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext
from app.services.notification_service import notification_service

router = APIRouter(dependencies=[Depends(get_organization_context)])


# ============================================
# Notification Endpoints
# ============================================
@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    priority: Optional[NotificationPriority] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List notifications for the current user.
    Supports filtering by read status, type, and priority.
    """
    # Build query
    conditions = [Notification.user_id == current_user.id]

    if unread_only:
        conditions.append(Notification.is_read == False)

    if notification_type:
        conditions.append(Notification.notification_type == notification_type)

    if priority:
        conditions.append(Notification.priority == priority)

    stmt = select(Notification).where(and_(*conditions))
    stmt = stmt.order_by(desc(Notification.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Count unread
    unread_count = await notification_service.get_unread_count(db, current_user.id)

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    notifications = result.scalars().all()

    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications"""
    count = await notification_service.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification statistics for the current user"""
    # Total notifications
    total_stmt = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id
    )
    total_result = await db.execute(total_stmt)
    total_notifications = total_result.scalar() or 0

    # Unread notifications
    unread_count = await notification_service.get_unread_count(db, current_user.id)

    # Notifications by type
    type_stmt = select(
        Notification.notification_type,
        func.count(Notification.id)
    ).where(
        Notification.user_id == current_user.id
    ).group_by(Notification.notification_type)
    type_result = await db.execute(type_stmt)
    notifications_by_type = {str(row[0]): row[1] for row in type_result.fetchall()}

    # Notifications by priority
    priority_stmt = select(
        Notification.priority,
        func.count(Notification.id)
    ).where(
        Notification.user_id == current_user.id
    ).group_by(Notification.priority)
    priority_result = await db.execute(priority_stmt)
    notifications_by_priority = {str(row[0]): row[1] for row in priority_result.fetchall()}

    return NotificationStats(
        total_notifications=total_notifications,
        unread_notifications=unread_count,
        notifications_by_type=notifications_by_type,
        notifications_by_priority=notifications_by_priority
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification details"""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return NotificationResponse.model_validate(notification)


@router.post("/mark-read", status_code=status.HTTP_200_OK)
async def mark_notifications_read(
    mark_data: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notifications as read"""
    count = await notification_service.mark_as_read(
        db,
        mark_data.notification_ids,
        current_user.id
    )

    return {"marked_read": count}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    from datetime import datetime

    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    count = 0
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        count += 1

    await db.commit()

    return {"marked_read": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification"""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    await db.delete(notification)
    await db.commit()


# ============================================
# Notification Preference Endpoints
# ============================================
@router.get("/preferences/", response_model=NotificationPreferenceListResponse)
async def list_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all notification preferences for the current user"""
    stmt = select(NotificationPreference).where(
        NotificationPreference.user_id == current_user.id
    )
    result = await db.execute(stmt)
    preferences = result.scalars().all()

    return NotificationPreferenceListResponse(
        preferences=[NotificationPreferenceResponse.model_validate(p) for p in preferences],
        total=len(preferences)
    )


@router.post("/preferences/", response_model=NotificationPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_preference(
    pref_data: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update a notification preference"""
    # Check if preference already exists
    stmt = select(NotificationPreference).where(
        and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.notification_type == pref_data.notification_type
        )
    )
    result = await db.execute(stmt)
    existing_pref = result.scalar_one_or_none()

    if existing_pref:
        # Update existing
        existing_pref.in_app_enabled = pref_data.in_app_enabled
        existing_pref.email_enabled = pref_data.email_enabled
        existing_pref.push_enabled = pref_data.push_enabled
        existing_pref.quiet_hours_start = pref_data.quiet_hours_start
        existing_pref.quiet_hours_end = pref_data.quiet_hours_end

        await db.commit()
        await db.refresh(existing_pref)

        return NotificationPreferenceResponse.model_validate(existing_pref)

    # Create new
    new_pref = NotificationPreference(
        user_id=current_user.id,
        notification_type=pref_data.notification_type,
        in_app_enabled=pref_data.in_app_enabled,
        email_enabled=pref_data.email_enabled,
        push_enabled=pref_data.push_enabled,
        quiet_hours_start=pref_data.quiet_hours_start,
        quiet_hours_end=pref_data.quiet_hours_end,
    )

    db.add(new_pref)
    await db.commit()
    await db.refresh(new_pref)

    return NotificationPreferenceResponse.model_validate(new_pref)


@router.put("/preferences/{notification_type}", response_model=NotificationPreferenceResponse)
async def update_notification_preference(
    notification_type: NotificationType,
    pref_update: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a notification preference"""
    stmt = select(NotificationPreference).where(
        and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.notification_type == notification_type
        )
    )
    result = await db.execute(stmt)
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found"
        )

    # Update fields
    update_data = pref_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)

    await db.commit()
    await db.refresh(preference)

    return NotificationPreferenceResponse.model_validate(preference)


@router.post("/preferences/bulk-update", status_code=status.HTTP_200_OK)
async def bulk_update_preferences(
    bulk_update: BulkPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update notification preferences for multiple notification types.
    Creates preferences if they don't exist.
    """
    updated_count = 0

    for notification_type in bulk_update.notification_types:
        # Check if preference exists
        stmt = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == current_user.id,
                NotificationPreference.notification_type == notification_type
            )
        )
        result = await db.execute(stmt)
        preference = result.scalar_one_or_none()

        if preference:
            # Update existing
            if bulk_update.in_app_enabled is not None:
                preference.in_app_enabled = bulk_update.in_app_enabled
            if bulk_update.email_enabled is not None:
                preference.email_enabled = bulk_update.email_enabled
            if bulk_update.push_enabled is not None:
                preference.push_enabled = bulk_update.push_enabled
            updated_count += 1
        else:
            # Create new
            new_pref = NotificationPreference(
                user_id=current_user.id,
                notification_type=notification_type,
                in_app_enabled=bulk_update.in_app_enabled if bulk_update.in_app_enabled is not None else True,
                email_enabled=bulk_update.email_enabled if bulk_update.email_enabled is not None else True,
                push_enabled=bulk_update.push_enabled if bulk_update.push_enabled is not None else False,
            )
            db.add(new_pref)
            updated_count += 1

    await db.commit()

    return {"updated_count": updated_count}


@router.delete("/preferences/{notification_type}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_preference(
    notification_type: NotificationType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification preference (revert to defaults)"""
    stmt = select(NotificationPreference).where(
        and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.notification_type == notification_type
        )
    )
    result = await db.execute(stmt)
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found"
        )

    await db.delete(preference)
    await db.commit()
