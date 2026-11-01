-- =============================================================================
-- CAMPUSPILOT AI — PHASE 3 UPDATE: SHARED ADMIN DOCUMENT LIBRARY & ACCESS RULES
-- Migration 002: Adds scope column ('personal' vs 'shared') and updates RLS policies
-- =============================================================================

-- 1. Add scope to documents table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'documents'
        AND column_name = 'scope'
    ) THEN
        ALTER TABLE public.documents
        ADD COLUMN scope TEXT NOT NULL DEFAULT 'personal'
        CHECK (scope IN ('personal', 'shared'));
    END IF;
END $$;

-- 2. Add scope to document_chunks table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'document_chunks'
        AND column_name = 'scope'
    ) THEN
        ALTER TABLE public.document_chunks
        ADD COLUMN scope TEXT NOT NULL DEFAULT 'personal'
        CHECK (scope IN ('personal', 'shared'));
    END IF;
END $$;

-- 3. Create indexes for performant scope queries
CREATE INDEX IF NOT EXISTS idx_documents_scope ON public.documents(scope);
CREATE INDEX IF NOT EXISTS idx_document_chunks_scope ON public.document_chunks(scope);
CREATE INDEX IF NOT EXISTS idx_documents_user_scope ON public.documents(user_id, scope);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_scope ON public.document_chunks(user_id, scope);

-- 4. Update Documents RLS Policies
DROP POLICY IF EXISTS "Users can view their own documents" ON public.documents;
DROP POLICY IF EXISTS "Users can view their own or shared documents" ON public.documents;

CREATE POLICY "Users can view their own or shared documents"
    ON public.documents FOR SELECT
    USING (auth.uid() = user_id OR scope = 'shared');

-- 5. Update Document Chunks RLS Policies
DROP POLICY IF EXISTS "Users can view their own document chunks" ON public.document_chunks;
DROP POLICY IF EXISTS "Users can view their own or shared document chunks" ON public.document_chunks;

CREATE POLICY "Users can view their own or shared document chunks"
    ON public.document_chunks FOR SELECT
    USING (auth.uid() = user_id OR scope = 'shared');
