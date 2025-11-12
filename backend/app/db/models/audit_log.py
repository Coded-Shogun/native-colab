"""
Universal Audit Log Models
Provides comprehensive audit trail for compliance (GDPR, SOC 2, ISO 27001)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AuditLog(Base):
    """
    Universal audit log for all system operations.
    Provides immutable record of all data access and modifications for compliance.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Context
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, read, update, delete, login, logout
    resource_type = Column(String(100), nullable=False, index=True)  # user, project, document, message, etc.
    resource_id = Column(String(255), nullable=True, index=True)  # ID of the affected resource

    # Data changes (for update operations)
    old_values = Column(JSON, nullable=True)  # Before change
    new_values = Column(JSON, nullable=True)  # After change

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)  # /api/v1/projects/123
    request_id = Column(String(100), nullable=True, index=True)  # For distributed tracing

    # Security context
    success = Column(Boolean, default=True, nullable=False)  # Did the action succeed?
    failure_reason = Column(Text, nullable=True)  # Why it failed (if applicable)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical

    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Any additional context
    duration_ms = Column(Integer, nullable=True)  # How long the operation took

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_workspace_created', 'workspace_id', 'created_at'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_resource', 'action', 'resource_type'),
        Index('idx_audit_resource_lookup', 'resource_type', 'resource_id'),
        Index('idx_audit_security', 'success', 'risk_level', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by user {self.user_id}>"


class SecurityEvent(Base):
    """
    Security-specific events for threat detection and incident response.
    Separate from general audit logs for focused security monitoring.
    """
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)

    # Event type
    event_type = Column(String(100), nullable=False, index=True)
    # Examples: failed_login, suspicious_activity, brute_force_attempt,
    # unauthorized_access, privilege_escalation, data_breach_attempt

    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)

    # Severity
    severity = Column(String(20), nullable=False, default="medium", index=True)  # low, medium, high, critical

    # Details
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)  # Approximate location from IP

    # Response
    action_taken = Column(String(100), nullable=True)  # blocked, flagged, notified_admin, etc.
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="security_events")
    workspace = relationship("Workspace", back_populates="security_events")
    resolver = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        Index('idx_security_unresolved', 'resolved', 'severity', 'created_at'),
        Index('idx_security_user_events', 'user_id', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} severity={self.severity}>"


class DataAccessLog(Base):
    """
    Logs all data access for sensitive information.
    Required for HIPAA, SOC 2, and other compliance frameworks.
    """
    __tablename__ = "data_access_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who accessed
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)

    # What was accessed
    resource_type = Column(String(100), nullable=False, index=True)  # document, message, user_profile, etc.
    resource_id = Column(String(255), nullable=False, index=True)
    access_type = Column(String(50), nullable=False)  # view, download, export, print, share

    # Data classification
    data_classification = Column(String(50), default="internal")  # public, internal, confidential, restricted

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    purpose = Column(String(500), nullable=True)  # Why was it accessed?

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="data_access_logs")
    workspace = relationship("Workspace", back_populates="data_access_logs")

    __table_args__ = (
        Index('idx_data_access_resource', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_data_access_user', 'user_id', 'access_type', 'created_at'),
        Index('idx_data_access_sensitive', 'data_classification', 'created_at'),
    )

    def __repr__(self):
        return f"<DataAccessLog {self.access_type} {self.resource_type} by user {self.user_id}>"


class ComplianceLog(Base):
    """
    Specific compliance-related logs (data exports, deletions, consent changes).
    Provides auditable trail for GDPR and other regulations.
    """
    __tablename__ = "compliance_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Type of compliance action
    action_type = Column(String(100), nullable=False, index=True)
    # Examples: data_export_requested, data_export_completed, data_deletion_requested,
    # data_deletion_completed, consent_granted, consent_revoked, privacy_policy_accepted

    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)

    # Details
    description = Column(Text, nullable=False)
    legal_basis = Column(String(100), nullable=True)  # consent, contract, legal_obligation, etc.

    # Data scope
    data_types = Column(JSON, nullable=True)  # Which types of data were affected
    record_count = Column(Integer, nullable=True)  # How many records

    # Verification
    verification_token = Column(String(255), nullable=True)  # For email verification
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    # Completion
    completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)  # For exports that expire

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="compliance_logs")
    workspace = relationship("Workspace", back_populates="compliance_logs")

    __table_args__ = (
        Index('idx_compliance_user_action', 'user_id', 'action_type', 'created_at'),
        Index('idx_compliance_pending', 'completed', 'expiry_date'),
    )

    def __repr__(self):
        return f"<ComplianceLog {self.action_type} for user {self.user_id}>"
