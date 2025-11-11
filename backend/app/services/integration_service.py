"""
Integration Service
Handles third-party integrations and OAuth connections
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Integration,
    IntegrationConnection,
    IntegrationType,
    IntegrationStatus,
)


class IntegrationService:
    """Service for handling integration operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Integration Management
    # ============================================
    async def create_integration(
        self,
        type: IntegrationType,
        name: str,
        description: Optional[str] = None,
        icon_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        authorization_url: Optional[str] = None,
        token_url: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        api_base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_enabled: bool = True,
        is_oauth: bool = False,
        is_system: bool = False,
    ) -> Integration:
        """Create a new integration"""
        integration = Integration(
            type=type,
            name=name,
            description=description,
            icon_url=icon_url,
            client_id=client_id,
            client_secret=client_secret,
            authorization_url=authorization_url,
            token_url=token_url,
            scopes=scopes or [],
            api_base_url=api_base_url,
            api_version=api_version,
            settings=settings or {},
            is_enabled=is_enabled,
            is_oauth=is_oauth,
            is_system=is_system,
        )

        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def get_integration(self, integration_id: int) -> Optional[Integration]:
        """Get an integration by ID"""
        stmt = select(Integration).where(Integration.id == integration_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_integration_by_type(self, type: IntegrationType) -> Optional[Integration]:
        """Get an integration by type"""
        stmt = select(Integration).where(
            and_(
                Integration.type == type,
                Integration.is_enabled == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_integrations(
        self,
        is_enabled: Optional[bool] = None,
        integration_type: Optional[IntegrationType] = None
    ) -> List[Integration]:
        """List all integrations"""
        stmt = select(Integration)

        if is_enabled is not None:
            stmt = stmt.where(Integration.is_enabled == is_enabled)

        if integration_type:
            stmt = stmt.where(Integration.type == integration_type)

        stmt = stmt.order_by(Integration.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_integration(
        self,
        integration_id: int,
        **update_data
    ) -> Optional[Integration]:
        """Update an integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(integration, key):
                setattr(integration, key, value)

        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def delete_integration(self, integration_id: int) -> bool:
        """Delete an integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return False

        # Don't allow deleting system integrations
        if integration.is_system:
            return False

        await self.db.delete(integration)
        await self.db.commit()
        return True

    # ============================================
    # Integration Connection Management
    # ============================================
    async def create_connection(
        self,
        integration_id: int,
        workspace_id: int,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        credentials: Optional[Dict[str, str]] = None,
        settings: Optional[Dict[str, Any]] = None,
        external_id: Optional[str] = None,
        external_data: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ) -> IntegrationConnection:
        """Create a new integration connection"""
        connection = IntegrationConnection(
            integration_id=integration_id,
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            description=description,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            credentials=credentials or {},
            settings=settings or {},
            external_id=external_id,
            external_data=external_data or {},
            status=IntegrationStatus.CONNECTED,
            is_active=is_active,
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def get_connection(
        self,
        connection_id: int,
        workspace_id: int
    ) -> Optional[IntegrationConnection]:
        """Get an integration connection"""
        stmt = select(IntegrationConnection).where(
            and_(
                IntegrationConnection.id == connection_id,
                IntegrationConnection.workspace_id == workspace_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_connections(
        self,
        workspace_id: int,
        integration_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[IntegrationStatus] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[IntegrationConnection], int]:
        """List integration connections"""
        stmt = select(IntegrationConnection).where(
            IntegrationConnection.workspace_id == workspace_id
        )

        if integration_id:
            stmt = stmt.where(IntegrationConnection.integration_id == integration_id)

        if user_id:
            stmt = stmt.where(IntegrationConnection.user_id == user_id)

        if status:
            stmt = stmt.where(IntegrationConnection.status == status)

        if is_active is not None:
            stmt = stmt.where(IntegrationConnection.is_active == is_active)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get connections
        stmt = stmt.order_by(desc(IntegrationConnection.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        connections = list(result.scalars().all())

        return connections, total

    async def update_connection(
        self,
        connection_id: int,
        workspace_id: int,
        **update_data
    ) -> Optional[IntegrationConnection]:
        """Update an integration connection"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(connection, key):
                setattr(connection, key, value)

        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def delete_connection(self, connection_id: int, workspace_id: int) -> bool:
        """Delete an integration connection"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False

        await self.db.delete(connection)
        await self.db.commit()
        return True

    async def disconnect_connection(self, connection_id: int, workspace_id: int) -> bool:
        """Disconnect an integration connection"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False

        connection.status = IntegrationStatus.DISCONNECTED
        connection.is_active = False
        await self.db.commit()
        return True

    # ============================================
    # Connection Token Management
    # ============================================
    async def refresh_token(
        self,
        connection_id: int,
        workspace_id: int,
        new_access_token: str,
        new_refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> Optional[IntegrationConnection]:
        """Refresh connection tokens"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return None

        connection.access_token = new_access_token

        if new_refresh_token:
            connection.refresh_token = new_refresh_token

        if expires_in:
            connection.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        connection.status = IntegrationStatus.CONNECTED
        connection.last_used_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def mark_token_expired(
        self,
        connection_id: int,
        workspace_id: int
    ) -> bool:
        """Mark connection token as expired"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False

        connection.status = IntegrationStatus.EXPIRED
        await self.db.commit()
        return True

    async def check_expired_tokens(self, workspace_id: int) -> int:
        """Check and mark expired tokens"""
        stmt = select(IntegrationConnection).where(
            and_(
                IntegrationConnection.workspace_id == workspace_id,
                IntegrationConnection.status == IntegrationStatus.CONNECTED,
                IntegrationConnection.token_expires_at <= datetime.utcnow()
            )
        )

        result = await self.db.execute(stmt)
        expired_connections = list(result.scalars().all())

        for connection in expired_connections:
            connection.status = IntegrationStatus.EXPIRED

        await self.db.commit()
        return len(expired_connections)

    # ============================================
    # Connection Statistics
    # ============================================
    async def record_sync(
        self,
        connection_id: int,
        workspace_id: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """Record a sync operation"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False

        connection.last_sync_at = datetime.utcnow()
        connection.total_syncs += 1

        if success:
            connection.last_used_at = datetime.utcnow()
            if connection.status != IntegrationStatus.CONNECTED:
                connection.status = IntegrationStatus.CONNECTED
            connection.last_error = None
            connection.last_error_at = None
        else:
            connection.failed_syncs += 1
            connection.last_error = error_message
            connection.last_error_at = datetime.utcnow()

            # Mark as error if too many failures
            failure_rate = connection.failed_syncs / connection.total_syncs
            if connection.total_syncs >= 5 and failure_rate > 0.6:
                connection.status = IntegrationStatus.ERROR

        await self.db.commit()
        return True

    async def update_last_used(
        self,
        connection_id: int,
        workspace_id: int
    ) -> bool:
        """Update last used timestamp"""
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False

        connection.last_used_at = datetime.utcnow()
        await self.db.commit()
        return True

    # ============================================
    # OAuth Helper Methods
    # ============================================
    async def get_oauth_config(
        self,
        integration_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get OAuth configuration for an integration"""
        integration = await self.get_integration(integration_id)
        if not integration or not integration.is_oauth:
            return None

        return {
            'client_id': integration.client_id,
            'client_secret': integration.client_secret,
            'authorization_url': integration.authorization_url,
            'token_url': integration.token_url,
            'scopes': integration.scopes,
        }

    # ============================================
    # Integration Test
    # ============================================
    async def test_connection(
        self,
        connection_id: int,
        workspace_id: int
    ) -> Tuple[bool, str]:
        """
        Test an integration connection

        Returns:
            Tuple of (success, message)
        """
        connection = await self.get_connection(connection_id, workspace_id)
        if not connection:
            return False, "Connection not found"

        if not connection.is_active:
            return False, "Connection is inactive"

        if connection.status == IntegrationStatus.EXPIRED:
            return False, "Connection token has expired"

        if connection.status == IntegrationStatus.ERROR:
            return False, f"Connection has errors: {connection.last_error}"

        # For basic test, just check if credentials exist
        integration = await self.get_integration(connection.integration_id)
        if not integration:
            return False, "Integration not found"

        if integration.is_oauth:
            if not connection.access_token:
                return False, "No access token available"
        else:
            if not connection.credentials:
                return False, "No credentials configured"

        # Update last used
        await self.update_last_used(connection_id, workspace_id)

        return True, "Connection test successful"
