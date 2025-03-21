#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== LiorSystem Setup and Run Script ===${NC}"

# Variables
DB_NAME="lior_system"
DB_USER="lior_user"
DB_PASSWORD="lior3412312qQ"
PG_VERSION="16"

# =====================
# PostgreSQL Setup
# =====================

echo -e "${YELLOW}Setting up PostgreSQL for LiorSystem...${NC}"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL client utilities not found. Please install PostgreSQL.${NC}"
    echo -e "${YELLOW}You can install PostgreSQL with Homebrew:${NC}"
    echo -e "${GREEN}brew install postgresql@${PG_VERSION}${NC}"
    exit 1
fi

# Check PostgreSQL service and restart if needed
echo -e "${YELLOW}Checking PostgreSQL service...${NC}"

# Try both version-specific and generic service names
if brew services info postgresql@${PG_VERSION} &>/dev/null; then
    PG_SERVICE="postgresql@${PG_VERSION}"
elif brew services info postgresql &>/dev/null; then
    PG_SERVICE="postgresql"
else
    echo -e "${RED}PostgreSQL service not found via Homebrew.${NC}"
    exit 1
fi

echo -e "${YELLOW}Found PostgreSQL service: ${PG_SERVICE}${NC}"

# Stop PostgreSQL service if it's running
echo -e "${YELLOW}Stopping PostgreSQL service...${NC}"
brew services stop ${PG_SERVICE} &>/dev/null

# Start PostgreSQL service
echo -e "${YELLOW}Starting PostgreSQL service...${NC}"
brew services start ${PG_SERVICE}

# Wait for PostgreSQL to start
echo -e "${YELLOW}Waiting for PostgreSQL to start...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while ! pg_isready -q; do
    if [ ${RETRY_COUNT} -ge ${MAX_RETRIES} ]; then
        echo -e "${RED}PostgreSQL failed to start after ${MAX_RETRIES} attempts. Please check your PostgreSQL installation.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Waiting for PostgreSQL to start (attempt ${RETRY_COUNT}/${MAX_RETRIES})...${NC}"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

echo -e "${GREEN}PostgreSQL is now running.${NC}"

# Create database and user with proper permissions
echo -e "${YELLOW}Creating database and user with proper permissions...${NC}"

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

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to set up PostgreSQL database.${NC}"
    exit 1
fi

echo -e "${GREEN}PostgreSQL setup completed successfully.${NC}"
echo -e "${GREEN}Database: $DB_NAME${NC}"
echo -e "${GREEN}User: $DB_USER${NC}"

# =====================
# Python Environment Setup
# =====================

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed. Please install pip3 first.${NC}"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install required packages
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install fastapi uvicorn pydantic asyncpg python-jose[cryptography] passlib[bcrypt] python-multipart email-validator pytz

# Check if requirements.txt exists and install from it
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
    pip install -r requirements.txt
fi

# Create necessary directories if they don't exist
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p mortgage_system/uploaded_files

# =====================
# Test Database Connection
# =====================

echo -e "${YELLOW}Testing database connection...${NC}"

# Create a temporary Python script to test the database connection
cat > test_db_connection.py << EOF
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
        )
        await conn.execute("SELECT 1")
        await conn.close()
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
EOF

# Run the test script
python test_db_connection.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Database connection test failed. Please check your PostgreSQL installation and database settings.${NC}"
    rm test_db_connection.py
    exit 1
fi

echo -e "${GREEN}Database connection test successful!${NC}"
rm test_db_connection.py

# =====================
# Run the Server
# =====================

echo -e "${GREEN}All setup steps completed successfully!${NC}"
echo -e "${BLUE}Starting the server...${NC}"
echo -e "${YELLOW}The server will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run the FastAPI server using the module path from the code
python -m server.api