-- =============================================================================
-- CAMPUSPILOT AI — MIGRATION 005: SEMANTIC SIMILARITY SEARCH RPC FUNCTION
-- Provides stored function match_document_chunks for sub-millisecond pgvector search.
-- Uses cosine distance operator (<=>), enforces student isolation, and filters threshold.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.match_document_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.0,
    match_count int DEFAULT 5,
    filter_user_id uuid DEFAULT NULL,
    filter_document_id uuid DEFAULT NULL
)
RETURNS TABLE (
    chunk_id uuid,
    document_id uuid,
    filename text,
    user_id uuid,
    chunk_index int,
    page_number int,
    content text,
    token_count int,
    character_count int,
    scope text,
    similarity_score float
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id AS chunk_id,
        dc.document_id,
        d.filename,
        dc.user_id,
        dc.chunk_index,
        dc.page_number,
        dc.content,
        dc.token_count,
        dc.character_count,
        dc.scope,
        (1 - (dc.embedding <=> query_embedding))::float AS similarity_score
    FROM public.document_chunks dc
    JOIN public.documents d ON dc.document_id = d.id
    WHERE dc.embedding IS NOT NULL
      AND (
          -- Isolation: Personal document owned by student OR shared academic document
          (filter_user_id IS NOT NULL AND (dc.user_id = filter_user_id OR dc.scope = 'shared'))
          OR (filter_user_id IS NULL AND (dc.user_id = auth.uid() OR dc.scope = 'shared'))
      )
      AND (filter_document_id IS NULL OR dc.document_id = filter_document_id)
      AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;
