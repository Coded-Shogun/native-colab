"""
Authentication Schemas
Pydantic models for authentication-related requests and responses
"""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema for access token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenResponse(BaseModel):
    """Schema for token response with user info"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="JWT refresh token")
