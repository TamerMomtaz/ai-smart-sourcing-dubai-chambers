-- Sourcing Intake API — Migration
-- Adds source_channel column and "intake" status to chamber_sourcing_cases.

-- 1. Add source_channel column
ALTER TABLE chamber_sourcing_cases
  ADD COLUMN IF NOT EXISTS source_channel TEXT DEFAULT 'manual';

-- 2. Drop the old status CHECK constraint and recreate with "intake" included.
--    The constraint name may vary; use a DO block to find and drop it safely.
DO $$
DECLARE
  _con_name TEXT;
BEGIN
  SELECT conname INTO _con_name
    FROM pg_constraint
   WHERE conrelid = 'chamber_sourcing_cases'::regclass
     AND contype = 'c'
     AND pg_get_constraintdef(oid) ILIKE '%status%';

  IF _con_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE chamber_sourcing_cases DROP CONSTRAINT %I', _con_name);
  END IF;
END;
$$;

ALTER TABLE chamber_sourcing_cases
  ADD CONSTRAINT chamber_sourcing_cases_status_check
  CHECK (status IN ('intake', 'open', 'matching', 'evaluating', 'shortlisted', 'pilot', 'completed', 'closed'));

NOTIFY pgrst, 'reload schema';
