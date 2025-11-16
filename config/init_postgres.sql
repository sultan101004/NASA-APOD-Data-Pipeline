-- Initialize APOD database and user
-- This script runs during PostgreSQL container initialization
-- It executes as the postgres superuser

-- Create APOD database
CREATE DATABASE apod_db;

-- Create APOD user
CREATE USER apod_user WITH PASSWORD 'apod_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE apod_db TO apod_user;

-- Connect to apod_db and grant schema privileges
\c apod_db
GRANT ALL ON SCHEMA public TO apod_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO apod_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO apod_user;

