#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting FastAPI Server ===${NC}"

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

# Check if database exists and is properly configured
echo -e "${YELLOW}Checking database connection...${NC}"
# You would need to customize this part based on your database setup

# Run the server
echo -e "${GREEN}Starting the server...${NC}"
echo -e "${YELLOW}The server will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run the FastAPI server using the module path from the code
python -m server.api