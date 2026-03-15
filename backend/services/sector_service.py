from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from uuid import UUID
from database import supabase


def get_sector_dashboard(user_id: str, sector: str) -> Optional[Dict[str, Any]]:
    """
    Get sector-specific dashboard metrics.
    Returns None if sector has no data or user lacks permissions.
    """
    # Verify user has analyst+ permissions
    user_response = supabase.table("users").select("role").eq("id", user_id).single().execute()
    if not user_response.data:
        return None
    
    user_role = user_response.data.get("role")
    if user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead"]:
        return None

    # Get total proposals for sector
    proposals_response = supabase.table("proposals").select("id, composite_score, relevance_score, feasibility_score, sector_alignment_score, compliance_score, technology_type, maturity_level, submitter_id").eq("sector", sector).execute()
    
    if not proposals_response.data:
        return None

    proposals = proposals_response.data
    total_proposals = len(proposals)

    # Calculate average scores
    relevance_scores = [p["relevance_score"] for p in proposals if p.get("relevance_score") is not None]
    feasibility_scores = [p["feasibility_score"] for p in proposals if p.get("feasibility_score") is not None]
    sector_alignment_scores = [p["sector_alignment_score"] for p in proposals if p.get("sector_alignment_score") is not None]
    compliance_scores = [p["compliance_score"] for p in proposals if p.get("compliance_score") is not None]
    composite_scores = [p["composite_score"] for p in proposals if p.get("composite_score") is not None]

    average_scores = {
        "relevance": round(sum(relevance_scores) / len(relevance_scores), 2) if relevance_scores else 0.0,
        "feasibility": round(sum(feasibility_scores) / len(feasibility_scores), 2) if feasibility_scores else 0.0,
        "sector_alignment": round(sum(sector_alignment_scores) / len(sector_alignment_scores), 2) if sector_alignment_scores else 0.0,
        "compliance": round(sum(compliance_scores) / len(compliance_scores), 2) if compliance_scores else 0.0,
        "composite": round(sum(composite_scores) / len(composite_scores), 2) if composite_scores else 0.0,
    }

    # Technology distribution
    tech_counts: Dict[str, int] = {}
    for p in proposals:
        tech_type = p.get("technology_type")
        if tech_type:
            tech_counts[tech_type] = tech_counts.get(tech_type, 0) + 1
    
    technology_distribution = [
        {"technology_type": tech, "count": count}
        for tech, count in tech_counts.items()
    ]
    technology_distribution.sort(key=lambda x: x["count"], reverse=True)

    # Maturity distribution
    maturity_counts: Dict[str, int] = {}
    for p in proposals:
        maturity = p.get("maturity_level")
        if maturity:
            maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1
    
    maturity_distribution = [
        {"maturity_level": maturity, "count": count}
        for maturity, count in maturity_counts.items()
    ]
    maturity_distribution.sort(key=lambda x: x["count"], reverse=True)

    # Top proposals (top 10 by composite_score)
    top_proposal_data = [
        p for p in proposals if p.get("composite_score") is not None
    ]
    top_proposal_data.sort(key=lambda x: x["composite_score"], reverse=True)
    top_proposal_data = top_proposal_data[:10]

    # Fetch vendor names for top proposals
    vendor_ids = [p["submitter_id"] for p in top_proposal_data if p.get("submitter_id")]
    vendor_names = {}
    if vendor_ids:
        vendors_response = supabase.table("chamber_vendors").select("id, name").in_("id", vendor_ids).execute()
        if vendors_response.data:
            for v in vendors_response.data:
                vendor_names[v["id"]] = v["name"]

    # Fetch proposal titles
    proposal_ids = [p["id"] for p in top_proposal_data]
    proposal_titles = {}
    if proposal_ids:
        proposals_title_response = supabase.table("proposals").select("id, title").in_("id", proposal_ids).execute()
        if proposals_title_response.data:
            for pt in proposals_title_response.data:
                proposal_titles[pt["id"]] = pt["title"]

    top_proposals = [
        {
            "proposal_id": p["id"],
            "title": proposal_titles.get(p["id"], "Untitled"),
            "composite_score": round(p["composite_score"], 2),
            "vendor_name": vendor_names.get(p["submitter_id"], "Unknown"),
        }
        for p in top_proposal_data
    ]

    return {
        "sector": sector,
        "total_proposals": total_proposals,
        "average_scores": average_scores,
        "technology_distribution": technology_distribution,
        "maturity_distribution": maturity_distribution,
        "top_proposals": top_proposals,
    }
