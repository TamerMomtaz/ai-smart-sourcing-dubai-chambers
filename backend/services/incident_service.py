from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
import logging

from database import supabase

logger = logging.getLogger(__name__)


def list_incidents() -> List[Dict[str, Any]]:
    """Return all incidents ordered by created_at DESC."""
    try:
        response = (
            supabase.table("chamber_incidents")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"Error listing incidents: {e}", exc_info=True)
        return []


def create_incident(
    *,
    title: str,
    description: Optional[str] = None,
    severity: str,
    incident_type: str,
    affected_systems: Optional[list] = None,
    reported_by: UUID,
    desc_report_required: bool = False,
) -> Optional[Dict[str, Any]]:
    """Create a new incident record."""
    try:
        data = {
            "title": title,
            "description": description,
            "severity": severity,
            "incident_type": incident_type,
            "affected_systems": affected_systems or [],
            "reported_by": str(reported_by),
            "desc_report_required": desc_report_required,
            "status": "open",
        }
        response = (
            supabase.table("chamber_incidents")
            .insert(data)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error creating incident: {e}", exc_info=True)
        return None


def update_incident(
    *,
    incident_id: UUID,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update an existing incident."""
    try:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        # If status is being set to 'resolved', set resolution_date
        if updates.get("status") == "resolved" and "resolution_date" not in updates:
            updates["resolution_date"] = datetime.now(timezone.utc).isoformat()

        # If status is being set to 'reported_to_desc', set desc_reported_at
        if updates.get("status") == "reported_to_desc" and "desc_reported_at" not in updates:
            updates["desc_reported_at"] = datetime.now(timezone.utc).isoformat()
            updates["desc_report_required"] = True

        response = (
            supabase.table("chamber_incidents")
            .update(updates)
            .eq("id", str(incident_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error updating incident {incident_id}: {e}", exc_info=True)
        return None


def get_incident_summary() -> Dict[str, Any]:
    """Return summary counts of incidents."""
    try:
        response = (
            supabase.table("chamber_incidents")
            .select("id, status, severity")
            .execute()
        )
        incidents = response.data or []

        total = len(incidents)
        open_count = sum(1 for i in incidents if i["status"] == "open")
        investigating = sum(1 for i in incidents if i["status"] == "investigating")
        resolved_count = sum(1 for i in incidents if i["status"] == "resolved")
        reported_count = sum(1 for i in incidents if i["status"] == "reported_to_desc")

        by_severity = {}
        for i in incidents:
            sev = i.get("severity", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total": total,
            "open": open_count + investigating,
            "resolved": resolved_count,
            "reported_to_desc": reported_count,
            "by_severity": by_severity,
        }
    except Exception as e:
        logger.error(f"Error getting incident summary: {e}", exc_info=True)
        return {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "reported_to_desc": 0,
            "by_severity": {},
        }
