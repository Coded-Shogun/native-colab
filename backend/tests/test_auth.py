"""
Authentication Tests
Comprehensive tests for user registration, login, token refresh, and logout
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User
from app.core.security import decode_token, verify_token_type


class TestUserRegistration:
    """Tests for user registration endpoint"""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email fails"""
        # Register first user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register again with same email
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_password_is_hashed(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that password is properly hashed in database"""
        password = "SecurePass123!"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "hash@example.com",
                "password": password,
                "full_name": "Hash Test"
            }
        )

        # Get user from database
        result = await db_session.execute(
            select(User).where(User.email == "hash@example.com")
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.hashed_password != password  # Password should be hashed
        assert user.hashed_password.startswith("$2b$")  # Bcrypt hash format


class TestUserLogin:
    """Tests for user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Test successful login"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        # Verify tokens are valid
        assert decode_token(data["access_token"]) is not None
        assert decode_token(data["refresh_token"]) is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        """Test login with wrong password fails"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Try to login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_updates_last_login(
        self,
        client: AsyncClient,
        test_user_data,
        db_session: AsyncSession
    ):
        """Test that login updates last_login timestamp"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Get user before login
        result = await db_session.execute(
            select(User).where(User.email == test_user_data["email"])
        )
        user_before = result.scalar_one_or_none()
        assert user_before.last_login is None

        # Login
        await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        # Get user after login
        await db_session.refresh(user_before)
        assert user_before.last_login is not None


class TestTokenRefresh:
    """Tests for token refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user_data):
        """Test successful token refresh"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify new tokens are valid and different
        assert decode_token(data["access_token"]) is not None
        assert data["access_token"] != login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(
        self,
        client: AsyncClient,
        test_user_data
    ):
        """Test that using access token for refresh fails"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        access_token = login_response.json()["access_token"]

        # Try to refresh with access token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for authenticated endpoints"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_user_data
    ):
        """Test getting current user info with valid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token fails"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint"""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test successful logout"""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout without token fails"""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401
