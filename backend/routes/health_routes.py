from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from models.health import HealthCheckResponse, AIServicesHealth
from models.common import ErrorResponse
from services.health_service import HealthService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["health"]
)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="System health check endpoint",
    responses={
        503: {
            "model": ErrorResponse,
            "description": "Service unavailable"
        }
    }
)
async def health_check(request: Request) -> Dict[str, Any]:
    """
    System health check endpoint.
    
    Returns health status for:
    - Database connection
    - AI services (Claude, OpenAI, Gemini)
    - Storage accessibility
    
    No authentication required.
    Rate limit: 300 requests per minute.
    """
    try:
        health_data = await HealthService.check_system_health()
        
        overall_status = "healthy"
        status_code = status.HTTP_200_OK
        
        # Check if any critical component is unhealthy
        if health_data.get("database") != "connected":
            overall_status = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        if health_data.get("storage") != "accessible":
            overall_status = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        ai_services = health_data.get("ai_services", {})
        if not any([
            ai_services.get("claude") == "available",
            ai_services.get("openai") == "available",
            ai_services.get("gemini") == "available"
        ]):
            overall_status = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        response_data = HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            database=health_data.get("database", "unknown"),
            ai_services=AIServicesHealth(
                claude=ai_services.get("claude", "unknown"),
                openai=ai_services.get("openai", "unknown"),
                gemini=ai_services.get("gemini", "unknown")
            ),
            storage=health_data.get("storage", "unknown")
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response_data.model_dump(mode="json")
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error="HealthCheckFailed",
            detail="System health check encountered an error",
            code="HEALTH_CHECK_ERROR"
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(mode="json")
        )
