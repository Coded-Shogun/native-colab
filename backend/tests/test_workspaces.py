"""
Workspace Management Tests
Comprehensive tests for workspaces, members, and RBAC
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User, Workspace, WorkspaceMember


@pytest.fixture
async def workspace_owner_data():
    """Test data for workspace owner"""
    return {
        "email": "owner@example.com",
        "password": "OwnerPass123!",
        "full_name": "Workspace Owner"
    }


@pytest.fixture
async def workspace_admin_data():
    """Test data for workspace admin"""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Workspace Admin"
    }


@pytest.fixture
async def workspace_member_data():
    """Test data for workspace member"""
    return {
        "email": "member@example.com",
        "password": "MemberPass123!",
        "full_name": "Workspace Member"
    }


class TestWorkspaceCreation:
    """Tests for creating workspaces"""

    @pytest.mark.asyncio
    async def test_create_workspace(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test creating a workspace"""
        workspace_data = {
            "name": "Test Workspace",
            "slug": "test-workspace",
            "description": "A test workspace"
        }

        response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json=workspace_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workspace"
        assert data["slug"] == "test-workspace"
        assert data["description"] == "A test workspace"
        assert "id" in data
        assert "owner_id" in data

    @pytest.mark.asyncio
    async def test_create_workspace_duplicate_slug(
        self,
        authenticated_client: AsyncClient
    ):
        """Test creating workspace with duplicate slug fails"""
        workspace_data = {
            "name": "Test Workspace 1",
            "slug": "test-workspace",
            "description": "First workspace"
        }

        # Create first workspace
        await authenticated_client.post("/api/v1/workspaces/", json=workspace_data)

        # Try to create second with same slug
        workspace_data2 = {
            "name": "Test Workspace 2",
            "slug": "test-workspace",  # Same slug
            "description": "Second workspace"
        }

        response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json=workspace_data2
        )

        assert response.status_code == 400
        assert "slug" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_creator_becomes_owner(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user_data
    ):
        """Test that workspace creator automatically becomes owner"""
        workspace_data = {
            "name": "My Workspace",
            "slug": "my-workspace"
        }

        response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json=workspace_data
        )

        workspace_id = response.json()["id"]

        # Check membership
        result = await db_session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        membership = result.scalar_one_or_none()

        assert membership is not None
        assert membership.role == "owner"


class TestListWorkspaces:
    """Tests for listing workspaces"""

    @pytest.mark.asyncio
    async def test_list_my_workspaces(
        self,
        authenticated_client: AsyncClient
    ):
        """Test listing user's workspaces"""
        # Create workspaces
        await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "Workspace 1", "slug": "workspace-1"}
        )
        await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "Workspace 2", "slug": "workspace-2"}
        )

        # List workspaces
        response = await authenticated_client.get("/api/v1/workspaces/")

        assert response.status_code == 200
        workspaces = response.json()
        assert len(workspaces) >= 2

    @pytest.mark.asyncio
    async def test_only_see_member_workspaces(
        self,
        client: AsyncClient
    ):
        """Test users only see workspaces they're members of"""
        # Create user 1
        user1_data = {
            "email": "user1@example.com",
            "password": "User1Pass123!",
            "full_name": "User 1"
        }
        await client.post("/api/v1/auth/register", json=user1_data)
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]}
        )
        token1 = login1.json()["access_token"]

        # Create user 2
        user2_data = {
            "email": "user2@example.com",
            "password": "User2Pass123!",
            "full_name": "User 2"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        # User 1 creates workspace
        await client.post(
            "/api/v1/workspaces/",
            json={"name": "User 1 Workspace", "slug": "user1-workspace"},
            headers={"Authorization": f"Bearer {token1}"}
        )

        # User 2 shouldn't see user 1's workspace
        response = await client.get(
            "/api/v1/workspaces/",
            headers={"Authorization": f"Bearer {token2}"}
        )

        workspaces = response.json()
        assert len(workspaces) == 0


class TestWorkspaceOperations:
    """Tests for workspace operations"""

    @pytest.mark.asyncio
    async def test_get_workspace_details(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting workspace details"""
        # Create workspace
        create_response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace", "slug": "test-workspace"}
        )
        workspace_id = create_response.json()["id"]

        # Get workspace
        response = await authenticated_client.get(
            f"/api/v1/workspaces/{workspace_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workspace_id
        assert "members" in data

    @pytest.mark.asyncio
    async def test_update_workspace_as_owner(
        self,
        authenticated_client: AsyncClient
    ):
        """Test updating workspace as owner"""
        # Create workspace
        create_response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "Original Name", "slug": "original-slug"}
        )
        workspace_id = create_response.json()["id"]

        # Update workspace
        update_response = await authenticated_client.put(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Updated Name", "description": "New description"}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_workspace_as_owner(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test deleting workspace as owner"""
        # Create workspace
        create_response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "To Delete", "slug": "to-delete"}
        )
        workspace_id = create_response.json()["id"]

        # Delete workspace
        delete_response = await authenticated_client.delete(
            f"/api/v1/workspaces/{workspace_id}"
        )

        assert delete_response.status_code == 204

        # Verify workspace is deactivated
        result = await db_session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        assert workspace is not None
        assert workspace.is_active is False


class TestWorkspaceMemberManagement:
    """Tests for managing workspace members"""

    @pytest.mark.asyncio
    async def test_invite_member_to_workspace(
        self,
        client: AsyncClient
    ):
        """Test inviting a member to workspace"""
        # Create owner
        owner_data = {
            "email": "owner@example.com",
            "password": "OwnerPass123!",
            "full_name": "Owner"
        }
        await client.post("/api/v1/auth/register", json=owner_data)
        owner_login = await client.post(
            "/api/v1/auth/login",
            data={"username": owner_data["email"], "password": owner_data["password"]}
        )
        owner_token = owner_login.json()["access_token"]

        # Create member
        member_data = {
            "email": "member@example.com",
            "password": "MemberPass123!",
            "full_name": "Member"
        }
        await client.post("/api/v1/auth/register", json=member_data)

        # Owner creates workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Team Workspace", "slug": "team-workspace"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        workspace_id = workspace_response.json()["id"]

        # Owner invites member
        invite_response = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": member_data["email"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert invite_response.status_code == 201
        data = invite_response.json()
        assert data["role"] == "member"
        assert data["user"]["email"] == member_data["email"]

    @pytest.mark.asyncio
    async def test_list_workspace_members(
        self,
        client: AsyncClient
    ):
        """Test listing workspace members"""
        # Setup
        owner_data = {
            "email": "owner@example.com",
            "password": "OwnerPass123!",
            "full_name": "Owner"
        }
        await client.post("/api/v1/auth/register", json=owner_data)
        owner_login = await client.post(
            "/api/v1/auth/login",
            data={"username": owner_data["email"], "password": owner_data["password"]}
        )
        owner_token = owner_login.json()["access_token"]

        # Create workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Team", "slug": "team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        workspace_id = workspace_response.json()["id"]

        # List members
        members_response = await client.get(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert members_response.status_code == 200
        members = members_response.json()
        assert len(members) >= 1  # At least the owner

    @pytest.mark.asyncio
    async def test_remove_member_from_workspace(
        self,
        client: AsyncClient
    ):
        """Test removing a member from workspace"""
        # Setup owner and workspace
        owner_data = {
            "email": "owner@example.com",
            "password": "OwnerPass123!",
            "full_name": "Owner"
        }
        await client.post("/api/v1/auth/register", json=owner_data)
        owner_login = await client.post(
            "/api/v1/auth/login",
            data={"username": owner_data["email"], "password": owner_data["password"]}
        )
        owner_token = owner_login.json()["access_token"]

        # Create member
        member_data = {
            "email": "member@example.com",
            "password": "MemberPass123!",
            "full_name": "Member"
        }
        member_response = await client.post("/api/v1/auth/register", json=member_data)
        member_id = member_response.json()["id"]

        # Create workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Team", "slug": "team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        workspace_id = workspace_response.json()["id"]

        # Invite member
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": member_data["email"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Remove member
        remove_response = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert remove_response.status_code == 204


class TestRBACPermissions:
    """Tests for Role-Based Access Control"""

    @pytest.mark.asyncio
    async def test_member_cannot_update_workspace(
        self,
        client: AsyncClient
    ):
        """Test that regular members cannot update workspace"""
        # Setup owner
        owner_data = {
            "email": "owner@example.com",
            "password": "OwnerPass123!",
            "full_name": "Owner"
        }
        await client.post("/api/v1/auth/register", json=owner_data)
        owner_login = await client.post(
            "/api/v1/auth/login",
            data={"username": owner_data["email"], "password": owner_data["password"]}
        )
        owner_token = owner_login.json()["access_token"]

        # Setup member
        member_data = {
            "email": "member@example.com",
            "password": "MemberPass123!",
            "full_name": "Member"
        }
        await client.post("/api/v1/auth/register", json=member_data)
        member_login = await client.post(
            "/api/v1/auth/login",
            data={"username": member_data["email"], "password": member_data["password"]}
        )
        member_token = member_login.json()["access_token"]

        # Create workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Team", "slug": "team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        workspace_id = workspace_response.json()["id"]

        # Invite member
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": member_data["email"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Member tries to update workspace
        update_response = await client.put(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Hacked Name"},
            headers={"Authorization": f"Bearer {member_token}"}
        )

        assert update_response.status_code == 403

    @pytest.mark.asyncio
    async def test_member_cannot_invite_others(
        self,
        client: AsyncClient
    ):
        """Test that regular members cannot invite others"""
        # Setup owner
        owner_data = {
            "email": "owner@example.com",
            "password": "OwnerPass123!",
            "full_name": "Owner"
        }
        await client.post("/api/v1/auth/register", json=owner_data)
        owner_login = await client.post(
            "/api/v1/auth/login",
            data={"username": owner_data["email"], "password": owner_data["password"]}
        )
        owner_token = owner_login.json()["access_token"]

        # Setup member
        member_data = {
            "email": "member@example.com",
            "password": "MemberPass123!",
            "full_name": "Member"
        }
        await client.post("/api/v1/auth/register", json=member_data)
        member_login = await client.post(
            "/api/v1/auth/login",
            data={"username": member_data["email"], "password": member_data["password"]}
        )
        member_token = member_login.json()["access_token"]

        # Setup another user to invite
        user3_data = {
            "email": "user3@example.com",
            "password": "User3Pass123!",
            "full_name": "User 3"
        }
        await client.post("/api/v1/auth/register", json=user3_data)

        # Create workspace
        workspace_response = await client.post(
            "/api/v1/workspaces/",
            json={"name": "Team", "slug": "team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        workspace_id = workspace_response.json()["id"]

        # Invite member
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": member_data["email"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Member tries to invite someone
        invite_response = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": user3_data["email"], "role": "member"},
            headers={"Authorization": f"Bearer {member_token}"}
        )

        assert invite_response.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_remove_last_owner(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that the last owner cannot be removed"""
        # Create workspace
        workspace_response = await authenticated_client.post(
            "/api/v1/workspaces/",
            json={"name": "Team", "slug": "team"}
        )
        workspace_id = workspace_response.json()["id"]

        # Get own user ID
        me_response = await authenticated_client.get("/api/v1/users/me")
        user_id = me_response.json()["id"]

        # Try to remove self (last owner)
        remove_response = await authenticated_client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/{user_id}"
        )

        assert remove_response.status_code == 400
        assert "last owner" in remove_response.json()["detail"].lower()
