from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date, timezone
from database import supabase


def list_trend_analyses(
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    sector: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    List trend analyses with optional sector filtering.
    Returns None if query fails.
    """
    try:
        offset = (page - 1) * page_size
        
        query = supabase.table("trend_analyses").select("*", count="exact")
        
        if sector:
            query = query.eq("sector", sector)
        
        response = query.order("analysis_date", desc=True).range(offset, offset + page_size - 1).execute()
        
        if not response.data:
            return {"analyses": [], "total": 0}
        
        return {
            "analyses": response.data,
            "total": response.count if response.count is not None else 0,
        }
    except Exception:
        return None


def get_trend_analysis_by_id(user_id: UUID, analysis_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a specific trend analysis by ID.
    Returns None if not found or query fails.
    """
    try:
        response = (
            supabase.table("trend_analyses")
            .select("*")
            .eq("id", str(analysis_id))
            .single()
            .execute()
        )
        
        return response.data if response.data else None
    except Exception:
        return None


def create_trend_analysis_job(
    user_id: UUID,
    sector: Optional[str],
    date_range_start: date,
    date_range_end: date,
) -> Optional[Dict[str, Any]]:
    """
    Create a background job for trend analysis generation.
    Returns job details or None if creation fails.
    """
    try:
        job_data = {
            "id": str(UUID(int=0)),
            "user_id": str(user_id),
            "job_type": "trend_analysis",
            "status": "queued",
            "parameters": {
                "sector": sector,
                "date_range_start": date_range_start.isoformat(),
                "date_range_end": date_range_end.isoformat(),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("background_jobs").insert(job_data).execute()
        
        if not response.data:
            return None
        
        return response.data[0]
    except Exception:
        return None


def generate_trend_analysis(
    user_id: UUID,
    sector: Optional[str],
    date_range_start: date,
    date_range_end: date,
) -> Optional[Dict[str, Any]]:
    """
    Generate trend analysis from proposal data.
    This is a synchronous fallback if background jobs aren't available.
    Returns analysis data or None if generation fails.
    """
    try:
        query = (
            supabase.table("proposals")
            .select(
                "id, sector, technology_type, maturity_level, composite_score, "
                "relevance_score, feasibility_score, sector_alignment_score, compliance_score, "
                "submission_date, status"
            )
            .gte("submission_date", date_range_start.isoformat())
            .lte("submission_date", date_range_end.isoformat())
            .eq("deleted_at", None)
        )
        
        if sector:
            query = query.eq("sector", sector)
        
        response = query.execute()
        
        if not response.data:
            return None
        
        proposals = response.data
        submission_volume = len(proposals)
        
        if submission_volume == 0:
            return None
        
        # Calculate average scores
        total_relevance = 0.0
        total_feasibility = 0.0
        total_sector_alignment = 0.0
        total_compliance = 0.0
        total_composite = 0.0
        count_with_scores = 0
        
        technology_counts: Dict[str, int] = {}
        maturity_counts: Dict[str, int] = {}
        
        for proposal in proposals:
            if proposal.get("composite_score") is not None:
                total_relevance += proposal.get("relevance_score", 0.0)
                total_feasibility += proposal.get("feasibility_score", 0.0)
                total_sector_alignment += proposal.get("sector_alignment_score", 0.0)
                total_compliance += proposal.get("compliance_score", 0.0)
                total_composite += proposal.get("composite_score", 0.0)
                count_with_scores += 1
            
            tech_type = proposal.get("technology_type", "other")
            technology_counts[tech_type] = technology_counts.get(tech_type, 0) + 1
            
            maturity = proposal.get("maturity_level", "unknown")
            maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1
        
        average_scores = {
            "relevance": round(total_relevance / count_with_scores, 2) if count_with_scores > 0 else 0.0,
            "feasibility": round(total_feasibility / count_with_scores, 2) if count_with_scores > 0 else 0.0,
            "sector_alignment": round(total_sector_alignment / count_with_scores, 2) if count_with_scores > 0 else 0.0,
            "compliance": round(total_compliance / count_with_scores, 2) if count_with_scores > 0 else 0.0,
            "composite": round(total_composite / count_with_scores, 2) if count_with_scores > 0 else 0.0,
        }
        
        # Identify emerging technologies (top 3 by count)
        sorted_technologies = sorted(technology_counts.items(), key=lambda x: x[1], reverse=True)
        emerging_technologies = [tech for tech, _ in sorted_technologies[:3]]
        
        technology_trends = {
            "distribution": technology_counts,
            "top_technologies": emerging_technologies,
        }
        
        analysis_data = {
            "analysis_date": date.today().isoformat(),
            "sector": sector,
            "technology_trends": technology_trends,
            "submission_volume": submission_volume,
            "average_scores": average_scores,
            "emerging_technologies": emerging_technologies,
            "generated_by": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        insert_response = supabase.table("trend_analyses").insert(analysis_data).execute()
        
        if not insert_response.data:
            return None
        
        return insert_response.data[0]
    except Exception:
        return None


def get_by_id(user_id: UUID, analysis_id: UUID) -> Optional[Dict[str, Any]]:
    """Alias for get_trend_analysis_by_id."""
    return get_trend_analysis_by_id(user_id, analysis_id)


def trigger_generation(
    user_id: UUID,
    sector: Optional[str] = None,
    date_range_start: Optional[date] = None,
    date_range_end: Optional[date] = None,
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """Alias for create_trend_analysis_job."""
    return create_trend_analysis_job(user_id, sector, date_range_start, date_range_end)


def delete(user_id: UUID, analysis_id: UUID) -> bool:
    """Alias for delete_trend_analysis."""
    return delete_trend_analysis(user_id, analysis_id)


def delete_trend_analysis(user_id: UUID, analysis_id: UUID) -> bool:
    """
    Soft delete a trend analysis (executive only, enforced at route level).
    Returns True if successful, False otherwise.
    """
    try:
        response = (
            supabase.table("trend_analyses")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", str(analysis_id))
            .execute()
        )
        
        return bool(response.data)
    except Exception:
        return False
