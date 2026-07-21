"""
Digital Signature Models
Represents signature requests, signers, fields, and audit logs for DocuSign-like functionality
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, Float, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class SignatureStatus(str, Enum):
    """Signature request status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SigningOrder(str, Enum):
    """Signing order enumeration"""
    PARALLEL = "parallel"  # All signers can sign at the same time
    SEQUENTIAL = "sequential"  # Signers must sign in order


class SignerStatus(str, Enum):
    """Signer status enumeration"""
    PENDING = "pending"
    NOTIFIED = "notified"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"


class SignatureType(str, Enum):
    """Signature type enumeration"""
    DRAWN = "drawn"  # Hand-drawn signature
    TYPED = "typed"  # Typed name as signature
    UPLOADED = "uploaded"  # Uploaded signature image
    CERTIFICATE = "certificate"  # Digital certificate


class FieldType(str, Enum):
    """Signature field type enumeration"""
    SIGNATURE = "signature"
    INITIALS = "initials"
    DATE = "date"
    TEXT = "text"
    CHECKBOX = "checkbox"


class SignatureRequest(Base):
    """Signature request model for managing document signing workflows."""
    __tablename__ = "signature_requests"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), nullable=True, index=True)

    # Request details
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(SQLEnum(SignatureStatus), default=SignatureStatus.DRAFT, nullable=False)
    signing_order = Column(SQLEnum(SigningOrder), default=SigningOrder.PARALLEL, nullable=False)

    # Completed document
    signed_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Deadlines
    expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Settings
    require_all_signers = Column(Boolean, default=True, nullable=False)
    allow_decline = Column(Boolean, default=True, nullable=False)
    send_reminders = Column(Boolean, default=True, nullable=False)

    # Metadata
    extra_data = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="signature_requests")
    document = relationship("Document", foreign_keys=[document_id], backref="signature_requests")
    signed_document = relationship("Document", foreign_keys=[signed_document_id], backref="signed_signature_requests")
    created_by = relationship("User", backref="signature_requests_created")
    signers = relationship("Signer", back_populates="signature_request", cascade="all, delete-orphan")
    fields = relationship("SignatureField", back_populates="signature_request", cascade="all, delete-orphan")
    audit_logs = relationship("SignatureAuditLog", back_populates="signature_request", cascade="all, delete-orphan")


class Signer(Base):
    """Signer model representing individuals who need to sign a document."""
    __tablename__ = "signers"

    id = Column(Integer, primary_key=True, index=True)
    signature_request_id = Column(Integer, ForeignKey("signature_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for external signers

    # Signer details
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)  # e.g., "Client", "Contractor", "Manager"

    # Signing order (for sequential signing)
    signing_order = Column(Integer, default=0, nullable=False)

    # Status
    status = Column(SQLEnum(SignerStatus), default=SignerStatus.PENDING, nullable=False)

    # Access control
    access_token = Column(String(255), nullable=True, unique=True)  # Unique token for external access
    access_expires_at = Column(DateTime, nullable=True)

    # Activity tracking
    notified_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    decline_reason = Column(Text, nullable=True)

    # IP address for audit trail
    ip_address = Column(String(45), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    signature_request = relationship("SignatureRequest", back_populates="signers")
    user = relationship("User", backref="signer_records")
    signatures = relationship("Signature", back_populates="signer", cascade="all, delete-orphan")


class SignatureField(Base):
    """Signature field model defining where signatures should be placed in the document."""
    __tablename__ = "signature_fields"

    id = Column(Integer, primary_key=True, index=True)
    signature_request_id = Column(Integer, ForeignKey("signature_requests.id"), nullable=False)
    signer_id = Column(Integer, ForeignKey("signers.id"), nullable=False)

    # Field details
    field_type = Column(SQLEnum(FieldType), default=FieldType.SIGNATURE, nullable=False)
    label = Column(String(255), nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)

    # Position in document (coordinates)
    page_number = Column(Integer, nullable=False)
    x_position = Column(Float, nullable=False)  # X coordinate (0-1, percentage)
    y_position = Column(Float, nullable=False)  # Y coordinate (0-1, percentage)
    width = Column(Float, nullable=False)  # Width (0-1, percentage)
    height = Column(Float, nullable=False)  # Height (0-1, percentage)

    # For text fields
    placeholder = Column(String(255), nullable=True)
    default_value = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    signature_request = relationship("SignatureRequest", back_populates="fields")
    signer = relationship("Signer", backref="fields")


class Signature(Base):
    """Signature model storing the actual signature data."""
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    signer_id = Column(Integer, ForeignKey("signers.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("signature_fields.id"), nullable=False)

    # Signature details
    signature_type = Column(SQLEnum(SignatureType), nullable=False)
    signature_data = Column(Text, nullable=True)  # Base64 encoded image or text
    storage_path = Column(String(500), nullable=True)  # Path to signature image in S3

    # For typed signatures
    typed_text = Column(String(255), nullable=True)
    font_family = Column(String(100), nullable=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    signer = relationship("Signer", back_populates="signatures")
    field = relationship("SignatureField", backref="signatures")


class SignatureAuditLog(Base):
    """Audit log for signature request activities for compliance and legal purposes."""
    __tablename__ = "signature_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    signature_request_id = Column(Integer, ForeignKey("signature_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signer_id = Column(Integer, ForeignKey("signers.id"), nullable=True)

    # Event details
    action = Column(String(100), nullable=False)  # e.g., "created", "sent", "viewed", "signed", "declined"
    description = Column(Text, nullable=False)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    signature_request = relationship("SignatureRequest", back_populates="audit_logs")
    user = relationship("User", backref="signature_audit_logs")
    signer = relationship("Signer", backref="audit_logs")
