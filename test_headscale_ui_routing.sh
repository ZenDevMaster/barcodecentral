#!/bin/bash
# Test script for Headscale UI routing fix
# Validates that /headscale-admin is properly configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo ""
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "FAILED"
        ((TESTS_FAILED++))
        return 1
    fi
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    
    echo ""
    echo -n "Testing: $test_name... "
    
    output=$(eval "$test_command" 2>&1)
    
    if echo "$output" | grep -q "$expected"; then
        print_success "PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "FAILED"
        echo "  Expected: $expected"
        echo "  Got: $output"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Main test execution
clear
print_header "Headscale UI Routing Validation"
echo ""
print_info "This script validates the /headscale-admin routing fixes"
echo ""

# Check if docker-compose.yml exists
if [ ! -f docker-compose.yml ]; then
    print_error "docker-compose.yml not found!"
    print_info "Run ./setup.sh first to generate configuration"
    exit 1
fi

# Test 1: Check if headscale-ui service exists in docker-compose.yml
print_header "Test 1: Configuration Files"
run_test "headscale-ui service exists" "grep -q 'headscale-ui:' docker-compose.yml"

# Test 2: Check if ports are exposed (not just expose)
run_test "headscale-ui ports exposed" "grep -A 5 'headscale-ui:' docker-compose.yml | grep -q 'ports:'"
run_test "Port 3000 mapped" "grep -A 10 'headscale-ui:' docker-compose.yml | grep -q '3000:3000'"

# Test 3: Check Traefik labels if Traefik is enabled
if grep -q 'traefik.enable=true' docker-compose.yml 2>/dev/null; then
    print_header "Test 2: Traefik Configuration"
    run_test "Traefik enabled for headscale-ui" "grep -A 20 'headscale-ui:' docker-compose.yml | grep -q 'traefik.enable=true'"
    run_test "PathPrefix rule configured" "grep -A 20 'headscale-ui:' docker-compose.yml | grep -q 'PathPrefix.*headscale-admin'"
    run_test "Priority set" "grep -A 20 'headscale-ui:' docker-compose.yml | grep -q 'priority=100'"
    run_test "StripPrefix middleware" "grep -A 20 'headscale-ui:' docker-compose.yml | grep -q 'stripprefix'"
else
    print_warning "Traefik not enabled - skipping Traefik tests"
    ((TESTS_SKIPPED+=4))
fi

# Test 4: Check nginx configuration if it exists
if [ -f config/nginx/barcode-central.conf ]; then
    print_header "Test 3: Nginx Configuration"
    run_test "Nginx config exists" "test -f config/nginx/barcode-central.conf"
    run_test "headscale-admin location block" "grep -q 'location /headscale-admin/' config/nginx/barcode-central.conf"
    run_test "Proxy to localhost:3000" "grep -A 5 'location /headscale-admin/' config/nginx/barcode-central.conf | grep -q 'proxy_pass.*localhost:3000'"
    run_test "X-Script-Name header" "grep -A 10 'location /headscale-admin/' config/nginx/barcode-central.conf | grep -q 'X-Script-Name'"
else
    print_warning "Nginx config not found - skipping nginx tests"
    ((TESTS_SKIPPED+=4))
fi

# Test 5: Check Flask app.py for diagnostic logging
print_header "Test 4: Flask Application"
run_test "Flask 404 handler exists" "grep -q 'def not_found_error' app.py"
run_test "Diagnostic logging added" "grep -A 10 'def not_found_error' app.py | grep -q 'headscale-admin'"

# Test 6: Runtime tests (if containers are running)
print_header "Test 5: Runtime Validation"

if docker ps | grep -q headscale-ui; then
    print_info "headscale-ui container is running"
    
    # Check if port is accessible
    run_test "Port 3000 accessible from host" "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ | grep -qE '200|401|302'"
    
    # Check if container can reach headscale
    if docker ps | grep -q headscale; then
        run_test "headscale-ui can reach headscale" "docker compose exec -T headscale-ui curl -s -o /dev/null -w '%{http_code}' http://headscale:8080/health | grep -q 200"
    else
        print_warning "headscale container not running - skipping connectivity test"
        ((TESTS_SKIPPED++))
    fi
    
    # Check Flask logs for /headscale-admin (should be empty)
    if docker compose logs app 2>/dev/null | grep -q "Flask received /headscale-admin"; then
        print_error "Flask is receiving /headscale-admin requests - reverse proxy misconfigured!"
        ((TESTS_FAILED++))
    else
        print_success "Flask not receiving /headscale-admin requests"
        ((TESTS_PASSED++))
    fi
else
    print_warning "headscale-ui container not running - skipping runtime tests"
    ((TESTS_SKIPPED+=3))
fi

# Test 7: Check .env configuration
print_header "Test 6: Environment Configuration"
if [ -f .env ]; then
    run_test ".env file exists" "test -f .env"
    run_test "HEADSCALE_UI_ENABLED set" "grep -q 'HEADSCALE_UI_ENABLED=true' .env"
    run_test "HEADSCALE_UI credentials set" "grep -q 'HEADSCALE_UI_USER=' .env && grep -q 'HEADSCALE_UI_PASSWORD=' .env"
else
    print_warning ".env file not found - skipping environment tests"
    ((TESTS_SKIPPED+=3))
fi

# Summary
echo ""
print_header "Test Summary"
echo ""
echo "Tests Passed:  $TESTS_PASSED"
echo "Tests Failed:  $TESTS_FAILED"
echo "Tests Skipped: $TESTS_SKIPPED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "All tests passed! ✓"
    echo ""
    print_info "Next steps:"
    echo "1. If containers are not running: docker compose up -d"
    echo "2. Generate Headscale API key: ./scripts/generate-headscale-api-key.sh"
    echo "3. Add API key to .env file"
    echo "4. Restart headscale-ui: docker compose restart headscale-ui"
    echo "5. Access UI at: https://your-domain.com/headscale-admin/"
    exit 0
else
    print_error "Some tests failed!"
    echo ""
    print_info "Troubleshooting:"
    echo "1. Run ./setup.sh to regenerate configuration"
    echo "2. Check docker-compose.yml for correct port mapping"
    echo "3. Verify Traefik labels include priority=100"
    echo "4. Check nginx config has /headscale-admin location block"
    echo "5. Review HEADSCALE_UI_FINAL_PLAN.md for detailed fixes"
    exit 1
fi