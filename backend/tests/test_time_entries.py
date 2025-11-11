"""
Tests for Time Tracking
Tests timer-based and manual time entry creation, updates, filtering, and statistics
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from decimal import Decimal


class TestTimerTracking:
    """Tests for timer-based time tracking"""

    @pytest.mark.asyncio
    async def test_start_timer(
        self,
        authenticated_client: AsyncClient,
        test_workspace,
        test_project
    ):
        """Test starting a timer"""
        timer_data = {
            "workspace_id": test_workspace["id"],
            "project_id": test_project["id"],
            "description": "Working on feature",
            "is_billable": True
        }

        response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json=timer_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workspace_id"] == test_workspace["id"]
        assert data["project_id"] == test_project["id"]
        assert data["description"] == "Working on feature"
        assert data["is_billable"] is True
        assert data["is_manual"] is False
        assert data["is_running"] is True
        assert data["end_time"] is None
        assert "start_time" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_start_timer_without_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test starting a timer without a project"""
        timer_data = {
            "workspace_id": test_workspace["id"],
            "description": "General work",
            "is_billable": False
        }

        response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json=timer_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] is None
        assert data["task_id"] is None
        assert data["is_running"] is True

    @pytest.mark.asyncio
    async def test_cannot_start_multiple_timers(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that only one timer can run at a time"""
        # Start first timer
        timer_data = {
            "workspace_id": test_workspace["id"],
            "description": "First timer"
        }

        response1 = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json=timer_data
        )
        assert response1.status_code == 201

        # Try to start second timer
        response2 = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json=timer_data
        )
        assert response2.status_code == 400
        assert "already have a running timer" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_stop_timer(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test stopping a running timer"""
        # Start timer
        start_response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json={
                "workspace_id": test_workspace["id"],
                "description": "Initial description"
            }
        )
        timer = start_response.json()

        # Stop timer with updated description
        stop_response = await authenticated_client.put(
            f"/api/v1/time-entries/{timer['id']}/stop",
            json={"description": "Completed task"}
        )

        assert stop_response.status_code == 200
        data = stop_response.json()
        assert data["is_running"] is False
        assert data["end_time"] is not None
        assert data["duration_minutes"] is not None
        assert float(data["duration_minutes"]) >= 0  # In tests, duration may be 0 due to quick execution
        assert data["description"] == "Completed task"

    @pytest.mark.asyncio
    async def test_cannot_stop_already_stopped_timer(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that cannot stop an already stopped timer"""
        # Start and stop timer
        start_response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json={"workspace_id": test_workspace["id"]}
        )
        timer = start_response.json()

        await authenticated_client.put(
            f"/api/v1/time-entries/{timer['id']}/stop",
            json={}
        )

        # Try to stop again
        response = await authenticated_client.put(
            f"/api/v1/time-entries/{timer['id']}/stop",
            json={}
        )

        assert response.status_code == 400
        assert "not running" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_timer(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting the currently running timer"""
        # No timer running
        response1 = await authenticated_client.get("/api/v1/time-entries/current")
        assert response1.status_code == 200
        assert response1.json() is None

        # Start timer
        start_response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json={"workspace_id": test_workspace["id"]}
        )
        timer = start_response.json()

        # Get current timer
        response2 = await authenticated_client.get("/api/v1/time-entries/current")
        assert response2.status_code == 200
        data = response2.json()
        assert data["id"] == timer["id"]
        assert data["is_running"] is True


class TestManualTimeEntry:
    """Tests for manual time entry creation"""

    @pytest.mark.asyncio
    async def test_create_manual_entry(
        self,
        authenticated_client: AsyncClient,
        test_workspace,
        test_project
    ):
        """Test creating a manual time entry"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()

        entry_data = {
            "workspace_id": test_workspace["id"],
            "project_id": test_project["id"],
            "description": "Manual entry for yesterday",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "is_billable": True
        }

        response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json=entry_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_manual"] is True
        assert data["is_running"] is False
        assert data["duration_minutes"] is not None
        assert float(data["duration_minutes"]) > 0
        assert data["is_billable"] is True

    @pytest.mark.asyncio
    async def test_manual_entry_validates_time_order(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that manual entry validates end_time > start_time"""
        start_time = datetime.utcnow()
        end_time = start_time - timedelta(hours=1)  # End before start

        entry_data = {
            "workspace_id": test_workspace["id"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

        response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json=entry_data
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_manual_entry_with_task(
        self,
        authenticated_client: AsyncClient,
        test_workspace,
        test_project
    ):
        """Test creating manual entry for a specific task"""
        # Create task first
        task_response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project["id"],
                "title": "Task to track time on"
            }
        )
        task = task_response.json()

        # Create time entry for the task
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        entry_data = {
            "workspace_id": test_workspace["id"],
            "project_id": test_project["id"],
            "task_id": task["id"],
            "description": "Time on specific task",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

        response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json=entry_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == task["id"]
        assert data["task_title"] == task["title"]


class TestListTimeEntries:
    """Tests for listing and filtering time entries"""

    @pytest.mark.asyncio
    async def test_list_time_entries(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test listing time entries in a workspace"""
        # Create multiple entries
        for i in range(3):
            start_time = datetime.utcnow() - timedelta(hours=i+1)
            end_time = datetime.utcnow() - timedelta(hours=i)

            await authenticated_client.post(
                "/api/v1/time-entries/manual",
                json={
                    "workspace_id": test_workspace["id"],
                    "description": f"Entry {i+1}",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )

        # List entries
        response = await authenticated_client.get(
            f"/api/v1/time-entries?workspace_id={test_workspace['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert "total_duration_minutes" in data
        assert data["total"] >= 3
        assert len(data["entries"]) >= 3
        assert float(data["total_duration_minutes"]) > 0

    @pytest.mark.asyncio
    async def test_filter_by_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace,
        test_project
    ):
        """Test filtering time entries by project"""
        # Create entry with project
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "project_id": test_project["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )

        # Create entry without project
        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )

        # Filter by project
        response = await authenticated_client.get(
            f"/api/v1/time-entries?workspace_id={test_workspace['id']}&project_id={test_project['id']}"
        )

        data = response.json()
        assert data["total"] >= 1
        for entry in data["entries"]:
            assert entry["project_id"] == test_project["id"]

    @pytest.mark.asyncio
    async def test_filter_by_billable(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test filtering by billable status"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Create billable entry
        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_billable": True
            }
        )

        # Create non-billable entry
        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_billable": False
            }
        )

        # Filter billable only
        response = await authenticated_client.get(
            f"/api/v1/time-entries?workspace_id={test_workspace['id']}&is_billable=true"
        )

        data = response.json()
        assert data["total"] >= 1
        for entry in data["entries"]:
            assert entry["is_billable"] is True

    @pytest.mark.asyncio
    async def test_filter_by_date_range(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test filtering time entries by date range"""
        # Create entry from yesterday
        yesterday_start = datetime.utcnow() - timedelta(days=1, hours=1)
        yesterday_end = datetime.utcnow() - timedelta(days=1)

        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": yesterday_start.isoformat(),
                "end_time": yesterday_end.isoformat()
            }
        )

        # Create entry from today
        today_start = datetime.utcnow() - timedelta(hours=1)
        today_end = datetime.utcnow()

        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": today_start.isoformat(),
                "end_time": today_end.isoformat()
            }
        )

        # Filter for today only
        today_midnight = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        response = await authenticated_client.get(
            f"/api/v1/time-entries?workspace_id={test_workspace['id']}&start_date={today_midnight.isoformat()}"
        )

        data = response.json()
        # Should only get today's entry
        assert data["total"] >= 1


class TestTimeEntryOperations:
    """Tests for time entry CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_time_entry_details(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting details of a specific time entry"""
        # Create entry
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        create_response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "description": "Test entry",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        entry = create_response.json()

        # Get entry details
        response = await authenticated_client.get(
            f"/api/v1/time-entries/{entry['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry["id"]
        assert data["description"] == "Test entry"

    @pytest.mark.asyncio
    async def test_update_time_entry(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test updating a time entry"""
        # Create entry
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow() - timedelta(hours=1)

        create_response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "description": "Original description",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_billable": False
            }
        )
        entry = create_response.json()

        # Update entry
        response = await authenticated_client.put(
            f"/api/v1/time-entries/{entry['id']}",
            json={
                "description": "Updated description",
                "is_billable": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["is_billable"] is True

    @pytest.mark.asyncio
    async def test_cannot_update_running_timer(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test that cannot update a running timer"""
        # Start timer
        start_response = await authenticated_client.post(
            "/api/v1/time-entries/start",
            json={"workspace_id": test_workspace["id"]}
        )
        timer = start_response.json()

        # Try to update running timer
        response = await authenticated_client.put(
            f"/api/v1/time-entries/{timer['id']}",
            json={"description": "Updated"}
        )

        assert response.status_code == 400
        assert "running timer" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_time_entry(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test deleting a time entry"""
        # Create entry
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        create_response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        entry = create_response.json()

        # Delete entry
        delete_response = await authenticated_client.delete(
            f"/api/v1/time-entries/{entry['id']}"
        )

        assert delete_response.status_code == 204

        # Verify deleted
        get_response = await authenticated_client.get(
            f"/api/v1/time-entries/{entry['id']}"
        )
        assert get_response.status_code == 404


class TestTimeSummary:
    """Tests for time tracking statistics and summaries"""

    @pytest.mark.asyncio
    async def test_get_time_summary(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test getting time tracking summary"""
        # Create multiple entries
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow() - timedelta(hours=1)

        # Billable entry
        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_billable": True
            }
        )

        # Non-billable entry
        await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_billable": False
            }
        )

        # Get summary
        response = await authenticated_client.get(
            f"/api/v1/time-entries/summary/stats?workspace_id={test_workspace['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert "total_duration_minutes" in data
        assert "billable_duration_minutes" in data
        assert "non_billable_duration_minutes" in data
        assert data["total_entries"] >= 2
        assert float(data["total_duration_minutes"]) > 0
        assert float(data["billable_duration_minutes"]) > 0
        assert float(data["non_billable_duration_minutes"]) > 0

    @pytest.mark.asyncio
    async def test_summary_by_project(
        self,
        authenticated_client: AsyncClient,
        test_workspace,
        test_project
    ):
        """Test getting summary filtered by project"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Create entries for project
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/time-entries/manual",
                json={
                    "workspace_id": test_workspace["id"],
                    "project_id": test_project["id"],
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )

        # Get summary for project
        response = await authenticated_client.get(
            f"/api/v1/time-entries/summary/stats?workspace_id={test_workspace['id']}&project_id={test_project['id']}"
        )

        data = response.json()
        assert data["total_entries"] >= 3
        assert data["project_id"] == test_project["id"]


class TestTimeEntryRBAC:
    """Tests for time entry RBAC enforcement"""

    @pytest.mark.asyncio
    async def test_cannot_access_other_workspace_entries(
        self,
        client: AsyncClient
    ):
        """Test that cannot access time entries from other workspaces"""
        # Create first user with workspace
        user1_data = {
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "full_name": "User One"
        }
        await client.post("/api/v1/auth/register", json=user1_data)
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]}
        )
        token1 = login1.json()["access_token"]

        # Create workspace and time entry
        ws_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace 1", "slug": "ws1"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        workspace = ws_response.json()

        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        entry_response = await client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        entry = entry_response.json()

        # Create second user
        user2_data = {
            "email": "user2@example.com",
            "password": "SecurePass123!",
            "full_name": "User Two"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        # Try to access entry from different user
        response = await client.get(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_can_only_update_own_entries(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient,
        test_workspace
    ):
        """Test that users can only update their own time entries"""
        # User 1 creates entry
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        entry_response = await authenticated_client.post(
            "/api/v1/time-entries/manual",
            json={
                "workspace_id": test_workspace["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        entry = entry_response.json()

        # Add user 2 to workspace
        user2_data = {
            "email": "member2@example.com",
            "password": "SecurePass123!",
            "full_name": "Member Two"
        }
        await client.post("/api/v1/auth/register", json=user2_data)

        # Add user 2 to workspace
        await authenticated_client.post(
            f"/api/v1/workspaces/{test_workspace['id']}/members",
            json={"email": user2_data["email"], "role": "member"}
        )

        # Login as user 2
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]}
        )
        token2 = login2.json()["access_token"]

        # Try to update user 1's entry
        response = await client.put(
            f"/api/v1/time-entries/{entry['id']}",
            json={"description": "Trying to update"},
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403
        assert "only update your own" in response.json()["detail"]
