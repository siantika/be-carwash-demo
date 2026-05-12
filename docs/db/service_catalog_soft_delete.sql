ALTER TABLE IF EXISTS service_catalog.service_types
    ADD COLUMN IF NOT EXISTS deleted_at timestamp with time zone;
