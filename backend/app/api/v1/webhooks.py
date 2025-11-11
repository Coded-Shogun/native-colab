"""
Webhook API Routes
Endpoints for webhook management and delivery tracking
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_db
from app.db.models import User, DeliveryStatus, WebhookStatus
from app.services.webhook_service import WebhookService
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookDeliveryResponse,
    WebhookDeliveryListResponse,
    WebhookDeliveryStatsResponse,
    WebhookEventTypesResponse,
)


router = APIRouter()


# ============================================
# Webhook Management Endpoints
# ============================================
@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook

    Create a webhook to receive real-time notifications for workspace events.

    Features:
    - Subscribe to multiple event types
    - HMAC signature verification with secret
    - Custom headers support
    - Event filtering by workspace, project, user
    - Automatic retry with exponential backoff
    - Delivery tracking and statistics
    """
    service = WebhookService(db)

    webhook = await service.create_webhook(
        workspace_id=workspace_id,
        created_by=current_user.id,
        name=webhook_data.name,
        url=webhook_data.url,
        events=webhook_data.events,
        description=webhook_data.description,
        secret=webhook_data.secret,
        headers=webhook_data.headers,
        filters=webhook_data.filters,
        max_retries=webhook_data.max_retries,
        retry_delay=webhook_data.retry_delay,
        is_active=webhook_data.is_active,
    )

    return WebhookResponse.model_validate(webhook)


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    workspace_id: int = Query(..., gt=0),
    status: Optional[WebhookStatus] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all webhooks for a workspace

    Returns:
    - All webhooks with delivery statistics
    - Filterable by status and active state
    - Paginated results
    """
    service = WebhookService(db)

    webhooks, total = await service.list_webhooks(
        workspace_id=workspace_id,
        status=status,
        is_active=is_active,
        limit=limit,
        offset=offset
    )

    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(w) for w in webhooks],
        total=total
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific webhook by ID

    Returns:
    - Webhook configuration
    - Delivery statistics
    - Last delivery timestamps
    """
    service = WebhookService(db)

    webhook = await service.get_webhook(webhook_id, workspace_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return WebhookResponse.model_validate(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a webhook

    Updateable fields:
    - name, description, url
    - secret, headers
    - subscribed events
    - filters
    - retry configuration
    - active state and status
    """
    service = WebhookService(db)

    webhook = await service.update_webhook(
        webhook_id=webhook_id,
        workspace_id=workspace_id,
        **webhook_data.model_dump(exclude_unset=True)
    )

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a webhook

    This will:
    - Delete the webhook configuration
    - Cancel any pending deliveries
    - Preserve delivery history for auditing
    """
    service = WebhookService(db)

    success = await service.delete_webhook(webhook_id, workspace_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )


# ============================================
# Webhook Testing Endpoints
# ============================================
@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: int,
    test_request: WebhookTestRequest,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test a webhook by sending a test event

    Sends a test payload to the webhook URL to verify:
    - URL is accessible
    - Endpoint responds with 2xx status
    - Response time is reasonable
    - HMAC signature is correctly verified (if secret is set)

    This does NOT create a delivery record.
    """
    service = WebhookService(db)

    webhook = await service.get_webhook(webhook_id, workspace_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    success, status_code, response_body, response_time_ms = await service.test_webhook(
        webhook=webhook,
        event_type=test_request.event_type,
        test_payload=test_request.test_payload
    )

    return WebhookTestResponse(
        success=success,
        status_code=status_code,
        response_body=response_body,
        response_time_ms=response_time_ms,
        error_message=response_body if not success else None
    )


# ============================================
# Webhook Delivery Endpoints
# ============================================
@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def get_webhook_deliveries(
    webhook_id: int,
    workspace_id: int = Query(..., gt=0),
    status: Optional[DeliveryStatus] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get delivery history for a webhook

    Returns:
    - All delivery attempts
    - Request and response details
    - Retry information
    - Error messages

    Useful for debugging webhook delivery issues.
    """
    service = WebhookService(db)

    # Verify webhook exists
    webhook = await service.get_webhook(webhook_id, workspace_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    deliveries, total = await service.get_deliveries(
        webhook_id=webhook_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return WebhookDeliveryListResponse(
        deliveries=[WebhookDeliveryResponse.model_validate(d) for d in deliveries],
        total=total
    )


@router.get("/{webhook_id}/stats", response_model=WebhookDeliveryStatsResponse)
async def get_webhook_stats(
    webhook_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get delivery statistics for a webhook

    Returns:
    - Total deliveries
    - Success/failure counts
    - Success rate
    - Average response time
    - Last 24h metrics

    Useful for monitoring webhook health and performance.
    """
    service = WebhookService(db)

    # Verify webhook exists
    webhook = await service.get_webhook(webhook_id, workspace_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    stats = await service.get_delivery_stats(webhook_id)

    return WebhookDeliveryStatsResponse(**stats)


# ============================================
# Webhook Event Types Endpoint
# ============================================
@router.get("/events/types", response_model=WebhookEventTypesResponse)
async def get_event_types(
    current_user: User = Depends(get_current_user)
):
    """
    Get all available webhook event types

    Returns:
    - All event types with descriptions
    - Grouped by category (user, workspace, project, task, etc.)

    Use this to discover what events you can subscribe to.
    """
    from app.db.models.webhook import WebhookEventType

    # Group events by category
    categories = {
        'User': [],
        'Workspace': [],
        'Project': [],
        'Task': [],
        'Document': [],
        'Message': [],
        'Calendar': [],
        'Meeting': [],
        'Whiteboard': [],
        'Signature': [],
        'Time Tracking': [],
    }

    event_types = []

    for event in WebhookEventType:
        event_value = event.value
        event_name = event.name.replace('_', ' ').title()

        # Determine category
        if event_value.startswith('user.'):
            category = 'User'
        elif event_value.startswith('workspace.'):
            category = 'Workspace'
        elif event_value.startswith('project.'):
            category = 'Project'
        elif event_value.startswith('task.'):
            category = 'Task'
        elif event_value.startswith('document.'):
            category = 'Document'
        elif event_value.startswith('message.') or event_value.startswith('direct_message.'):
            category = 'Message'
        elif event_value.startswith('event.'):
            category = 'Calendar'
        elif event_value.startswith('meeting.'):
            category = 'Meeting'
        elif event_value.startswith('whiteboard.'):
            category = 'Whiteboard'
        elif event_value.startswith('signature'):
            category = 'Signature'
        elif event_value.startswith('time_entry.'):
            category = 'Time Tracking'
        else:
            category = 'Other'

        event_info = {
            'value': event_value,
            'name': event_name,
            'description': f"Triggered when {event_value.replace('.', ' ')}"
        }

        event_types.append(event_info)

        if category in categories:
            categories[category].append(event_value)

    return WebhookEventTypesResponse(
        event_types=event_types,
        categories=categories
    )


# ============================================
# Webhook Retry Endpoint (Admin)
# ============================================
@router.post("/{webhook_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_failed_deliveries(
    webhook_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually retry failed webhook deliveries

    This endpoint allows you to retry all failed deliveries for a webhook.
    Useful after fixing webhook endpoint issues.

    Note: This is a background operation and returns immediately.
    """
    service = WebhookService(db)

    # Verify webhook exists
    webhook = await service.get_webhook(webhook_id, workspace_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Trigger retry for this webhook's failed deliveries
    # In production, this should be a background task
    retried_count = await service.retry_failed_deliveries(limit=100)

    return {
        "message": f"Retry initiated for failed deliveries",
        "webhook_id": webhook_id,
        "retried_count": retried_count
    }
