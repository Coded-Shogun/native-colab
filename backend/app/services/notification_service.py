"""
Notification Service
Handles creating and sending notifications through multiple channels
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.db.models import (
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    User,
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and sending notifications"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        action_url: Optional[str] = None,
        event_id: Optional[int] = None,
        message_id: Optional[int] = None,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        send_immediately: bool = True
    ) -> Notification:
        """
        Create a notification and optionally send it through enabled channels.

        Args:
            db: Database session
            user_id: ID of the user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            action_url: URL for action button
            event_id: Related event ID
            message_id: Related message ID
            task_id: Related task ID
            project_id: Related project ID
            workspace_id: Related workspace ID
            metadata: Additional metadata
            send_immediately: Whether to send notification immediately

        Returns:
            Notification: Created notification instance
        """
        # Create notification record
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            action_url=action_url,
            event_id=event_id,
            message_id=message_id,
            task_id=task_id,
            project_id=project_id,
            workspace_id=workspace_id,
            metadata=metadata or {},
            is_read=False,
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Send through appropriate channels if requested
        if send_immediately:
            await NotificationService._send_notification(db, notification)

        return notification

    @staticmethod
    async def _send_notification(db: AsyncSession, notification: Notification):
        """
        Send notification through enabled channels based on user preferences.

        Args:
            db: Database session
            notification: Notification to send
        """
        # Get user preferences for this notification type
        pref_stmt = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == notification.user_id,
                NotificationPreference.notification_type == notification.notification_type
            )
        )
        pref_result = await db.execute(pref_stmt)
        preference = pref_result.scalar_one_or_none()

        # Default preferences if not set
        if not preference:
            preference = NotificationPreference(
                user_id=notification.user_id,
                notification_type=notification.notification_type,
                in_app_enabled=True,
                email_enabled=True,
                push_enabled=False,
            )

        # Check quiet hours (if set)
        if preference.quiet_hours_start and preference.quiet_hours_end:
            current_hour = datetime.utcnow().hour
            in_quiet_hours = NotificationService._is_in_quiet_hours(
                current_hour,
                preference.quiet_hours_start,
                preference.quiet_hours_end
            )
            if in_quiet_hours and notification.priority != NotificationPriority.URGENT:
                logger.info(f"Notification {notification.id} deferred due to quiet hours")
                return

        # Send through enabled channels
        # In-app notification (always create, controlled by marking as sent)
        if preference.in_app_enabled:
            notification.sent_in_app = True

        # Email notification
        if preference.email_enabled:
            await NotificationService._send_email_notification(db, notification)

        # Push notification (placeholder for future implementation)
        if preference.push_enabled:
            # TODO: Implement push notifications (FCM, WebPush, etc.)
            notification.sent_push = True
            logger.info(f"Push notification would be sent for notification {notification.id}")

        await db.commit()

    @staticmethod
    async def _send_email_notification(db: AsyncSession, notification: Notification):
        """
        Send email for the notification.

        Args:
            db: Database session
            notification: Notification to send via email
        """
        try:
            # Get user details
            user_stmt = select(User).where(User.id == notification.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user or not user.email:
                logger.warning(f"Cannot send email for notification {notification.id}: user not found or no email")
                return

            # Map notification types to email methods
            email_sent = False

            if notification.notification_type == NotificationType.EVENT_REMINDER:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_event_reminder(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    event_title=notification.title,
                    event_start=metadata.get('event_start', 'N/A'),
                    event_location=metadata.get('event_location'),
                    event_url=notification.action_url
                )

            elif notification.notification_type == NotificationType.EVENT_INVITATION:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_event_invitation(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    organizer_name=metadata.get('organizer_name', 'Someone'),
                    event_title=notification.title,
                    event_start=metadata.get('event_start', 'N/A'),
                    event_end=metadata.get('event_end', 'N/A'),
                    event_location=metadata.get('event_location'),
                    event_description=notification.message,
                    rsvp_url=notification.action_url
                )

            elif notification.notification_type == NotificationType.TASK_ASSIGNED:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_task_assignment(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    assigner_name=metadata.get('assigner_name', 'Someone'),
                    task_title=notification.title,
                    task_description=notification.message,
                    task_due_date=metadata.get('task_due_date'),
                    task_url=notification.action_url
                )

            elif notification.notification_type == NotificationType.DIRECT_MESSAGE:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_direct_message_notification(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    sender_name=metadata.get('sender_name', 'Someone'),
                    message_preview=notification.message,
                    message_url=notification.action_url
                )

            elif notification.notification_type == NotificationType.CHANNEL_MENTION:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_mention_notification(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    mentioner_name=metadata.get('mentioner_name', 'Someone'),
                    channel_name=metadata.get('channel_name', 'channel'),
                    message_preview=notification.message,
                    message_url=notification.action_url
                )

            elif notification.notification_type == NotificationType.WORKSPACE_INVITATION:
                metadata = notification.metadata or {}
                email_sent = await email_service.send_workspace_invitation(
                    recipient_email=user.email,
                    recipient_name=user.full_name or user.email,
                    inviter_name=metadata.get('inviter_name', 'Someone'),
                    workspace_name=metadata.get('workspace_name', 'a workspace'),
                    invitation_url=notification.action_url or ''
                )

            if email_sent:
                notification.sent_email = True
                logger.info(f"Email sent for notification {notification.id}")
            else:
                logger.warning(f"Failed to send email for notification {notification.id}")

        except Exception as e:
            logger.error(f"Error sending email for notification {notification.id}: {str(e)}", exc_info=True)

    @staticmethod
    def _is_in_quiet_hours(current_hour: int, start_hour: int, end_hour: int) -> bool:
        """
        Check if current time is within quiet hours.

        Args:
            current_hour: Current hour (0-23)
            start_hour: Quiet hours start (0-23)
            end_hour: Quiet hours end (0-23)

        Returns:
            bool: True if in quiet hours
        """
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:  # Spans midnight
            return current_hour >= start_hour or current_hour < end_hour

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_ids: List[int],
        user_id: int
    ) -> int:
        """
        Mark notifications as read.

        Args:
            db: Database session
            notification_ids: List of notification IDs to mark as read
            user_id: User ID (for security check)

        Returns:
            int: Number of notifications marked as read
        """
        stmt = select(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1

        await db.commit()
        return count

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: int) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            int: Count of unread notifications
        """
        from sqlalchemy import func

        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await db.execute(stmt)
        count = result.scalar()
        return count or 0


# Export singleton instance
notification_service = NotificationService()
