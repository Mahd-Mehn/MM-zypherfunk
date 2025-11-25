#!/bin/bash

# Obscura V2 - Multi-Exchange Trading Platform
# Quick Start Setup Script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=============================================="
echo "  Obscura V2 - Trading Infrastructure Setup  "
echo "=============================================="
echo -e "${NC}"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}Error: Python 3.9+ is required. You have Python $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Navigate to backend directory
cd "$(dirname "$0")"
echo -e "${YELLOW}Working directory: $(pwd)${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ Pip upgraded${NC}"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API credentials${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Check if .env has been configured
if grep -q "your-binance-api-key-here" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: .env appears to have default values${NC}"
    echo -e "${YELLOW}   Please update with your actual credentials${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p backups
echo -e "${GREEN}✓ Directories created${NC}"

# Test imports
echo -e "${YELLOW}Testing imports...${NC}"
python3 -c "
from exchanges.orchestrator import TradingOrchestrator
from exchanges.binance_connector import BinanceConnector
from exchanges.coinbase_connector import CoinbaseConnector
from exchanges.uniswap_connector import UniswapConnector
from exchanges.starknet_connector import StarknetConnector
print('✓ All imports successful')
" && echo -e "${GREEN}✓ All modules imported successfully${NC}" || {
    echo -e "${RED}✗ Import test failed${NC}"
    exit 1
}

# Display setup summary
echo -e "\n${BLUE}=============================================="
echo "  Setup Complete!"
echo "===============================================${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Configure your credentials:"
echo -e "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Run the test suite:"
echo -e "   ${YELLOW}python test_trading.py${NC}"
echo ""
echo "3. Start the trading server:"
echo -e "   ${YELLOW}cd conductor${NC}"
echo -e "   ${YELLOW}uvicorn main:app --reload --port 8001${NC}"
echo ""
echo "4. Check the health endpoint:"
echo -e "   ${YELLOW}curl http://localhost:8001/health${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - Trading Guide: exchanges/README.md"
echo "  - Deployment: DEPLOYMENT.md"
echo "  - Examples: examples_trading.py"
echo ""
echo -e "${GREEN}For support, check the documentation or open an issue.${NC}"
echo ""

# Optional: Run initial test
read -p "Would you like to run the test suite now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Running tests...${NC}"
    python test_trading.py
fi

echo -e "\n${GREEN}Setup completed successfully! 🚀${NC}\n"
