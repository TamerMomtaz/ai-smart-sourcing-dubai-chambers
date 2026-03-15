from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class NotificationPreferences(BaseModel):
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    proposal_status_updates: bool = Field(default=True, description="Notify on proposal status changes")
    weekly_digest: bool = Field(default=True, description="Send weekly summary digest")
    compliance_alerts: bool = Field(default=True, description="Notify on compliance issues")


class UserProfile(BaseModel):
    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    full_name: str = Field(..., description="User full name")
    chamber: str = Field(..., description="Associated chamber")
    business_group_id: Optional[UUID] = Field(None, description="Associated business group ID")
    business_group_name: Optional[str] = Field(None, description="Associated business group name")
    preferred_language: Literal["en", "ar"] = Field(default="en", description="Preferred UI language")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="User full name")
    preferred_language: Optional[Literal["en", "ar"]] = Field(None, description="Preferred UI language")
    notification_preferences: Optional[NotificationPreferences] = Field(None, description="Notification settings")


class UserProfileUpdateResponse(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    updated_at: datetime = Field(..., description="Update timestamp")
