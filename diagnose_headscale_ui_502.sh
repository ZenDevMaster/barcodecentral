#!/bin/bash
# Diagnostic script for Headscale UI 502 error

set -e

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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header "Headscale UI 502 Diagnostic"
echo ""

# Check 1: Can we reach headscale-ui from host?
print_info "Test 1: Checking if headscale-ui responds on localhost:3009"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3009/ | grep -qE "200|401|302"; then
    print_success "headscale-ui is responding"
else
    print_error "headscale-ui is NOT responding on localhost:3009"
    echo "  This means the container itself has an issue"
fi
echo ""

# Check 2: Check headscale-ui logs
print_info "Test 2: Checking headscale-ui logs for errors"
echo "Last 20 lines of headscale-ui logs:"
docker compose logs --tail=20 headscale-ui
echo ""

# Check 3: Can headscale-ui reach headscale?
print_info "Test 3: Checking if headscale-ui can reach headscale backend"
if docker compose exec -T headscale-ui curl -s -o /dev/null -w "%{http_code}" http://headscale:8080/health 2>/dev/null | grep -q "200"; then
    print_success "headscale-ui CAN reach headscale backend"
else
    print_error "headscale-ui CANNOT reach headscale backend"
    echo "  This is likely the cause of the 502 error"
fi
echo ""

# Check 4: Is headscale healthy?
print_info "Test 4: Checking headscale container health"
if docker compose ps headscale | grep -q "healthy"; then
    print_success "headscale is healthy"
else
    print_error "headscale is UNHEALTHY"
    echo "  Headscale logs:"
    docker compose logs --tail=30 headscale
fi
echo ""

# Check 5: Check environment variables
print_info "Test 5: Checking headscale-ui environment variables"
echo "HS_SERVER setting:"
docker compose exec -T headscale-ui env | grep HS_SERVER || echo "  HS_SERVER not set!"
echo ""
echo "HEADSCALE_API_KEY setting:"
docker compose exec -T headscale-ui env | grep "^KEY=" || echo "  KEY (API key) not set!"
echo ""

# Check 6: Check if API key is set in .env
print_info "Test 6: Checking .env for HEADSCALE_API_KEY"
if grep -q "^HEADSCALE_API_KEY=.\+" .env 2>/dev/null; then
    print_success "HEADSCALE_API_KEY is set in .env"
else
    print_error "HEADSCALE_API_KEY is NOT set or empty in .env"
    echo ""
    echo "  To fix this:"
    echo "  1. Generate API key: docker compose exec headscale headscale apikeys create"
    echo "  2. Add to .env: HEADSCALE_API_KEY=your-key-here"
    echo "  3. Restart: docker compose restart headscale-ui"
fi
echo ""

# Check 7: Network connectivity
print_info "Test 7: Checking Docker network connectivity"
echo "Networks for headscale-ui:"
docker inspect headscale-ui --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
echo ""
echo "Networks for headscale:"
docker inspect headscale --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
echo ""

# Summary
print_header "Diagnosis Summary"
echo ""
print_info "Common causes of 502 Bad Gateway:"
echo "1. HEADSCALE_API_KEY not set or invalid"
echo "2. Headscale container is unhealthy"
echo "3. Network connectivity issues between containers"
echo "4. headscale-ui cannot reach headscale:8080"
echo ""
print_info "Recommended fixes:"
echo "1. Check if headscale is healthy: docker compose ps"
echo "2. Generate API key if missing: docker compose exec headscale headscale apikeys create"
echo "3. Add API key to .env: HEADSCALE_API_KEY=your-key"
echo "4. Restart headscale-ui: docker compose restart headscale-ui"
echo "5. Check logs: docker compose logs -f headscale-ui"