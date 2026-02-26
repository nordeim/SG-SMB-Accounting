-- Migration: Add missing columns to fiscal_period table
-- Columns: label, locked_at, locked_by

-- Add label column
ALTER TABLE core.fiscal_period
    ADD COLUMN IF NOT EXISTS label VARCHAR(50);

-- Add locked_at column  
ALTER TABLE core.fiscal_period
    ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ;

-- Add locked_by column
ALTER TABLE core.fiscal_period
    ADD COLUMN IF NOT EXISTS locked_by UUID;

-- Update existing records with generated labels
UPDATE core.fiscal_period
SET label = TO_CHAR(start_date, 'Mon YYYY')
WHERE label IS NULL;

-- Add comments
COMMENT ON COLUMN core.fiscal_period.label IS 'Human-readable period label (e.g., "Jan 2024")';
COMMENT ON COLUMN core.fiscal_period.locked_at IS 'When the period was locked (prevents new entries)';
COMMENT ON COLUMN core.fiscal_period.locked_by IS 'User ID who locked the period';
