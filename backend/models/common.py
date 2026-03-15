from typing import Optional
from pydantic import BaseModel, Field


class PaginationResponse(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Error code")
