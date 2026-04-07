-- Migration: Add compliance gate columns to chamber_proposals
-- Pre-Evaluation Compliance Gate — deterministic, rule-based checks

ALTER TABLE chamber_proposals
  ADD COLUMN IF NOT EXISTS compliance_gate_result JSONB,
  ADD COLUMN IF NOT EXISTS compliance_gate_status TEXT DEFAULT 'pending';

-- Add CHECK constraint for compliance_gate_status
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chamber_proposals_compliance_gate_status_check'
  ) THEN
    ALTER TABLE chamber_proposals
      ADD CONSTRAINT chamber_proposals_compliance_gate_status_check
      CHECK (compliance_gate_status IN ('pending', 'pass', 'flagged', 'fail'));
  END IF;
END$$;
