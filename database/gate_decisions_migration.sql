-- Stage-Gate Decision Workflow for Proposals
-- After AI evaluation, proposals go through structured gate decisions made by human committees.

CREATE TABLE IF NOT EXISTS chamber_gate_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID REFERENCES chamber_proposals(id) NOT NULL,
  gate_name TEXT NOT NULL CHECK (gate_name IN
    ('discovery', 'scoping', 'evaluation', 'pilot_approval', 'procurement')),
  decision TEXT CHECK (decision IN
    ('go', 'kill', 'hold', 'recycle', 'conditional_go')),
  decision_reason TEXT,
  decided_by UUID,
  committee_members JSONB,
  ai_recommendation TEXT,
  ai_score NUMERIC,
  conditions TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_gate_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to gate decisions" ON chamber_gate_decisions
  FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON chamber_gate_decisions TO anon, authenticated;
NOTIFY pgrst, 'reload schema';
