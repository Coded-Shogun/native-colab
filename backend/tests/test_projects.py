"""
Tests for Project Management
Tests project creation, updates, filtering, and RBAC
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestProjectCreation:
    """Tests for project creation"""

    @pytest.mark.asyncio
    async def test_create_project_in_workspace(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a project in a workspace"""
        project_data = {
            "workspace_id": test_workspace["id"],
            "name": "Website Redesign",
            "description": "Redesign company website",
            "status": "planning",
            "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }

        response = await authenticated_client.post(
            "/api/v1/projects",
            json=project_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["status"] == project_data["status"]
        assert data["workspace_id"] == test_workspace["id"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_project_without_workspace_access_fails(
        self,
        client: AsyncClient
    ):
        """Test that non-members cannot create projects"""
        # Register new user
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

        # Try to create project in workspace they're not a member of
        project_data = {
            "workspace_id": 1,
            "name": "Unauthorized Project"
        }

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_project_with_team(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a project assigned to a team"""
        # Create team first
        team_response = await authenticated_client.post(
            "/api/v1/teams",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Development Team"
            }
        )
        team = team_response.json()

        # Create project with team
        project_data = {
            "workspace_id": test_workspace["id"],
            "team_id": team["id"],
            "name": "Team Project",
            "description": "Project for the dev team"
        }

        response = await authenticated_client.post(
            "/api/v1/projects",
            json=project_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["team_id"] == team["id"]


class TestListProjects:
    """Tests for listing projects"""

    @pytest.mark.asyncio
    async def test_list_workspace_projects(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test listing all projects in a workspace"""
        # Create multiple projects
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/projects",
                json={
                    "workspace_id": test_workspace["id"],
                    "name": f"Project {i+1}",
                    "status": "active"
                }
            )

        # List projects
        response = await authenticated_client.get(
            f"/api/v1/projects/workspace/{test_workspace['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert data["total"] >= 3
        assert len(data["projects"]) >= 3

    @pytest.mark.asyncio
    async def test_list_projects_with_status_filter(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test filtering projects by status"""
        # Create projects with different statuses
        await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Planning Project",
                "status": "planning"
            }
        )
        await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Active Project",
                "status": "active"
            }
        )

        # Filter by status
        response = await authenticated_client.get(
            f"/api/v1/projects/workspace/{test_workspace['id']}?status=active"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for project in data["projects"]:
            assert project["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_projects_excludes_archived_by_default(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that archived projects are excluded by default"""
        # Create and archive a project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Archived Project"
            }
        )
        project = project_response.json()

        await authenticated_client.post(f"/api/v1/projects/{project['id']}/archive")

        # List projects (should not include archived)
        response = await authenticated_client.get(
            f"/api/v1/projects/workspace/{test_workspace['id']}"
        )

        data = response.json()
        archived_project_ids = [p["id"] for p in data["projects"] if p["is_archived"]]
        assert len(archived_project_ids) == 0


class TestProjectOperations:
    """Tests for project CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_project_details(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting project details with statistics"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Get project details
        response = await authenticated_client.get(f"/api/v1/projects/{project['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project["id"]
        assert data["name"] == project["name"]
        assert "task_count" in data
        assert "completed_task_count" in data
        assert data["task_count"] == 0

    @pytest.mark.asyncio
    async def test_update_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating project information"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Original Name",
                "status": "planning"
            }
        )
        project = project_response.json()

        # Update project
        response = await authenticated_client.put(
            f"/api/v1/projects/{project['id']}",
            json={
                "name": "Updated Name",
                "description": "New description",
                "status": "active"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_delete_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting a project"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Project to Delete"
            }
        )
        project = project_response.json()

        # Delete project
        response = await authenticated_client.delete(f"/api/v1/projects/{project['id']}")

        assert response.status_code == 204

        # Verify project is deleted
        get_response = await authenticated_client.get(f"/api/v1/projects/{project['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_and_unarchive_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test archiving and unarchiving a project"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Project to Archive"
            }
        )
        project = project_response.json()

        # Archive project
        archive_response = await authenticated_client.post(
            f"/api/v1/projects/{project['id']}/archive"
        )

        assert archive_response.status_code == 200
        assert archive_response.json()["is_archived"] is True

        # Unarchive project
        unarchive_response = await authenticated_client.post(
            f"/api/v1/projects/{project['id']}/unarchive"
        )

        assert unarchive_response.status_code == 200
        assert unarchive_response.json()["is_archived"] is False


class TestProjectWithTasks:
    """Tests for projects with task statistics"""

    @pytest.mark.asyncio
    async def test_project_task_statistics(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that project shows accurate task statistics"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Project with Tasks"
            }
        )
        project = project_response.json()

        # Create tasks
        for i in range(3):
            status = "done" if i == 0 else "todo"
            await authenticated_client.post(
                "/api/v1/tasks",
                json={
                    "project_id": project["id"],
                    "title": f"Task {i+1}",
                    "status": status
                }
            )

        # Get project details
        response = await authenticated_client.get(f"/api/v1/projects/{project['id']}")

        data = response.json()
        assert data["task_count"] == 3
        assert data["completed_task_count"] == 1


class TestProjectRBAC:
    """Tests for project RBAC enforcement"""

    @pytest.mark.asyncio
    async def test_non_member_cannot_access_project(
        self,
        client: AsyncClient,
        test_workspace
    ):
        """Test that non-workspace members cannot access projects"""
        # Create project as member
        user1_data = {
            "email": "member@example.com",
            "password": "SecurePass123!",
            "full_name": "Member"
        }
        await client.post("/api/v1/auth/register", json=user1_data)
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]}
        )
        token1 = login1.json()["access_token"]

        # Create workspace and project
        ws_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Private Workspace", "slug": "private-ws"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        workspace = ws_response.json()

        project_response = await client.post(
            "/api/v1/projects",
            json={"workspace_id": workspace["id"], "name": "Private Project"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        project = project_response.json()

        # Try to access as non-member
        user2_data = {
            "email": "outsider@example.com",
            "password": "SecurePass123!",
            "full_name": "Outsider"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        response = await client.get(
            f"/api/v1/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403
