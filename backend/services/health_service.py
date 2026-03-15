from datetime import datetime, timezone
from typing import Dict, Any
import os
import logging

from database import supabase

logger = logging.getLogger(__name__)


class HealthService:
    """Health check service for system status monitoring."""

    @staticmethod
    async def check_system_health() -> Dict[str, Any]:
        """
        Perform comprehensive system health check.
        
        Returns:
            Dict containing health status for all system components
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc),
            "database": "unknown",
            "ai_services": {
                "claude": "unknown",
                "openai": "unknown",
                "gemini": "unknown"
            },
            "storage": "unknown"
        }

        # Check database connectivity
        try:
            result = supabase.table("chamber_vendors").select("id").limit(1).execute()
            health_status["database"] = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            health_status["database"] = "disconnected"
            health_status["status"] = "unhealthy"

        # Check AI services availability
        claude_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        gemini_api_key = os.getenv("GOOGLE_API_KEY", "").strip()

        health_status["ai_services"]["claude"] = "available" if claude_api_key else "not_configured"
        health_status["ai_services"]["openai"] = "available" if openai_api_key else "not_configured"
        health_status["ai_services"]["gemini"] = "available" if gemini_api_key else "not_configured"

        # Check storage (Supabase Storage)
        try:
            supabase_url = os.getenv("SUPABASE_URL", "").strip()
            if supabase_url:
                health_status["storage"] = "accessible"
            else:
                health_status["storage"] = "not_configured"
                health_status["status"] = "degraded"
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            health_status["storage"] = "inaccessible"
            health_status["status"] = "degraded"

        # Determine overall status
        if health_status["database"] == "disconnected":
            health_status["status"] = "unhealthy"
        elif (
            health_status["storage"] in ["inaccessible", "not_configured"]
            or all(
                status == "not_configured"
                for status in health_status["ai_services"].values()
            )
        ):
            health_status["status"] = "degraded"

        return health_status


health_service = HealthService()
