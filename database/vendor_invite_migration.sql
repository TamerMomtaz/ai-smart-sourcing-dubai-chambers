-- Vendor Invite / Onboarding table
CREATE TABLE IF NOT EXISTS chamber_vendor_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token UUID UNIQUE NOT NULL,
    vendor_name TEXT NOT NULL,
    vendor_email TEXT NOT NULL,
    sector TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '30 days'),
    completed_at TIMESTAMPTZ
);

-- Grant access
GRANT ALL ON chamber_vendor_invites TO anon, authenticated;

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
