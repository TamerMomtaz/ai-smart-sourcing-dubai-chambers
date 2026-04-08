-- DEVONEERS updated_at trigger function

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create chamber_vendors table
CREATE TABLE chamber_vendors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  company_registration text UNIQUE,
  country text NOT NULL,
  contact_email text NOT NULL,
  contact_phone text,
  website text,
  is_desc_approved boolean NOT NULL DEFAULT false,
  desc_badge_issued_date timestamptz,
  onboarding_status text CHECK (onboarding_status IN ('submitted', 'shortlisted', 'pilot', 'procurement', 'rejected')) DEFAULT 'submitted',
  submission_history_count integer NOT NULL DEFAULT 0,
  average_compliance_score numeric(5,2),
  api_access_enabled boolean NOT NULL DEFAULT false,
  api_key_hash text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_vendors_email ON chamber_vendors(contact_email);
CREATE INDEX idx_chamber_vendors_desc_approved ON chamber_vendors(is_desc_approved);
CREATE INDEX idx_chamber_vendors_onboarding_status ON chamber_vendors(onboarding_status);
CREATE INDEX idx_chamber_vendors_name ON chamber_vendors(name);
CREATE INDEX idx_chamber_vendors_country ON chamber_vendors(country);

ALTER TABLE chamber_vendors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view own data" ON chamber_vendors
  FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Vendors can update own data" ON chamber_vendors
  FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Analysts can view all vendors" ON chamber_vendors
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'admin'));

-- Create chamber_vendor_profiles table
CREATE TABLE chamber_vendor_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id uuid NOT NULL REFERENCES chamber_vendors(id) ON DELETE CASCADE,
  team_size integer,
  funding_stage text CHECK (funding_stage IN ('pre-seed', 'seed', 'series-a', 'series-b', 'series-c', 'series-d+', 'bootstrapped', 'established')),
  technology_stack jsonb,
  certifications jsonb,
  onboarding_stage text,
  pilot_status text CHECK (pilot_status IN ('not_started', 'in_progress', 'completed', 'failed')),
  procurement_status text CHECK (procurement_status IN ('not_initiated', 'under_review', 'approved', 'contract_signed', 'rejected')),
  api_documentation_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_chamber_vendor_profiles_vendor_id ON chamber_vendor_profiles(vendor_id);
CREATE INDEX idx_chamber_vendor_profiles_pilot_status ON chamber_vendor_profiles(pilot_status);
CREATE INDEX idx_chamber_vendor_profiles_procurement_status ON chamber_vendor_profiles(procurement_status);

ALTER TABLE chamber_vendor_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view own profile" ON chamber_vendor_profiles
  FOR SELECT USING (vendor_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text));

CREATE POLICY "Vendors can update own profile" ON chamber_vendor_profiles
  FOR UPDATE USING (vendor_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text));

CREATE POLICY "Analysts can view all profiles" ON chamber_vendor_profiles
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'admin'));

-- Create chamber_business_groups table
CREATE TABLE chamber_business_groups (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  chamber text NOT NULL,
  description text,
  sector_kpis_json jsonb,
  evaluation_weight_config_json jsonb DEFAULT '{"relevance": 0.25, "feasibility": 0.25, "sector_alignment": 0.25, "compliance": 0.25}'::jsonb,
  lead_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_business_groups_chamber ON chamber_business_groups(chamber);
CREATE INDEX idx_chamber_business_groups_lead ON chamber_business_groups(lead_user_id);
CREATE INDEX idx_chamber_business_groups_name ON chamber_business_groups(name);

ALTER TABLE chamber_business_groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "All authenticated users can view business groups" ON chamber_business_groups
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Group leads can update their groups" ON chamber_business_groups
  FOR UPDATE USING (auth.uid() = lead_user_id);

CREATE POLICY "Admins can manage all groups" ON chamber_business_groups
  FOR ALL USING (auth.jwt()->>'role' = 'admin');

-- Create chamber_business_councils table
CREATE TABLE chamber_business_councils (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  country text NOT NULL,
  description text,
  representative_office_locations jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_business_councils_country ON chamber_business_councils(country);
CREATE INDEX idx_chamber_business_councils_name ON chamber_business_councils(name);

ALTER TABLE chamber_business_councils ENABLE ROW LEVEL SECURITY;

CREATE POLICY "All authenticated users can view councils" ON chamber_business_councils
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage councils" ON chamber_business_councils
  FOR ALL USING (auth.jwt()->>'role' = 'admin');

-- Create chamber_users table
CREATE TABLE chamber_users (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('viewer', 'analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin')) DEFAULT 'viewer',
  full_name text NOT NULL,
  chamber text,
  business_group_id uuid REFERENCES chamber_business_groups(id) ON DELETE SET NULL,
  preferred_language text CHECK (preferred_language IN ('en', 'ar')) DEFAULT 'en',
  last_login timestamptz,
  rbac_permissions_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_users_role ON chamber_users(role);
CREATE INDEX idx_chamber_users_business_group ON chamber_users(business_group_id);
CREATE UNIQUE INDEX idx_chamber_users_email ON chamber_users(email);

ALTER TABLE chamber_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON chamber_users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON chamber_users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Analysts can view all users" ON chamber_users
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'admin'));

CREATE POLICY "Admins can manage all users" ON chamber_users
  FOR ALL USING (auth.jwt()->>'role' = 'admin');

-- Create chamber_notification_preferences table
CREATE TABLE chamber_notification_preferences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES chamber_users(id) ON DELETE CASCADE,
  email_enabled boolean NOT NULL DEFAULT true,
  proposal_status_updates boolean NOT NULL DEFAULT true,
  weekly_digest boolean NOT NULL DEFAULT true,
  compliance_alerts boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_chamber_notification_preferences_user_id ON chamber_notification_preferences(user_id);

ALTER TABLE chamber_notification_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own preferences" ON chamber_notification_preferences
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON chamber_notification_preferences
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON chamber_notification_preferences
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create chamber_proposals table
CREATE TABLE chamber_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  submitter_id uuid NOT NULL REFERENCES chamber_vendors(id) ON DELETE CASCADE,
  submission_date timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL CHECK (status IN ('queued', 'submitted', 'evaluating', 'evaluated', 'approved', 'rejected', 'requires_review', 'requires_manual_review', 'shortlisted', 'under_review', 'needs_improvement', 'revision_requested')) DEFAULT 'queued',
  sector text,
  technology_type text,
  maturity_level text CHECK (maturity_level IN ('concept', 'prototype', 'mvp', 'production', 'scaled')),
  language text CHECK (language IN ('en', 'ar', 'mixed')) DEFAULT 'en',
  composite_score numeric(5,2) CHECK (composite_score >= 0 AND composite_score <= 100),
  relevance_score numeric(5,2) CHECK (relevance_score >= 0 AND relevance_score <= 100),
  feasibility_score numeric(5,2) CHECK (feasibility_score >= 0 AND feasibility_score <= 100),
  sector_alignment_score numeric(5,2) CHECK (sector_alignment_score >= 0 AND sector_alignment_score <= 100),
  compliance_score numeric(5,2) CHECK (compliance_score >= 0 AND compliance_score <= 100),
  evaluation_timestamp timestamptz,
  is_duplicate boolean NOT NULL DEFAULT false,
  requires_manual_review boolean NOT NULL DEFAULT false,
  d33_alignment_metrics jsonb,
  business_group_id uuid REFERENCES chamber_business_groups(id) ON DELETE SET NULL,
  business_council_id uuid REFERENCES chamber_business_councils(id) ON DELETE SET NULL,
  embedding vector(1536),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_proposals_submitter ON chamber_proposals(submitter_id);
CREATE INDEX idx_chamber_proposals_status ON chamber_proposals(status);
CREATE INDEX idx_chamber_proposals_sector ON chamber_proposals(sector);
CREATE INDEX idx_chamber_proposals_submission_date ON chamber_proposals(submission_date);
CREATE INDEX idx_chamber_proposals_composite_score ON chamber_proposals(composite_score);
CREATE INDEX idx_chamber_proposals_business_group ON chamber_proposals(business_group_id);
CREATE INDEX idx_chamber_proposals_business_council ON chamber_proposals(business_council_id);
CREATE INDEX idx_chamber_proposals_embedding ON chamber_proposals USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_chamber_proposals_technology_type ON chamber_proposals(technology_type);
CREATE INDEX idx_chamber_proposals_title ON chamber_proposals(title);

ALTER TABLE chamber_proposals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view own proposals" ON chamber_proposals
  FOR SELECT USING (submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text));

CREATE POLICY "Vendors can insert own proposals" ON chamber_proposals
  FOR INSERT WITH CHECK (submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text));

CREATE POLICY "Analysts can view all proposals" ON chamber_proposals
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

CREATE POLICY "Analysts can update all proposals" ON chamber_proposals
  FOR UPDATE USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

-- Create chamber_documents table
CREATE TABLE chamber_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL REFERENCES chamber_proposals(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_type text NOT NULL CHECK (file_type IN ('pdf', 'docx', 'pptx', 'xlsx')),
  file_size bigint NOT NULL,
  storage_path text NOT NULL,
  encryption_key_id text,
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  extracted_text text,
  extracted_tables_json jsonb,
  extracted_charts_json jsonb,
  financial_data_json jsonb,
  language_detected text CHECK (language_detected IN ('en', 'ar', 'mixed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_documents_proposal_id ON chamber_documents(proposal_id);
CREATE INDEX idx_chamber_documents_file_type ON chamber_documents(file_type);
CREATE INDEX idx_chamber_documents_uploaded_at ON chamber_documents(uploaded_at);

ALTER TABLE chamber_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view documents for own proposals" ON chamber_documents
  FOR SELECT USING (proposal_id IN (SELECT id FROM chamber_proposals WHERE submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text)));

CREATE POLICY "Vendors can insert documents for own proposals" ON chamber_documents
  FOR INSERT WITH CHECK (proposal_id IN (SELECT id FROM chamber_proposals WHERE submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text)));

CREATE POLICY "Analysts can view all documents" ON chamber_documents
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

-- Create chamber_evaluations table
CREATE TABLE chamber_evaluations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL REFERENCES chamber_proposals(id) ON DELETE CASCADE,
  relevance_score numeric(5,2) CHECK (relevance_score >= 0 AND relevance_score <= 100),
  relevance_reasoning text,
  feasibility_score numeric(5,2) CHECK (feasibility_score >= 0 AND feasibility_score <= 100),
  feasibility_reasoning text,
  sector_alignment_score numeric(5,2) CHECK (sector_alignment_score >= 0 AND sector_alignment_score <= 100),
  sector_reasoning text,
  compliance_score numeric(5,2) CHECK (compliance_score >= 0 AND compliance_score <= 100),
  compliance_reasoning text,
  composite_score numeric(5,2) CHECK (composite_score >= 0 AND composite_score <= 100),
  evaluated_at timestamptz NOT NULL DEFAULT now(),
  evaluator_agent_versions jsonb,
  hallucination_check_passed boolean NOT NULL DEFAULT true,
  prompt_injection_detected boolean NOT NULL DEFAULT false,
  summary_en text,
  summary_ar text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_chamber_evaluations_proposal_id ON chamber_evaluations(proposal_id);
CREATE INDEX idx_chamber_evaluations_composite_score ON chamber_evaluations(composite_score);
CREATE INDEX idx_chamber_evaluations_evaluated_at ON chamber_evaluations(evaluated_at);

ALTER TABLE chamber_evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view evaluations for own proposals" ON chamber_evaluations
  FOR SELECT USING (proposal_id IN (SELECT id FROM chamber_proposals WHERE submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text)));

CREATE POLICY "Analysts can view all evaluations" ON chamber_evaluations
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

CREATE POLICY "Analysts can insert evaluations" ON chamber_evaluations
  FOR INSERT WITH CHECK (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

-- Create chamber_compliance_audits table
CREATE TABLE chamber_compliance_audits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL REFERENCES chamber_proposals(id) ON DELETE CASCADE,
  audit_type text NOT NULL CHECK (audit_type IN ('automated', 'manual', 'hybrid')),
  isr_v3_compliance boolean,
  ai_security_policy_compliance boolean,
  csp_standards_compliance boolean,
  data_residency_verified boolean,
  audit_timestamp timestamptz NOT NULL DEFAULT now(),
  auditor_user_id uuid REFERENCES chamber_users(id) ON DELETE SET NULL,
  findings_json jsonb,
  remediation_required boolean NOT NULL DEFAULT false,
  audit_report_path text,
  hash_chain_signature text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_compliance_audits_proposal_id ON chamber_compliance_audits(proposal_id);
CREATE INDEX idx_chamber_compliance_audits_audit_timestamp ON chamber_compliance_audits(audit_timestamp);
CREATE INDEX idx_chamber_compliance_audits_remediation_required ON chamber_compliance_audits(remediation_required);
CREATE INDEX idx_chamber_compliance_audits_auditor_user_id ON chamber_compliance_audits(auditor_user_id);

ALTER TABLE chamber_compliance_audits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Compliance officers can view all audits" ON chamber_compliance_audits
  FOR SELECT USING (auth.jwt()->>'role' IN ('compliance_officer', 'admin'));

CREATE POLICY "Analysts can view audits for assigned proposals" ON chamber_compliance_audits
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'business_group_lead'));

CREATE POLICY "Compliance officers can insert audits" ON chamber_compliance_audits
  FOR INSERT WITH CHECK (auth.jwt()->>'role' IN ('compliance_officer', 'admin'));

-- Create chamber_comments table
CREATE TABLE chamber_comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL REFERENCES chamber_proposals(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES chamber_users(id) ON DELETE CASCADE,
  comment_text text NOT NULL,
  visibility text CHECK (visibility IN ('internal', 'vendor_visible')) DEFAULT 'internal',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_comments_proposal_id ON chamber_comments(proposal_id);
CREATE INDEX idx_chamber_comments_user_id ON chamber_comments(user_id);
CREATE INDEX idx_chamber_comments_created_at ON chamber_comments(created_at);

ALTER TABLE chamber_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vendors can view vendor-visible comments on own proposals" ON chamber_comments
  FOR SELECT USING (visibility = 'vendor_visible' AND proposal_id IN (SELECT id FROM chamber_proposals WHERE submitter_id IN (SELECT id FROM chamber_vendors WHERE auth.uid()::text = id::text)));

CREATE POLICY "Analysts can view all comments" ON chamber_comments
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

CREATE POLICY "Analysts can insert comments" ON chamber_comments
  FOR INSERT WITH CHECK (auth.jwt()->>'role' IN ('analyst', 'executive', 'compliance_officer', 'business_group_lead', 'admin'));

-- Create chamber_ai_interactions table
CREATE TABLE chamber_ai_interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL,
  user_id uuid REFERENCES chamber_users(id) ON DELETE SET NULL,
  evaluation_id uuid REFERENCES chamber_evaluations(id) ON DELETE SET NULL,
  model_name text NOT NULL,
  prompt_tokens integer NOT NULL,
  completion_tokens integer NOT NULL,
  latency_ms integer NOT NULL,
  cost_usd numeric(10,6) NOT NULL,
  energy_kwh numeric(12,8) NOT NULL,
  carbon_gco2 numeric(12,6) NOT NULL,
  intelligence_units numeric(12,4) NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  operation_type text CHECK (operation_type IN ('evaluation', 'extraction', 'classification', 'summary', 'trend_analysis', 'compliance_check')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_ai_interactions_session_id ON chamber_ai_interactions(session_id);
CREATE INDEX idx_chamber_ai_interactions_user_id ON chamber_ai_interactions(user_id);
CREATE INDEX idx_chamber_ai_interactions_evaluation_id ON chamber_ai_interactions(evaluation_id);
CREATE INDEX idx_chamber_ai_interactions_timestamp ON chamber_ai_interactions(timestamp);
CREATE INDEX idx_chamber_ai_interactions_operation_type ON chamber_ai_interactions(operation_type);

ALTER TABLE chamber_ai_interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Executives can view all AI interactions" ON chamber_ai_interactions
  FOR SELECT USING (auth.jwt()->>'role' IN ('executive', 'admin'));

CREATE POLICY "Users can view own interactions" ON chamber_ai_interactions
  FOR SELECT USING (auth.uid() = user_id);

-- Create chamber_trend_analyses table
CREATE TABLE chamber_trend_analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_date date NOT NULL,
  sector text,
  technology_trends_json jsonb,
  submission_volume integer NOT NULL,
  average_scores jsonb,
  emerging_technologies jsonb,
  generated_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_trend_analyses_analysis_date ON chamber_trend_analyses(analysis_date);
CREATE INDEX idx_chamber_trend_analyses_sector ON chamber_trend_analyses(sector);

ALTER TABLE chamber_trend_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Analysts can view all trend analyses" ON chamber_trend_analyses
  FOR SELECT USING (auth.jwt()->>'role' IN ('analyst', 'executive', 'business_group_lead', 'admin'));

CREATE POLICY "Analysts can insert trend analyses" ON chamber_trend_analyses
  FOR INSERT WITH CHECK (auth.jwt()->>'role' IN ('analyst', 'executive', 'business_group_lead', 'admin'));

-- Create chamber_desc_certified_providers table
CREATE TABLE chamber_desc_certified_providers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_name text NOT NULL UNIQUE,
  certification_number text NOT NULL UNIQUE,
  valid_until date NOT NULL,
  services_offered jsonb,
  compliance_frameworks jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chamber_desc_certified_providers_valid_until ON chamber_desc_certified_providers(valid_until);
CREATE UNIQUE INDEX idx_chamber_desc_certified_providers_certification_number ON chamber_desc_certified_providers(certification_number);
CREATE INDEX idx_chamber_desc_certified_providers_provider_name ON chamber_desc_certified_providers(provider_name);

ALTER TABLE chamber_desc_certified_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "All authenticated users can view certified providers" ON chamber_desc_certified_providers
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Compliance officers can manage certified providers" ON chamber_desc_certified_providers
  FOR ALL USING (auth.jwt()->>'role' IN ('compliance_officer', 'admin'));

-- Updated_at Triggers

CREATE TRIGGER set_updated_at_chamber_business_groups
    BEFORE UPDATE ON chamber_business_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_business_councils
    BEFORE UPDATE ON chamber_business_councils
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_proposals
    BEFORE UPDATE ON chamber_proposals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_ai_interactions
    BEFORE UPDATE ON chamber_ai_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_trend_analyses
    BEFORE UPDATE ON chamber_trend_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_vendors
    BEFORE UPDATE ON chamber_vendors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_evaluations
    BEFORE UPDATE ON chamber_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_desc_certified_providers
    BEFORE UPDATE ON chamber_desc_certified_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_compliance_audits
    BEFORE UPDATE ON chamber_compliance_audits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_users
    BEFORE UPDATE ON chamber_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_notification_preferences
    BEFORE UPDATE ON chamber_notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_vendor_profiles
    BEFORE UPDATE ON chamber_vendor_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_documents
    BEFORE UPDATE ON chamber_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_chamber_comments
    BEFORE UPDATE ON chamber_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add hash chain columns for tamper-evident audit logging
ALTER TABLE chamber_ai_interactions
  ADD COLUMN IF NOT EXISTS integrity_hash TEXT,
  ADD COLUMN IF NOT EXISTS previous_hash TEXT;
