"""
Tests for Task Management
Tests task creation, updates, assignments, comments, and RBAC
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestTaskCreation:
    """Tests for task creation"""

    @pytest.mark.asyncio
    async def test_create_task_in_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a task in a project"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Create task
        task_data = {
            "project_id": project["id"],
            "title": "Implement login feature",
            "description": "Add user authentication",
            "status": "todo",
            "priority": "high",
            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }

        response = await authenticated_client.post(
            "/api/v1/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == task_data["status"]
        assert data["priority"] == task_data["priority"]
        assert data["project_id"] == project["id"]
        assert "id" in data
        assert "position" in data

    @pytest.mark.asyncio
    async def test_create_task_with_assignee(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test creating a task with an assignee"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Register and add a second user to workspace
        user2_email = "developer@example.com"
        user2_response = await authenticated_client.post(
            "/api/v1/auth/register",
            json={
                "email": user2_email,
                "password": "SecurePass123!",
                "full_name": "Developer"
            }
        )
        user2 = user2_response.json()

        await authenticated_client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"email": user2_email, "role": "member"}
        )

        # Create task with assignee
        task_data = {
            "project_id": project["id"],
            "title": "Assigned Task",
            "assignee_id": user2["id"]
        }

        response = await authenticated_client.post(
            "/api/v1/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == user2["id"]
        assert data["assignee_email"] == user2_email

    @pytest.mark.asyncio
    async def test_create_task_without_project_access_fails(
        self,
        client: AsyncClient
    ):
        """Test that non-members cannot create tasks"""
        # Register new user
        user_data = {
            "email": "outsider@example.com",
            "password": "SecurePass123!",
            "full_name": "Outsider"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        # Try to create task in project they don't have access to
        task_data = {
            "project_id": 1,
            "title": "Unauthorized Task"
        }

        response = await client.post(
            "/api/v1/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [403, 404]


class TestListTasks:
    """Tests for listing tasks"""

    @pytest.mark.asyncio
    async def test_list_project_tasks(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test listing all tasks in a project"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Create multiple tasks
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/tasks",
                json={
                    "project_id": project["id"],
                    "title": f"Task {i+1}",
                    "priority": "medium"
                }
            )

        # List tasks
        response = await authenticated_client.get(
            f"/api/v1/tasks/project/{project['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["tasks"]) == 3

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test filtering tasks by status"""
        # Create project
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Create tasks with different statuses
        await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Todo Task",
                "status": "todo"
            }
        )
        await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "In Progress Task",
                "status": "in_progress"
            }
        )

        # Filter by status
        response = await authenticated_client.get(
            f"/api/v1/tasks/project/{project['id']}?status=todo"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["status"] == "todo"


class TestTaskOperations:
    """Tests for task CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_task_details_with_comments(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting task details with comments"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task"
            }
        )
        task = task_response.json()

        # Add comment
        await authenticated_client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": "This is a comment"}
        )

        # Get task details
        response = await authenticated_client.get(f"/api/v1/tasks/{task['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task["id"]
        assert "comments" in data
        assert len(data["comments"]) == 1
        assert data["comments"][0]["content"] == "This is a comment"

    @pytest.mark.asyncio
    async def test_update_task(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating task information"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Original Title",
                "status": "todo"
            }
        )
        task = task_response.json()

        # Update task
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task['id']}",
            json={
                "title": "Updated Title",
                "description": "New description",
                "priority": "high"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "New description"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_delete_task(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting a task"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Task to Delete"
            }
        )
        task = task_response.json()

        # Delete task
        response = await authenticated_client.delete(f"/api/v1/tasks/{task['id']}")

        assert response.status_code == 204

        # Verify task is deleted
        get_response = await authenticated_client.get(f"/api/v1/tasks/{task['id']}")
        assert get_response.status_code == 404


class TestTaskStatusAndAssignment:
    """Tests for task status and assignee updates"""

    @pytest.mark.asyncio
    async def test_update_task_status(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating task status"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task",
                "status": "todo"
            }
        )
        task = task_response.json()

        # Update status to done
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": "done"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_task_assignee(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test assigning a task to a user"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task"
            }
        )
        task = task_response.json()

        # Register and add a second user to workspace
        user2_email = "assignee@example.com"
        user2_response = await authenticated_client.post(
            "/api/v1/auth/register",
            json={
                "email": user2_email,
                "password": "SecurePass123!",
                "full_name": "Assignee"
            }
        )
        user2 = user2_response.json()

        await authenticated_client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"email": user2_email, "role": "member"}
        )

        # Assign task
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task['id']}/assignee",
            json={"assignee_id": user2["id"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == user2["id"]
        assert data["assignee_email"] == user2_email

    @pytest.mark.asyncio
    async def test_unassign_task(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test unassigning a task"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        # Register user and assign task
        user2_email = "assignee@example.com"
        user2_response = await authenticated_client.post(
            "/api/v1/auth/register",
            json={
                "email": user2_email,
                "password": "SecurePass123!",
                "full_name": "Assignee"
            }
        )
        user2 = user2_response.json()

        await authenticated_client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"email": user2_email, "role": "member"}
        )

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task",
                "assignee_id": user2["id"]
            }
        )
        task = task_response.json()

        # Unassign task
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task['id']}/assignee",
            json={"assignee_id": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] is None


class TestTaskComments:
    """Tests for task comments"""

    @pytest.mark.asyncio
    async def test_add_comment_to_task(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test adding a comment to a task"""
        # Create project and task
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task"
            }
        )
        task = task_response.json()

        # Add comment
        comment_data = {"content": "This is a test comment"}
        response = await authenticated_client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json=comment_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == comment_data["content"]
        assert data["task_id"] == task["id"]
        assert "author_email" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_update_own_comment(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating your own comment"""
        # Create project, task, and comment
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task"
            }
        )
        task = task_response.json()

        comment_response = await authenticated_client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": "Original comment"}
        )
        comment = comment_response.json()

        # Update comment
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task['id']}/comments/{comment['id']}",
            json={"content": "Updated comment"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated comment"

    @pytest.mark.asyncio
    async def test_delete_own_comment(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting your own comment"""
        # Create project, task, and comment
        project_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace["id"],
                "name": "Test Project"
            }
        )
        project = project_response.json()

        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project["id"],
                "title": "Test Task"
            }
        )
        task = task_response.json()

        comment_response = await authenticated_client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": "Comment to delete"}
        )
        comment = comment_response.json()

        # Delete comment
        response = await authenticated_client.delete(
            f"/api/v1/tasks/{task['id']}/comments/{comment['id']}"
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cannot_update_others_comment(
        self,
        client: AsyncClient
    ):
        """Test that users cannot update other users' comments"""
        # Create workspace, project, task as user1
        user1_data = {
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "full_name": "User 1"
        }
        await client.post("/api/v1/auth/register", json=user1_data)
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]}
        )
        token1 = login1.json()["access_token"]

        ws_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Test Workspace", "slug": "test-ws-comments"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        workspace = ws_response.json()

        project_response = await client.post(
            "/api/v1/projects",
            json={"workspace_id": workspace["id"], "name": "Test Project"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        project = project_response.json()

        task_response = await client.post(
            "/api/v1/tasks",
            json={"project_id": project["id"], "title": "Test Task"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        task = task_response.json()

        comment_response = await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": "User1's comment"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        comment = comment_response.json()

        # Register user2 and add to workspace
        user2_email = "user2@example.com"
        user2_data = {
            "email": user2_email,
            "password": "SecurePass123!",
            "full_name": "User 2"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        await client.post(
            f"/api/v1/workspaces/{workspace['id']}/members",
            json={"email": user2_email, "role": "member"},
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Try to update user1's comment as user2
        response = await client.put(
            f"/api/v1/tasks/{task['id']}/comments/{comment['id']}",
            json={"content": "Trying to update"},
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403
