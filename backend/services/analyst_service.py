from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from database import supabase


def get_analyst_dashboard(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get analyst dashboard with pending reviews, recent evaluations, and daily stats.
    
    Args:
        user_id: The analyst user ID
        
    Returns:
        Dashboard data dictionary or None if error
    """
    try:
        # Get pending reviews (proposals requiring manual review or under_review status)
        pending_response = (
            supabase.table("chamber_proposals")
            .select(
                "id, title, submission_date, sector, composite_score, requires_manual_review"
            )
            .in_("status", ["requires_manual_review", "under_review", "evaluated"])
            .eq("requires_manual_review", True)
            .order("submission_date", desc=False)
            .limit(20)
            .execute()
        )
        
        pending_reviews = []
        for proposal in pending_response.data:
            pending_reviews.append({
                "proposal_id": proposal["id"],
                "title": proposal["title"],
                "submission_date": proposal["submission_date"],
                "sector": proposal["sector"],
                "composite_score": proposal.get("composite_score"),
                "requires_manual_review": proposal["requires_manual_review"]
            })
        
        # Get recent evaluations (last 10 evaluated proposals)
        recent_response = (
            supabase.table("chamber_proposals")
            .select("id, title, evaluation_timestamp, composite_score")
            .not_.is_("evaluation_timestamp", "null")
            .order("evaluation_timestamp", desc=True)
            .limit(10)
            .execute()
        )
        
        recent_evaluations = []
        for proposal in recent_response.data:
            recent_evaluations.append({
                "proposal_id": proposal["id"],
                "title": proposal["title"],
                "evaluated_at": proposal["evaluation_timestamp"],
                "composite_score": proposal.get("composite_score")
            })
        
        # Calculate daily stats (today's activity)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count proposals reviewed today (status changes to under_review, approved, rejected)
        reviewed_response = (
            supabase.table("chamber_proposals")
            .select("id", count="exact")
            .gte("updated_at", today_start.isoformat())
            .in_("status", ["under_review", "approved", "rejected"])
            .execute()
        )
        proposals_reviewed = reviewed_response.count or 0
        
        # Count evaluations triggered today
        evaluations_response = (
            supabase.table("chamber_proposals")
            .select("id", count="exact")
            .gte("evaluation_timestamp", today_start.isoformat())
            .execute()
        )
        evaluations_triggered = evaluations_response.count or 0
        
        # Calculate average review time (simplified - using evaluation timestamp delta)
        avg_time_response = (
            supabase.table("chamber_proposals")
            .select("submission_date, evaluation_timestamp")
            .gte("evaluation_timestamp", today_start.isoformat())
            .not_.is_("evaluation_timestamp", "null")
            .execute()
        )
        
        average_review_time_minutes = 0.0
        if avg_time_response.data:
            total_minutes = 0
            count = 0
            for record in avg_time_response.data:
                submission = datetime.fromisoformat(record["submission_date"].replace("Z", "+00:00"))
                evaluation = datetime.fromisoformat(record["evaluation_timestamp"].replace("Z", "+00:00"))
                delta_minutes = (evaluation - submission).total_seconds() / 60
                total_minutes += delta_minutes
                count += 1
            if count > 0:
                average_review_time_minutes = round(total_minutes / count, 2)
        
        return {
            "pending_reviews": pending_reviews,
            "recent_evaluations": recent_evaluations,
            "daily_stats": {
                "proposals_reviewed": proposals_reviewed,
                "average_review_time_minutes": average_review_time_minutes,
                "evaluations_triggered": evaluations_triggered
            }
        }
        
    except Exception:
        return None
