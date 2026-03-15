from typing import Literal
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class CommentCreate(BaseModel):
    comment_text: str = Field(..., max_length=2000, description="Comment text")
    visibility: Literal["internal", "vendor_visible"] = Field(
        default="internal", description="Comment visibility"
    )


class CommentResponse(BaseModel):
    comment_id: UUID = Field(..., description="Comment UUID")
    proposal_id: UUID = Field(..., description="Proposal UUID")
    user_id: UUID = Field(..., description="User UUID")
    comment_text: str = Field(..., description="Comment text")
    created_at: datetime = Field(..., description="Creation timestamp")
    visibility: str = Field(..., description="Comment visibility")
