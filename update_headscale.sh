#!/bin/bash
set -e

# Headscale Update Script - Update from v0.22 to v0.27.1
# This script updates Headscale to the latest version v0.27.1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Headscale Update Script - Upgrading to v0.27.1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if docker-compose.yml exists and has headscale service
if [ -f "docker-compose.yml" ]; then
    if grep -q "headscale" docker-compose.yml; then
        echo "✓ Found Headscale service in docker-compose.yml"
        HAS_HEADSCALE=true
    else
        echo "✗ No Headscale service found in docker-compose.yml"
        HAS_HEADSCALE=false
    fi
else
    echo "✗ docker-compose.yml not found"
    HAS_HEADSCALE=false
fi

echo ""

if [ "$HAS_HEADSCALE" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 1: Backup current configuration"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    BACKUP_DIR="backups/headscale-upgrade-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    echo "Creating backup in: $BACKUP_DIR"
    
    # Backup docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_DIR/"
        echo "✓ Backed up docker-compose.yml"
    fi
    
    # Backup Headscale data
    if [ -d "data/headscale" ]; then
        cp -r data/headscale "$BACKUP_DIR/"
        echo "✓ Backed up Headscale data"
    fi
    
    # Backup Headscale config
    if [ -d "config/headscale" ]; then
        cp -r config/headscale "$BACKUP_DIR/"
        echo "✓ Backed up Headscale config"
    fi
    
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 2: Stop Headscale services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Stopping Headscale and related services..."
    docker compose stop headscale headscale-ui tailscale 2>/dev/null || true
    
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 3: Update docker-compose.yml"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Update Headscale version in docker-compose.yml
    if grep -q "headscale/headscale:0.22" docker-compose.yml; then
        sed -i 's|headscale/headscale:0.22|headscale/headscale:v0.27.1|g' docker-compose.yml
        echo "✓ Updated Headscale image to v0.27.1"
    elif grep -q "headscale/headscale:v0.22" docker-compose.yml; then
        sed -i 's|headscale/headscale:v0.22|headscale/headscale:v0.27.1|g' docker-compose.yml
        echo "✓ Updated Headscale image to v0.27.1"
    else
        echo "⚠ Could not find Headscale 0.22 image reference"
        echo "  Please manually update the image version in docker-compose.yml"
    fi
    
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 4: Pull new images"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker compose pull headscale headscale-ui
    
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 5: Start updated services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker compose up -d headscale headscale-ui
    
    echo ""
    echo "Waiting for Headscale to start..."
    sleep 5
    
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 6: Verify installation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo ""
    echo "Headscale version:"
    docker exec headscale headscale version || echo "⚠ Could not get version (container may still be starting)"
    
    echo ""
    echo "Container status:"
    docker compose ps headscale headscale-ui
    
    echo ""
    echo "Recent logs:"
    docker compose logs --tail=20 headscale
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ Update Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Check logs: docker compose logs -f headscale"
    echo "  2. Verify nodes: docker exec headscale headscale nodes list"
    echo "  3. Check health: docker compose ps"
    echo ""
    
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Regenerating docker-compose.yml with updated Headscale"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "It appears you need to regenerate your docker-compose.yml"
    echo "The setup.sh script has been updated to use Headscale v0.27.1"
    echo ""
    echo "Run: ./setup.sh"
    echo ""
    echo "This will generate a new docker-compose.yml with the latest Headscale version."
    echo ""
fi