-- Migration: chamber_evaluation_overrides
-- Human Override system for AI evaluations
-- Analysts can adjust AI scores with documented reasoning

CREATE TABLE IF NOT EXISTS chamber_evaluation_overrides (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID REFERENCES chamber_evaluations(id) NOT NULL,
  dimension TEXT NOT NULL CHECK (dimension IN
    ('relevance', 'feasibility', 'compliance', 'sector_alignment', 'composite')),
  ai_original_score NUMERIC NOT NULL,
  human_adjusted_score NUMERIC NOT NULL,
  override_reason TEXT NOT NULL,
  overridden_by UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_evaluation_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access to overrides" ON chamber_evaluation_overrides
  FOR ALL USING (true) WITH CHECK (true);

GRANT ALL ON chamber_evaluation_overrides TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
