-- σI Hallucination Shield — Database Migration
-- Creates chamber_hallucination_checks table for AI integrity verification

CREATE TABLE IF NOT EXISTS chamber_hallucination_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES chamber_evaluations(id),
    proposal_id UUID REFERENCES chamber_proposals(id),
    grounding_score NUMERIC DEFAULT 0,
    total_claims INTEGER DEFAULT 0,
    grounded_claims INTEGER DEFAULT 0,
    partial_claims INTEGER DEFAULT 0,
    ungrounded_claims INTEGER DEFAULT 0,
    claims_detail JSONB DEFAULT '[]',
    cross_model_score NUMERIC,
    cross_model_provider TEXT,
    primary_score NUMERIC,
    score_deviation NUMERIC,
    deviation_within_threshold BOOLEAN DEFAULT true,
    hallucination_risk TEXT DEFAULT 'low',
    desc_lifecycle_phase TEXT DEFAULT 'monitor',
    desc_compliance_status JSONB DEFAULT '{}',
    verification_iu NUMERIC DEFAULT 0,
    verification_cost_usd NUMERIC DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE chamber_hallucination_checks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for authenticated" ON chamber_hallucination_checks
    FOR ALL USING (true) WITH CHECK (true);

-- Add 'hallucination_check' to chamber_ai_interactions operation_type constraint if it exists
-- Check and update the constraint
DO $$
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname LIKE '%operation_type%'
        AND conrelid = 'chamber_ai_interactions'::regclass
    ) INTO constraint_exists;

    IF constraint_exists THEN
        -- Drop and recreate with new value
        ALTER TABLE chamber_ai_interactions
            DROP CONSTRAINT IF EXISTS chamber_ai_interactions_operation_type_check;
        ALTER TABLE chamber_ai_interactions
            ADD CONSTRAINT chamber_ai_interactions_operation_type_check
            CHECK (operation_type IN (
                'evaluation', 'extraction', 'classification', 'summary',
                'trend_analysis', 'compliance_check', 'proposal_evaluation',
                'hallucination_check'
            ));
    END IF;
END $$;
