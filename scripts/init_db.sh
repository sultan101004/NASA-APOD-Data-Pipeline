#!/bin/bash
# Initialize PostgreSQL database for APOD data

set -e

echo "Initializing APOD database..."

# Wait for PostgreSQL to be ready
until PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready. Creating APOD database and user..."

# Create database and user
PGPASSWORD=airflow psql -h postgres -U airflow -d airflow <<-EOSQL
    SELECT 'CREATE DATABASE apod_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'apod_db')\gexec
    
    SELECT 'CREATE USER apod_user WITH PASSWORD ''apod_password'''
    WHERE NOT EXISTS (SELECT FROM pg_user WHERE usename = 'apod_user')\gexec
    
    GRANT ALL PRIVILEGES ON DATABASE apod_db TO apod_user;
EOSQL

echo "APOD database initialization complete!"

