#!/bin/bash

# ReMarkable to Markdown Converter - Setup Script
# This script automates the installation of remarks and its dependencies

set -e  # Exit on error

echo "===================="
echo "Remarks Setup Script"
echo "===================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew not found. Please install it first:${NC}"
        echo "https://brew.sh"
        exit 1
    fi

    # Install Cairo if not present
    if ! brew list cairo &> /dev/null; then
        echo -e "${YELLOW}Installing Cairo library...${NC}"
        brew install cairo
    else
        echo -e "${GREEN}Cairo already installed${NC}"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"

    # Install Cairo for Linux
    if command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}Installing Cairo library...${NC}"
        sudo apt-get update
        sudo apt-get install -y libcairo2-dev pkg-config python3-dev
    elif command -v yum &> /dev/null; then
        echo -e "${YELLOW}Installing Cairo library...${NC}"
        sudo yum install -y cairo-devel pkgconfig python3-devel
    fi
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3.12 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing..."
    rm -rf venv
fi
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install PyMuPDF pyyaml parsita numpy flask 'sentry-sdk[flask]' gunicorn

# Install git dependencies
echo -e "${YELLOW}Installing rmscene and rmc from GitHub...${NC}"
pip install git+https://github.com/scrybbling-together/rmscene.git@main
pip install git+https://github.com/scrybbling-together/rmc.git@main

# Verify installation
echo ""
echo -e "${GREEN}===================="
echo "Setup Complete!"
echo "====================${NC}"
echo ""
echo "To use remarks:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run: python -m remarks INPUT_DIR OUTPUT_DIR"
echo ""
echo "Example:"
echo "  python -m remarks ~/remarkable-backup/xochitl ~/output"
echo ""
