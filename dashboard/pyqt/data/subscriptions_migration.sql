-- Migration script for Subscriptions & Billing feature
-- Run this in your Supabase SQL Editor

-- ============================================
-- 1. SKU Items Table (Product Catalog)
-- ============================================
CREATE TABLE IF NOT EXISTS public.sku_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    device_limit INTEGER NOT NULL DEFAULT 1,
    duration_days INTEGER NOT NULL DEFAULT 30,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add some sample SKU items
INSERT INTO public.sku_items (name, description, price, device_limit, duration_days) VALUES
    ('Basic Plan', 'Perfect for small homes with 1-2 HVAC systems', 9.99, 2, 30),
    ('Pro Plan', 'Ideal for medium homes with multiple HVAC zones', 19.99, 5, 30),
    ('Premium Plan', 'Best for large properties or commercial use', 49.99, 15, 30),
    ('Annual Basic', 'Save 20% with annual billing', 95.90, 2, 365),
    ('Annual Pro', 'Save 20% with annual billing', 191.90, 5, 365),
    ('Annual Premium', 'Save 20% with annual billing', 479.90, 15, 365);

-- ============================================
-- 2. Orders Table (Purchase History)
-- ============================================
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sku_id UUID REFERENCES public.sku_items(id) ON DELETE SET NULL,
    sku_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled', 'expired')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON public.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);

-- ============================================
-- 3. Subscriptions Table (Current Active Subscription)
-- ============================================
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    plan_name TEXT NOT NULL,
    device_limit INTEGER NOT NULL DEFAULT 1,
    devices_used INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    starts_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique index to ensure one active subscription per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_user_active
    ON public.subscriptions(user_id)
    WHERE is_active = TRUE;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);

-- ============================================
-- 4. Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.sku_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- SKU Items: Anyone can read (public catalog)
CREATE POLICY "Anyone can view SKU items"
    ON public.sku_items
    FOR SELECT
    USING (true);

-- SKU Items: Only admins can modify (you can adjust this based on your needs)
CREATE POLICY "Admins can manage SKU items"
    ON public.sku_items
    FOR ALL
    USING (auth.uid() IN (
        SELECT id FROM auth.users WHERE email LIKE '%@yourdomain.com'
    ));

-- Orders: Users can only view their own orders
CREATE POLICY "Users can view own orders"
    ON public.orders
    FOR SELECT
    USING (auth.uid() = user_id);

-- Orders: Users can create their own orders
CREATE POLICY "Users can create own orders"
    ON public.orders
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Orders: Users can update their own orders
CREATE POLICY "Users can update own orders"
    ON public.orders
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Subscriptions: Users can only view their own subscriptions
CREATE POLICY "Users can view own subscriptions"
    ON public.subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Subscriptions: Users can create their own subscriptions
CREATE POLICY "Users can create own subscriptions"
    ON public.subscriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Subscriptions: Users can update their own subscriptions
CREATE POLICY "Users can update own subscriptions"
    ON public.subscriptions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================
-- 5. Triggers for automatic timestamp updates
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to orders table
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON public.orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to subscriptions table
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON public.subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to sku_items table
CREATE TRIGGER update_sku_items_updated_at
    BEFORE UPDATE ON public.sku_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. Function to automatically expire orders
-- ============================================

CREATE OR REPLACE FUNCTION expire_old_orders()
RETURNS void AS $$
BEGIN
    -- Update orders that have passed their expiry date
    UPDATE public.orders
    SET status = 'expired'
    WHERE status = 'active'
    AND expires_at IS NOT NULL
    AND expires_at < NOW();

    -- Deactivate subscriptions for expired orders
    UPDATE public.subscriptions
    SET is_active = FALSE
    WHERE is_active = TRUE
    AND expires_at IS NOT NULL
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. Sample Data (Optional - for testing)
-- ============================================

-- This section creates sample orders and subscriptions for testing
-- Remove or comment out in production

-- First, you need to replace 'YOUR_USER_ID' with an actual user ID from auth.users
-- You can get this by running: SELECT id FROM auth.users LIMIT 1;

-- Sample order (replace the user_id)
/*
INSERT INTO public.orders (user_id, sku_id, sku_name, quantity, amount, status, expires_at)
SELECT
    'YOUR_USER_ID'::UUID,
    id,
    name,
    1,
    price,
    'active',
    NOW() + INTERVAL '30 days'
FROM public.sku_items
WHERE name = 'Pro Plan'
LIMIT 1;

-- Sample subscription (replace the user_id)
INSERT INTO public.subscriptions (user_id, plan_name, device_limit, devices_used, is_active, expires_at)
VALUES (
    'YOUR_USER_ID'::UUID,
    'Pro Plan',
    5,
    2,
    TRUE,
    NOW() + INTERVAL '30 days'
);
*/

-- ============================================
-- 8. Helpful Queries
-- ============================================

-- View all active subscriptions with user info
-- SELECT
--     s.id,
--     s.user_id,
--     u.email,
--     s.plan_name,
--     s.device_limit,
--     s.devices_used,
--     s.expires_at,
--     s.is_active
-- FROM subscriptions s
-- JOIN auth.users u ON s.user_id = u.id
-- WHERE s.is_active = TRUE;

-- View all orders with user info
-- SELECT
--     o.id,
--     o.user_id,
--     u.email,
--     o.sku_name,
--     o.amount,
--     o.status,
--     o.created_at,
--     o.expires_at
-- FROM orders o
-- JOIN auth.users u ON o.user_id = u.id
-- ORDER BY o.created_at DESC;

-- Check expired orders
-- SELECT * FROM orders
-- WHERE status = 'active'
-- AND expires_at < NOW();

COMMIT;