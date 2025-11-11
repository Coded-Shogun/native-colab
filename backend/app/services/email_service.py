"""
Email Service
Handles sending emails using fastapi-mail with Jinja2 templates
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

# Email configuration
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=settings.SMTP_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
)

# Initialize FastMail
fast_mail = FastMail(email_conf)

# Initialize Jinja2 environment for email templates
template_dir = Path(__file__).parent.parent / "templates" / "email"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    async def send_email(
        recipient_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Send an email using a template.

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            template_name: Name of the template file (without .html extension)
            template_data: Data to pass to the template

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not settings.SMTP_ENABLED:
            logger.info(f"SMTP disabled. Would send email to {recipient_email}: {subject}")
            return True

        try:
            # Render template
            template = jinja_env.get_template(f"{template_name}.html")
            html_content = template.render(**template_data)

            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[recipient_email],
                body=html_content,
                subtype=MessageType.html
            )

            # Send email
            await fast_mail.send_message(message)
            logger.info(f"Email sent successfully to {recipient_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    async def send_bulk_email(
        recipients: List[str],
        subject: str,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send the same email to multiple recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            template_name: Name of the template file
            template_data: Data to pass to the template

        Returns:
            dict: Summary of sent/failed emails
        """
        results = {
            "sent": 0,
            "failed": 0,
            "failed_recipients": []
        }

        for recipient in recipients:
            success = await EmailService.send_email(
                recipient_email=recipient,
                subject=subject,
                template_name=template_name,
                template_data=template_data
            )

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["failed_recipients"].append(recipient)

        return results

    @staticmethod
    async def send_event_reminder(
        recipient_email: str,
        recipient_name: str,
        event_title: str,
        event_start: str,
        event_location: str = None,
        event_url: str = None
    ) -> bool:
        """Send event reminder email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"Reminder: {event_title}",
            template_name="event_reminder",
            template_data={
                "recipient_name": recipient_name,
                "event_title": event_title,
                "event_start": event_start,
                "event_location": event_location,
                "event_url": event_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )

    @staticmethod
    async def send_event_invitation(
        recipient_email: str,
        recipient_name: str,
        organizer_name: str,
        event_title: str,
        event_start: str,
        event_end: str,
        event_location: str = None,
        event_description: str = None,
        rsvp_url: str = None
    ) -> bool:
        """Send event invitation email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"Event Invitation: {event_title}",
            template_name="event_invitation",
            template_data={
                "recipient_name": recipient_name,
                "organizer_name": organizer_name,
                "event_title": event_title,
                "event_start": event_start,
                "event_end": event_end,
                "event_location": event_location,
                "event_description": event_description,
                "rsvp_url": rsvp_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )

    @staticmethod
    async def send_task_assignment(
        recipient_email: str,
        recipient_name: str,
        assigner_name: str,
        task_title: str,
        task_description: str = None,
        task_due_date: str = None,
        task_url: str = None
    ) -> bool:
        """Send task assignment email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"Task Assigned: {task_title}",
            template_name="task_assignment",
            template_data={
                "recipient_name": recipient_name,
                "assigner_name": assigner_name,
                "task_title": task_title,
                "task_description": task_description,
                "task_due_date": task_due_date,
                "task_url": task_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )

    @staticmethod
    async def send_direct_message_notification(
        recipient_email: str,
        recipient_name: str,
        sender_name: str,
        message_preview: str,
        message_url: str = None
    ) -> bool:
        """Send direct message notification email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"New message from {sender_name}",
            template_name="direct_message",
            template_data={
                "recipient_name": recipient_name,
                "sender_name": sender_name,
                "message_preview": message_preview,
                "message_url": message_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )

    @staticmethod
    async def send_mention_notification(
        recipient_email: str,
        recipient_name: str,
        mentioner_name: str,
        channel_name: str,
        message_preview: str,
        message_url: str = None
    ) -> bool:
        """Send mention notification email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"{mentioner_name} mentioned you in #{channel_name}",
            template_name="mention_notification",
            template_data={
                "recipient_name": recipient_name,
                "mentioner_name": mentioner_name,
                "channel_name": channel_name,
                "message_preview": message_preview,
                "message_url": message_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )

    @staticmethod
    async def send_workspace_invitation(
        recipient_email: str,
        recipient_name: str,
        inviter_name: str,
        workspace_name: str,
        invitation_url: str
    ) -> bool:
        """Send workspace invitation email"""
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=f"Invitation to join {workspace_name}",
            template_name="workspace_invitation",
            template_data={
                "recipient_name": recipient_name,
                "inviter_name": inviter_name,
                "workspace_name": workspace_name,
                "invitation_url": invitation_url,
                "frontend_url": settings.FRONTEND_URL
            }
        )


# Export singleton instance
email_service = EmailService()
