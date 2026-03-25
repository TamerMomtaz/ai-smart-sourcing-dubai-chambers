-- Migration: Add 'vendor_profile_edit' to chamber_ai_interactions operation_type constraint
-- This enables audit logging when admins edit vendor profile data.

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
        ALTER TABLE chamber_ai_interactions
            DROP CONSTRAINT IF EXISTS chamber_ai_interactions_operation_type_check;
    END IF;

    ALTER TABLE chamber_ai_interactions
        ADD CONSTRAINT chamber_ai_interactions_operation_type_check
        CHECK (operation_type IN (
            'evaluation', 'extraction', 'classification', 'summary',
            'trend_analysis', 'compliance_check', 'proposal_evaluation',
            'hallucination_check', 'vendor_profile_edit'
        ));
END $$;
