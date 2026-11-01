-- =============================================================================
-- CAMPUSPILOT AI — MIGRATION 004: PGVECTOR STORAGE & EMBEDDING PERSISTENCE
-- Enables pgvector extension, extends document_chunks schema with vector(768),
-- creates HNSW cosine index, and reinforces RLS access control.
-- =============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Extend document_chunks table with embedding metadata and vector(768)
DO $$
BEGIN
    -- Embedding vector column (768 dimensions for gemini-embedding-2 MRL)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN embedding vector(768);
    END IF;

    -- Embedding model name
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'embedding_model'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN embedding_model TEXT DEFAULT 'gemini-embedding-2';
    END IF;

    -- Embedding dimension
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'embedding_dimension'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN embedding_dimension INTEGER DEFAULT 768;
    END IF;

    -- Content hash (SHA-256 for idempotency)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'content_hash'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN content_hash TEXT;
    END IF;

    -- Configuration signature (e.g. gemini-embedding-2:768:RETRIEVAL_DOCUMENT)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'config_signature'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN config_signature TEXT;
    END IF;

    -- Updated timestamp
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN updated_at TIMESTAMPTZ DEFAULT timezone('utc', now());
    END IF;
END $$;

-- 3. Dedicated Indexes
-- Fast lookup by document and content hash for idempotency checking
CREATE INDEX IF NOT EXISTS idx_document_chunks_lookup 
    ON public.document_chunks (document_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_document_chunks_hash 
    ON public.document_chunks (document_id, content_hash);

-- HNSW Cosine Distance Index on vector(768)
-- Supports sub-millisecond approximate nearest neighbor searches for future RAG queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
    ON public.document_chunks USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

-- 4. Access Control & Row Level Security (RLS)
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

-- Ensure SELECT policy covers personal ownership and shared academic documents
DROP POLICY IF EXISTS "Users can view their own or shared document chunks" ON public.document_chunks;
CREATE POLICY "Users can view their own or shared document chunks"
    ON public.document_chunks FOR SELECT
    USING (auth.uid() = user_id OR scope = 'shared');

-- Ensure INSERT policy enforces user ownership
DROP POLICY IF EXISTS "Users can insert their own document chunks" ON public.document_chunks;
CREATE POLICY "Users can insert their own document chunks"
    ON public.document_chunks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Ensure UPDATE policy allows updating chunk embeddings for own documents
DROP POLICY IF EXISTS "Users can update their own document chunks" ON public.document_chunks;
CREATE POLICY "Users can update their own document chunks"
    ON public.document_chunks FOR UPDATE
    USING (auth.uid() = user_id);

-- Ensure DELETE policy allows deleting own chunks
DROP POLICY IF EXISTS "Users can delete their own document chunks" ON public.document_chunks;
CREATE POLICY "Users can delete their own document chunks"
    ON public.document_chunks FOR DELETE
    USING (auth.uid() = user_id);
