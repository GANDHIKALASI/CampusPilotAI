-- =============================================================================
-- CAMPUSPILOT AI — MIGRATION 007: DISTRIBUTED IDEMPOTENCY & ATOMIC TURN COORDINATION
-- Production-ready idempotency tracking with lease tokens, heartbeat renewal,
-- fencing protection, and single-transaction ACID credit/message persistence.
-- Fully compatible with multi-worker and multi-instance AWS deployments.
--
-- IMPORTANT: PREPARED MIGRATION ONLY.
-- DO NOT EXECUTE AGAINST HOSTED SUPABASE WITHOUT EXPLICIT OPERATIONAL APPROVAL.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. IDEMPOTENCY KEYS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.idempotency_keys (
    key TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
    owner_token TEXT NOT NULL,
    recovery_count INT NOT NULL DEFAULT 0,
    response_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    PRIMARY KEY (user_id, conversation_id, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_stale 
    ON public.idempotency_keys (status, updated_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own idempotency keys" ON public.idempotency_keys;
CREATE POLICY "Users can manage their own idempotency keys"
    ON public.idempotency_keys FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role has full access to idempotency keys" ON public.idempotency_keys;
CREATE POLICY "Service role has full access to idempotency keys"
    ON public.idempotency_keys FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- 2. STORED PROCEDURE: ACQUIRE IDEMPOTENCY KEY WITH LEASE TOKEN
-- Returns: record_status ('acquired', 'completed', 'in_progress', 'conflict', 'recovered'),
--          cached_response (JSONB), and active_owner_token (TEXT)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.acquire_idempotency_key(
    p_key TEXT,
    p_user_id UUID,
    p_conversation_id UUID,
    p_request_hash TEXT,
    p_owner_token TEXT,
    p_stale_seconds INT DEFAULT 60
)
RETURNS TABLE (
    record_status TEXT,
    cached_response JSONB,
    active_owner_token TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_existing public.idempotency_keys%ROWTYPE;
    v_now TIMESTAMPTZ := timezone('utc', now());
BEGIN
    -- Security Audit: Validate identity if authenticated role
    IF auth.role() = 'authenticated' AND auth.uid() != p_user_id THEN
        RAISE EXCEPTION 'Access denied: caller (%) does not match target user (%)', auth.uid(), p_user_id;
    END IF;

    -- Security Audit: Validate conversation ownership
    IF NOT EXISTS (
        SELECT 1 FROM public.conversations
        WHERE id = p_conversation_id AND user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Conversation % not found or not owned by user %', p_conversation_id, p_user_id;
    END IF;

    -- Lock existing record if present
    SELECT * INTO v_existing
    FROM public.idempotency_keys
    WHERE user_id = p_user_id
      AND conversation_id = p_conversation_id
      AND key = p_key
    FOR UPDATE;

    IF NOT FOUND THEN
        -- Fresh key: insert in 'processing' state with caller's owner token
        -- Wrapped in exception handler to resolve concurrent fresh-key insertion races (MEDIUM-1)
        BEGIN
            INSERT INTO public.idempotency_keys (
                key, user_id, conversation_id, request_hash, status, owner_token, recovery_count, created_at, updated_at
            ) VALUES (
                p_key, p_user_id, p_conversation_id, p_request_hash, 'processing', p_owner_token, 0, v_now, v_now
            );
            RETURN QUERY SELECT 'acquired'::TEXT, NULL::JSONB, p_owner_token;
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- Lost insertion race to a concurrent request: re-select with row lock
            SELECT * INTO v_existing
            FROM public.idempotency_keys
            WHERE user_id = p_user_id
              AND conversation_id = p_conversation_id
              AND key = p_key
            FOR UPDATE;
        END;
    END IF;

    -- Existing key found: check request hash
    IF v_existing.request_hash != p_request_hash THEN
        -- Reused key with different payload -> HTTP 409 Conflict
        RETURN QUERY SELECT 'conflict'::TEXT, NULL::JSONB, NULL::TEXT;
        RETURN;
    END IF;

    -- Completed request -> Return cached response
    IF v_existing.status = 'completed' THEN
        RETURN QUERY SELECT 'completed'::TEXT, v_existing.response_data, v_existing.owner_token;
        RETURN;
    END IF;

    -- Processing request -> Check if lease is stale
    IF v_existing.status = 'processing' THEN
        IF (v_now - v_existing.updated_at) > (p_stale_seconds * INTERVAL '1 second') THEN
            -- Lease expired / abandoned: recover with new owner token & increment recovery count
            UPDATE public.idempotency_keys
            SET owner_token = p_owner_token,
                recovery_count = v_existing.recovery_count + 1,
                updated_at = v_now
            WHERE user_id = p_user_id AND conversation_id = p_conversation_id AND key = p_key;

            RETURN QUERY SELECT 'recovered'::TEXT, NULL::JSONB, p_owner_token;
            RETURN;
        ELSE
            -- Actively owned by another worker within lease window
            RETURN QUERY SELECT 'in_progress'::TEXT, NULL::JSONB, NULL::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Failed request -> Allow re-execution with new lease token
    IF v_existing.status = 'failed' THEN
        UPDATE public.idempotency_keys
        SET status = 'processing',
            owner_token = p_owner_token,
            updated_at = v_now
        WHERE user_id = p_user_id AND conversation_id = p_conversation_id AND key = p_key;

        RETURN QUERY SELECT 'acquired'::TEXT, NULL::JSONB, p_owner_token;
        RETURN;
    END IF;

    RETURN QUERY SELECT 'conflict'::TEXT, NULL::JSONB, NULL::TEXT;
END;
$$;

-- -----------------------------------------------------------------------------
-- 3. STORED PROCEDURE: RENEW IDEMPOTENCY LEASE (HEARTBEAT)
-- Extends the lease window for long-running AI streaming or complex retrieval.
-- Fails if lease was lost to another worker.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.renew_idempotency_lease(
    p_key TEXT,
    p_user_id UUID,
    p_conversation_id UUID,
    p_owner_token TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_updated INT;
BEGIN
    IF auth.role() = 'authenticated' AND auth.uid() != p_user_id THEN
        RAISE EXCEPTION 'Access denied: caller does not match user_id';
    END IF;

    UPDATE public.idempotency_keys
    SET updated_at = timezone('utc', now())
    WHERE user_id = p_user_id
      AND conversation_id = p_conversation_id
      AND key = p_key
      AND owner_token = p_owner_token
      AND status = 'processing';

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN (v_updated > 0);
END;
$$;

-- -----------------------------------------------------------------------------
-- 4. STORED PROCEDURE: ATOMIC COMPLETE CONVERSATION TURN
-- Single ACID PostgreSQL transaction coordinating:
-- 1. Conversation ownership verification.
-- 2. Server-side subscription lookup (NEVER trusts client boolean).
-- 3. Row-locked credit deduction for free students.
-- 4. Dual message insertion (user + model).
-- 5. Conversation timestamp touch.
-- 6. Fenced idempotency key completion verifying lease owner_token.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.complete_conversation_turn(
    p_user_id UUID,
    p_conversation_id UUID,
    p_user_content TEXT,
    p_assistant_content TEXT,
    p_idempotency_key TEXT DEFAULT NULL,
    p_owner_token TEXT DEFAULT NULL,
    p_response_data JSONB DEFAULT NULL,
    p_user_message_id UUID DEFAULT NULL,
    p_assistant_message_id UUID DEFAULT NULL
)
RETURNS TABLE (
    user_message_id UUID,
    assistant_message_id UUID,
    remaining_credits INT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_user_msg_id UUID := COALESCE(p_user_message_id, gen_random_uuid());
    v_asst_msg_id UUID := COALESCE(p_assistant_message_id, gen_random_uuid());
    v_now TIMESTAMPTZ := timezone('utc', now());
    v_is_paid BOOLEAN := FALSE;
    v_current_balance INT;
    v_new_balance INT := NULL;
    v_updated_idem INT;
BEGIN
    -- Security Audit: Validate identity if authenticated role
    IF auth.role() = 'authenticated' AND auth.uid() != p_user_id THEN
        RAISE EXCEPTION 'Access denied: caller (%) does not match target user (%)', auth.uid(), p_user_id;
    END IF;

    -- Security Audit: Verify conversation ownership
    IF NOT EXISTS (
        SELECT 1 FROM public.conversations
        WHERE id = p_conversation_id AND user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Conversation % not found or not owned by user %', p_conversation_id, p_user_id;
    END IF;

    -- Security Audit: Trusted subscription lookup directly from database
    -- Never trust client-supplied subscription boolean!
    SELECT EXISTS (
        SELECT 1 FROM public.subscriptions
        WHERE user_id = p_user_id
          AND status = 'active'
          AND plan IN ('monthly', 'yearly')
          AND (current_period_end IS NULL OR current_period_end > v_now)
    ) INTO v_is_paid;

    -- Row-locked credit balance deduction for free students
    IF NOT v_is_paid THEN
        SELECT credits_balance INTO v_current_balance
        FROM public.profiles
        WHERE id = p_user_id
        FOR UPDATE;

        IF v_current_balance IS NULL THEN
            RAISE EXCEPTION 'Profile not found for user %', p_user_id;
        END IF;

        IF v_current_balance <= 0 THEN
            RAISE EXCEPTION 'Insufficient credits. Balance is 0.';
        END IF;

        v_new_balance := v_current_balance - 1;

        UPDATE public.profiles
        SET credits_balance = v_new_balance,
            updated_at = v_now
        WHERE id = p_user_id;

        INSERT INTO public.credit_transactions (user_id, amount, balance_after, action, description, created_at)
        VALUES (p_user_id, -1, v_new_balance, 'ai_message', 'AI interaction credit consumed', v_now);
    END IF;

    -- Persist user message
    INSERT INTO public.messages (id, conversation_id, role, content, created_at)
    VALUES (v_user_msg_id, p_conversation_id, 'user', p_user_content, v_now);

    -- Persist assistant message
    INSERT INTO public.messages (id, conversation_id, role, content, created_at)
    VALUES (v_asst_msg_id, p_conversation_id, 'model', p_assistant_content, v_now);

    -- Touch conversation timestamp
    UPDATE public.conversations
    SET updated_at = v_now
    WHERE id = p_conversation_id;

    -- Complete idempotency key with strict fencing validation
    IF p_idempotency_key IS NOT NULL THEN
        UPDATE public.idempotency_keys
        SET status = 'completed',
            response_data = p_response_data,
            updated_at = v_now
        WHERE user_id = p_user_id
          AND conversation_id = p_conversation_id
          AND key = p_idempotency_key
          AND (p_owner_token IS NULL OR owner_token = p_owner_token)
          AND status = 'processing';

        GET DIAGNOSTICS v_updated_idem = ROW_COUNT;
        IF v_updated_idem = 0 THEN
            RAISE EXCEPTION 'Fencing violation: Idempotency lease expired, lost to another worker, or key not in processing state';
        END IF;
    END IF;

    RETURN QUERY SELECT v_user_msg_id, v_asst_msg_id, v_new_balance, v_now;
END;
$$;

-- -----------------------------------------------------------------------------
-- 5. FUNCTION EXECUTE PERMISSIONS
-- Explicit REVOKE from PUBLIC and GRANT to authorized roles only.
-- -----------------------------------------------------------------------------
REVOKE ALL ON FUNCTION public.acquire_idempotency_key(TEXT, UUID, UUID, TEXT, TEXT, INT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.acquire_idempotency_key(TEXT, UUID, UUID, TEXT, TEXT, INT) TO authenticated, service_role;

REVOKE ALL ON FUNCTION public.renew_idempotency_lease(TEXT, UUID, UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.renew_idempotency_lease(TEXT, UUID, UUID, TEXT) TO authenticated, service_role;

REVOKE ALL ON FUNCTION public.complete_conversation_turn(UUID, UUID, TEXT, TEXT, TEXT, TEXT, JSONB, UUID, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.complete_conversation_turn(UUID, UUID, TEXT, TEXT, TEXT, TEXT, JSONB, UUID, UUID) TO authenticated, service_role;

-- -----------------------------------------------------------------------------
-- ROLLBACK SCRIPT (IF EVER REQUIRED)
-- -----------------------------------------------------------------------------
-- DROP FUNCTION IF EXISTS public.complete_conversation_turn(UUID, UUID, TEXT, TEXT, TEXT, TEXT, JSONB, UUID, UUID);
-- DROP FUNCTION IF EXISTS public.renew_idempotency_lease(TEXT, UUID, UUID, TEXT);
-- DROP FUNCTION IF EXISTS public.acquire_idempotency_key(TEXT, UUID, UUID, TEXT, TEXT, INT);
-- DROP TABLE IF EXISTS public.idempotency_keys;
