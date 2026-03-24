from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def create(
    user_id: UUID,
    session_id: UUID,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    cost_usd: float,
    energy_kwh: float,
    carbon_gco2: float,
    intelligence_units: float,
    operation_type: str,
    evaluation_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a new AI interaction log entry.
    """
    payload = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "model_name": model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "energy_kwh": energy_kwh,
        "carbon_gco2": carbon_gco2,
        "intelligence_units": intelligence_units,
        "operation_type": operation_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if evaluation_id:
        payload["evaluation_id"] = str(evaluation_id)

    response = supabase.table("chamber_ai_interactions").insert(payload).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def list_interactions(
    user_id: UUID,
    page: int = 1,
    page_size: int = 50,
    session_id: Optional[UUID] = None,
    operation_type: Optional[str] = None,
    platform_wide: bool = False,
) -> tuple[List[Dict[str, Any]], int]:
    """
    List AI interactions with optional filters and pagination.
    When platform_wide=True, returns all interactions across all users.
    """
    offset = (page - 1) * page_size

    query = supabase.table("chamber_ai_interactions").select("*", count="exact")
    if not platform_wide:
        query = query.eq("user_id", str(user_id))

    if session_id:
        query = query.eq("session_id", str(session_id))
    if operation_type:
        query = query.eq("operation_type", operation_type)

    query = query.order("timestamp", desc=True).range(offset, offset + page_size - 1)

    response = query.execute()
    total = response.count if response.count else 0
    return response.data if response.data else [], total


def get_by_id(user_id: UUID, interaction_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a specific AI interaction by ID (ownership verified).
    """
    response = (
        supabase.table("chamber_ai_interactions")
        .select("*")
        .eq("id", str(interaction_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_summary(
    user_id: UUID,
    session_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    platform_wide: bool = False,
) -> Dict[str, Any]:
    """
    Get summary statistics for AI interactions.
    When platform_wide=True, returns aggregate metrics across all users.
    """
    query = supabase.table("chamber_ai_interactions").select("*")
    if not platform_wide:
        query = query.eq("user_id", str(user_id))

    if session_id:
        query = query.eq("session_id", str(session_id))
    if start_date:
        query = query.gte("timestamp", start_date.isoformat())
    if end_date:
        query = query.lte("timestamp", end_date.isoformat())

    response = query.execute()
    interactions = response.data if response.data else []

    total_interactions = len(interactions)
    total_tokens = sum(i["prompt_tokens"] + i["completion_tokens"] for i in interactions)
    total_cost_usd = sum(float(i["cost_usd"]) for i in interactions)
    total_energy_kwh = sum(float(i["energy_kwh"]) for i in interactions)
    total_carbon_gco2 = sum(float(i["carbon_gco2"]) for i in interactions)
    total_intelligence_units = sum(float(i["intelligence_units"]) for i in interactions)

    model_breakdown = {}
    for interaction in interactions:
        model = interaction["model_name"]
        if model not in model_breakdown:
            model_breakdown[model] = {
                "model_name": model,
                "interaction_count": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "latencies": [],
            }
        model_breakdown[model]["interaction_count"] += 1
        model_breakdown[model]["total_tokens"] += interaction["prompt_tokens"] + interaction["completion_tokens"]
        model_breakdown[model]["total_cost_usd"] += float(interaction["cost_usd"])
        model_breakdown[model]["latencies"].append(interaction["latency_ms"])

    for model_data in model_breakdown.values():
        latencies = model_data.pop("latencies")
        model_data["average_latency_ms"] = sum(latencies) / len(latencies) if latencies else 0.0

    recent_interactions = sorted(interactions, key=lambda x: x["timestamp"], reverse=True)[:10]

    return {
        "total_interactions": total_interactions,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "total_energy_kwh": total_energy_kwh,
        "total_carbon_gco2": total_carbon_gco2,
        "total_intelligence_units": total_intelligence_units,
        "model_breakdown": list(model_breakdown.values()),
        "recent_interactions": recent_interactions,
    }


def get_by_evaluation(user_id: UUID, evaluation_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all AI interactions associated with a specific evaluation.
    """
    response = (
        supabase.table("chamber_ai_interactions")
        .select("*")
        .eq("evaluation_id", str(evaluation_id))
        .eq("user_id", str(user_id))
        .order("timestamp", desc=False)
        .execute()
    )
    return response.data if response.data else []


def get_by_session(user_id: UUID, session_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all AI interactions for a specific session.
    """
    response = (
        supabase.table("chamber_ai_interactions")
        .select("*")
        .eq("session_id", str(session_id))
        .eq("user_id", str(user_id))
        .order("timestamp", desc=False)
        .execute()
    )
    return response.data if response.data else []


def get_ai_interaction_summary(
    user_id: UUID,
    limit: int = 10,
    session_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    platform_wide: bool = False,
) -> Dict[str, Any]:
    """
    Convenience wrapper around get_summary that accepts a limit parameter.
    The limit controls how many recent_interactions are returned.
    """
    result = get_summary(
        user_id=user_id,
        session_id=session_id,
        start_date=start_date,
        end_date=end_date,
        platform_wide=platform_wide,
    )
    if limit and result.get("recent_interactions"):
        result["recent_interactions"] = result["recent_interactions"][:limit]
    return result


def delete(user_id: UUID, interaction_id: UUID) -> bool:
    """
    Soft delete an AI interaction (mark as deleted, never actually remove for audit).
    Note: This table doesn't have deleted_at column per schema, so we perform hard delete.
    For audit compliance, consider adding deleted_at column or using archive table.
    """
    response = (
        supabase.table("chamber_ai_interactions")
        .delete()
        .eq("id", str(interaction_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    return bool(response.data)
