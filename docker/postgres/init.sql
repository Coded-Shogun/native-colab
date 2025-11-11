-- Native Colab Database Initialization Script
-- This script runs when the PostgreSQL container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For better indexing
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- For better indexing

-- Create custom types (if needed)
-- Example: CREATE TYPE user_role AS ENUM ('super_admin', 'workspace_admin', 'manager', 'member', 'guest');

-- Set default timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Native Colab database initialized successfully';
END $$;
