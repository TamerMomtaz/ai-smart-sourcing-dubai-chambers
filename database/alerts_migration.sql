-- Alert system migration
-- Tracks anomalous events for Dashboard and Compliance pages

CREATE TABLE IF NOT EXISTS chamber_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_type TEXT NOT NULL CHECK (alert_type IN
    ('security', 'compliance', 'ai_anomaly', 'system')),
  severity TEXT DEFAULT 'medium' CHECK (severity IN
    ('low', 'medium', 'high', 'critical')),
  title TEXT NOT NULL,
  description TEXT,
  is_read BOOLEAN DEFAULT false,
  is_resolved BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

ALTER TABLE chamber_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access to alerts" ON chamber_alerts
  FOR ALL USING (true) WITH CHECK (true);

GRANT ALL ON chamber_alerts TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
