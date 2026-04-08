-- Migration: RAG-based Compliance Knowledge Base
-- Stores official compliance documents with vector embeddings for claim verification

-- pgvector extension is already enabled

CREATE TABLE IF NOT EXISTS chamber_compliance_knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chamber_compliance_knowledge_embedding_idx
  ON chamber_compliance_knowledge
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

ALTER TABLE chamber_compliance_knowledge ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'chamber_compliance_knowledge'
      AND policyname = 'Allow read access'
  ) THEN
    CREATE POLICY "Allow read access" ON chamber_compliance_knowledge
      FOR SELECT USING (true);
  END IF;
END $$;

GRANT SELECT ON chamber_compliance_knowledge TO anon, authenticated;
GRANT ALL ON chamber_compliance_knowledge TO authenticated;

NOTIFY pgrst, 'reload schema';
