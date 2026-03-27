-- Incident Management Migration
-- Addresses DESC requirement for incident response and disaster recovery

-- Create chamber_incidents table
CREATE TABLE IF NOT EXISTS chamber_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    incident_type TEXT CHECK (incident_type IN (
        'security_breach', 'data_leak', 'system_outage',
        'ai_anomaly', 'compliance_violation', 'vendor_issue',
        'performance_degradation', 'unauthorized_access'
    )),
    status TEXT DEFAULT 'open' CHECK (status IN (
        'open', 'investigating', 'contained', 'resolved', 'reported_to_desc'
    )),
    affected_systems TEXT[],
    reported_by UUID,
    assigned_to UUID,
    desc_report_required BOOLEAN DEFAULT false,
    desc_reported_at TIMESTAMPTZ,
    resolution_notes TEXT,
    resolution_date TIMESTAMPTZ,
    root_cause TEXT,
    preventive_measures TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chamber_incidents_status ON chamber_incidents(status);
CREATE INDEX IF NOT EXISTS idx_chamber_incidents_severity ON chamber_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_chamber_incidents_created_at ON chamber_incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chamber_incidents_incident_type ON chamber_incidents(incident_type);

-- Enable Row Level Security
ALTER TABLE chamber_incidents ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role full access on chamber_incidents"
    ON chamber_incidents
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Authenticated users can read incidents
CREATE POLICY "Authenticated users can read incidents"
    ON chamber_incidents
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Seed data: 3 example incidents
INSERT INTO chamber_incidents (title, description, severity, incident_type, status, affected_systems, desc_report_required, resolution_notes, resolution_date, root_cause, preventive_measures, created_at)
VALUES
(
    'AI Anomaly — Cross-Model Score Deviation Detected',
    'Hallucination Shield detected >15% score deviation between Claude and GPT-4o on proposal evaluation. Investigation confirmed model-specific interpretation differences, not data issue.',
    'medium',
    'ai_anomaly',
    'resolved',
    ARRAY['ai_evaluation_engine', 'hallucination_shield'],
    false,
    'Added cross-model calibration threshold. σI now flags deviations >15% for human review.',
    NOW() - INTERVAL '5 days',
    'Model-specific interpretation differences in evaluation criteria weighting',
    'Implemented cross-model calibration threshold with automatic flagging for deviations exceeding 15%',
    NOW() - INTERVAL '7 days'
),
(
    'Scheduled Maintenance — Database Backup Verification',
    'Routine backup verification completed. All Supabase automated backups confirmed intact for past 30 days.',
    'low',
    'system_outage',
    'resolved',
    ARRAY['database', 'supabase_storage'],
    false,
    'Backup integrity verified. No data loss risk.',
    NOW() - INTERVAL '2 days',
    'Routine maintenance — no root cause applicable',
    'Continue monthly backup verification schedule',
    NOW() - INTERVAL '3 days'
),
(
    'Vendor Data Update — Unauthorized Edit Attempt',
    'Non-admin user attempted to modify vendor reputation data via direct API call. Request blocked by RLS policy.',
    'high',
    'unauthorized_access',
    'reported_to_desc',
    ARRAY['vendor_management', 'rls_policies', 'api_gateway'],
    true,
    'RLS policies confirmed effective. Added logging for blocked modification attempts. Reported to DESC per policy.',
    NOW() - INTERVAL '1 day',
    'Non-admin user attempted direct API manipulation to bypass frontend access controls',
    'Enhanced API request logging for blocked RLS attempts. Added real-time alerting for unauthorized data modification attempts.',
    NOW() - INTERVAL '2 days'
);

-- Update desc_reported_at for the third incident
UPDATE chamber_incidents
SET desc_reported_at = NOW()
WHERE title = 'Vendor Data Update — Unauthorized Edit Attempt';
