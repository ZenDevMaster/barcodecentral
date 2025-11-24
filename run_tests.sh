#!/bin/bash
# Run all tests with coverage for Barcode Central

echo "=========================================="
echo "Running Barcode Central Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt

echo ""
echo "=========================================="
echo "Running Tests"
echo "=========================================="
echo ""

# Run tests with coverage
pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-config=.coveragerc \
    -v \
    --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo ""
echo "Coverage report generated in: htmlcov/index.html"
echo "To view coverage report, run: open htmlcov/index.html"
echo ""

# Exit with test exit code
exit $TEST_EXIT_CODE
