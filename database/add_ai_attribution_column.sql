-- Migration: Add ai_attribution JSONB column to chamber_evaluations
-- Stores dimension-level evidence attribution from AI evaluations
-- Structure: { dimensions: { relevance: { score, evidence[], risks[], confidence }, ... }, composite_score, overall_reasoning }

ALTER TABLE chamber_evaluations
  ADD COLUMN IF NOT EXISTS ai_attribution jsonb DEFAULT NULL;

COMMENT ON COLUMN chamber_evaluations.ai_attribution IS 'Structured evidence attribution per dimension: evidence points, risk factors, and confidence levels';
