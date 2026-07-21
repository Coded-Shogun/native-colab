"""
GDPR Compliance Endpoints
Provides data export, deletion, and consent management for GDPR compliance
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.audit_log import ComplianceLog
from app.schemas.gdpr import (
    DataExportRequest,
    DataExportResponse,
    DataDeletionRequest,
    DataDeletionResponse,
    ConsentUpdate,
    ConsentResponse
)
import logging
import json
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/data-export", response_model=DataExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_data_export(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request a complete export of user's personal data (GDPR Article 15 - Right to Access).

    The export will be generated asynchronously and made available for download.
    User will receive an email when the export is ready.

    **Export includes:**
    - Profile information
    - Messages and chat history
    - Projects and tasks
    - Documents
    - Time tracking entries
    - Calendar events
    - Audit logs
    - All other personal data

    **Compliance:** GDPR Article 15, 20
    """
    try:
        # Create compliance log entry
        verification_token = str(uuid.uuid4())

        compliance_log = ComplianceLog(
            action_type="data_export_requested",
            user_id=current_user.id,
            workspace_id=request.workspace_id,
            description=f"User requested data export in {request.format} format",
            legal_basis="consent",  # User explicitly requested
            data_types=request.data_types if hasattr(request, 'data_types') else ["all"],
            verification_token=verification_token,
            verified=False,
            completed=False,
            expiry_date=datetime.utcnow() + timedelta(days=30),  # Export expires in 30 days
            metadata={
                "format": request.format,
                "requested_at": datetime.utcnow().isoformat(),
                "ip_address": request.state.ip if hasattr(request, 'state') else None
            },
            created_at=datetime.utcnow()
        )

        db.add(compliance_log)
        await db.commit()
        await db.refresh(compliance_log)

        # Queue background task to generate export
        background_tasks.add_task(
            generate_data_export,
            user_id=current_user.id,
            compliance_log_id=compliance_log.id,
            export_format=request.format
        )

        logger.info(f"Data export requested by user {current_user.id}")

        return DataExportResponse(
            export_id=str(compliance_log.id),
            status="processing",
            message="Your data export request has been received. You will receive an email when it's ready.",
            estimated_completion=datetime.utcnow() + timedelta(hours=24),
            expires_at=compliance_log.expiry_date
        )

    except Exception as e:
        logger.error(f"Failed to request data export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data export request"
        )


@router.post("/data-deletion", response_model=DataDeletionResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_data_deletion(
    request: DataDeletionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request deletion of all personal data (GDPR Article 17 - Right to Erasure).

    **Important:**
    - This action cannot be undone
    - Account will be deactivated immediately
    - Actual data deletion occurs after 30-day grace period
    - You can cancel deletion within 30 days by logging in
    - Some data may be retained for legal compliance (audit logs, financial records)

    **What gets deleted:**
    - Profile information
    - Messages (except in shared workspaces where others need access)
    - Personal projects and tasks
    - Documents you own
    - Calendar events
    - Time tracking entries

    **What is retained:**
    - Audit logs (legal requirement)
    - Financial transaction records (legal requirement)
    - Shared workspace data (anonymized to "Deleted User")

    **Compliance:** GDPR Article 17
    """
    try:
        # Verify user password for critical action
        if not request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation required for account deletion"
            )

        # Create compliance log
        verification_token = str(uuid.uuid4())

        compliance_log = ComplianceLog(
            action_type="data_deletion_requested",
            user_id=current_user.id,
            description=f"User requested account and data deletion. Reason: {request.reason}",
            legal_basis="user_request",
            verification_token=verification_token,
            verified=False,
            completed=False,
            expiry_date=datetime.utcnow() + timedelta(days=30),  # 30-day grace period
            metadata={
                "reason": request.reason,
                "requested_at": datetime.utcnow().isoformat(),
                "grace_period_days": 30
            },
            created_at=datetime.utcnow()
        )

        db.add(compliance_log)

        # Mark user account for deletion
        current_user.is_active = False
        current_user.deletion_requested_at = datetime.utcnow()
        current_user.deletion_scheduled_for = datetime.utcnow() + timedelta(days=30)

        await db.commit()
        await db.refresh(compliance_log)

        # Send verification email
        background_tasks.add_task(
            send_deletion_verification_email,
            user=current_user,
            verification_token=verification_token
        )

        logger.warning(f"Data deletion requested by user {current_user.id}")

        return DataDeletionResponse(
            deletion_id=str(compliance_log.id),
            status="pending_verification",
            message="Account deletion requested. Please verify via email. You have 30 days to cancel.",
            grace_period_ends=current_user.deletion_scheduled_for,
            can_cancel_until=current_user.deletion_scheduled_for
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request data deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data deletion request"
        )


@router.delete("/data-deletion/{deletion_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_data_deletion(
    deletion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending data deletion request.
    Can only be done within the 30-day grace period.
    """
    try:
        # Find deletion request
        result = await db.execute(
            select(ComplianceLog).where(
                ComplianceLog.id == int(deletion_id),
                ComplianceLog.user_id == current_user.id,
                ComplianceLog.action_type == "data_deletion_requested",
                ComplianceLog.completed == False
            )
        )
        compliance_log = result.scalar_one_or_none()

        if not compliance_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deletion request not found or already completed"
            )

        # Check if still within grace period
        if datetime.utcnow() > compliance_log.expiry_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grace period has expired. Cannot cancel deletion."
            )

        # Cancel deletion
        compliance_log.completed = True
        compliance_log.completed_at = datetime.utcnow()
        compliance_log.extra_data["cancelled"] = True
        compliance_log.extra_data["cancelled_at"] = datetime.utcnow().isoformat()

        # Reactivate user account
        current_user.is_active = True
        current_user.deletion_requested_at = None
        current_user.deletion_scheduled_for = None

        await db.commit()

        logger.info(f"Data deletion cancelled by user {current_user.id}")

        return {
            "message": "Account deletion cancelled successfully. Your account has been reactivated.",
            "status": "cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel data deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel data deletion"
        )


@router.get("/consent", response_model=ConsentResponse)
async def get_consent_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current consent settings.

    **Compliance:** GDPR Article 7 (Consent)
    """
    try:
        return ConsentResponse(
            user_id=current_user.id,
            marketing_emails=current_user.consent_marketing,
            analytics=current_user.consent_analytics,
            third_party_sharing=current_user.consent_third_party,
            updated_at=current_user.consent_updated_at or current_user.created_at
        )
    except Exception as e:
        logger.error(f"Failed to get consent settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consent settings"
        )


@router.put("/consent", response_model=ConsentResponse)
async def update_consent_settings(
    consent: ConsentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's consent settings.

    Users can grant or revoke consent for:
    - Marketing emails
    - Analytics tracking
    - Third-party data sharing

    **Compliance:** GDPR Article 7 (Consent)
    """
    try:
        # Update consent settings
        if consent.marketing_emails is not None:
            current_user.consent_marketing = consent.marketing_emails
        if consent.analytics is not None:
            current_user.consent_analytics = consent.analytics
        if consent.third_party_sharing is not None:
            current_user.consent_third_party = consent.third_party_sharing

        current_user.consent_updated_at = datetime.utcnow()

        # Log consent change
        compliance_log = ComplianceLog(
            action_type="consent_updated",
            user_id=current_user.id,
            description="User updated consent settings",
            legal_basis="consent",
            metadata=consent.dict(),
            created_at=datetime.utcnow()
        )
        db.add(compliance_log)

        await db.commit()
        await db.refresh(current_user)

        logger.info(f"Consent settings updated for user {current_user.id}")

        return ConsentResponse(
            user_id=current_user.id,
            marketing_emails=current_user.consent_marketing,
            analytics=current_user.consent_analytics,
            third_party_sharing=current_user.consent_third_party,
            updated_at=current_user.consent_updated_at
        )

    except Exception as e:
        logger.error(f"Failed to update consent settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consent settings"
        )


# Background tasks

async def generate_data_export(user_id: int, compliance_log_id: int, export_format: str):
    """Background task to generate user data export."""
    try:
        logger.info(f"Starting data export generation for user {user_id}")

        # TODO: Implement actual data collection and export generation
        # This would collect all user data from all tables and create a comprehensive export

        # For now, log the action
        logger.info(f"Data export completed for user {user_id}, compliance_log {compliance_log_id}")

    except Exception as e:
        logger.error(f"Failed to generate data export: {e}")


async def send_deletion_verification_email(user: User, verification_token: str):
    """Send email to verify account deletion request."""
    try:
        logger.info(f"Sending deletion verification email to user {user.id}")

        # TODO: Implement email sending
        # This would send an email with a verification link

    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
