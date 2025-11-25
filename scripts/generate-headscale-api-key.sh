#!/bin/bash
# Generate or retrieve Headscale API key for UI

set -e

CRED_FILE="config/headscale/.credentials"
ENV_FILE=".env"

echo "=== Headscale API Key Management ==="
echo ""

# Check if Headscale is running
if ! docker ps | grep -q headscale; then
    echo "Error: Headscale container is not running"
    echo "Start it with: docker compose up -d headscale"
    exit 1
fi

# Check for existing API key
if [ -f "$CRED_FILE" ]; then
    source "$CRED_FILE"
    
    if [ -n "$HEADSCALE_API_KEY" ]; then
        echo "Found existing API key in credentials file"
        echo ""
        echo "Do you want to:"
        echo "1) Use existing API key (recommended)"
        echo "2) Generate new API key (will require UI reconfiguration)"
        read -p "Choice [1-2]: " key_choice
        
        if [ "$key_choice" = "1" ]; then
            echo ""
            echo "✓ Using existing API key"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "API Key: $HEADSCALE_API_KEY"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            
            # Ensure it's in .env
            if [ -f "$ENV_FILE" ]; then
                if ! grep -q "HEADSCALE_API_KEY=" "$ENV_FILE"; then
                    echo "HEADSCALE_API_KEY=$HEADSCALE_API_KEY" >> "$ENV_FILE"
                    echo "✓ Added to .env file"
                fi
            fi
            
            echo "Restart UI: docker compose restart headscale-ui"
            exit 0
        fi
    fi
fi

# Generate new API key
echo "Generating new API key..."
API_KEY=$(docker exec headscale headscale apikeys create --expiration 365d 2>&1 | grep -oP 'Key: \K.*' || echo "")

if [ -z "$API_KEY" ]; then
    echo "Error: Failed to generate API key"
    exit 1
fi

echo ""
echo "✓ API Key generated successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Key: $API_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save to credentials file
if [ -f "$CRED_FILE" ]; then
    if grep -q "HEADSCALE_API_KEY=" "$CRED_FILE"; then
        sed -i "s|HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$API_KEY|" "$CRED_FILE"
    else
        echo "HEADSCALE_API_KEY=$API_KEY" >> "$CRED_FILE"
    fi
    echo "HEADSCALE_API_KEY_CREATED=$(date -u +"%Y-%m-%d %H:%M:%S UTC")" >> "$CRED_FILE"
    echo "✓ Saved to: $CRED_FILE"
fi

# Update .env file
if [ -f "$ENV_FILE" ]; then
    if grep -q "HEADSCALE_API_KEY=" "$ENV_FILE"; then
        sed -i "s|HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$API_KEY|" "$ENV_FILE"
        echo "✓ Updated: $ENV_FILE"
    else
        echo "" >> "$ENV_FILE"
        echo "# Headscale API Key (generated $(date -u +"%Y-%m-%d"))" >> "$ENV_FILE"
        echo "HEADSCALE_API_KEY=$API_KEY" >> "$ENV_FILE"
        echo "✓ Added to: $ENV_FILE"
    fi
fi

echo ""
echo "Next steps:"
echo "1. Restart Headscale UI: docker compose restart headscale-ui"
echo "2. Access UI at: https://your-domain.com/headscale-admin/"
echo ""