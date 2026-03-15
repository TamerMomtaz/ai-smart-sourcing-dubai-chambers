from typing import Literal
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class UserInfo(BaseModel):
    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    role: Literal[
        "analyst",
        "executive",
        "compliance_officer",
        "business_group_lead",
        "vendor",
    ] = Field(..., description="User role")
    full_name: str = Field(..., description="User full name")
    chamber: str = Field(..., description="Associated chamber")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    user: UserInfo = Field(..., description="User information")


class LogoutResponse(BaseModel):
    message: str = Field(default="Logged out successfully", description="Logout confirmation message")
