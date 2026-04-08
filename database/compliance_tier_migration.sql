-- Compliance Tier Migration
-- Adds compliance_tier column to chamber_sourcing_cases for tier-based vendor filtering.

ALTER TABLE chamber_sourcing_cases ADD COLUMN IF NOT EXISTS
  compliance_tier TEXT DEFAULT 'standard' CHECK (compliance_tier IN
    ('open', 'standard', 'government', 'critical'));

NOTIFY pgrst, 'reload schema';
