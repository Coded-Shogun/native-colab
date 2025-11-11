"""
Digital Signatures API
Endpoints for signature request management and document signing
"""

from typing import Optional
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    WorkspaceMember,
    Document,
    SignatureRequest,
    Signer,
    SignatureField,
    Signature,
    SignatureAuditLog,
    SignatureStatus,
    SignerStatus,
    NotificationType,
    NotificationPriority,
)
from app.schemas.signature import (
    SignatureRequestCreate,
    SignatureRequestUpdate,
    SignatureRequestResponse,
    SignatureRequestDetailResponse,
    SignatureRequestListResponse,
    SignDocumentRequest,
    DeclineRequest,
    SignatureAccessResponse,
    AuditLogResponse,
    AuditLogListResponse,
    SignatureStats,
    SignerResponse,
)
from app.core.deps import get_current_user
from app.services import notification_service
from app.core.config import settings

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(workspace_id: int, user: User, db: AsyncSession) -> bool:
    """Check if user has access to workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_signature_request_access(
    request_id: int,
    user: User,
    db: AsyncSession
) -> Optional[SignatureRequest]:
    """Check if user has access to signature request via workspace membership"""
    stmt = select(SignatureRequest).where(SignatureRequest.id == request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one_or_none()

    if not sig_request:
        return None

    # Check workspace access
    has_access = await check_workspace_access(sig_request.workspace_id, user, db)
    if not has_access:
        return None

    return sig_request


async def build_signature_request_response(
    sig_request: SignatureRequest,
    db: AsyncSession,
    include_details: bool = False
) -> SignatureRequestResponse:
    """Build signature request response with nested information"""
    # Load relationships
    stmt = select(SignatureRequest).options(
        selectinload(SignatureRequest.created_by),
        selectinload(SignatureRequest.document),
        selectinload(SignatureRequest.signers)
    ).where(SignatureRequest.id == sig_request.id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    # Count signer statuses
    signed_count = sum(1 for s in sig_request.signers if s.status == SignerStatus.SIGNED)
    pending_count = sum(1 for s in sig_request.signers if s.status in [SignerStatus.PENDING, SignerStatus.NOTIFIED, SignerStatus.VIEWED])

    base_response = SignatureRequestResponse(
        id=sig_request.id,
        workspace_id=sig_request.workspace_id,
        document_id=sig_request.document_id,
        created_by_id=sig_request.created_by_id,
        title=sig_request.title,
        message=sig_request.message,
        status=sig_request.status,
        signing_order=sig_request.signing_order,
        signed_document_id=sig_request.signed_document_id,
        expires_at=sig_request.expires_at,
        completed_at=sig_request.completed_at,
        require_all_signers=sig_request.require_all_signers,
        allow_decline=sig_request.allow_decline,
        send_reminders=sig_request.send_reminders,
        created_at=sig_request.created_at,
        updated_at=sig_request.updated_at,
        document_name=sig_request.document.name if sig_request.document else None,
        creator_name=sig_request.created_by.full_name if sig_request.created_by else None,
        creator_email=sig_request.created_by.email if sig_request.created_by else None,
        total_signers=len(sig_request.signers),
        signed_count=signed_count,
        pending_count=pending_count,
    )

    if include_details:
        # Load fields as well
        stmt = select(SignatureRequest).options(
            selectinload(SignatureRequest.signers),
            selectinload(SignatureRequest.fields)
        ).where(SignatureRequest.id == sig_request.id)
        result = await db.execute(stmt)
        sig_request = result.scalar_one()

        return SignatureRequestDetailResponse(
            **base_response.model_dump(),
            signers=[SignerResponse.model_validate(s) for s in sig_request.signers],
            fields=[f for f in sig_request.fields],
        )

    return base_response


async def log_audit(
    db: AsyncSession,
    request_id: int,
    action: str,
    description: str,
    user_id: Optional[int] = None,
    signer_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log an audit entry"""
    audit_log = SignatureAuditLog(
        signature_request_id=request_id,
        user_id=user_id,
        signer_id=signer_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {},
    )
    db.add(audit_log)
    await db.flush()


# ============================================
# Signature Request CRUD Endpoints
# ============================================
@router.post("/", response_model=SignatureRequestDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_signature_request(
    request_data: SignatureRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new signature request.
    Document must exist and user must have workspace access.
    """
    # Get document and verify access
    doc_stmt = select(Document).where(Document.id == request_data.document_id)
    doc_result = await db.execute(doc_stmt)
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check workspace access
    has_access = await check_workspace_access(document.workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Create signature request
    new_request = SignatureRequest(
        workspace_id=document.workspace_id,
        document_id=request_data.document_id,
        created_by_id=current_user.id,
        title=request_data.title,
        message=request_data.message,
        status=SignatureStatus.DRAFT,
        signing_order=request_data.signing_order,
        expires_at=request_data.expires_at,
        require_all_signers=request_data.require_all_signers,
        allow_decline=request_data.allow_decline,
        send_reminders=request_data.send_reminders,
    )

    db.add(new_request)
    await db.flush()

    # Create signers
    signer_map = {}  # Map email to signer object
    for idx, signer_data in enumerate(request_data.signers):
        # Check if email belongs to a user in the workspace
        user_stmt = select(User).where(User.email == signer_data.email)
        user_result = await db.execute(user_stmt)
        signer_user = user_result.scalar_one_or_none()

        new_signer = Signer(
            signature_request_id=new_request.id,
            user_id=signer_user.id if signer_user else None,
            email=signer_data.email,
            full_name=signer_data.full_name,
            role=signer_data.role,
            signing_order=signer_data.signing_order,
            status=SignerStatus.PENDING,
        )
        db.add(new_signer)
        await db.flush()
        signer_map[signer_data.email] = new_signer

    # Create signature fields
    for field_data in request_data.fields:
        signer = signer_map.get(field_data.signer_email)
        if not signer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signer with email {field_data.signer_email} not found in signers list"
            )

        new_field = SignatureField(
            signature_request_id=new_request.id,
            signer_id=signer.id,
            field_type=field_data.field_type,
            label=field_data.label,
            is_required=field_data.is_required,
            page_number=field_data.page_number,
            x_position=field_data.x_position,
            y_position=field_data.y_position,
            width=field_data.width,
            height=field_data.height,
            placeholder=field_data.placeholder,
            default_value=field_data.default_value,
        )
        db.add(new_field)

    await db.commit()

    # Log audit
    await log_audit(
        db,
        new_request.id,
        "created",
        f"Signature request created by {current_user.email}",
        user_id=current_user.id
    )
    await db.commit()

    return await build_signature_request_response(new_request, db, include_details=True)


@router.get("/", response_model=SignatureRequestListResponse)
async def list_signature_requests(
    workspace_id: int = Query(..., gt=0),
    status_filter: Optional[SignatureStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List signature requests in a workspace"""
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Build query
    conditions = [SignatureRequest.workspace_id == workspace_id]

    if status_filter:
        conditions.append(SignatureRequest.status == status_filter)

    stmt = select(SignatureRequest).where(and_(*conditions))
    stmt = stmt.order_by(desc(SignatureRequest.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    requests = result.scalars().all()

    # Build responses
    request_responses = []
    for req in requests:
        request_responses.append(await build_signature_request_response(req, db))

    return SignatureRequestListResponse(
        requests=request_responses,
        total=total
    )


@router.get("/{request_id}", response_model=SignatureRequestDetailResponse)
async def get_signature_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get signature request details"""
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    return await build_signature_request_response(sig_request, db, include_details=True)


@router.put("/{request_id}", response_model=SignatureRequestDetailResponse)
async def update_signature_request(
    request_id: int,
    request_update: SignatureRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update signature request (only allowed in draft status)"""
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    if sig_request.status != SignatureStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update signature requests in draft status"
        )

    # Update fields
    update_data = request_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sig_request, field, value)

    await db.commit()

    # Log audit
    await log_audit(
        db,
        request_id,
        "updated",
        f"Signature request updated by {current_user.email}",
        user_id=current_user.id
    )
    await db.commit()

    return await build_signature_request_response(sig_request, db, include_details=True)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signature_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete signature request (only allowed in draft status)"""
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    if sig_request.status != SignatureStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete signature requests in draft status"
        )

    await db.delete(sig_request)
    await db.commit()


# ============================================
# Signature Request Actions
# ============================================
@router.post("/{request_id}/send", response_model=SignatureRequestDetailResponse)
async def send_signature_request(
    request_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send signature request to all signers.
    Changes status from DRAFT to PENDING and sends notifications.
    """
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    if sig_request.status != SignatureStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature request has already been sent"
        )

    # Update status
    sig_request.status = SignatureStatus.PENDING

    # Load signers
    signers_stmt = select(Signer).where(Signer.signature_request_id == request_id)
    signers_result = await db.execute(signers_stmt)
    signers = signers_result.scalars().all()

    # Generate access tokens and send notifications
    for signer in signers:
        # Generate unique access token
        access_token = secrets.token_urlsafe(32)
        signer.access_token = access_token
        signer.access_expires_at = datetime.utcnow() + timedelta(days=30)
        signer.status = SignerStatus.NOTIFIED
        signer.notified_at = datetime.utcnow()

        # Send notification
        try:
            signing_url = f"{settings.FRONTEND_URL}/sign/{access_token}"

            await notification_service.create_notification(
                db=db,
                user_id=signer.user_id if signer.user_id else None,
                notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,  # Could add specific type
                title=f"Signature Request: {sig_request.title}",
                message=f"You have been requested to sign a document by {current_user.full_name or current_user.email}",
                priority=NotificationPriority.HIGH,
                action_url=signing_url,
                metadata={
                    "signature_request_id": request_id,
                    "signer_email": signer.email,
                    "expires_at": sig_request.expires_at.isoformat() if sig_request.expires_at else None,
                },
                send_immediately=True
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send signature notification: {e}")

    await db.commit()

    # Log audit
    await log_audit(
        db,
        request_id,
        "sent",
        f"Signature request sent to {len(signers)} signers by {current_user.email}",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    await db.commit()

    return await build_signature_request_response(sig_request, db, include_details=True)


@router.post("/{request_id}/cancel", response_model=SignatureRequestDetailResponse)
async def cancel_signature_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel signature request"""
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    if sig_request.status in [SignatureStatus.COMPLETED, SignatureStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or already cancelled requests"
        )

    sig_request.status = SignatureStatus.CANCELLED
    await db.commit()

    # Log audit
    await log_audit(
        db,
        request_id,
        "cancelled",
        f"Signature request cancelled by {current_user.email}",
        user_id=current_user.id
    )
    await db.commit()

    return await build_signature_request_response(sig_request, db, include_details=True)


# ============================================
# Audit Log Endpoints
# ============================================
@router.get("/{request_id}/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    request_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for a signature request"""
    sig_request = await check_signature_request_access(request_id, current_user, db)

    if not sig_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature request not found or you don't have access"
        )

    # Get audit logs
    stmt = select(SignatureAuditLog).options(
        selectinload(SignatureAuditLog.user),
        selectinload(SignatureAuditLog.signer)
    ).where(
        SignatureAuditLog.signature_request_id == request_id
    ).order_by(desc(SignatureAuditLog.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    log_responses = []
    for log in logs:
        log_responses.append(AuditLogResponse(
            id=log.id,
            signature_request_id=log.signature_request_id,
            user_id=log.user_id,
            signer_id=log.signer_id,
            action=log.action,
            description=log.description,
            ip_address=log.ip_address,
            created_at=log.created_at,
            user_name=log.user.full_name if log.user else None,
            signer_name=log.signer.full_name if log.signer else None,
        ))

    return AuditLogListResponse(
        logs=log_responses,
        total=total
    )


# ============================================
# Statistics Endpoint
# ============================================
@router.get("/workspace/{workspace_id}/stats", response_model=SignatureStats)
async def get_signature_stats(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get signature statistics for a workspace"""
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Total requests
    total_stmt = select(func.count(SignatureRequest.id)).where(
        SignatureRequest.workspace_id == workspace_id
    )
    total_result = await db.execute(total_stmt)
    total_requests = total_result.scalar() or 0

    # By status
    status_stmt = select(
        SignatureRequest.status,
        func.count(SignatureRequest.id)
    ).where(
        SignatureRequest.workspace_id == workspace_id
    ).group_by(SignatureRequest.status)
    status_result = await db.execute(status_stmt)
    requests_by_status = {str(row[0]): row[1] for row in status_result.fetchall()}

    pending_requests = requests_by_status.get(SignatureStatus.PENDING, 0) + requests_by_status.get(SignatureStatus.IN_PROGRESS, 0)
    completed_requests = requests_by_status.get(SignatureStatus.COMPLETED, 0)
    expired_requests = requests_by_status.get(SignatureStatus.EXPIRED, 0)

    # Average completion time
    completion_stmt = select(
        func.avg(
            func.extract('epoch', SignatureRequest.completed_at - SignatureRequest.created_at) / 3600
        )
    ).where(
        and_(
            SignatureRequest.workspace_id == workspace_id,
            SignatureRequest.status == SignatureStatus.COMPLETED,
            SignatureRequest.completed_at.isnot(None)
        )
    )
    completion_result = await db.execute(completion_stmt)
    avg_completion_time = completion_result.scalar()

    return SignatureStats(
        total_requests=total_requests,
        pending_requests=pending_requests,
        completed_requests=completed_requests,
        expired_requests=expired_requests,
        average_completion_time=float(avg_completion_time) if avg_completion_time else None,
        requests_by_status=requests_by_status,
    )
