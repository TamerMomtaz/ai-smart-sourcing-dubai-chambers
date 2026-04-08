-- Migration: Create chamber_pilots table for Pilot Tracker
-- Tracks the lifecycle after shortlisting: pilot setup → execution → outcome

CREATE TABLE IF NOT EXISTS chamber_pilots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID REFERENCES chamber_proposals(id) NOT NULL,
  vendor_id UUID REFERENCES chamber_vendors(id),
  title TEXT NOT NULL,
  status TEXT DEFAULT 'setup' CHECK (status IN
    ('setup', 'active', 'completed', 'cancelled', 'extended')),
  start_date DATE,
  end_date DATE,
  success_criteria TEXT,
  budget_allocated NUMERIC,
  budget_spent NUMERIC,
  outcome_rating INTEGER CHECK (outcome_rating BETWEEN 1 AND 5),
  outcome_summary TEXT,
  lessons_learned TEXT,
  adoption_decision TEXT CHECK (adoption_decision IN
    ('adopt', 'extend', 'pivot', 'terminate', 'pending')),
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_pilots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to pilots" ON chamber_pilots
  FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON chamber_pilots TO anon, authenticated;
NOTIFY pgrst, 'reload schema';
