-- Migration: Add Innovation Novelty dimension to evaluations
-- Adds novelty_score and novelty_reasoning to chamber_evaluations
-- Adds novelty_score to chamber_proposals for denormalized access
-- Updates override dimension constraint to include 'novelty'

-- Add novelty columns to chamber_evaluations
ALTER TABLE chamber_evaluations
  ADD COLUMN IF NOT EXISTS novelty_score NUMERIC(5,2) CHECK (novelty_score >= 0 AND novelty_score <= 100),
  ADD COLUMN IF NOT EXISTS novelty_reasoning TEXT;

-- Add novelty_score to chamber_proposals (denormalized, like other scores)
ALTER TABLE chamber_proposals
  ADD COLUMN IF NOT EXISTS novelty_score NUMERIC(5,2) CHECK (novelty_score >= 0 AND novelty_score <= 100);

-- Update chamber_evaluation_overrides dimension constraint to include 'novelty'
-- Drop the old constraint and add the new one
ALTER TABLE chamber_evaluation_overrides
  DROP CONSTRAINT IF EXISTS chamber_evaluation_overrides_dimension_check;

ALTER TABLE chamber_evaluation_overrides
  ADD CONSTRAINT chamber_evaluation_overrides_dimension_check
  CHECK (dimension IN ('relevance', 'feasibility', 'compliance', 'sector_alignment', 'composite', 'novelty'));

NOTIFY pgrst, 'reload schema';
