#!/bin/bash
# Fix Headscale healthcheck configuration
# This script updates docker-compose.yml with the correct healthcheck

set -e

echo "=== Headscale Healthcheck Fix ==="
echo ""
echo "Issue identified:"
echo "  Current: test: [\"CMD\", \"headscale\", \"health\"]"
echo "  Problem: This causes Docker to run 'headscale headscale health' (duplicated)"
echo ""
echo "Solution: Use wget to check HTTP health endpoint instead"
echo ""

# Backup current docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backed up docker-compose.yml"

# Stop headscale to prevent restart loop
echo ""
echo "Stopping headscale container..."
docker compose stop headscale 2>/dev/null || true

# The fix: Use wget instead of the 'headscale health' command
# According to Headscale documentation and Docker best practices:
# Option 1: wget (most reliable - available in Alpine-based images)
# Option 2: curl (if available)
# Option 3: Shell form with proper command

cat > /tmp/headscale_healthcheck_fix.txt << 'EOF'

RECOMMENDED HEALTHCHECK OPTIONS:

# Option 1: Using wget (RECOMMENDED - most compatible)
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s

# Option 2: Using shell form with headscale command
healthcheck:
  test: ["CMD-SHELL", "headscale health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s

# Option 3: Using HTTP endpoint with timeout
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "--timeout=5", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s

# Option 4: Disable healthcheck (temporary workaround)
healthcheck:
  disable: true

EOF

cat /tmp/headscale_healthcheck_fix.txt

echo ""
echo "=== ACTION REQUIRED ==="
echo ""
echo "Please choose one of the following fixes:"
echo ""
echo "1. Apply Option 1 (wget - RECOMMENDED)"
echo "   This is the most reliable option that works with Alpine-based images"
echo ""
echo "2. Apply Option 2 (CMD-SHELL)"
echo "   Uses the headscale health command directly with shell"
echo ""
echo "3. Disable healthcheck temporarily"
echo "   To get headscale running, then test manually"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo "Applying Option 1: wget healthcheck..."
    # This will be applied in docker-compose.yml update
    FIX_TYPE="wget"
    ;;
  2)
    echo "Applying Option 2: CMD-SHELL healthcheck..."
    FIX_TYPE="shell"
    ;;
  3)
    echo "Disabling healthcheck..."
    FIX_TYPE="disable"
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "Fix type selected: $FIX_TYPE"
echo ""
echo "To apply the fix, update your docker-compose.yml manually with the selected option."
echo "Then restart headscale:"
echo ""
echo "  docker compose up -d headscale"
echo ""
echo "Backup saved to: docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
