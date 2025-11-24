#!/bin/bash
# Development script for Barcode Central
# WSL-friendly Flask development server launcher

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Barcode Central Development Server ===${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/.requirements_installed" ]; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install requirements${NC}"
        exit 1
    fi
    touch venv/.requirements_installed
    echo -e "${GREEN}Requirements installed${NC}"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please update it with your settings.${NC}"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Ensure logs directory exists
mkdir -p logs

# Run Flask application
echo -e "${GREEN}Starting Flask development server on http://localhost:5000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

python app.py