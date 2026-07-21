"""
Pydantic schemas for GDPR compliance endpoints
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class DataExportRequest(BaseModel):
    """Request for user data export (GDPR Article 15)"""
    format: str = Field("json", description="Export format: json, csv, or pdf")
    include_metadata: bool = Field(True, description="Include metadata in export")
    include_audit_logs: bool = Field(True, description="Include audit logs in export")


class DataExportResponse(BaseModel):
    """Response for data export request"""
    request_id: str = Field(..., description="Unique export request ID")
    status: str = Field(..., description="Status: processing, completed, failed")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "dsar_abc123xyz",
                "status": "processing",
                "estimated_completion": "2025-01-15T11:00:00Z",
                "download_url": None,
                "expires_at": None
            }
        }


class DataDeletionRequest(BaseModel):
    """Request for user data deletion (GDPR Article 17)"""
    reason: str = Field(..., description="Reason for deletion request")
    delete_all: bool = Field(True, description="Delete all data including contributions")
    anonymize_contributions: bool = Field(
        True,
        description="Anonymize contributions instead of deleting (keeps work context)"
    )
    confirm_email: EmailStr = Field(..., description="Email confirmation")


class DataDeletionResponse(BaseModel):
    """Response for data deletion request"""
    deletion_id: str = Field(..., description="Unique deletion request ID")
    status: str = Field(..., description="Status: scheduled, processing, completed, cancelled")
    scheduled_date: datetime = Field(..., description="Scheduled deletion date (after grace period)")
    cancellable_until: datetime = Field(..., description="Can cancel until this date")
    what_will_be_deleted: List[str] = Field(..., description="List of data categories to be deleted")
    what_will_be_retained: List[str] = Field(..., description="List of data to be retained")

    class Config:
        json_schema_extra = {
            "example": {
                "deletion_id": "del_xyz789",
                "status": "scheduled",
                "scheduled_date": "2025-02-14T00:00:00Z",
                "cancellable_until": "2025-02-13T23:59:59Z",
                "what_will_be_deleted": [
                    "User profile",
                    "Personal messages",
                    "Account credentials"
                ],
                "what_will_be_retained": [
                    "Anonymized audit logs",
                    "Financial records",
                    "Work contributions (anonymized)"
                ]
            }
        }


class ConsentUpdate(BaseModel):
    """Update user consent preferences (GDPR Article 7)"""
    consent_marketing: Optional[bool] = Field(None, description="Consent for marketing communications")
    consent_analytics: Optional[bool] = Field(None, description="Consent for analytics tracking")
    consent_third_party: Optional[bool] = Field(None, description="Consent for third-party sharing")
    consent_profiling: Optional[bool] = Field(None, description="Consent for profiling activities")


class ConsentRecord(BaseModel):
    """Individual consent record"""
    type: str = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent is granted")
    granted_at: Optional[datetime] = Field(None, description="When consent was granted")
    withdrawn_at: Optional[datetime] = Field(None, description="When consent was withdrawn")
    method: Optional[str] = Field(None, description="Method of consent collection")
    ip_address: Optional[str] = Field(None, description="IP address when consent given")


class ConsentsResponse(BaseModel):
    """Response with all user consents"""
    user_id: str = Field(..., description="User ID")
    consents: List[ConsentRecord] = Field(..., description="List of consent records")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_abc123",
                "consents": [
                    {
                        "type": "marketing",
                        "granted": True,
                        "granted_at": "2025-01-15T10:30:00Z",
                        "method": "explicit_opt_in",
                        "ip_address": "192.168.1.100"
                    },
                    {
                        "type": "analytics",
                        "granted": False,
                        "withdrawn_at": "2025-01-15T10:30:00Z"
                    }
                ]
            }
        }


ConsentResponse = ConsentsResponse


class DataAccessLogEntry(BaseModel):
    """Single data access log entry"""
    accessed_at: datetime = Field(..., description="When data was accessed")
    resource_type: str = Field(..., description="Type of resource accessed")
    resource_id: str = Field(..., description="ID of resource accessed")
    action: str = Field(..., description="Action performed")
    ip_address: Optional[str] = Field(None, description="IP address of accessor")
    justification: Optional[str] = Field(None, description="Justification for access")


class DataAccessLogsResponse(BaseModel):
    """Response with data access logs"""
    user_id: str = Field(..., description="User ID")
    total_accesses: int = Field(..., description="Total number of access events")
    logs: List[DataAccessLogEntry] = Field(..., description="List of access log entries")
    period_start: datetime = Field(..., description="Start of query period")
    period_end: datetime = Field(..., description="End of query period")


class ProcessingActivity(BaseModel):
    """Data processing activity (GDPR Article 30)"""
    name: str = Field(..., description="Name of processing activity")
    purposes: List[str] = Field(..., description="Purposes of processing")
    legal_basis: str = Field(..., description="Legal basis for processing")
    categories_of_data: List[str] = Field(..., description="Categories of personal data")
    categories_of_recipients: List[str] = Field(..., description="Categories of recipients")
    international_transfers: Optional[Dict[str, Any]] = Field(None, description="International transfer details")
    retention_period: str = Field(..., description="Data retention period")
    security_measures: List[str] = Field(..., description="Technical and organizational measures")


class ProcessingActivitiesResponse(BaseModel):
    """Response with records of processing activities"""
    controller: Dict[str, str] = Field(..., description="Data controller information")
    activities: List[ProcessingActivity] = Field(..., description="List of processing activities")


class SubProcessor(BaseModel):
    """Sub-processor information"""
    name: str = Field(..., description="Sub-processor name")
    purpose: str = Field(..., description="Purpose of processing")
    location: str = Field(..., description="Location of processing")
    safeguards: str = Field(..., description="Safeguards in place")
    dpa_signed: bool = Field(..., description="Whether DPA is signed")


class SubProcessorsResponse(BaseModel):
    """Response with list of sub-processors"""
    sub_processors: List[SubProcessor] = Field(..., description="List of sub-processors")


class DataPortabilityRequest(BaseModel):
    """Request for data portability (GDPR Article 20)"""
    format: str = Field("json", description="Format: json or csv")
    include_attachments: bool = Field(True, description="Include file attachments")


class DataPortabilityResponse(BaseModel):
    """Response for data portability request"""
    export_id: str = Field(..., description="Export ID")
    status: str = Field(..., description="Status of export")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    size_bytes: Optional[int] = Field(None, description="Size of export in bytes")
    expires_at: Optional[datetime] = Field(None, description="URL expiration")


class DataRectificationRequest(BaseModel):
    """Request to rectify inaccurate personal data (GDPR Article 16)"""
    field: str = Field(..., description="Field to rectify")
    old_value: str = Field(..., description="Current incorrect value")
    new_value: str = Field(..., description="Corrected value")
    justification: str = Field(..., description="Reason for rectification")


class DataRectificationResponse(BaseModel):
    """Response for data rectification"""
    rectification_id: str = Field(..., description="Rectification request ID")
    status: str = Field(..., description="Status: approved, pending_review, rejected")
    applied_at: Optional[datetime] = Field(None, description="When rectification was applied")
    message: str = Field(..., description="Response message")


class DataRestrictionRequest(BaseModel):
    """Request to restrict processing (GDPR Article 18)"""
    reason: str = Field(
        ...,
        description="Reason: accuracy_contested, unlawful_processing, no_longer_needed, objection_pending"
    )
    description: str = Field(..., description="Detailed description")
    duration: Optional[int] = Field(None, description="Duration in days")


class DataRestrictionResponse(BaseModel):
    """Response for processing restriction"""
    restriction_id: str = Field(..., description="Restriction ID")
    status: str = Field(..., description="Status of restriction")
    restricted_until: Optional[datetime] = Field(None, description="Restriction end date")
    restricted_operations: List[str] = Field(..., description="Operations that are restricted")


class ObjectionRequest(BaseModel):
    """Request to object to processing (GDPR Article 21)"""
    processing_purpose: str = Field(..., description="Purpose of processing to object to")
    reason: str = Field(..., description="Reason for objection")


class ObjectionResponse(BaseModel):
    """Response for objection to processing"""
    objection_id: str = Field(..., description="Objection ID")
    status: str = Field(..., description="Status: accepted, rejected, under_review")
    ceased_at: Optional[datetime] = Field(None, description="When processing ceased")
    message: str = Field(..., description="Response message")


class BreachNotification(BaseModel):
    """Data breach notification"""
    breach_id: str = Field(..., description="Breach ID")
    detected_at: datetime = Field(..., description="When breach was detected")
    nature_of_breach: str = Field(..., description="Nature of the breach")
    categories_affected: List[str] = Field(..., description="Categories of data affected")
    approximate_individuals: int = Field(..., description="Approximate number of individuals affected")
    likely_consequences: str = Field(..., description="Likely consequences of breach")
    measures_taken: List[str] = Field(..., description="Measures taken to address breach")
    dpo_contact: str = Field(..., description="DPO contact information")
