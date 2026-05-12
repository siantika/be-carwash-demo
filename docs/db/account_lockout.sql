ALTER TABLE IF EXISTS identity.accounts
    ADD COLUMN IF NOT EXISTS failed_login_attempts integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until timestamp with time zone,
    ADD COLUMN IF NOT EXISTS last_login_at timestamp with time zone;
