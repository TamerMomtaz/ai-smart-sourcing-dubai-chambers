-- Document Sanitization Migration
-- Adds sanitized_text and content_flags columns to chamber_proposals
-- for storing cleaned text and security scan results.

ALTER TABLE chamber_proposals
  ADD COLUMN IF NOT EXISTS sanitized_text TEXT,
  ADD COLUMN IF NOT EXISTS content_flags JSONB;

-- Add 'content_scan' to operation_type check constraint on chamber_ai_interactions
-- (if a CHECK constraint exists on operation_type, update it to include the new value)
DO $$
BEGIN
  -- Drop existing constraint if it exists, then re-create with new value
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'chamber_ai_interactions'::regclass
      AND conname LIKE '%operation_type%'
  ) THEN
    EXECUTE (
      SELECT 'ALTER TABLE chamber_ai_interactions DROP CONSTRAINT ' || conname
      FROM pg_constraint
      WHERE conrelid = 'chamber_ai_interactions'::regclass
        AND conname LIKE '%operation_type%'
      LIMIT 1
    );
    ALTER TABLE chamber_ai_interactions
      ADD CONSTRAINT chamber_ai_interactions_operation_type_check
      CHECK (operation_type IN (
        'evaluation', 'extraction', 'classification', 'summary',
        'trend_analysis', 'compliance_check', 'proposal_evaluation',
        'content_scan'
      ));
  END IF;
END $$;

-- Create index on content_flags for quick filtering of flagged proposals
CREATE INDEX IF NOT EXISTS idx_chamber_proposals_content_flags
  ON chamber_proposals USING gin (content_flags)
  WHERE content_flags IS NOT NULL;
