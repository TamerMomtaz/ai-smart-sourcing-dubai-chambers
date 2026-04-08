from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from uuid import UUID
from datetime import datetime, date


class VendorProfile(BaseModel):
    team_size: Optional[int] = Field(None, description="Number of employees")
    funding_stage: Optional[str] = Field(None, description="Current funding stage")
    technology_stack: Optional[List[str]] = Field(None, description="Technologies used")
    certifications: Optional[List[str]] = Field(None, description="Certifications held")
    onboarding_stage: Optional[str] = Field(None, description="Current onboarding milestone")
    pilot_status: Optional[str] = Field(None, description="Pilot program status")


class Vendor(BaseModel):
    id: UUID = Field(..., description="Vendor UUID")
    name: str = Field(..., description="Company/startup name")
    company_registration: str = Field(..., description="Official registration number")
    country: str = Field(..., description="Country of incorporation")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    website: Optional[str] = Field(None, description="Company website URL")
    is_desc_approved: bool = Field(default=False, description="Whether vendor has DESC certification")
    desc_badge_issued_date: Optional[date] = Field(None, description="Date DESC badge was issued")
    onboarding_status: str = Field(..., description="Current stage in vendor lifecycle")


class VendorResponse(BaseModel):
    id: UUID = Field(..., description="Vendor UUID")
    name: str = Field(..., description="Company name")
    company_registration: str = Field(..., description="Registration number")
    country: str = Field(..., description="Country")
    contact_email: str = Field(..., description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Website")
    is_desc_approved: bool = Field(..., description="DESC approval status")
    desc_badge_issued_date: Optional[date] = Field(None, description="DESC badge issued date")
    onboarding_status: str = Field(..., description="Onboarding status")
    submission_history_count: int = Field(..., description="Total proposals submitted")
    average_compliance_score: Optional[float] = Field(None, description="Average compliance score")
    profile: Optional[VendorProfile] = Field(None, description="Extended vendor profile")
    desc_certified: bool = Field(default=False, description="Whether vendor is DESC certified")
    desc_certification_level: Optional[str] = Field(None, description="Certification level: certified or in_progress")
    desc_provider_name: Optional[str] = Field(None, description="DESC certified provider name")
    reputation_score: Optional[float] = Field(None, description="Vendor reputation score 0-100")
    reputation_tier: Optional[str] = Field(None, description="Reputation tier: trusted, established, emerging, new, flagged")
    vscore: Optional[int] = Field(None, description="vScore 300-900")
    vscore_tier: Optional[str] = Field(None, description="vScore tier: platinum, gold, silver, bronze, under_review")
    trade_license_status: Optional[str] = Field(None, description="Trade license verification status")


class TradeLicenseVerifyRequest(BaseModel):
    trade_license_number: str = Field(..., description="Dubai trade license number to verify")


class TradeLicenseStatusResponse(BaseModel):
    vendor_id: UUID = Field(..., description="Vendor UUID")
    trade_license_number: Optional[str] = Field(None, description="Trade license number")
    trade_license_status: str = Field(..., description="Verification status")
    trade_license_verified_at: Optional[datetime] = Field(None, description="When license was verified")
    trade_license_details: Optional[dict] = Field(None, description="Additional license details")
    message: Optional[str] = Field(None, description="Status message")


class VendorProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Company name")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[HttpUrl] = Field(None, description="Website URL")
    profile: Optional[VendorProfile] = Field(None, description="Extended profile data")


class VendorUpdateResponse(BaseModel):
    vendor_id: UUID = Field(..., description="Vendor UUID")
    updated_at: datetime = Field(..., description="Update timestamp")
