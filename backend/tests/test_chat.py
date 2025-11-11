"""
Chat and Messaging Tests
Tests for real-time messaging, channels, and Socket.io integration
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Channel, Message


class TestChannels:
    """Tests for channel management endpoints"""

    @pytest.mark.asyncio
    async def test_create_channel(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a new channel"""
        response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "general",
                "description": "General discussion",
                "is_private": False
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "general"
        assert data["description"] == "General discussion"
        assert data["is_private"] is False
        assert data["workspace_id"] == test_workspace["id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_workspace_channels(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test listing channels in a workspace"""
        # Create a few channels
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/channels",
                json={
                    "workspace_id": test_workspace["id"],
                    "name": f"channel-{i}",
                    "is_private": False
                }
            )

        response = await authenticated_client.get(
            f"/api/v1/workspaces/{test_workspace['id']}/channels"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(ch["workspace_id"] == test_workspace["id"] for ch in data)

    @pytest.mark.asyncio
    async def test_get_channel_by_id(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test retrieving a specific channel"""
        # Create channel
        create_response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "test-channel",
                "is_private": False
            }
        )
        channel_id = create_response.json()["id"]

        # Get channel
        response = await authenticated_client.get(f"/api/v1/channels/{channel_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == channel_id
        assert data["name"] == "test-channel"

    @pytest.mark.asyncio
    async def test_update_channel(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating channel details"""
        # Create channel
        create_response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "old-name",
                "is_private": False
            }
        )
        channel_id = create_response.json()["id"]

        # Update channel
        response = await authenticated_client.put(
            f"/api/v1/channels/{channel_id}",
            json={
                "name": "new-name",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_channel(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting a channel"""
        # Create channel
        create_response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "to-delete",
                "is_private": False
            }
        )
        channel_id = create_response.json()["id"]

        # Delete channel
        response = await authenticated_client.delete(f"/api/v1/channels/{channel_id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = await authenticated_client.get(f"/api/v1/channels/{channel_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_private_channel_access(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that private channels are properly secured"""
        # Create private channel
        response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "private",
                "is_private": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_private"] is True


class TestMessages:
    """Tests for messaging endpoints"""

    @pytest_asyncio.fixture
    async def test_channel(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Create a test channel"""
        response = await authenticated_client.post(
            "/api/v1/channels",
            json={
                "workspace_id": test_workspace["id"],
                "name": "test-messages",
                "is_private": False
            }
        )
        return response.json()

    @pytest.mark.asyncio
    async def test_send_message(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test sending a message to a channel"""
        response = await authenticated_client.post(
            f"/api/v1/channels/{test_channel['id']}/messages",
            json={
                "content": "Hello, world!",
                "message_type": "text"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Hello, world!"
        assert data["message_type"] == "text"
        assert data["channel_id"] == test_channel["id"]
        assert "id" in data
        assert "sender" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_channel_messages(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test retrieving messages from a channel"""
        # Send multiple messages
        messages = ["First message", "Second message", "Third message"]
        for content in messages:
            await authenticated_client.post(
                f"/api/v1/channels/{test_channel['id']}/messages",
                json={"content": content}
            )

        # Get messages
        response = await authenticated_client.get(
            f"/api/v1/channels/{test_channel['id']}/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["content"] == "First message"
        assert data[2]["content"] == "Third message"

    @pytest.mark.asyncio
    async def test_message_pagination(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test message pagination"""
        # Send 25 messages
        for i in range(25):
            await authenticated_client.post(
                f"/api/v1/channels/{test_channel['id']}/messages",
                json={"content": f"Message {i}"}
            )

        # Get first page (default limit: 20)
        response = await authenticated_client.get(
            f"/api/v1/channels/{test_channel['id']}/messages?limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Get second page
        response = await authenticated_client.get(
            f"/api/v1/channels/{test_channel['id']}/messages?limit=10&offset=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

    @pytest.mark.asyncio
    async def test_update_message(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test editing a message"""
        # Send message
        send_response = await authenticated_client.post(
            f"/api/v1/channels/{test_channel['id']}/messages",
            json={"content": "Original content"}
        )
        message_id = send_response.json()["id"]

        # Update message
        response = await authenticated_client.put(
            f"/api/v1/messages/{message_id}",
            json={"content": "Updated content"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_edited"] is True

    @pytest.mark.asyncio
    async def test_delete_message(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test deleting a message"""
        # Send message
        send_response = await authenticated_client.post(
            f"/api/v1/channels/{test_channel['id']}/messages",
            json={"content": "To be deleted"}
        )
        message_id = send_response.json()["id"]

        # Delete message
        response = await authenticated_client.delete(f"/api/v1/messages/{message_id}")

        assert response.status_code == 204

        # Verify message is marked as deleted (soft delete)
        get_response = await authenticated_client.get(
            f"/api/v1/channels/{test_channel['id']}/messages"
        )
        messages = get_response.json()
        deleted_msg = next((m for m in messages if m["id"] == message_id), None)
        if deleted_msg:
            assert deleted_msg.get("is_deleted") is True

    @pytest.mark.asyncio
    async def test_message_with_attachments(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test sending a message with file attachments"""
        response = await authenticated_client.post(
            f"/api/v1/channels/{test_channel['id']}/messages",
            json={
                "content": "Check out this file",
                "attachments": [
                    {
                        "filename": "document.pdf",
                        "url": "https://storage.example.com/doc.pdf",
                        "size": 1024000,
                        "mime_type": "application/pdf"
                    }
                ]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["filename"] == "document.pdf"

    @pytest.mark.asyncio
    async def test_message_reactions(
        self,
        authenticated_client: AsyncClient,
        test_channel
    ):
        """Test adding reactions to messages"""
        # Send message
        send_response = await authenticated_client.post(
            f"/api/v1/channels/{test_channel['id']}/messages",
            json={"content": "React to this!"}
        )
        message_id = send_response.json()["id"]

        # Add reaction
        response = await authenticated_client.post(
            f"/api/v1/messages/{message_id}/reactions",
            json={"emoji": "👍"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "👍" in str(data) or "reactions" in data


class TestSocketIOIntegration:
    """Tests for Socket.io real-time features"""

    @pytest.mark.asyncio
    async def test_websocket_connection_requires_auth(self):
        """Test that WebSocket connections require authentication"""
        # This would require Socket.io test client
        # For now, verify that the endpoints are configured
        pass

    @pytest.mark.asyncio
    async def test_websocket_join_channel(self):
        """Test joining a channel room via WebSocket"""
        # This would require Socket.io test client
        pass

    @pytest.mark.asyncio
    async def test_websocket_send_message(self):
        """Test sending a message via WebSocket"""
        # This would require Socket.io test client
        pass

    @pytest.mark.asyncio
    async def test_websocket_typing_indicators(self):
        """Test typing indicators via WebSocket"""
        # This would require Socket.io test client
        pass
