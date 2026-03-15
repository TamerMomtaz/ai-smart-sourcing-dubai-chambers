from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


class ChamberDocumentService:
    """Service for managing chamber document operations."""

    @staticmethod
    def create(
        user_id: UUID,
        proposal_id: UUID,
        file_name: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        encryption_key_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new chamber document record.
        
        Args:
            user_id: User UUID creating the document
            proposal_id: Associated proposal UUID
            file_name: Original file name
            file_type: File type (pdf, docx, pptx, xlsx)
            file_size: File size in bytes
            storage_path: Supabase Storage path
            encryption_key_id: Optional encryption key reference
            
        Returns:
            Document record or None if creation fails
        """
        # Verify user owns the proposal
        proposal_check = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id")
            .eq("id", str(proposal_id))
            .eq("submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not proposal_check.data:
            return None
        
        document_data = {
            "proposal_id": str(proposal_id),
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "storage_path": storage_path,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if encryption_key_id:
            document_data["encryption_key_id"] = encryption_key_id
        
        result = (
            supabase.table("chamber_documents")
            .insert(document_data)
            .execute()
        )
        
        return result.data[0] if result.data else None

    @staticmethod
    def list(
        user_id: UUID,
        proposal_id: Optional[UUID] = None,
        file_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List chamber documents with pagination and filters.
        
        Args:
            user_id: User UUID requesting documents
            proposal_id: Optional filter by proposal ID
            file_type: Optional filter by file type
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (document list, total count)
        """
        # Build base query - check ownership through proposals
        query = (
            supabase.table("chamber_documents")
            .select(
                "*",
                count="exact"
            )
        )
        
        # Filter by proposal_id if provided
        if proposal_id:
            # Verify user owns the proposal
            proposal_check = (
                supabase.table("chamber_proposals")
                .select("id")
                .eq("id", str(proposal_id))
                .eq("submitter_id", str(user_id))
                .maybe_single()
                .execute()
            )
            
            if not proposal_check.data:
                return [], 0
            
            query = query.eq("proposal_id", str(proposal_id))
        else:
            # Get all proposals owned by user
            user_proposals = (
                supabase.table("chamber_proposals")
                .select("id")
                .eq("submitter_id", str(user_id))
                .execute()
            )
            
            if not user_proposals.data:
                return [], 0
            
            proposal_ids = [p["id"] for p in user_proposals.data]
            query = query.in_("proposal_id", proposal_ids)
        
        # Apply file_type filter
        if file_type:
            query = query.eq("file_type", file_type)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        # Order by upload time descending
        query = query.order("uploaded_at", desc=True)
        
        result = query.execute()
        
        total = result.count if result.count else 0
        documents = result.data if result.data else []
        
        return documents, total

    @staticmethod
    def get_by_id(user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single document by ID with ownership verification.
        
        Args:
            user_id: User UUID requesting the document
            document_id: Document UUID
            
        Returns:
            Document record or None if not found/unauthorized
        """
        # Get document with proposal join to verify ownership
        result = (
            supabase.table("chamber_documents")
            .select("*, chamber_proposals!inner(submitter_id)")
            .eq("id", str(document_id))
            .eq("chamber_proposals.submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        return result.data if result.data else None

    @staticmethod
    def update(
        user_id: UUID,
        document_id: UUID,
        extracted_text: Optional[str] = None,
        extracted_tables_json: Optional[Dict[str, Any]] = None,
        extracted_charts_json: Optional[Dict[str, Any]] = None,
        financial_data_json: Optional[Dict[str, Any]] = None,
        language_detected: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update document extracted data (typically after processing).
        
        Args:
            user_id: User UUID performing update
            document_id: Document UUID
            extracted_text: Extracted plain text
            extracted_tables_json: Structured table data
            extracted_charts_json: Chart metadata and data
            financial_data_json: Financial metrics
            language_detected: Detected language code
            
        Returns:
            Updated document record or None if not found/unauthorized
        """
        # Verify ownership through proposal
        ownership_check = (
            supabase.table("chamber_documents")
            .select("id, chamber_proposals!inner(submitter_id)")
            .eq("id", str(document_id))
            .eq("chamber_proposals.submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not ownership_check.data:
            return None
        
        update_data: Dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if extracted_text is not None:
            update_data["extracted_text"] = extracted_text
        
        if extracted_tables_json is not None:
            update_data["extracted_tables_json"] = extracted_tables_json
        
        if extracted_charts_json is not None:
            update_data["extracted_charts_json"] = extracted_charts_json
        
        if financial_data_json is not None:
            update_data["financial_data_json"] = financial_data_json
        
        if language_detected is not None:
            update_data["language_detected"] = language_detected
        
        result = (
            supabase.table("chamber_documents")
            .update(update_data)
            .eq("id", str(document_id))
            .execute()
        )
        
        return result.data[0] if result.data else None

    @staticmethod
    def delete(user_id: UUID, document_id: UUID) -> bool:
        """
        Delete a document (hard delete due to CASCADE on proposal).
        
        Args:
            user_id: User UUID performing deletion
            document_id: Document UUID
            
        Returns:
            True if deleted, False if not found/unauthorized
        """
        # Verify ownership through proposal
        ownership_check = (
            supabase.table("chamber_documents")
            .select("id, storage_path, chamber_proposals!inner(submitter_id)")
            .eq("id", str(document_id))
            .eq("chamber_proposals.submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not ownership_check.data:
            return False
        
        # Delete from database (storage cleanup should be handled separately)
        result = (
            supabase.table("chamber_documents")
            .delete()
            .eq("id", str(document_id))
            .execute()
        )
        
        return len(result.data) > 0 if result.data else False

    @staticmethod
    def get_by_proposal(user_id: UUID, proposal_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all documents for a specific proposal.
        
        Args:
            user_id: User UUID requesting documents
            proposal_id: Proposal UUID
            
        Returns:
            List of document records
        """
        # Verify user owns the proposal
        proposal_check = (
            supabase.table("chamber_proposals")
            .select("id")
            .eq("id", str(proposal_id))
            .eq("submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not proposal_check.data:
            return []
        
        result = (
            supabase.table("chamber_documents")
            .select("*")
            .eq("proposal_id", str(proposal_id))
            .order("uploaded_at", desc=True)
            .execute()
        )
        
        return result.data if result.data else []

    @staticmethod
    def get_storage_path(user_id: UUID, document_id: UUID) -> Optional[str]:
        """
        Get the storage path for a document (for generating signed URLs).
        
        Args:
            user_id: User UUID requesting storage path
            document_id: Document UUID
            
        Returns:
            Storage path or None if not found/unauthorized
        """
        document = ChamberDocumentService.get_by_id(user_id, document_id)
        
        if not document:
            return None
        
        return document.get("storage_path")

    @staticmethod
    def get_extracted_data(user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get all extracted data for a document.
        
        Args:
            user_id: User UUID requesting data
            document_id: Document UUID
            
        Returns:
            Dictionary with extracted data or None
        """
        result = (
            supabase.table("chamber_documents")
            .select(
                "id, file_name, extracted_text, extracted_tables_json, "
                "extracted_charts_json, financial_data_json, language_detected, "
                "chamber_proposals!inner(submitter_id)"
            )
            .eq("id", str(document_id))
            .eq("chamber_proposals.submitter_id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not result.data:
            return None
        
        return {
            "document_id": result.data["id"],
            "file_name": result.data["file_name"],
            "extracted_text": result.data.get("extracted_text"),
            "extracted_tables": result.data.get("extracted_tables_json"),
            "extracted_charts": result.data.get("extracted_charts_json"),
            "financial_data": result.data.get("financial_data_json"),
            "language_detected": result.data.get("language_detected"),
        }
