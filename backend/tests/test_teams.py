"""
Tests for Team Management
Tests team creation, member management, and RBAC permissions
"""

import pytest
from httpx import AsyncClient


class TestTeamCreation:
    """Tests for team creation"""

    @pytest.mark.asyncio
    async def test_create_team_as_workspace_owner(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a team as workspace owner"""
        team_data = {
            "workspace_id": test_workspace["id"],
            "name": "Engineering Team",
            "description": "Software development team"
        }

        response = await authenticated_client.post(
            "/api/v1/teams",
            json=team_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == team_data["name"]
        assert data["description"] == team_data["description"]
        assert data["workspace_id"] == test_workspace["id"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_team_as_workspace_member_fails(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test that regular members cannot create teams"""
        # Create and login as a new user
        user2_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Team Member"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Try to create team (should fail - not even a workspace member)
        team_data = {
            "workspace_id": test_workspace["id"],
            "name": "Test Team",
        }

        response = await client.post(
            "/api/v1/teams",
            json=team_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_team_without_workspace_access(
        self,
        authenticated_client: AsyncClient
    ):
        """Test creating team in nonexistent workspace fails"""
        team_data = {
            "workspace_id": 99999,
            "name": "Test Team"
        }

        response = await authenticated_client.post(
            "/api/v1/teams",
            json=team_data
        )

        assert response.status_code == 403


class TestListTeams:
    """Tests for listing teams"""

    @pytest.mark.asyncio
    async def test_list_workspace_teams(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test listing all teams in a workspace"""
        # Create multiple teams
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/teams",
                json={
                    "workspace_id": test_workspace["id"],
                    "name": f"Team {i+1}",
                    "description": f"Description {i+1}"
                }
            )

        # List teams
        response = await authenticated_client.get(
            f"/api/v1/teams/workspace/{test_workspace['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["teams"]) == 3

    @pytest.mark.asyncio
    async def test_list_teams_without_workspace_access(
        self,
        client: AsyncClient,
        test_workspace
    ):
        """Test that non-members cannot list workspace teams"""
        # Create and login as a new user
        user2_data = {
            "email": "outsider@example.com",
            "password": "SecurePass123!",
            "full_name": "Outsider"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Try to list teams
        response = await client.get(
            f"/api/v1/teams/workspace/{test_workspace['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403


class TestTeamOperations:
    """Tests for team CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_team_details(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting team details with members"""
        # Create team
        team_response = await authenticated_client.post(
            "/api/v1/teams",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Team",
                "description": "Test Description"
            }
        )
        team = team_response.json()

        # Get team details
        response = await authenticated_client.get(f"/api/v1/teams/{team['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == team["id"]
        assert data["name"] == team["name"]
        assert data["description"] == team["description"]
        assert "members" in data
        assert isinstance(data["members"], list)

    @pytest.mark.asyncio
    async def test_update_team_as_owner(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating team as workspace owner"""
        # Create team
        team_response = await authenticated_client.post(
            "/api/v1/teams",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Original Name"
            }
        )
        team = team_response.json()

        # Update team
        response = await authenticated_client.put(
            f"/api/v1/teams/{team['id']}",
            json={
                "name": "Updated Name",
                "description": "New description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_team_as_owner(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting team as workspace owner"""
        # Create team
        team_response = await authenticated_client.post(
            "/api/v1/teams",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Team to Delete"
            }
        )
        team = team_response.json()

        # Delete team
        response = await authenticated_client.delete(f"/api/v1/teams/{team['id']}")

        assert response.status_code == 204

        # Verify team is deleted
        get_response = await authenticated_client.get(f"/api/v1/teams/{team['id']}")
        assert get_response.status_code == 404


class TestTeamMemberManagement:
    """Tests for team member operations"""

    @pytest.mark.asyncio
    async def test_add_member_to_team(
        self,
        authenticated_client: AsyncClient
    ):
        """Test adding a member to a team"""
        # Create workspace
        ws_response = await authenticated_client.post(
            "/api/v1/workspaces",
            json={"name": "Test Workspace", "slug": "test-ws-member"}
        )
        workspace = ws_response.json()

        # Register a second user using the authenticated client but without re-authenticating
        # We'll use authenticated_client for all operations
        user2_email = "teammember@example.com"
        user2_response = await authenticated_client.post(
            "/api/v1/auth/register",
            json={
                "email": user2_email,
                "password": "SecurePass123!",
                "full_name": "Team Member"
            }
        )
        user2 = user2_response.json()

        # Add user2 to workspace
        add_ws_response = await authenticated_client.post(
            f"/api/v1/workspaces/{workspace['id']}/members",
            json={"email": user2_email, "role": "member"}
        )

        # Create team
        team_response = await authenticated_client.post(
            "/api/v1/teams",
            json={
                "workspace_id": workspace["id"],
                "name": "Test Team"
            }
        )
        team = team_response.json()

        # Add user2 to team
        response = await authenticated_client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user2["id"]
        assert data["team_id"] == team["id"]
        assert data["role"] == "member"

    @pytest.mark.asyncio
    async def test_add_non_workspace_member_to_team_fails(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test that only workspace members can be added to teams"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create a second user but DON'T add to workspace
        user2_data = {
            "email": "outsider@example.com",
            "password": "SecurePass123!",
            "full_name": "Outsider"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        # Create team
        team_response = await client.post(
            "/api/v1/teams",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Team"
            },
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        # Try to add user2 to team (should fail)
        response = await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 400
        assert "workspace member" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_team_member_role(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test updating a team member's role"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create user2 and add to workspace
        user2_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Member"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        await client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Create team and add member
        team_response = await client.post(
            "/api/v1/teams",
            json={"workspace_id": test_workspace["id"], "name": "Test Team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Update role to lead
        response = await client.put(
            f"/api/v1/teams/{team['id']}/members/{user2['id']}",
            json={"role": "lead"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "lead"

    @pytest.mark.asyncio
    async def test_remove_team_member(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test removing a member from a team"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create user2 and add to workspace
        user2_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Member"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        await client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Create team and add member
        team_response = await client.post(
            "/api/v1/teams",
            json={"workspace_id": test_workspace["id"], "name": "Test Team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Remove member
        response = await client.delete(
            f"/api/v1/teams/{team['id']}/members/{user2['id']}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_user_can_remove_themselves_from_team(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test that users can remove themselves from a team"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create user2 and add to workspace
        user2_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Member"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        await client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Login as user2
        user2_login = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        user2_token = user2_login.json()["access_token"]

        # Create team and add user2
        team_response = await client.post(
            "/api/v1/teams",
            json={"workspace_id": test_workspace["id"], "name": "Test Team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # User2 removes themselves
        response = await client.delete(
            f"/api/v1/teams/{team['id']}/members/{user2['id']}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert response.status_code == 204


class TestRBACPermissions:
    """Tests for RBAC enforcement"""

    @pytest.mark.asyncio
    async def test_team_lead_can_manage_team(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test that team leads can manage their team"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create user2 and add to workspace
        user2_data = {
            "email": "lead@example.com",
            "password": "SecurePass123!",
            "full_name": "Team Lead"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        await client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Login as user2
        user2_login = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        user2_token = user2_login.json()["access_token"]

        # Create team and add user2 as lead
        team_response = await client.post(
            "/api/v1/teams",
            json={"workspace_id": test_workspace["id"], "name": "Test Team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "lead"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Team lead should be able to update team
        response = await client.put(
            f"/api/v1/teams/{team['id']}",
            json={"name": "Updated by Lead"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_team_member_cannot_manage_team(
        self,
        client: AsyncClient,
        test_user_data,
        test_workspace
    ):
        """Test that regular team members cannot manage the team"""
        # Login as workspace owner
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        owner_token = login_response.json()["access_token"]

        # Create user2 and add to workspace
        user2_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Member"
        }
        user2_response = await client.post("/api/v1/auth/register", json=user2_data)
        user2 = user2_response.json()

        await client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Login as user2
        user2_login = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        user2_token = user2_login.json()["access_token"]

        # Create team and add user2 as regular member
        team_response = await client.post(
            "/api/v1/teams",
            json={"workspace_id": test_workspace["id"], "name": "Test Team"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        team = team_response.json()

        await client.post(
            f"/api/v1/teams/{team['id']}/members",
            json={"user_id": user2["id"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        # Regular member should NOT be able to update team
        response = await client.put(
            f"/api/v1/teams/{team['id']}",
            json={"name": "Should Fail"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert response.status_code == 403
