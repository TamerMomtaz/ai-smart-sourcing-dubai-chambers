from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class BusinessCouncil(BaseModel):
    id: UUID = Field(..., description="Business council UUID")
    name: str = Field(..., description="Council name")
    country: str = Field(..., description="Country focus")
    description: Optional[str] = Field(None, description="Council description")
    representative_office_locations: Optional[List[Dict[str, Any]]] = Field(None, description="Office locations")
