from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from database import supabase


def get_executive_dashboard(user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get aggregated executive dashboard metrics.
    Returns None if data cannot be retrieved.
    """
    try:
        # Pipeline Status
        pipeline_result = supabase.table("chamber_proposals").select(
            "status",
            count="exact"
        ).execute()
        
        proposals = pipeline_result.data if pipeline_result.data else []
        
        status_counts = {
            "total_proposals": len(proposals),
            "submitted": 0,
            "evaluating": 0,
            "under_review": 0,
            "approved": 0,
            "rejected": 0
        }
        
        for proposal in proposals:
            status = proposal.get("status", "")
            if status in ["submitted", "queued_for_evaluation"]:
                status_counts["submitted"] += 1
            elif status in ["evaluating", "evaluated"]:
                status_counts["evaluating"] += 1
            elif status == "under_review":
                status_counts["under_review"] += 1
            elif status == "approved":
                status_counts["approved"] += 1
            elif status == "rejected":
                status_counts["rejected"] += 1
        
        # Sector Trends
        sector_result = supabase.rpc(
            "get_sector_trends",
            {}
        ).execute()
        
        sector_trends = []
        if sector_result.data:
            for row in sector_result.data:
                trend_direction = "stable"
                if row.get("trend_indicator", 0) > 0:
                    trend_direction = "up"
                elif row.get("trend_indicator", 0) < 0:
                    trend_direction = "down"
                
                sector_trends.append({
                    "sector": row.get("sector", "unknown"),
                    "proposal_count": row.get("proposal_count", 0),
                    "average_score": round(row.get("average_score", 0.0), 2),
                    "trend": trend_direction
                })
        
        # D33 Alignment
        d33_result = supabase.table("chamber_proposals").select(
            "d33_alignment_metrics",
            count="exact"
        ).not_.is_("d33_alignment_metrics", "null").execute()
        
        total_aligned = len(d33_result.data) if d33_result.data else 0
        total_proposals = status_counts["total_proposals"]
        alignment_percentage = round((total_aligned / total_proposals * 100) if total_proposals > 0 else 0.0, 2)
        
        top_areas = []
        if d33_result.data:
            area_counts: Dict[str, int] = {}
            for proposal in d33_result.data:
                metrics = proposal.get("d33_alignment_metrics", {})
                if isinstance(metrics, dict):
                    for area in metrics.get("aligned_areas", []):
                        area_counts[area] = area_counts.get(area, 0) + 1
            
            top_areas = sorted(area_counts.keys(), key=lambda x: area_counts[x], reverse=True)[:5]
        
        d33_alignment = {
            "total_aligned_proposals": total_aligned,
            "alignment_percentage": alignment_percentage,
            "top_alignment_areas": top_areas
        }
        
        # Vendor Onboarding Funnel
        vendor_result = supabase.table("chamber_vendors").select(
            "onboarding_status",
            count="exact"
        ).execute()
        
        funnel_counts = {
            "submission": 0,
            "shortlist": 0,
            "desc_badge_verify": 0,
            "pilot": 0,
            "procurement_decision": 0
        }
        
        if vendor_result.data:
            for vendor in vendor_result.data:
                status = vendor.get("onboarding_status", "")
                if status == "submitted":
                    funnel_counts["submission"] += 1
                elif status == "shortlisted":
                    funnel_counts["shortlist"] += 1
                    funnel_counts["submission"] += 1
                elif status in ["pilot", "desc_verified"]:
                    funnel_counts["desc_badge_verify"] += 1
                    funnel_counts["shortlist"] += 1
                    funnel_counts["submission"] += 1
                    if status == "pilot":
                        funnel_counts["pilot"] += 1
                elif status == "procurement":
                    funnel_counts["procurement_decision"] += 1
                    funnel_counts["pilot"] += 1
                    funnel_counts["desc_badge_verify"] += 1
                    funnel_counts["shortlist"] += 1
                    funnel_counts["submission"] += 1
        
        vendor_onboarding_funnel = funnel_counts
        
        # Compliance Summary
        compliance_result = supabase.table("chamber_compliance_audits").select(
            "remediation_required",
            count="exact"
        ).execute()
        
        total_audits = len(compliance_result.data) if compliance_result.data else 0
        remediation_count = 0
        
        if compliance_result.data:
            for audit in compliance_result.data:
                if audit.get("remediation_required", False):
                    remediation_count += 1
        
        compliant_count = total_audits - remediation_count
        
        compliance_summary = {
            "total_audits": total_audits,
            "compliant": compliant_count,
            "remediation_required": remediation_count
        }
        
        return {
            "pipeline_status": status_counts,
            "sector_trends": sector_trends,
            "d33_alignment": d33_alignment,
            "vendor_onboarding_funnel": vendor_onboarding_funnel,
            "compliance_summary": compliance_summary
        }
    
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Executive dashboard error: {str(e)}")
        return None
