"""
Digital Signature Schemas
Pydantic schemas for signature requests, signers, and signing workflows
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

from app.db.models.signature import (
    SignatureStatus,
    SigningOrder,
    SignerStatus,
    SignatureType,
    FieldType,
)


# ============================================
# Signer Schemas
# ============================================
class SignerBase(BaseModel):
    """Base signer schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    signing_order: int = Field(default=0, ge=0)


class SignerCreate(SignerBase):
    """Schema for adding a signer to a signature request"""
    pass


class SignerResponse(BaseModel):
    """Schema for signer response"""
    id: int
    signature_request_id: int
    user_id: Optional[int] = None
    email: str
    full_name: str
    role: Optional[str] = None
    signing_order: int
    status: SignerStatus
    notified_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Signature Field Schemas
# ============================================
class SignatureFieldBase(BaseModel):
    """Base signature field schema"""
    field_type: FieldType = Field(default=FieldType.SIGNATURE)
    label: Optional[str] = Field(None, max_length=255)
    is_required: bool = Field(default=True)
    page_number: int = Field(..., ge=1)
    x_position: float = Field(..., ge=0, le=1)
    y_position: float = Field(..., ge=0, le=1)
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)
    placeholder: Optional[str] = Field(None, max_length=255)
    default_value: Optional[str] = Field(None, max_length=500)


class SignatureFieldCreate(SignatureFieldBase):
    """Schema for creating a signature field"""
    signer_email: EmailStr  # Will be mapped to signer_id


class SignatureFieldResponse(BaseModel):
    """Schema for signature field response"""
    id: int
    signature_request_id: int
    signer_id: int
    field_type: FieldType
    label: Optional[str] = None
    is_required: bool
    page_number: int
    x_position: float
    y_position: float
    width: float
    height: float
    placeholder: Optional[str] = None
    default_value: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Signature Request Schemas
# ============================================
class SignatureRequestBase(BaseModel):
    """Base signature request schema"""
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = Field(None, max_length=2000)
    signing_order: SigningOrder = Field(default=SigningOrder.PARALLEL)
    require_all_signers: bool = Field(default=True)
    allow_decline: bool = Field(default=True)
    send_reminders: bool = Field(default=True)
    expires_at: Optional[datetime] = None


class SignatureRequestCreate(SignatureRequestBase):
    """Schema for creating a signature request"""
    document_id: int = Field(..., gt=0)
    signers: List[SignerCreate] = Field(..., min_length=1)
    fields: List[SignatureFieldCreate] = Field(..., min_length=1)


class SignatureRequestUpdate(BaseModel):
    """Schema for updating a signature request"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, max_length=2000)
    expires_at: Optional[datetime] = None


class SignatureRequestResponse(BaseModel):
    """Schema for signature request response"""
    id: int
    workspace_id: int
    document_id: int
    created_by_id: int
    title: str
    message: Optional[str] = None
    status: SignatureStatus
    signing_order: SigningOrder
    signed_document_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    require_all_signers: bool
    allow_decline: bool
    send_reminders: bool
    created_at: datetime
    updated_at: datetime

    # Nested info
    document_name: Optional[str] = None
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    total_signers: int = 0
    signed_count: int = 0
    pending_count: int = 0

    model_config = {"from_attributes": True}


class SignatureRequestDetailResponse(SignatureRequestResponse):
    """Schema for detailed signature request response with signers and fields"""
    signers: List[SignerResponse] = []
    fields: List[SignatureFieldResponse] = []


class SignatureRequestListResponse(BaseModel):
    """Schema for signature request list response"""
    requests: List[SignatureRequestResponse]
    total: int


# ============================================
# Signing Schemas
# ============================================
class SignatureCreate(BaseModel):
    """Schema for creating a signature"""
    field_id: int = Field(..., gt=0)
    signature_type: SignatureType
    signature_data: Optional[str] = Field(None, max_length=100000)  # Base64 image
    typed_text: Optional[str] = Field(None, max_length=255)
    font_family: Optional[str] = Field(None, max_length=100)


class SignatureResponse(BaseModel):
    """Schema for signature response"""
    id: int
    signer_id: int
    field_id: int
    signature_type: SignatureType
    storage_path: Optional[str] = None
    typed_text: Optional[str] = None
    font_family: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SignDocumentRequest(BaseModel):
    """Schema for signing a document"""
    signatures: List[SignatureCreate] = Field(..., min_length=1)


class DeclineRequest(BaseModel):
    """Schema for declining to sign"""
    reason: Optional[str] = Field(None, max_length=500)


# ============================================
# Audit Log Schemas
# ============================================
class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    signature_request_id: int
    user_id: Optional[int] = None
    signer_id: Optional[int] = None
    action: str
    description: str
    ip_address: Optional[str] = None
    created_at: datetime

    # Nested info
    user_name: Optional[str] = None
    signer_name: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response"""
    logs: List[AuditLogResponse]
    total: int


# ============================================
# Signature Access Schemas
# ============================================
class SignatureAccessResponse(BaseModel):
    """Schema for signature access (for external signers)"""
    signature_request_id: int
    signer_id: int
    access_token: str
    signer_email: str
    signer_name: str
    document_name: str
    expires_at: Optional[datetime] = None


# ============================================
# Signature Statistics
# ============================================
class SignatureStats(BaseModel):
    """Schema for signature statistics"""
    total_requests: int
    pending_requests: int
    completed_requests: int
    expired_requests: int
    average_completion_time: Optional[float] = None  # in hours
    requests_by_status: dict
