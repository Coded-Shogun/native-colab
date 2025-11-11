"""
Webhook Service
Handles webhook delivery, retries, and management
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import httpx
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Webhook,
    WebhookDelivery,
    WebhookEventType,
    WebhookStatus,
    DeliveryStatus,
)


class WebhookService:
    """Service for handling webhook operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Webhook Management
    # ============================================
    async def create_webhook(
        self,
        workspace_id: int,
        created_by: int,
        name: str,
        url: str,
        events: List[WebhookEventType],
        description: Optional[str] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: int = 60,
        is_active: bool = True,
    ) -> Webhook:
        """Create a new webhook"""
        # Convert events to list of strings
        event_strings = [event.value for event in events]

        webhook = Webhook(
            workspace_id=workspace_id,
            created_by=created_by,
            name=name,
            description=description,
            url=url,
            secret=secret,
            headers=headers or {},
            events=event_strings,
            filters=filters or {},
            max_retries=max_retries,
            retry_delay=retry_delay,
            is_active=is_active,
            status=WebhookStatus.ACTIVE if is_active else WebhookStatus.INACTIVE,
        )

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def get_webhook(self, webhook_id: int, workspace_id: int) -> Optional[Webhook]:
        """Get a webhook by ID"""
        stmt = select(Webhook).where(
            and_(
                Webhook.id == webhook_id,
                Webhook.workspace_id == workspace_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_webhooks(
        self,
        workspace_id: int,
        status: Optional[WebhookStatus] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Webhook], int]:
        """List webhooks for a workspace"""
        stmt = select(Webhook).where(Webhook.workspace_id == workspace_id)

        if status:
            stmt = stmt.where(Webhook.status == status)

        if is_active is not None:
            stmt = stmt.where(Webhook.is_active == is_active)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get webhooks
        stmt = stmt.order_by(desc(Webhook.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        webhooks = list(result.scalars().all())

        return webhooks, total

    async def update_webhook(
        self,
        webhook_id: int,
        workspace_id: int,
        **update_data
    ) -> Optional[Webhook]:
        """Update a webhook"""
        webhook = await self.get_webhook(webhook_id, workspace_id)
        if not webhook:
            return None

        # Convert events if provided
        if 'events' in update_data and update_data['events']:
            update_data['events'] = [
                event.value if isinstance(event, WebhookEventType) else event
                for event in update_data['events']
            ]

        for key, value in update_data.items():
            if value is not None and hasattr(webhook, key):
                setattr(webhook, key, value)

        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def delete_webhook(self, webhook_id: int, workspace_id: int) -> bool:
        """Delete a webhook"""
        webhook = await self.get_webhook(webhook_id, workspace_id)
        if not webhook:
            return False

        await self.db.delete(webhook)
        await self.db.commit()
        return True

    async def disable_webhook(self, webhook_id: int, workspace_id: int) -> bool:
        """Disable a webhook after too many failures"""
        webhook = await self.get_webhook(webhook_id, workspace_id)
        if not webhook:
            return False

        webhook.status = WebhookStatus.FAILED
        webhook.is_active = False
        await self.db.commit()
        return True

    # ============================================
    # Webhook Delivery
    # ============================================
    async def dispatch_event(
        self,
        event_type: WebhookEventType,
        workspace_id: int,
        data: Dict[str, Any],
        actor_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Dispatch an event to all matching webhooks

        Args:
            event_type: Type of event
            workspace_id: Workspace where event occurred
            data: Event data
            actor_id: User who triggered the event
            metadata: Additional metadata

        Returns:
            Number of webhooks triggered
        """
        # Find all active webhooks that subscribe to this event
        stmt = select(Webhook).where(
            and_(
                Webhook.workspace_id == workspace_id,
                Webhook.is_active == True,
                Webhook.status == WebhookStatus.ACTIVE
            )
        )
        result = await self.db.execute(stmt)
        all_webhooks = list(result.scalars().all())

        # Filter webhooks that subscribe to this event type
        matching_webhooks = [
            webhook for webhook in all_webhooks
            if event_type.value in webhook.events
        ]

        # Apply additional filters if needed
        filtered_webhooks = []
        for webhook in matching_webhooks:
            if self._matches_filters(webhook.filters, data):
                filtered_webhooks.append(webhook)

        # Create event payload
        event_id = str(uuid.uuid4())
        payload = {
            'event_id': event_id,
            'event_type': event_type.value,
            'timestamp': datetime.utcnow().isoformat(),
            'workspace_id': workspace_id,
            'actor_id': actor_id,
            'data': data,
            'metadata': metadata or {},
        }

        # Create delivery records
        for webhook in filtered_webhooks:
            await self._create_delivery(webhook, event_type, event_id, payload)

        return len(filtered_webhooks)

    def _matches_filters(self, filters: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Check if data matches webhook filters"""
        if not filters:
            return True

        for key, value in filters.items():
            if key not in data:
                return False
            if isinstance(value, list):
                if data[key] not in value:
                    return False
            elif data[key] != value:
                return False

        return True

    async def _create_delivery(
        self,
        webhook: Webhook,
        event_type: WebhookEventType,
        event_id: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Create a webhook delivery record"""
        # Generate HMAC signature if secret is provided
        signature = None
        if webhook.secret:
            signature = self._generate_signature(payload, webhook.secret)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            request_url=webhook.url,
            request_method='POST',
            request_headers=webhook.headers or {},
            request_signature=signature,
            status=DeliveryStatus.PENDING,
            max_attempts=webhook.max_retries + 1,  # Initial attempt + retries
        )

        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)

        # Trigger delivery asynchronously
        await self._attempt_delivery(delivery, webhook)

        return delivery

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def _attempt_delivery(self, delivery: WebhookDelivery, webhook: Webhook) -> bool:
        """
        Attempt to deliver a webhook

        Args:
            delivery: Delivery record
            webhook: Webhook configuration

        Returns:
            True if successful, False otherwise
        """
        delivery.attempts += 1
        delivery.status = DeliveryStatus.RETRYING if delivery.attempts > 1 else DeliveryStatus.PENDING

        try:
            # Prepare headers
            headers = dict(delivery.request_headers or {})
            headers['Content-Type'] = 'application/json'
            headers['User-Agent'] = 'NativeColab-Webhook/1.0'
            headers['X-Webhook-Event'] = delivery.event_type.value
            headers['X-Webhook-Event-ID'] = delivery.event_id
            headers['X-Webhook-Delivery-ID'] = str(delivery.id)

            if delivery.request_signature:
                headers['X-Webhook-Signature'] = delivery.request_signature

            # Send webhook
            start_time = datetime.utcnow()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    delivery.request_url,
                    json=delivery.payload,
                    headers=headers
                )

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Record response
            delivery.response_status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit size
            delivery.response_time_ms = response_time_ms

            # Check if successful (2xx status codes)
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.SUCCESS
                delivery.delivered_at = datetime.utcnow()

                # Update webhook statistics
                webhook.total_deliveries += 1
                webhook.successful_deliveries += 1
                webhook.last_delivery_at = datetime.utcnow()
                webhook.last_success_at = datetime.utcnow()

                await self.db.commit()
                return True
            else:
                # Non-2xx response is considered a failure
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                return await self._handle_delivery_failure(delivery, webhook)

        except httpx.TimeoutException as e:
            delivery.error_message = f"Timeout: {str(e)}"
            return await self._handle_delivery_failure(delivery, webhook)

        except httpx.RequestError as e:
            delivery.error_message = f"Request error: {str(e)}"
            return await self._handle_delivery_failure(delivery, webhook)

        except Exception as e:
            delivery.error_message = f"Unexpected error: {str(e)}"
            return await self._handle_delivery_failure(delivery, webhook)

    async def _handle_delivery_failure(
        self,
        delivery: WebhookDelivery,
        webhook: Webhook
    ) -> bool:
        """Handle failed webhook delivery"""
        # Check if we should retry
        if delivery.attempts < delivery.max_attempts:
            # Schedule retry with exponential backoff
            retry_delay = webhook.retry_delay * (2 ** (delivery.attempts - 1))
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            delivery.status = DeliveryStatus.RETRYING
        else:
            # Max retries reached
            delivery.status = DeliveryStatus.FAILED
            webhook.failed_deliveries += 1

            # Check if webhook should be disabled due to too many failures
            failure_rate = webhook.failed_deliveries / max(webhook.total_deliveries, 1)
            if webhook.total_deliveries >= 10 and failure_rate > 0.8:
                await self.disable_webhook(webhook.id, webhook.workspace_id)

        webhook.total_deliveries += 1
        webhook.last_delivery_at = datetime.utcnow()
        webhook.last_failure_at = datetime.utcnow()

        await self.db.commit()
        return False

    async def retry_failed_deliveries(self, limit: int = 100) -> int:
        """
        Retry failed webhook deliveries that are due for retry

        Returns:
            Number of deliveries retried
        """
        stmt = select(WebhookDelivery).where(
            and_(
                WebhookDelivery.status == DeliveryStatus.RETRYING,
                WebhookDelivery.next_retry_at <= datetime.utcnow(),
                WebhookDelivery.attempts < WebhookDelivery.max_attempts
            )
        ).limit(limit)

        result = await self.db.execute(stmt)
        deliveries = list(result.scalars().all())

        retried_count = 0
        for delivery in deliveries:
            # Get webhook
            webhook_stmt = select(Webhook).where(Webhook.id == delivery.webhook_id)
            webhook_result = await self.db.execute(webhook_stmt)
            webhook = webhook_result.scalar_one_or_none()

            if webhook and webhook.is_active:
                await self._attempt_delivery(delivery, webhook)
                retried_count += 1

        return retried_count

    # ============================================
    # Webhook Testing
    # ============================================
    async def test_webhook(
        self,
        webhook: Webhook,
        event_type: WebhookEventType,
        test_payload: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[int], Optional[str], Optional[int]]:
        """
        Test a webhook by sending a test event

        Returns:
            Tuple of (success, status_code, response_body, response_time_ms)
        """
        # Create test payload
        if test_payload is None:
            test_payload = {
                'test': True,
                'message': 'This is a test webhook delivery'
            }

        payload = {
            'event_id': f"test-{uuid.uuid4()}",
            'event_type': event_type.value,
            'timestamp': datetime.utcnow().isoformat(),
            'workspace_id': webhook.workspace_id,
            'data': test_payload,
        }

        try:
            # Prepare headers
            headers = dict(webhook.headers or {})
            headers['Content-Type'] = 'application/json'
            headers['User-Agent'] = 'NativeColab-Webhook/1.0'
            headers['X-Webhook-Event'] = event_type.value
            headers['X-Webhook-Test'] = 'true'

            if webhook.secret:
                signature = self._generate_signature(payload, webhook.secret)
                headers['X-Webhook-Signature'] = signature

            # Send test webhook
            start_time = datetime.utcnow()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                )

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            success = 200 <= response.status_code < 300
            return success, response.status_code, response.text[:500], response_time_ms

        except Exception as e:
            return False, None, str(e), None

    # ============================================
    # Delivery Management
    # ============================================
    async def get_deliveries(
        self,
        webhook_id: int,
        status: Optional[DeliveryStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WebhookDelivery], int]:
        """Get webhook deliveries"""
        stmt = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)

        if status:
            stmt = stmt.where(WebhookDelivery.status == status)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get deliveries
        stmt = stmt.order_by(desc(WebhookDelivery.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        deliveries = list(result.scalars().all())

        return deliveries, total

    async def get_delivery_stats(self, webhook_id: int) -> Dict[str, Any]:
        """Get delivery statistics for a webhook"""
        # Get counts by status
        stmt = select(
            WebhookDelivery.status,
            func.count(WebhookDelivery.id)
        ).where(
            WebhookDelivery.webhook_id == webhook_id
        ).group_by(WebhookDelivery.status)

        result = await self.db.execute(stmt)
        status_counts = {status: count for status, count in result.all()}

        # Get average response time
        avg_time_stmt = select(
            func.avg(WebhookDelivery.response_time_ms)
        ).where(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.status == DeliveryStatus.SUCCESS
            )
        )
        avg_time_result = await self.db.execute(avg_time_stmt)
        avg_response_time = avg_time_result.scalar()

        # Get last 24h stats
        yesterday = datetime.utcnow() - timedelta(hours=24)
        last_24h_stmt = select(
            func.count(WebhookDelivery.id)
        ).where(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.created_at >= yesterday
            )
        )
        last_24h_result = await self.db.execute(last_24h_stmt)
        last_24h_deliveries = last_24h_result.scalar() or 0

        last_24h_failures_stmt = select(
            func.count(WebhookDelivery.id)
        ).where(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.created_at >= yesterday,
                WebhookDelivery.status == DeliveryStatus.FAILED
            )
        )
        last_24h_failures_result = await self.db.execute(last_24h_failures_stmt)
        last_24h_failures = last_24h_failures_result.scalar() or 0

        total_deliveries = sum(status_counts.values())
        successful_deliveries = status_counts.get(DeliveryStatus.SUCCESS, 0)
        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

        return {
            'webhook_id': webhook_id,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': status_counts.get(DeliveryStatus.FAILED, 0),
            'pending_deliveries': status_counts.get(DeliveryStatus.PENDING, 0) + status_counts.get(DeliveryStatus.RETRYING, 0),
            'average_response_time_ms': float(avg_response_time) if avg_response_time else None,
            'success_rate': success_rate,
            'last_24h_deliveries': last_24h_deliveries,
            'last_24h_failures': last_24h_failures,
        }
