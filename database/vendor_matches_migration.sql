-- Vendor Matches — Migration
-- Stores AI-discovered vendor matches for sourcing cases.

CREATE TABLE IF NOT EXISTS chamber_vendor_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sourcing_case_id UUID REFERENCES chamber_sourcing_cases(id) NOT NULL,
  vendor_id UUID REFERENCES chamber_vendors(id) NOT NULL,
  match_score NUMERIC,
  match_reasoning TEXT,
  status TEXT DEFAULT 'suggested' CHECK (status IN ('suggested', 'invited', 'submitted', 'declined')),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_vendor_matches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to vendor matches" ON chamber_vendor_matches
  FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON chamber_vendor_matches TO anon, authenticated;

-- Add 'vendor_matching' to the valid operation_type values for chamber_ai_interactions.
-- If the constraint exists, drop and recreate it; otherwise this is a no-op safety measure.
DO $$
BEGIN
  -- Attempt to drop the existing check constraint on operation_type
  ALTER TABLE chamber_ai_interactions
    DROP CONSTRAINT IF EXISTS chamber_ai_interactions_operation_type_check;
  -- Recreate with the expanded set including vendor_matching
  ALTER TABLE chamber_ai_interactions
    ADD CONSTRAINT chamber_ai_interactions_operation_type_check
    CHECK (operation_type IN (
      'evaluation', 'extraction', 'classification', 'summary',
      'trend_analysis', 'compliance_check', 'proposal_evaluation',
      'vendor_matching'
    ));
EXCEPTION WHEN OTHERS THEN
  -- If the column has no constraint, this is fine — the insert will work anyway
  RAISE NOTICE 'Could not update operation_type constraint: %', SQLERRM;
END
$$;

NOTIFY pgrst, 'reload schema';
