"""
Integration API Routes
Endpoints for third-party integrations and OAuth connections
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext
from app.db.session import get_db
from app.db.models import User, IntegrationType, IntegrationStatus
from app.services.integration_service import IntegrationService
from app.schemas.webhook import (
    IntegrationCreate,
    IntegrationUpdate,
    IntegrationResponse,
    IntegrationDetailResponse,
    IntegrationListResponse,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
    IntegrationConnectionResponse,
    IntegrationConnectionDetailResponse,
    IntegrationConnectionListResponse,
    IntegrationConnectionTestResponse,
)


router = APIRouter(dependencies=[Depends(get_organization_context)])


# ============================================
# Integration Management Endpoints (Admin)
# ============================================
@router.post("/", response_model=IntegrationDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new integration (Admin only)

    System administrators can add new third-party integrations:
    - OAuth integrations (Slack, GitHub, Google Calendar)
    - API key integrations (custom services)
    - Webhook-based integrations
    """
    # TODO: Add admin permission check
    # if not current_user.is_super_admin():
    #     raise HTTPException(status_code=403, detail="Admin access required")

    service = IntegrationService(db)

    integration = await service.create_integration(
        type=integration_data.type,
        name=integration_data.name,
        description=integration_data.description,
        icon_url=integration_data.icon_url,
        client_id=integration_data.client_id,
        client_secret=integration_data.client_secret,
        authorization_url=integration_data.authorization_url,
        token_url=integration_data.token_url,
        scopes=integration_data.scopes,
        api_base_url=integration_data.api_base_url,
        api_version=integration_data.api_version,
        settings=integration_data.settings,
        is_enabled=integration_data.is_enabled,
        is_oauth=integration_data.is_oauth,
        is_system=False,
    )

    return IntegrationDetailResponse.model_validate(integration)


@router.get("/", response_model=IntegrationListResponse)
async def list_integrations(
    integration_type: Optional[IntegrationType] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available integrations

    Returns:
    - All integrations that can be connected
    - Filtered by type and enabled status
    - Includes OAuth and API key integrations
    """
    service = IntegrationService(db)

    integrations = await service.list_integrations(
        is_enabled=is_enabled,
        integration_type=integration_type
    )

    return IntegrationListResponse(
        integrations=[IntegrationResponse.model_validate(i) for i in integrations],
        total=len(integrations)
    )


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific integration

    Returns:
    - Integration details (excludes sensitive credentials)
    - OAuth configuration (if applicable)
    - API endpoints
    """
    service = IntegrationService(db)

    integration = await service.get_integration(integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    return IntegrationResponse.model_validate(integration)


@router.patch("/{integration_id}", response_model=IntegrationDetailResponse)
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an integration (Admin only)

    Update integration configuration:
    - OAuth credentials
    - API endpoints
    - Scopes
    - Enabled state
    """
    # TODO: Add admin permission check

    service = IntegrationService(db)

    integration = await service.update_integration(
        integration_id=integration_id,
        **integration_data.model_dump(exclude_unset=True)
    )

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    return IntegrationDetailResponse.model_validate(integration)


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an integration (Admin only)

    This will:
    - Delete the integration
    - Disconnect all connections
    - Cannot delete system integrations
    """
    # TODO: Add admin permission check

    service = IntegrationService(db)

    success = await service.delete_integration(integration_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found or cannot be deleted"
        )


# ============================================
# Integration Connection Endpoints
# ============================================
@router.post("/connections", response_model=IntegrationConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: IntegrationConnectionCreate,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new integration connection

    Connect your workspace to a third-party service:
    - For OAuth integrations: Complete OAuth flow first
    - For API key integrations: Provide credentials directly

    Examples:
    - Connect to Slack for notifications
    - Connect to GitHub for issue sync
    - Connect to Google Calendar for event sync
    """
    service = IntegrationService(db)

    # Verify integration exists
    integration = await service.get_integration(connection_data.integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    if not integration.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration is not enabled"
        )

    connection = await service.create_connection(
        integration_id=connection_data.integration_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=connection_data.name,
        description=connection_data.description,
        credentials=connection_data.credentials,
        settings=connection_data.settings,
        is_active=connection_data.is_active,
    )

    return IntegrationConnectionResponse.model_validate(connection)


@router.get("/connections", response_model=IntegrationConnectionListResponse)
async def list_connections(
    workspace_id: int = Query(..., gt=0),
    integration_id: Optional[int] = Query(None, gt=0),
    status: Optional[IntegrationStatus] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List integration connections for a workspace

    Returns:
    - All active connections
    - Connection status and health
    - Last sync information
    - Error details if any
    """
    service = IntegrationService(db)

    connections, total = await service.list_connections(
        workspace_id=workspace_id,
        integration_id=integration_id,
        user_id=None,  # All users
        status=status,
        is_active=is_active,
        limit=limit,
        offset=offset
    )

    return IntegrationConnectionListResponse(
        connections=[IntegrationConnectionResponse.model_validate(c) for c in connections],
        total=total
    )


@router.get("/connections/{connection_id}", response_model=IntegrationConnectionDetailResponse)
async def get_connection(
    connection_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific integration connection

    Returns:
    - Connection details
    - Integration information
    - Status and health metrics
    - Last sync and error details
    """
    service = IntegrationService(db)

    connection = await service.get_connection(connection_id, workspace_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    # Get integration details
    integration = await service.get_integration(connection.integration_id)

    response_data = IntegrationConnectionDetailResponse.model_validate(connection)
    if integration:
        response_data.integration = IntegrationResponse.model_validate(integration)

    return response_data


@router.patch("/connections/{connection_id}", response_model=IntegrationConnectionResponse)
async def update_connection(
    connection_id: int,
    connection_data: IntegrationConnectionUpdate,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an integration connection

    Update connection settings:
    - Name and description
    - Credentials (for API key integrations)
    - Settings
    - Active state
    """
    service = IntegrationService(db)

    connection = await service.update_connection(
        connection_id=connection_id,
        workspace_id=workspace_id,
        **connection_data.model_dump(exclude_unset=True)
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    return IntegrationConnectionResponse.model_validate(connection)


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an integration connection

    This will:
    - Remove the connection
    - Revoke access tokens (if applicable)
    - Stop all sync operations
    """
    service = IntegrationService(db)

    success = await service.delete_connection(connection_id, workspace_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )


@router.post("/connections/{connection_id}/disconnect", status_code=status.HTTP_200_OK)
async def disconnect_connection(
    connection_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect an integration connection

    Temporarily disconnect without deleting:
    - Preserves connection settings
    - Stops sync operations
    - Can be reconnected later
    """
    service = IntegrationService(db)

    success = await service.disconnect_connection(connection_id, workspace_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    return {"message": "Connection disconnected successfully"}


@router.post("/connections/{connection_id}/test", response_model=IntegrationConnectionTestResponse)
async def test_connection(
    connection_id: int,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test an integration connection

    Verify the connection is working:
    - Check credentials are valid
    - Test API connectivity
    - Verify permissions
    - Update connection status
    """
    service = IntegrationService(db)

    success, message = await service.test_connection(connection_id, workspace_id)

    connection = await service.get_connection(connection_id, workspace_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    return IntegrationConnectionTestResponse(
        success=success,
        status=connection.status,
        message=message,
        external_data=connection.external_data if success else None
    )


# ============================================
# OAuth Endpoints (Placeholder)
# ============================================
@router.get("/oauth/authorize")
async def oauth_authorize(
    integration_id: int = Query(..., gt=0),
    workspace_id: int = Query(..., gt=0),
    redirect_uri: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate OAuth authorization flow

    Step 1 of OAuth:
    - Redirects user to integration's authorization page
    - User grants permissions
    - Returns to callback URL with authorization code

    Note: Full OAuth implementation requires additional setup
    """
    service = IntegrationService(db)

    integration = await service.get_integration(integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    if not integration.is_oauth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration does not use OAuth"
        )

    # TODO: Implement full OAuth flow
    # - Generate state parameter
    # - Build authorization URL
    # - Redirect to provider

    return {
        "message": "OAuth flow not yet implemented",
        "integration": integration.name,
        "authorization_url": integration.authorization_url
    }


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback

    Step 2 of OAuth:
    - Receives authorization code
    - Exchanges code for access token
    - Creates integration connection
    - Redirects to success page

    Note: Full OAuth implementation requires additional setup
    """
    # TODO: Implement OAuth callback
    # - Verify state parameter
    # - Exchange code for tokens
    # - Store tokens in connection
    # - Return success response

    return {
        "message": "OAuth callback not yet implemented"
    }
