#!/bin/bash

# Backend Test Suite Runner
# Runs all available backend test suites and reports results

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_BACKENDS=0
PASSED_BACKENDS=0
FAILED_BACKENDS=0
SKIPPED_BACKENDS=0

# Array to store test results
declare -a TEST_RESULTS

echo -e "${BLUE}🧪 Backend Test Suite Runner${NC}"
echo "============================================="

# Function to run tests for a specific backend
run_backend_tests() {
    local backend_name="$1"
    local backend_dir="$2"
    
    echo -e "\n${BLUE}📁 Testing ${backend_name} backend...${NC}"
    
    if [ ! -f "$backend_dir/test.sh" ]; then
        echo -e "${YELLOW}⚠️  No test suite found for ${backend_name} backend${NC}"
        TEST_RESULTS+=("${backend_name}: SKIPPED (no test suite)")
        SKIPPED_BACKENDS=$((SKIPPED_BACKENDS + 1))
        return 0
    fi
    
    if [ ! -x "$backend_dir/test.sh" ]; then
        echo -e "${YELLOW}⚠️  Test script not executable for ${backend_name} backend${NC}"
        chmod +x "$backend_dir/test.sh"
    fi
    
    # Change to backend directory and run tests
    cd "$backend_dir"
    
    if ./test.sh; then
        echo -e "${GREEN}✅ ${backend_name} backend tests PASSED${NC}"
        TEST_RESULTS+=("${backend_name}: PASSED")
        PASSED_BACKENDS=$((PASSED_BACKENDS + 1))
    else
        echo -e "${RED}❌ ${backend_name} backend tests FAILED${NC}"
        TEST_RESULTS+=("${backend_name}: FAILED")
        FAILED_BACKENDS=$((FAILED_BACKENDS + 1))
    fi
    
    # Return to backend root directory
    cd ..
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# List of all backends to check
BACKENDS=(
    "bash"
    "javascript" 
    "python"
    "ruby"
    "php"
    "kotlin"
    "haskell"
    "perl"
    "session-manager"
)

echo "Scanning for backend test suites..."

# Run tests for each backend
for backend in "${BACKENDS[@]}"; do
    if [ -d "$backend" ]; then
        TOTAL_BACKENDS=$((TOTAL_BACKENDS + 1))
        run_backend_tests "$backend" "$backend"
    else
        echo -e "${YELLOW}⚠️  Backend directory not found: $backend${NC}"
    fi
done

# Print summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "============================================="
echo -e "Total backends checked: ${TOTAL_BACKENDS}"
echo -e "${GREEN}Passed: ${PASSED_BACKENDS}${NC}"
echo -e "${RED}Failed: ${FAILED_BACKENDS}${NC}"
echo -e "${YELLOW}Skipped: ${SKIPPED_BACKENDS}${NC}"

echo -e "\n${BLUE}📋 Detailed Results:${NC}"
for result in "${TEST_RESULTS[@]}"; do
    if [[ "$result" == *"PASSED"* ]]; then
        echo -e "  ${GREEN}$result${NC}"
    elif [[ "$result" == *"FAILED"* ]]; then
        echo -e "  ${RED}$result${NC}"
    else
        echo -e "  ${YELLOW}$result${NC}"
    fi
done

# Exit with appropriate code
if [ $FAILED_BACKENDS -gt 0 ]; then
    echo -e "\n${RED}❌ Some backend tests failed!${NC}"
    exit 1
elif [ $PASSED_BACKENDS -gt 0 ]; then
    echo -e "\n${GREEN}✅ All available backend tests passed!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  No backend tests were run${NC}"
    exit 1
fi