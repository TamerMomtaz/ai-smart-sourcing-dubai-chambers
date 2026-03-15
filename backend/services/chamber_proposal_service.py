from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


class ChamberProposalService:
    """Service layer for chamber_proposals table operations."""

    @staticmethod
    async def create(
        user_id: UUID,
        title: str,
        submitter_id: UUID,
        status: str = "queued",
        sector: Optional[str] = None,
        technology_type: Optional[str] = None,
        maturity_level: Optional[str] = None,
        language: str = "en",
        business_group_id: Optional[UUID] = None,
        business_council_id: Optional[UUID] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Create a new chamber proposal.
        
        Args:
            user_id: UUID of the user creating the proposal
            title: Proposal title
            submitter_id: UUID of the vendor submitting the proposal
            status: Proposal status (default: 'queued')
            sector: Industry sector
            technology_type: Technology category
            maturity_level: Product maturity stage
            language: Proposal language (default: 'en')
            business_group_id: Optional target business group ID
            business_council_id: Optional associated business council ID
            **kwargs: Additional fields (composite_score, relevance_score, etc.)
            
        Returns:
            Created proposal record or None if creation fails
        """
        try:
            proposal_data = {
                "title": title,
                "submitter_id": str(submitter_id),
                "submission_date": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "language": language,
                "is_duplicate": False,
                "requires_manual_review": False,
            }
            
            if sector:
                proposal_data["sector"] = sector
            if technology_type:
                proposal_data["technology_type"] = technology_type
            if maturity_level:
                proposal_data["maturity_level"] = maturity_level
            if business_group_id:
                proposal_data["business_group_id"] = str(business_group_id)
            if business_council_id:
                proposal_data["business_council_id"] = str(business_council_id)
            
            # Add optional score fields
            for score_field in [
                "composite_score",
                "relevance_score",
                "feasibility_score",
                "sector_alignment_score",
                "compliance_score",
            ]:
                if score_field in kwargs and kwargs[score_field] is not None:
                    proposal_data[score_field] = kwargs[score_field]
            
            # Add optional flags and timestamps
            if "is_duplicate" in kwargs:
                proposal_data["is_duplicate"] = kwargs["is_duplicate"]
            if "requires_manual_review" in kwargs:
                proposal_data["requires_manual_review"] = kwargs["requires_manual_review"]
            if "evaluation_timestamp" in kwargs and kwargs["evaluation_timestamp"]:
                proposal_data["evaluation_timestamp"] = kwargs["evaluation_timestamp"].isoformat()
            
            # Add JSON fields
            if "d33_alignment_metrics" in kwargs and kwargs["d33_alignment_metrics"]:
                proposal_data["d33_alignment_metrics"] = kwargs["d33_alignment_metrics"]
            
            result = supabase.table("chamber_proposals").insert(proposal_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error creating chamber proposal: {e}")
            return None

    @staticmethod
    async def list(
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        sector: Optional[str] = None,
        business_group_id: Optional[UUID] = None,
        submitter_id: Optional[UUID] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List chamber proposals with pagination and filters.
        
        Args:
            user_id: UUID of the requesting user
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional status filter
            sector: Optional sector filter
            business_group_id: Optional business group filter
            submitter_id: Optional submitter filter
            
        Returns:
            Tuple of (list of proposals, total count)
        """
        try:
            offset = (page - 1) * page_size
            
            # Build base query
            query = supabase.table("chamber_proposals").select(
                "*",
                count="exact"
            )
            
            # Apply filters
            if status:
                query = query.eq("status", status)
            if sector:
                query = query.eq("sector", sector)
            if business_group_id:
                query = query.eq("business_group_id", str(business_group_id))
            if submitter_id:
                query = query.eq("submitter_id", str(submitter_id))
            
            # Order by submission date descending
            query = query.order("submission_date", desc=True)
            
            # Apply pagination
            query = query.range(offset, offset + page_size - 1)
            
            result = query.execute()
            
            proposals = result.data if result.data else []
            total = result.count if result.count is not None else 0
            
            return proposals, total
            
        except Exception as e:
            print(f"Error listing chamber proposals: {e}")
            return [], 0

    @staticmethod
    async def get_by_id(user_id: UUID, proposal_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a chamber proposal by ID.
        
        Args:
            user_id: UUID of the requesting user
            proposal_id: UUID of the proposal to retrieve
            
        Returns:
            Proposal record or None if not found
        """
        try:
            result = supabase.table("chamber_proposals").select("*").eq(
                "id", str(proposal_id)
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting chamber proposal by ID: {e}")
            return None

    @staticmethod
    async def update(
        user_id: UUID,
        proposal_id: UUID,
        **update_fields
    ) -> Optional[Dict[str, Any]]:
        """Update a chamber proposal.
        
        Args:
            user_id: UUID of the user updating the proposal
            proposal_id: UUID of the proposal to update
            **update_fields: Fields to update
            
        Returns:
            Updated proposal record or None if update fails
        """
        try:
            # Verify proposal exists
            existing = await ChamberProposalService.get_by_id(user_id, proposal_id)
            if not existing:
                return None
            
            update_data = {}
            
            # Update allowed fields
            allowed_fields = [
                "title",
                "status",
                "sector",
                "technology_type",
                "maturity_level",
                "language",
                "composite_score",
                "relevance_score",
                "feasibility_score",
                "sector_alignment_score",
                "compliance_score",
                "is_duplicate",
                "requires_manual_review",
                "business_group_id",
                "business_council_id",
            ]
            
            for field in allowed_fields:
                if field in update_fields:
                    value = update_fields[field]
                    if value is not None:
                        if field.endswith("_id"):
                            update_data[field] = str(value)
                        else:
                            update_data[field] = value
            
            # Handle timestamp fields
            if "evaluation_timestamp" in update_fields and update_fields["evaluation_timestamp"]:
                if isinstance(update_fields["evaluation_timestamp"], datetime):
                    update_data["evaluation_timestamp"] = update_fields["evaluation_timestamp"].isoformat()
                else:
                    update_data["evaluation_timestamp"] = update_fields["evaluation_timestamp"]
            
            # Handle JSON fields
            if "d33_alignment_metrics" in update_fields:
                update_data["d33_alignment_metrics"] = update_fields["d33_alignment_metrics"]
            
            # Handle vector field
            if "embedding" in update_fields:
                update_data["embedding"] = update_fields["embedding"]
            
            if not update_data:
                return existing
            
            # Set updated_at
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = supabase.table("chamber_proposals").update(update_data).eq(
                "id", str(proposal_id)
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error updating chamber proposal: {e}")
            return None

    @staticmethod
    async def delete(user_id: UUID, proposal_id: UUID) -> bool:
        """Soft delete a chamber proposal by setting status to 'rejected'.
        
        Args:
            user_id: UUID of the user deleting the proposal
            proposal_id: UUID of the proposal to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Verify proposal exists
            existing = await ChamberProposalService.get_by_id(user_id, proposal_id)
            if not existing:
                return False
            
            # Soft delete by updating status
            result = supabase.table("chamber_proposals").update({
                "status": "rejected",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", str(proposal_id)).execute()
            
            return result.data is not None and len(result.data) > 0
            
        except Exception as e:
            print(f"Error deleting chamber proposal: {e}")
            return False

    @staticmethod
    async def get_by_submitter(
        user_id: UUID,
        submitter_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all proposals submitted by a specific vendor.
        
        Args:
            user_id: UUID of the requesting user
            submitter_id: UUID of the vendor
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of proposals, total count)
        """
        return await ChamberProposalService.list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            submitter_id=submitter_id
        )

    @staticmethod
    async def get_by_status(
        user_id: UUID,
        status: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all proposals with a specific status.
        
        Args:
            user_id: UUID of the requesting user
            status: Proposal status to filter by
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of proposals, total count)
        """
        return await ChamberProposalService.list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status
        )

    @staticmethod
    async def get_requiring_review(
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all proposals requiring manual review.
        
        Args:
            user_id: UUID of the requesting user
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of proposals, total count)
        """
        try:
            offset = (page - 1) * page_size
            
            query = supabase.table("chamber_proposals").select(
                "*",
                count="exact"
            ).eq("requires_manual_review", True).order(
                "submission_date", desc=True
            ).range(offset, offset + page_size - 1)
            
            result = query.execute()
            
            proposals = result.data if result.data else []
            total = result.count if result.count is not None else 0
            
            return proposals, total
            
        except Exception as e:
            print(f"Error getting proposals requiring review: {e}")
            return [], 0

    @staticmethod
    async def get_duplicates(
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all proposals flagged as duplicates.
        
        Args:
            user_id: UUID of the requesting user
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of proposals, total count)
        """
        try:
            offset = (page - 1) * page_size
            
            query = supabase.table("chamber_proposals").select(
                "*",
                count="exact"
            ).eq("is_duplicate", True).order(
                "submission_date", desc=True
            ).range(offset, offset + page_size - 1)
            
            result = query.execute()
            
            proposals = result.data if result.data else []
            total = result.count if result.count is not None else 0
            
            return proposals, total
            
        except Exception as e:
            print(f"Error getting duplicate proposals: {e}")
            return [], 0

    @staticmethod
    async def update_scores(
        user_id: UUID,
        proposal_id: UUID,
        relevance_score: Optional[float] = None,
        feasibility_score: Optional[float] = None,
        sector_alignment_score: Optional[float] = None,
        compliance_score: Optional[float] = None,
        composite_score: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Update evaluation scores for a proposal.
        
        Args:
            user_id: UUID of the user updating scores
            proposal_id: UUID of the proposal
            relevance_score: Relevance score (0-100)
            feasibility_score: Feasibility score (0-100)
            sector_alignment_score: Sector alignment score (0-100)
            compliance_score: Compliance score (0-100)
            composite_score: Composite score (0-100)
            
        Returns:
            Updated proposal record or None if update fails
        """
        update_fields = {}
        
        if relevance_score is not None:
            update_fields["relevance_score"] = relevance_score
        if feasibility_score is not None:
            update_fields["feasibility_score"] = feasibility_score
        if sector_alignment_score is not None:
            update_fields["sector_alignment_score"] = sector_alignment_score
        if compliance_score is not None:
            update_fields["compliance_score"] = compliance_score
        if composite_score is not None:
            update_fields["composite_score"] = composite_score
        
        # Set evaluation timestamp
        update_fields["evaluation_timestamp"] = datetime.now(timezone.utc)
        
        return await ChamberProposalService.update(
            user_id=user_id,
            proposal_id=proposal_id,
            **update_fields
        )
