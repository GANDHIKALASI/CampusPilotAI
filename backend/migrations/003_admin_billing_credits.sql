-- =============================================================================
-- CAMPUSPILOT AI — MIGRATION 003: ADMIN, BILLING & CREDIT SUBSYSTEM
-- Profiles extension, Subscriptions, Payments, Credit tracking, and Audit logs
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. EXTEND PROFILES TABLE
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    -- Role column ('student', 'admin')
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'role'
    ) THEN
        ALTER TABLE public.profiles
        ADD COLUMN role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin'));
    END IF;

    -- Account status ('active', 'suspended', 'deactivated')
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'status'
    ) THEN
        ALTER TABLE public.profiles
        ADD COLUMN status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deactivated'));
    END IF;

    -- Educational institution
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'institution'
    ) THEN
        ALTER TABLE public.profiles
        ADD COLUMN institution TEXT;
    END IF;

    -- Free credits balance (Initial grant: exactly 20 credits)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'credits_balance'
    ) THEN
        ALTER TABLE public.profiles
        ADD COLUMN credits_balance INTEGER NOT NULL DEFAULT 20 CHECK (credits_balance >= 0);
    END IF;
END $$;

-- Update handle_new_user trigger to grant exactly 20 initial free credits on trusted account creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, avatar_url, role, institution, credits_balance)
    VALUES (
        new.id,
        COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        new.raw_user_meta_data->>'avatar_url',
        COALESCE(new.raw_app_meta_data->>'role', 'student'),
        new.raw_user_meta_data->>'institution',
        20 -- Exactly 20 free credits on trusted account creation
    )
    ON CONFLICT (id) DO UPDATE
    SET full_name = EXCLUDED.full_name,
        updated_at = timezone('utc', now());
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 2. SUBSCRIPTIONS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'monthly', 'yearly')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    current_period_start TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    current_period_end TIMESTAMPTZ NOT NULL,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON public.subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON public.subscriptions(current_period_end);

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own subscriptions" ON public.subscriptions;
CREATE POLICY "Users can view their own subscriptions"
    ON public.subscriptions FOR SELECT
    USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 3. PAYMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL CHECK (plan IN ('monthly', 'yearly')),
    amount_paise INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    razorpay_order_id TEXT NOT NULL UNIQUE,
    razorpay_payment_id TEXT UNIQUE,
    razorpay_signature TEXT,
    status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'captured', 'failed', 'refunded')),
    error_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON public.payments(razorpay_order_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON public.payments(razorpay_payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON public.payments(created_at DESC);

ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own payments" ON public.payments;
CREATE POLICY "Users can view their own payments"
    ON public.payments FOR SELECT
    USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 4. CREDIT TRANSACTIONS AUDIT TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL, -- +20 (initial grant), -1 (ai query), etc.
    balance_after INTEGER NOT NULL,
    action TEXT NOT NULL, -- 'initial_grant', 'ai_message', 'admin_adjustment', 'plan_purchase'
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON public.credit_transactions(user_id, created_at DESC);

ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own credit transactions" ON public.credit_transactions;
CREATE POLICY "Users can view their own credit transactions"
    ON public.credit_transactions FOR SELECT
    USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 5. ADMIN AUDIT LOGS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action TEXT NOT NULL, -- e.g. 'update_student_status', 'manual_plan_grant', 'delete_shared_doc'
    target_type TEXT NOT NULL, -- e.g. 'student', 'subscription', 'document'
    target_id TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON public.admin_audit_logs(created_at DESC);

ALTER TABLE public.admin_audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Deny public reads on admin audit logs" ON public.admin_audit_logs;
CREATE POLICY "Deny public reads on admin audit logs"
    ON public.admin_audit_logs FOR SELECT
    USING (false);

-- -----------------------------------------------------------------------------
-- 6. ATOMIC STORED PROCEDURE: CREDIT DEDUCTION WITH ROW LOCKING
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.deduct_student_credit(
    p_user_id UUID,
    p_action TEXT,
    p_description TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_current_balance INTEGER;
    v_new_balance INTEGER;
BEGIN
    -- Acquire exclusive row lock on profile to prevent concurrent double-spending
    SELECT credits_balance INTO v_current_balance
    FROM public.profiles
    WHERE id = p_user_id
    FOR UPDATE;

    IF v_current_balance IS NULL THEN
        RAISE EXCEPTION 'Student profile not found for id %', p_user_id;
    END IF;

    IF v_current_balance <= 0 THEN
        RAISE EXCEPTION 'Insufficient credits. Balance is 0.';
    END IF;

    v_new_balance := v_current_balance - 1;

    UPDATE public.profiles
    SET credits_balance = v_new_balance,
        updated_at = timezone('utc', now())
    WHERE id = p_user_id;

    INSERT INTO public.credit_transactions (user_id, amount, balance_after, action, description)
    VALUES (p_user_id, -1, v_new_balance, p_action, p_description);

    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
