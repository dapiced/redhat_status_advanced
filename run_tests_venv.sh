#!/bin/bash
# Test runner wrapper that ensures virtual environment is used

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

echo -e "${BLUE}🔧 Red Hat Status Checker - Test Runner${NC}"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Creating one...${NC}"
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
echo -e "${GREEN}✅ Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Installing test dependencies...${NC}"
    pip install pytest pytest-cov
fi

# Run the test runner with all provided arguments
echo -e "${GREEN}✅ Running tests with virtual environment...${NC}"
python "$PROJECT_ROOT/run_tests.py" "$@"
