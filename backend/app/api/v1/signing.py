"""
Document Signing API
Public endpoints for signers to view and sign documents using access tokens
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    SignatureRequest,
    Signer,
    SignatureField,
    Signature,
    SignatureStatus,
    SignerStatus,
    SignatureType,
)
from app.schemas.signature import (
    SignatureAccessResponse,
    SignatureRequestDetailResponse,
    SignDocumentRequest,
    DeclineRequest,
    SignerResponse,
)
from app.services import storage_service

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def get_signer_by_token(access_token: str, db: AsyncSession) -> Signer:
    """Get signer by access token"""
    stmt = select(Signer).where(Signer.access_token == access_token)
    result = await db.execute(stmt)
    signer = result.scalar_one_or_none()

    if not signer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid access token"
        )

    # Check if token has expired
    if signer.access_expires_at and signer.access_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access token has expired"
        )

    # Check if signer has already signed or declined
    if signer.status in [SignerStatus.SIGNED, SignerStatus.DECLINED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have already {signer.status.value} this document"
        )

    return signer


async def log_signing_audit(
    db: AsyncSession,
    request_id: int,
    signer_id: int,
    action: str,
    description: str,
    ip_address: str = None,
    user_agent: str = None
):
    """Log audit entry for signing activities"""
    from app.db.models import SignatureAuditLog

    audit_log = SignatureAuditLog(
        signature_request_id=request_id,
        signer_id=signer_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    await db.flush()


# ============================================
# Public Signing Endpoints
# ============================================
@router.get("/access/{access_token}", response_model=SignatureAccessResponse)
async def get_signing_access(
    access_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get signature request details using access token.
    This is a public endpoint for external signers.
    """
    signer = await get_signer_by_token(access_token, db)

    # Load signature request with document
    stmt = select(SignatureRequest).options(
        selectinload(SignatureRequest.document)
    ).where(SignatureRequest.id == signer.signature_request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    # Update viewed status if first time viewing
    if signer.status == SignerStatus.NOTIFIED:
        signer.status = SignerStatus.VIEWED
        signer.viewed_at = datetime.utcnow()
        signer.ip_address = request.client.host if request.client else None

        # Log audit
        await log_signing_audit(
            db,
            sig_request.id,
            signer.id,
            "viewed",
            f"Document viewed by {signer.email}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        await db.commit()

    return SignatureAccessResponse(
        signature_request_id=sig_request.id,
        signer_id=signer.id,
        access_token=access_token,
        signer_email=signer.email,
        signer_name=signer.full_name,
        document_name=sig_request.document.name if sig_request.document else "Unknown",
        expires_at=sig_request.expires_at,
    )


@router.get("/request/{access_token}", response_model=SignatureRequestDetailResponse)
async def get_signature_request_by_token(
    access_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full signature request details for signing.
    Returns fields that need to be signed by this signer.
    """
    signer = await get_signer_by_token(access_token, db)

    # Load signature request with all details
    stmt = select(SignatureRequest).options(
        selectinload(SignatureRequest.document),
        selectinload(SignatureRequest.created_by),
        selectinload(SignatureRequest.signers),
        selectinload(SignatureRequest.fields)
    ).where(SignatureRequest.id == signer.signature_request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    # Filter fields to only show fields for this signer
    signer_fields = [f for f in sig_request.fields if f.signer_id == signer.id]

    # Build response
    from app.api.v1.signatures import build_signature_request_response
    response = await build_signature_request_response(sig_request, db, include_details=True)

    # Override fields to only show signer's fields
    response.fields = signer_fields

    return response


@router.post("/sign/{access_token}", response_model=SignerResponse)
async def sign_document(
    access_token: str,
    sign_data: SignDocumentRequest,
    request: Request,
    user_agent: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Sign a document by providing signatures for all required fields.
    This endpoint finalizes the signer's part of the signing process.
    """
    signer = await get_signer_by_token(access_token, db)

    # Load signature request
    stmt = select(SignatureRequest).where(SignatureRequest.id == signer.signature_request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    # Check if request has expired
    if sig_request.expires_at and sig_request.expires_at < datetime.utcnow():
        sig_request.status = SignatureStatus.EXPIRED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This signature request has expired"
        )

    # Load signer's fields
    fields_stmt = select(SignatureField).where(
        and_(
            SignatureField.signature_request_id == signer.signature_request_id,
            SignatureField.signer_id == signer.id
        )
    )
    fields_result = await db.execute(fields_stmt)
    signer_fields = fields_result.scalars().all()

    # Check if all required fields are being signed
    required_field_ids = {f.id for f in signer_fields if f.is_required}
    provided_field_ids = {sig.field_id for sig in sign_data.signatures}

    if not required_field_ids.issubset(provided_field_ids):
        missing = required_field_ids - provided_field_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing signatures for required fields: {missing}"
        )

    # Create signatures
    ip_address = request.client.host if request.client else None

    for signature_data in sign_data.signatures:
        # Verify field belongs to this signer
        field = next((f for f in signer_fields if f.id == signature_data.field_id), None)
        if not field:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Field {signature_data.field_id} does not belong to this signer"
            )

        # Handle signature data based on type
        storage_path = None
        if signature_data.signature_type == SignatureType.DRAWN and signature_data.signature_data:
            # For drawn signatures, we could optionally store in S3
            # For now, we'll keep it in the database as base64
            pass
        elif signature_data.signature_type == SignatureType.UPLOADED and signature_data.signature_data:
            # Could upload to S3 here
            pass

        new_signature = Signature(
            signer_id=signer.id,
            field_id=signature_data.field_id,
            signature_type=signature_data.signature_type,
            signature_data=signature_data.signature_data,
            storage_path=storage_path,
            typed_text=signature_data.typed_text,
            font_family=signature_data.font_family,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(new_signature)

    # Update signer status
    signer.status = SignerStatus.SIGNED
    signer.signed_at = datetime.utcnow()
    signer.ip_address = ip_address

    # Check if signature request should be marked as completed
    # Load all signers
    all_signers_stmt = select(Signer).where(Signer.signature_request_id == signer.signature_request_id)
    all_signers_result = await db.execute(all_signers_stmt)
    all_signers = all_signers_result.scalars().all()

    signed_count = sum(1 for s in all_signers if s.status == SignerStatus.SIGNED)
    total_signers = len(all_signers)

    # Update signature request status
    if sig_request.status == SignatureStatus.PENDING:
        sig_request.status = SignatureStatus.IN_PROGRESS

    if sig_request.require_all_signers:
        if signed_count == total_signers:
            sig_request.status = SignatureStatus.COMPLETED
            sig_request.completed_at = datetime.utcnow()
    else:
        # If not requiring all signers, mark as completed when at least one signs
        if signed_count > 0:
            sig_request.status = SignatureStatus.COMPLETED
            sig_request.completed_at = datetime.utcnow()

    # Log audit
    await log_signing_audit(
        db,
        sig_request.id,
        signer.id,
        "signed",
        f"Document signed by {signer.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )

    await db.commit()

    # Refresh signer to get updated data
    await db.refresh(signer)

    return SignerResponse.model_validate(signer)


@router.post("/decline/{access_token}", response_model=SignerResponse)
async def decline_to_sign(
    access_token: str,
    decline_data: DeclineRequest,
    request: Request,
    user_agent: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Decline to sign a document.
    Signer must provide a reason if allowed by the signature request.
    """
    signer = await get_signer_by_token(access_token, db)

    # Load signature request
    stmt = select(SignatureRequest).where(SignatureRequest.id == signer.signature_request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    # Check if decline is allowed
    if not sig_request.allow_decline:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Declining is not allowed for this signature request"
        )

    # Update signer status
    signer.status = SignerStatus.DECLINED
    signer.declined_at = datetime.utcnow()
    signer.decline_reason = decline_data.reason
    signer.ip_address = request.client.host if request.client else None

    # Log audit
    await log_signing_audit(
        db,
        sig_request.id,
        signer.id,
        "declined",
        f"Document declined by {signer.email}: {decline_data.reason or 'No reason provided'}",
        ip_address=request.client.host if request.client else None,
        user_agent=user_agent
    )

    await db.commit()

    # Refresh signer
    await db.refresh(signer)

    return SignerResponse.model_validate(signer)


@router.get("/download-document/{access_token}")
async def download_document_for_signing(
    access_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download the document for review before signing.
    Returns the original document without signatures.
    """
    signer = await get_signer_by_token(access_token, db)

    # Load signature request with document
    stmt = select(SignatureRequest).options(
        selectinload(SignatureRequest.document)
    ).where(SignatureRequest.id == signer.signature_request_id)
    result = await db.execute(stmt)
    sig_request = result.scalar_one()

    document = sig_request.document

    # Download from storage
    file_data = await storage_service.download_file(document.storage_path)

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )

    from fastapi.responses import StreamingResponse
    import io

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.name}"'
        }
    )
