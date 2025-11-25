-- Obscura V2 Database Initialization Script
-- This script runs when PostgreSQL container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application schema (optional, for organization)
-- CREATE SCHEMA IF NOT EXISTS obscura;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE obscura TO obscura;

-- Create indexes for common queries (if tables exist)
-- Note: Alembic will create tables, but we can add extra indexes here

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Obscura V2 database initialized at %', now();
END $$;
