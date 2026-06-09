"""Pydantic v2 schemas for authentication endpoints.

Request  → RegisterRequest, LoginRequest
Response → TokenResponse, UserResponse, TokenWithUserResponse
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must contain at least one non-digit character")
        if v.isalpha():
            raise ValueError("Password must contain at least one digit")
        return v

class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """JWT token pair returned after successful auth."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  

class UserResponse(BaseModel):
    """Safe public representation of a User (no password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    plan: str
    created_at: datetime
    updated_at: datetime

class TokenWithUserResponse(BaseModel):
    """Combined token + user returned on register and login."""

    tokens: TokenResponse
    user: UserResponse
