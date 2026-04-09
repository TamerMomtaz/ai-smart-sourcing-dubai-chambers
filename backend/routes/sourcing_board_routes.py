"""Public Sourcing Board — browse open cases and proposal counts (no auth)."""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
import logging

from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/sourcing-board", tags=["Public Sourcing Board"])

# Fields safe for public exposure
PUBLIC_FIELDS = (
    "id, title, sector, technology_domain, urgency, compliance_tier,"
    " problem_statement, created_at, status"
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List open sourcing cases (no auth required)",
)
async def list_open_cases(
    sector: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest", pattern="^(newest|urgency|proposals)$"),
):
    """Return all sourcing cases with status 'open' or 'matching'.

    Only public-safe fields are returned. problem_statement is truncated
    to 500 characters. Internal fields (requesting_entity,
    assigned_analyst_id, etc.) are never exposed.
    """
    try:
        query = (
            supabase.table("chamber_sourcing_cases")
            .select(PUBLIC_FIELDS)
            .in_("status", ["open", "matching"])
        )

        if sector:
            query = query.eq("sector", sector)
        if urgency:
            query = query.eq("urgency", urgency)

        if sort == "urgency":
            query = query.order("urgency", desc=False).order("created_at", desc=True)
        else:
            query = query.order("created_at", desc=True)

        result = query.execute()
        cases = result.data or []

        # Attach proposal counts
        if cases:
            case_ids = [c["id"] for c in cases]
            proposals_result = (
                supabase.table("chamber_proposals")
                .select("sourcing_case_id")
                .in_("sourcing_case_id", case_ids)
                .execute()
            )
            count_map: dict[str, int] = {}
            for p in proposals_result.data or []:
                cid = p["sourcing_case_id"]
                count_map[cid] = count_map.get(cid, 0) + 1

            for c in cases:
                c["proposal_count"] = count_map.get(c["id"], 0)
        else:
            for c in cases:
                c["proposal_count"] = 0

        # Truncate problem_statement to 500 chars for list view
        for c in cases:
            ps = c.get("problem_statement") or ""
            c["problem_statement"] = ps[:500]

        # Sort by proposal count client-side if requested
        if sort == "proposals":
            cases.sort(key=lambda x: x.get("proposal_count", 0), reverse=True)

        return {"cases": cases, "total": len(cases)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching public sourcing board: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "code": 500},
        )


@router.get(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Get single open sourcing case detail (no auth required)",
)
async def get_case_detail(case_id: str):
    """Return full public detail for a single open sourcing case.

    Only cases with status 'open' or 'matching' are accessible.
    Internal fields are never exposed.
    """
    try:
        result = (
            supabase.table("chamber_sourcing_cases")
            .select(PUBLIC_FIELDS + ", compliance_requirements")
            .eq("id", case_id)
            .in_("status", ["open", "matching"])
            .maybe_single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Case not found or not publicly available", "code": 404},
            )

        case = result.data

        # Count proposals for this case
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("id", count="exact")
            .eq("sourcing_case_id", case_id)
            .execute()
        )
        case["proposal_count"] = len(proposals_result.data or [])

        return case

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching public case detail %s: %s", case_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "code": 500},
        )
