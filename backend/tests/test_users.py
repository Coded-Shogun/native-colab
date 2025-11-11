"""
User Management Tests
Comprehensive tests for user profile management, password changes, and admin operations
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User, UserRole


class TestUserProfile:
    """Tests for user profile management"""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self,
        authenticated_client: AsyncClient,
        test_user_data
    ):
        """Test getting current user's profile"""
        response = await authenticated_client.get("/api/v1/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user_data
    ):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name",
            "bio": "This is my new bio"
        }

        response = await authenticated_client.put(
            "/api/v1/users/me",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "This is my new bio"
        assert data["email"] == test_user_data["email"]  # Email unchanged

    @pytest.mark.asyncio
    async def test_update_user_avatar(
        self,
        authenticated_client: AsyncClient
    ):
        """Test updating user avatar URL"""
        update_data = {
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = await authenticated_client.put(
            "/api/v1/users/me",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_profile_partial(
        self,
        authenticated_client: AsyncClient
    ):
        """Test updating only some profile fields"""
        update_data = {
            "full_name": "Just Update Name"
        }

        response = await authenticated_client.put(
            "/api/v1/users/me",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Just Update Name"
        # Bio should remain None if not updated
        assert data["bio"] is None or data["bio"] == ""


class TestPasswordChange:
    """Tests for password change functionality"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        authenticated_client: AsyncClient,
        test_user_data,
        db_session: AsyncSession
    ):
        """Test successfully changing password"""
        response = await authenticated_client.put(
            "/api/v1/users/me/password",
            params={
                "current_password": test_user_data["password"],
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 204

        # Verify can login with new password
        login_response = await authenticated_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "NewSecurePass123!"
            }
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self,
        authenticated_client: AsyncClient
    ):
        """Test changing password with wrong current password"""
        response = await authenticated_client.put(
            "/api/v1/users/me/password",
            params={
                "current_password": "WrongPassword123!",
                "new_password": "NewSecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_weak_new(
        self,
        authenticated_client: AsyncClient,
        test_user_data
    ):
        """Test changing to a weak password"""
        response = await authenticated_client.put(
            "/api/v1/users/me/password",
            params={
                "current_password": test_user_data["password"],
                "new_password": "weak"
            }
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


class TestAccountDeletion:
    """Tests for account deletion"""

    @pytest.mark.asyncio
    async def test_delete_account_success(
        self,
        authenticated_client: AsyncClient,
        test_user_data,
        db_session: AsyncSession
    ):
        """Test successfully deleting account"""
        response = await authenticated_client.delete(
            "/api/v1/users/me",
            params={"password": test_user_data["password"]}
        )

        assert response.status_code == 204

        # Verify account is deactivated (soft delete)
        result = await db_session.execute(
            select(User).where(User.email == test_user_data["email"])
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_delete_account_wrong_password(
        self,
        authenticated_client: AsyncClient
    ):
        """Test deleting account with wrong password"""
        response = await authenticated_client.delete(
            "/api/v1/users/me",
            params={"password": "WrongPassword123!"}
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_deleted_account_cannot_login(
        self,
        client: AsyncClient,
        test_user_data,
        db_session: AsyncSession
    ):
        """Test that deactivated accounts cannot login"""
        # Register and get token
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_resp.json()["access_token"]

        # Delete account
        await client.delete(
            "/api/v1/users/me",
            params={"password": test_user_data["password"]},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to login again
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 403
        assert "inactive" in login_response.json()["detail"].lower()


class TestGetUserById:
    """Tests for getting user by ID"""

    @pytest.mark.asyncio
    async def test_get_own_user_by_id(
        self,
        authenticated_client: AsyncClient,
        test_user_data
    ):
        """Test getting own user profile by ID"""
        # Get own profile first to get ID
        me_response = await authenticated_client.get("/api/v1/users/me")
        user_id = me_response.json()["id"]

        # Get by ID
        response = await authenticated_client.get(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_other_user_unauthorized(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient
    ):
        """Test getting other user's profile (should fail for non-admins)"""
        # Create another user
        other_user_data = {
            "email": "other@example.com",
            "password": "OtherPass123!",
            "full_name": "Other User"
        }
        other_response = await client.post(
            "/api/v1/auth/register",
            json=other_user_data
        )
        other_user_id = other_response.json()["id"]

        # Try to get other user's profile
        response = await authenticated_client.get(f"/api/v1/users/{other_user_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting nonexistent user"""
        response = await authenticated_client.get("/api/v1/users/99999")

        assert response.status_code == 404


class TestAdminOperations:
    """Tests for admin-only user operations"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test listing all users as admin"""
        # Create admin user
        admin_data = {
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Admin User"
        }
        admin_response = await client.post("/api/v1/auth/register", json=admin_data)
        admin_id = admin_response.json()["id"]

        # Promote to super admin
        result = await db_session.execute(
            select(User).where(User.id == admin_id)
        )
        admin_user = result.scalar_one()
        admin_user.role = UserRole.SUPER_ADMIN.value
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": admin_data["email"],
                "password": admin_data["password"]
            }
        )
        admin_token = login_response.json()["access_token"]

        # List users
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_list_users_as_non_admin(
        self,
        authenticated_client: AsyncClient
    ):
        """Test listing users as non-admin (should fail)"""
        response = await authenticated_client.get("/api/v1/users/")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_update_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test admin updating another user's profile"""
        # Create regular user
        user_data = {
            "email": "user@example.com",
            "password": "UserPass123!",
            "full_name": "Regular User"
        }
        user_response = await client.post("/api/v1/auth/register", json=user_data)
        user_id = user_response.json()["id"]

        # Create admin
        admin_data = {
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Admin User"
        }
        admin_response = await client.post("/api/v1/auth/register", json=admin_data)
        admin_id = admin_response.json()["id"]

        # Promote to super admin
        result = await db_session.execute(
            select(User).where(User.id == admin_id)
        )
        admin_user = result.scalar_one()
        admin_user.role = UserRole.SUPER_ADMIN.value
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": admin_data["email"],
                "password": admin_data["password"]
            }
        )
        admin_token = login_response.json()["access_token"]

        # Update user
        update_data = {
            "full_name": "Updated by Admin"
        }
        response = await client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated by Admin"

    @pytest.mark.asyncio
    async def test_admin_delete_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test admin deleting another user"""
        # Create regular user
        user_data = {
            "email": "user@example.com",
            "password": "UserPass123!",
            "full_name": "Regular User"
        }
        user_response = await client.post("/api/v1/auth/register", json=user_data)
        user_id = user_response.json()["id"]

        # Create admin
        admin_data = {
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Admin User"
        }
        admin_response = await client.post("/api/v1/auth/register", json=admin_data)
        admin_id = admin_response.json()["id"]

        # Promote to super admin
        result = await db_session.execute(
            select(User).where(User.id == admin_id)
        )
        admin_user = result.scalar_one()
        admin_user.role = UserRole.SUPER_ADMIN.value
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": admin_data["email"],
                "password": admin_data["password"]
            }
        )
        admin_token = login_response.json()["access_token"]

        # Delete user
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204

        # Verify user is deactivated
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self_through_admin_endpoint(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that admin cannot delete their own account through admin endpoint"""
        # Create admin
        admin_data = {
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Admin User"
        }
        admin_response = await client.post("/api/v1/auth/register", json=admin_data)
        admin_id = admin_response.json()["id"]

        # Promote to super admin
        result = await db_session.execute(
            select(User).where(User.id == admin_id)
        )
        admin_user = result.scalar_one()
        admin_user.role = UserRole.SUPER_ADMIN.value
        await db_session.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": admin_data["email"],
                "password": admin_data["password"]
            }
        )
        admin_token = login_response.json()["access_token"]

        # Try to delete self through admin endpoint
        response = await client.delete(
            f"/api/v1/users/{admin_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "own account" in response.json()["detail"].lower()
