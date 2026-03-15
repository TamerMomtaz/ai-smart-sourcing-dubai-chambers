from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class DocumentCreate(BaseModel):
    file_name: str = Field(..., description="Original file name")
    file_type: Literal["pdf", "docx", "pptx", "xlsx"] = Field(..., description="File type")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class DocumentResponse(BaseModel):
    id: UUID = Field(..., description="Document UUID")
    file_name: str = Field(..., description="File name")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class DocumentUploadResponse(BaseModel):
    document_id: UUID = Field(..., description="Document UUID")
    upload_url: str = Field(..., description="Pre-signed upload URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")


class DocumentDownloadResponse(BaseModel):
    download_url: str = Field(..., description="Pre-signed download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")


class ExtractedDocumentData(BaseModel):
    document_id: UUID = Field(..., description="Document UUID")
    file_name: str = Field(..., description="File name")
    extracted_text: Optional[str] = Field(None, description="Extracted plain text")
    extracted_tables: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted tables")
    extracted_charts: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted charts")
    financial_data: Optional[Dict[str, Any]] = Field(None, description="Extracted financial data")
    language_detected: Optional[str] = Field(None, description="Detected language")
