-- Sector-to-analyst assignment mapping for auto-assignment on sourcing case creation
CREATE TABLE IF NOT EXISTS chamber_sector_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sector TEXT NOT NULL,
  assigned_user_id UUID REFERENCES chamber_users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chamber_sector_assignments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access" ON chamber_sector_assignments
  FOR ALL USING (true) WITH CHECK (true);

GRANT ALL ON chamber_sector_assignments TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
