-- Vendor Factsheets — Migration
-- Stores auto-generated one-page vendor factsheets used by
-- chamber analysts for introductions (mirrors DCDE Business in Dubai workflow).

CREATE TABLE IF NOT EXISTS chamber_vendor_factsheets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id UUID REFERENCES chamber_vendors(id) NOT NULL,
  sourcing_case_id UUID REFERENCES chamber_sourcing_cases(id),
  content JSONB NOT NULL,
  ai_summary TEXT,
  generated_by UUID,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_vendor_factsheets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to factsheets" ON chamber_vendor_factsheets
  FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON chamber_vendor_factsheets TO anon, authenticated;

-- Add 'factsheet_generation' to the valid operation_type values for chamber_ai_interactions.
DO $$
BEGIN
  ALTER TABLE chamber_ai_interactions
    DROP CONSTRAINT IF EXISTS chamber_ai_interactions_operation_type_check;
  ALTER TABLE chamber_ai_interactions
    ADD CONSTRAINT chamber_ai_interactions_operation_type_check
    CHECK (operation_type IN (
      'evaluation', 'extraction', 'classification', 'summary',
      'trend_analysis', 'compliance_check', 'proposal_evaluation',
      'vendor_matching', 'factsheet_generation'
    ));
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'Could not update operation_type constraint: %', SQLERRM;
END
$$;

NOTIFY pgrst, 'reload schema';
