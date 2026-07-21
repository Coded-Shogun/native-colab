"""
Authentication Tests
Tests for Supabase-backed auth endpoints: /me, /logout, and removed legacy endpoints.
"""

import pytest
from httpx import AsyncClient


class TestProtectedEndpoints:
    """Tests for authenticated endpoints"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_user
    ):
        """Test getting current user info with valid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["full_name"] == test_user["full_name"]

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


class TestRemovedEndpoints:
    """Tests that legacy endpoints are no longer available"""

    @pytest.mark.asyncio
    async def test_register_returns_405(self, client: AsyncClient):
        """POST /register should return 405 Method Not Allowed"""
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_login_returns_405(self, client: AsyncClient):
        """POST /login should return 405 Method Not Allowed"""
        response = await client.post("/api/v1/auth/login", data={})
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_refresh_returns_405(self, client: AsyncClient):
        """POST /refresh should return 405 Method Not Allowed"""
        response = await client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 405
