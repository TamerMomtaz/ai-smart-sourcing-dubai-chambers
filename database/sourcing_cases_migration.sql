-- Sourcing Cases Engine — Migration
-- Creates the chamber_sourcing_cases table and links proposals to cases.

CREATE TABLE IF NOT EXISTS chamber_sourcing_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  problem_statement TEXT NOT NULL,
  requesting_entity TEXT,
  business_group_id UUID REFERENCES chamber_business_groups(id),
  sector TEXT,
  technology_domain TEXT,
  urgency TEXT DEFAULT 'medium' CHECK (urgency IN ('low', 'medium', 'high', 'critical')),
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'matching', 'evaluating', 'shortlisted', 'pilot', 'completed', 'closed')),
  compliance_requirements TEXT,
  assigned_analyst_id UUID,
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  closed_at TIMESTAMPTZ
);

ALTER TABLE chamber_sourcing_cases ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to sourcing cases" ON chamber_sourcing_cases
  FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON chamber_sourcing_cases TO anon, authenticated;

-- Link proposals to sourcing cases
ALTER TABLE chamber_proposals ADD COLUMN IF NOT EXISTS sourcing_case_id UUID REFERENCES chamber_sourcing_cases(id);

NOTIFY pgrst, 'reload schema';
