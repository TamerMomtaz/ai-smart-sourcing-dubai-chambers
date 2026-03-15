from typing import Dict
from pydantic import BaseModel, Field
from datetime import datetime


class AIServicesHealth(BaseModel):
    claude: str = Field(default="available", description="Claude service status")
    openai: str = Field(default="available", description="OpenAI service status")
    gemini: str = Field(default="available", description="Gemini service status")


class HealthCheckResponse(BaseModel):
    status: str = Field(default="healthy", description="System health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: str = Field(default="connected", description="Database connection status")
    ai_services: AIServicesHealth = Field(..., description="AI services status")
    storage: str = Field(default="accessible", description="Storage accessibility status")
