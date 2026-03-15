from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ExportResponse(BaseModel):
    export_url: str = Field(..., description="Export file download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")
    format: Optional[Literal["csv", "xlsx"]] = Field(None, description="Export format")
    hash_chain_signature: Optional[str] = Field(None, description="Hash chain signature for compliance exports")
