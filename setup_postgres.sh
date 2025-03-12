#!/bin/bash
# PostgreSQL setup script for LiorSystem

echo "Setting up PostgreSQL for LiorSystem..."

# Variables
DB_NAME="lior_system"
DB_USER="lior_user"
DB_PASSWORD="lior3412312qQ"

# Check if PostgreSQL is running
if ! command -v pg_isready &> /dev/null; then
    echo "PostgreSQL client utilities not found. Please install PostgreSQL."
    exit 1
fi

if ! pg_isready &> /dev/null; then
    echo "PostgreSQL server is not running. Starting PostgreSQL..."
    brew services start postgresql@16 || brew services start postgresql
fi

# Create database and user with proper permissions
echo "Creating database and user with proper permissions..."

# Connect as the current user (which has admin privileges)
psql postgres << EOF
-- Drop database and user if they exist
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Create user and database with proper encoding
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME WITH OWNER = $DB_USER ENCODING = 'UTF8';

-- Connect to the newly created database
\c $DB_NAME

-- Grant privileges
ALTER USER $DB_USER WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;
ALTER SCHEMA public OWNER TO $DB_USER;

-- Create extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

if [ $? -eq 0 ]; then
    echo "PostgreSQL setup completed successfully."
    echo "Database: $DB_NAME"
    echo "User: $DB_USER"
    echo "You can now run your FastAPI application."
else
    echo "Failed to set up PostgreSQL."
    exit 1
fi