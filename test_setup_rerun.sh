#!/bin/bash
# Test script for setup.sh credential detection
# This script creates a mock .env file and tests the detection logic

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Create test .env file
create_test_env() {
    print_test "Creating test .env file..."
    cat > .env.test << 'EOF'
# Test configuration
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO

# Security
SECRET_KEY=test_secret_key_12345678901234567890123456789012
LOGIN_USER=testadmin
LOGIN_PASSWORD=TestPassword123!

# Network
HTTP_PORT=5001

# Traefik Configuration
DOMAIN=test.example.com
ACME_EMAIL=test@example.com

# Headscale Configuration
HEADSCALE_DOMAIN=headscale.test.example.com
HEADSCALE_PORT=8081
HEADSCALE_SERVER_URL=http://headscale.test.example.com:8081

# Docker Compose Profiles
COMPOSE_PROFILES=traefik,headscale
EOF
    print_pass "Test .env file created"
}

# Test the load_existing_config function
test_load_function() {
    print_test "Testing load_existing_config function..."
    
    # Source the function from setup.sh
    source <(grep -A 15 "^load_existing_config()" setup.sh)
    
    # Temporarily rename .env.test to .env for testing
    if [ -f .env ]; then
        mv .env .env.backup.test
    fi
    mv .env.test .env
    
    # Call the function
    if load_existing_config; then
        print_pass "load_existing_config returned success"
    else
        print_fail "load_existing_config returned failure"
        return 1
    fi
    
    # Restore original .env
    mv .env .env.test
    if [ -f .env.backup.test ]; then
        mv .env.backup.test .env
    fi
}

# Test individual variable detection
test_variable_detection() {
    print_test "Testing variable detection..."
    
    # Temporarily rename .env.test to .env for testing
    if [ -f .env ]; then
        mv .env .env.backup.test
    fi
    mv .env.test .env
    
    # Source the function and run it
    source <(grep -A 15 "^load_existing_config()" setup.sh)
    load_existing_config
    
    # Test each variable
    local failed=0
    
    if [ "$EXISTING_SECRET_KEY" = "test_secret_key_12345678901234567890123456789012" ]; then
        print_pass "SECRET_KEY detected correctly"
    else
        print_fail "SECRET_KEY not detected (got: '$EXISTING_SECRET_KEY')"
        failed=1
    fi
    
    if [ "$EXISTING_LOGIN_USER" = "testadmin" ]; then
        print_pass "LOGIN_USER detected correctly"
    else
        print_fail "LOGIN_USER not detected (got: '$EXISTING_LOGIN_USER')"
        failed=1
    fi
    
    if [ "$EXISTING_LOGIN_PASSWORD" = "TestPassword123!" ]; then
        print_pass "LOGIN_PASSWORD detected correctly"
    else
        print_fail "LOGIN_PASSWORD not detected (got: '$EXISTING_LOGIN_PASSWORD')"
        failed=1
    fi
    
    if [ "$EXISTING_HTTP_PORT" = "5001" ]; then
        print_pass "HTTP_PORT detected correctly"
    else
        print_fail "HTTP_PORT not detected (got: '$EXISTING_HTTP_PORT')"
        failed=1
    fi
    
    if [ "$EXISTING_DOMAIN" = "test.example.com" ]; then
        print_pass "DOMAIN detected correctly"
    else
        print_fail "DOMAIN not detected (got: '$EXISTING_DOMAIN')"
        failed=1
    fi
    
    if [ "$EXISTING_ACME_EMAIL" = "test@example.com" ]; then
        print_pass "ACME_EMAIL detected correctly"
    else
        print_fail "ACME_EMAIL not detected (got: '$EXISTING_ACME_EMAIL')"
        failed=1
    fi
    
    if [ "$EXISTING_HEADSCALE_DOMAIN" = "headscale.test.example.com" ]; then
        print_pass "HEADSCALE_DOMAIN detected correctly"
    else
        print_fail "HEADSCALE_DOMAIN not detected (got: '$EXISTING_HEADSCALE_DOMAIN')"
        failed=1
    fi
    
    if [ "$EXISTING_HEADSCALE_PORT" = "8081" ]; then
        print_pass "HEADSCALE_PORT detected correctly"
    else
        print_fail "HEADSCALE_PORT not detected (got: '$EXISTING_HEADSCALE_PORT')"
        failed=1
    fi
    
    # Restore original .env
    mv .env .env.test
    if [ -f .env.backup.test ]; then
        mv .env.backup.test .env
    fi
    
    return $failed
}

# Test with missing .env file
test_missing_env() {
    print_test "Testing with missing .env file..."
    
    # Ensure no .env exists
    if [ -f .env ]; then
        mv .env .env.backup.test
    fi
    
    # Source the function and run it
    source <(grep -A 15 "^load_existing_config()" setup.sh)
    
    if load_existing_config; then
        print_fail "load_existing_config should return failure when .env is missing"
        return 1
    else
        print_pass "load_existing_config correctly returns failure when .env is missing"
    fi
    
    # Restore original .env
    if [ -f .env.backup.test ]; then
        mv .env.backup.test .env
    fi
}

# Test with partial .env file
test_partial_env() {
    print_test "Testing with partial .env file..."
    
    # Create partial .env
    cat > .env.test << 'EOF'
SECRET_KEY=partial_secret_key
LOGIN_USER=partialuser
# Missing LOGIN_PASSWORD
HTTP_PORT=5002
EOF
    
    # Temporarily rename .env.test to .env for testing
    if [ -f .env ]; then
        mv .env .env.backup.test
    fi
    mv .env.test .env
    
    # Source the function and run it
    source <(grep -A 15 "^load_existing_config()" setup.sh)
    load_existing_config
    
    local failed=0
    
    if [ -n "$EXISTING_SECRET_KEY" ]; then
        print_pass "Partial detection: SECRET_KEY found"
    else
        print_fail "Partial detection: SECRET_KEY not found"
        failed=1
    fi
    
    if [ -z "$EXISTING_LOGIN_PASSWORD" ]; then
        print_pass "Partial detection: Missing LOGIN_PASSWORD correctly not detected"
    else
        print_fail "Partial detection: LOGIN_PASSWORD should be empty"
        failed=1
    fi
    
    # Restore original .env
    mv .env .env.test
    if [ -f .env.backup.test ]; then
        mv .env.backup.test .env
    fi
    
    return $failed
}

# Main test execution
main() {
    echo ""
    echo "=========================================="
    echo "  Setup.sh Credential Detection Tests"
    echo "=========================================="
    echo ""
    
    local total_tests=0
    local passed_tests=0
    
    # Run tests
    create_test_env
    echo ""
    
    total_tests=$((total_tests + 1))
    if test_load_function; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    total_tests=$((total_tests + 1))
    if test_variable_detection; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    total_tests=$((total_tests + 1))
    if test_missing_env; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    total_tests=$((total_tests + 1))
    if test_partial_env; then
        passed_tests=$((passed_tests + 1))
    fi
    echo ""
    
    # Cleanup
    rm -f .env.test
    
    # Summary
    echo "=========================================="
    echo "  Test Summary"
    echo "=========================================="
    echo "Total tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $((total_tests - passed_tests))"
    echo ""
    
    if [ $passed_tests -eq $total_tests ]; then
        print_pass "All tests passed!"
        return 0
    else
        print_fail "Some tests failed"
        return 1
    fi
}

# Run main
main