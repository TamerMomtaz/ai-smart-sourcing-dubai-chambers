from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
import logging

from database import supabase

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def list_unresolved_alerts() -> List[Dict[str, Any]]:
    """Return unresolved alerts sorted by severity then created_at."""
    try:
        response = (
            supabase.table("chamber_alerts")
            .select("*")
            .eq("is_resolved", False)
            .order("created_at", desc=True)
            .execute()
        )
        alerts = response.data or []
        # Sort by severity (critical first), then by created_at desc
        alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a.get("severity", "medium"), 2),))
        return alerts
    except Exception as e:
        logger.error(f"Error listing alerts: {e}", exc_info=True)
        return []


def resolve_alert(*, alert_id: UUID) -> Optional[Dict[str, Any]]:
    """Mark an alert as resolved."""
    try:
        response = (
            supabase.table("chamber_alerts")
            .update({
                "is_resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", str(alert_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}", exc_info=True)
        return None


def create_alert(
    *,
    alert_type: str,
    severity: str = "medium",
    title: str,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new alert record."""
    try:
        data = {
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
        }
        response = (
            supabase.table("chamber_alerts")
            .insert(data)
            .execute()
        )
        if response.data:
            logger.info(f"Alert created: type={alert_type} severity={severity} title={title}")
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        return None
