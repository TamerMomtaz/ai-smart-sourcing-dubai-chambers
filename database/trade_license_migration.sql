-- Migration: Trade License Verification stub
-- Adds trade license columns to chamber_vendors for Dubai GRP integration.

ALTER TABLE chamber_vendors
  ADD COLUMN IF NOT EXISTS trade_license_number TEXT,
  ADD COLUMN IF NOT EXISTS trade_license_status TEXT DEFAULT 'unverified'
    CHECK (trade_license_status IN ('unverified', 'pending', 'verified', 'expired', 'invalid')),
  ADD COLUMN IF NOT EXISTS trade_license_verified_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS trade_license_details JSONB;

-- Add 'license_verification' to chamber_ai_interactions operation_type constraint
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
            'hallucination_check', 'vendor_profile_edit', 'content_scan',
            'license_verification'
        ));
END $$;
