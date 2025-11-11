"""
Webhook Schemas
Pydantic schemas for webhooks and integrations
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

from app.db.models.webhook import (
    WebhookEventType,
    WebhookStatus,
    DeliveryStatus,
    IntegrationType,
    IntegrationStatus,
)


# ============================================
# Webhook Schemas
# ============================================
class WebhookCreate(BaseModel):
    """Schema for creating a webhook"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    url: str = Field(..., description="Webhook endpoint URL")
    secret: Optional[str] = Field(None, max_length=255, description="Secret for HMAC signature")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Custom headers")
    events: List[WebhookEventType] = Field(..., min_items=1, description="Event types to subscribe to")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: int = Field(default=60, ge=10, le=3600, description="Retry delay in seconds")
    is_active: bool = Field(default=True)


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    url: Optional[str] = None
    secret: Optional[str] = Field(None, max_length=255)
    headers: Optional[Dict[str, str]] = None
    events: Optional[List[WebhookEventType]] = Field(None, min_items=1)
    filters: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=10, le=3600)
    is_active: Optional[bool] = None
    status: Optional[WebhookStatus] = None


class WebhookResponse(BaseModel):
    """Schema for webhook response"""
    id: int
    workspace_id: int
    created_by: int
    name: str
    description: Optional[str] = None
    url: str
    headers: Optional[Dict[str, str]] = None
    events: List[str]
    filters: Optional[Dict[str, Any]] = None
    status: WebhookStatus
    is_active: bool
    max_retries: int
    retry_delay: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """Schema for webhook list response"""
    webhooks: List[WebhookResponse]
    total: int


class WebhookTestRequest(BaseModel):
    """Schema for testing a webhook"""
    event_type: WebhookEventType
    test_payload: Optional[Dict[str, Any]] = Field(default=None)


class WebhookTestResponse(BaseModel):
    """Schema for webhook test response"""
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None


# ============================================
# Webhook Delivery Schemas
# ============================================
class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response"""
    id: int
    webhook_id: int
    event_type: WebhookEventType
    event_id: str
    payload: Dict[str, Any]
    request_url: str
    request_method: str
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    status: DeliveryStatus
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    created_at: datetime
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WebhookDeliveryListResponse(BaseModel):
    """Schema for webhook delivery list response"""
    deliveries: List[WebhookDeliveryResponse]
    total: int


class WebhookDeliveryStatsResponse(BaseModel):
    """Schema for webhook delivery statistics"""
    webhook_id: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    pending_deliveries: int
    average_response_time_ms: Optional[float] = None
    success_rate: float
    last_24h_deliveries: int
    last_24h_failures: int


# ============================================
# Webhook Event Schemas
# ============================================
class WebhookEventPayload(BaseModel):
    """Base schema for webhook event payloads"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: WebhookEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    workspace_id: int
    actor_id: Optional[int] = Field(None, description="User who triggered the event")
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class WebhookEventTypesResponse(BaseModel):
    """Schema for available webhook event types"""
    event_types: List[Dict[str, str]]
    categories: Dict[str, List[str]]


# ============================================
# Integration Schemas
# ============================================
class IntegrationCreate(BaseModel):
    """Schema for creating an integration"""
    type: IntegrationType
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    icon_url: Optional[str] = None
    client_id: Optional[str] = Field(None, max_length=255)
    client_secret: Optional[str] = Field(None, max_length=255)
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    scopes: Optional[List[str]] = Field(default=None)
    api_base_url: Optional[str] = None
    api_version: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = Field(default=None)
    is_enabled: bool = Field(default=True)
    is_oauth: bool = Field(default=False)


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    icon_url: Optional[str] = None
    client_id: Optional[str] = Field(None, max_length=255)
    client_secret: Optional[str] = Field(None, max_length=255)
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    scopes: Optional[List[str]] = None
    api_base_url: Optional[str] = None
    api_version: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class IntegrationResponse(BaseModel):
    """Schema for integration response"""
    id: int
    type: IntegrationType
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_enabled: bool
    is_oauth: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    # Exclude sensitive fields like client_secret

    model_config = {"from_attributes": True}


class IntegrationDetailResponse(IntegrationResponse):
    """Schema for detailed integration response (admin only)"""
    client_id: Optional[str] = None
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    scopes: Optional[List[str]] = None
    api_base_url: Optional[str] = None
    api_version: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class IntegrationListResponse(BaseModel):
    """Schema for integration list response"""
    integrations: List[IntegrationResponse]
    total: int


# ============================================
# Integration Connection Schemas
# ============================================
class IntegrationConnectionCreate(BaseModel):
    """Schema for creating an integration connection"""
    integration_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    credentials: Optional[Dict[str, str]] = Field(
        default=None,
        description="API keys, tokens for non-OAuth integrations"
    )
    settings: Optional[Dict[str, Any]] = Field(default=None)
    is_active: bool = Field(default=True)


class IntegrationConnectionUpdate(BaseModel):
    """Schema for updating an integration connection"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    credentials: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationConnectionResponse(BaseModel):
    """Schema for integration connection response"""
    id: int
    integration_id: int
    workspace_id: int
    user_id: int
    name: str
    description: Optional[str] = None
    status: IntegrationStatus
    is_active: bool
    external_id: Optional[str] = None
    external_data: Optional[Dict[str, Any]] = None
    last_used_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    total_syncs: int
    failed_syncs: int
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntegrationConnectionDetailResponse(IntegrationConnectionResponse):
    """Schema for detailed integration connection response"""
    integration: IntegrationResponse
    token_expires_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None


class IntegrationConnectionListResponse(BaseModel):
    """Schema for integration connection list response"""
    connections: List[IntegrationConnectionResponse]
    total: int


class IntegrationConnectionTestResponse(BaseModel):
    """Schema for testing integration connection"""
    success: bool
    status: IntegrationStatus
    message: Optional[str] = None
    external_data: Optional[Dict[str, Any]] = None


# ============================================
# OAuth Schemas
# ============================================
class OAuthAuthorizeRequest(BaseModel):
    """Schema for OAuth authorization request"""
    integration_id: int = Field(..., gt=0)
    workspace_id: int = Field(..., gt=0)
    redirect_uri: str
    state: Optional[str] = None


class OAuthAuthorizeResponse(BaseModel):
    """Schema for OAuth authorization response"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback"""
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Schema for OAuth callback response"""
    success: bool
    connection_id: Optional[int] = None
    error: Optional[str] = None


# ============================================
# Integration Action Schemas
# ============================================
class IntegrationSyncRequest(BaseModel):
    """Schema for triggering integration sync"""
    connection_id: int = Field(..., gt=0)
    sync_type: Optional[str] = Field(
        default="full",
        description="Type of sync: full, incremental"
    )
    options: Optional[Dict[str, Any]] = Field(default=None)


class IntegrationSyncResponse(BaseModel):
    """Schema for integration sync response"""
    success: bool
    synced_items: int
    failed_items: int
    sync_duration_ms: int
    errors: Optional[List[str]] = None


class IntegrationActionRequest(BaseModel):
    """Schema for custom integration action"""
    connection_id: int = Field(..., gt=0)
    action: str = Field(..., description="Action name")
    parameters: Optional[Dict[str, Any]] = Field(default=None)


class IntegrationActionResponse(BaseModel):
    """Schema for integration action response"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
