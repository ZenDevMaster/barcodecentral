# Headscale Routing Implementation Specification

## Overview

This document provides detailed specifications for implementing the automated Headscale mesh routing system. Each section contains exact code to be implemented, file locations, and integration points.

---

## File Structure

```
/
├── docker-entrypoint-wrapper.sh         # NEW - App container routing
├── tailscale-startup.sh                 # NEW - Tailscale initialization
├── tailscale-iptables.sh                # NEW - Firewall configuration
├── Dockerfile                           # MODIFIED - Add networking tools
├── setup.sh                             # MODIFIED - Generate scripts & update docker-compose
├── docker-compose.yml                   # GENERATED - Will be overwritten by setup.sh
└── scripts/
    ├── join-headscale-mesh.sh           # NEW - Automated mesh joining
    ├── generate-authkey.sh              # EXISTING - No changes
    └── enable-routes.sh                 # EXISTING - No changes
```

---

## 1. Docker Entrypoint Wrapper Script

**File**: `docker-entrypoint-wrapper.sh`  
**Created by**: `setup.sh` (when Headscale is enabled)  
**Permissions**: `755` (executable)  
**Used by**: App container as entrypoint

### Complete Script Content

```bash
#!/bin/bash
set -e

echo "[$(date)] Starting barcode-central with Tailscale routing configuration..."

# Wait for Docker networking to stabilize
# This ensures DNS resolution is available
sleep 3

# Resolve tailscale container IP on shared network using Docker DNS
TAILSCALE_IP=$(getent hosts barcode-central-tailscale | awk '{ print $1 }')

if [ -n "$TAILSCALE_IP" ]; then
    echo "[$(date)] Configuring routes via Tailscale gateway: $TAILSCALE_IP"
    
    # Add route to Tailscale mesh network (100.64.0.0/10)
    # This is the standard Tailscale IP range
    if ip route add 100.64.0.0/10 via $TAILSCALE_IP 2>/dev/null; then
        echo "[$(date)] ✓ Added route: 100.64.0.0/10 via $TAILSCALE_IP"
    else
        echo "[$(date)] Route 100.64.0.0/10 already exists or failed to add"
    fi
    
    # Add routes for advertised subnets (if configured via environment variable)
    # Format: ADVERTISED_ROUTES="192.168.11.0/24 10.0.1.0/24"
    if [ -n "$ADVERTISED_ROUTES" ]; then
        echo "[$(date)] Adding routes for advertised subnets..."
        for ROUTE in $ADVERTISED_ROUTES; do
            if ip route add $ROUTE via $TAILSCALE_IP 2>/dev/null; then
                echo "[$(date)] ✓ Added route: $ROUTE via $TAILSCALE_IP"
            else
                echo "[$(date)] Route $ROUTE already exists or failed to add"
            fi
        done
    fi
    
    # Display configured routes for verification
    echo "[$(date)] Current routes to Tailscale gateway:"
    ip route | grep -E "(100.64|$TAILSCALE_IP)" || echo "  (No routes found - check for errors above)"
    
    echo "[$(date)] ✓ Routing configuration complete"
else
    echo "[$(date)] ERROR: Could not resolve Tailscale container IP"
    echo "[$(date)] DNS lookup for 'barcode-central-tailscale' failed"
    echo "[$(date)] Continuing without Tailscale routing..."
fi

echo "[$(date)] Executing application: $@"

# Execute the original application command
# This passes through to gunicorn or whatever was specified in CMD
exec "$@"
```

---

## 2. Tailscale Startup Script

**File**: `tailscale-startup.sh`  
**Created by**: `setup.sh` (when Headscale is enabled)  
**Permissions**: `755` (executable)  
**Used by**: Tailscale container as entrypoint

### Complete Script Content

```bash
#!/bin/sh
set -e

echo "[$(date)] ========================================"
echo "[$(date)] Tailscale Container Initialization"
echo "[$(date)] ========================================"

# Start Tailscale daemon in background
echo "[$(date)] Starting tailscaled daemon..."
tailscaled --tun=userspace-networking --state=/var/lib/tailscale/tailscaled.state &

# Wait for daemon to be ready
echo "[$(date)] Waiting for tailscaled to be ready..."
RETRIES=10
while [ $RETRIES -gt 0 ]; do
    if tailscale status >/dev/null 2>&1; then
        echo "[$(date)] ✓ Tailscale daemon is ready"
        break
    fi
    echo "[$(date)] Daemon not ready yet... ($RETRIES retries left)"
    sleep 2
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -eq 0 ]; then
    echo "[$(date)] ERROR: Tailscale daemon failed to start after 20 seconds"
    exit 1
fi

# Prepare connection parameters
HEADSCALE_URL="${HEADSCALE_URL:-http://headscale:8080}"
echo "[$(date)] Headscale server: $HEADSCALE_URL"

# Connect to Headscale
echo "[$(date)] Connecting to Headscale mesh network..."

if [ -n "$TS_AUTHKEY" ]; then
    # Authkey provided - automatic authentication
    echo "[$(date)] Using provided authkey for automatic authentication"
    
    tailscale up \
        --authkey="$TS_AUTHKEY" \
        --accept-routes=true \
        --login-server="$HEADSCALE_URL" \
        --hostname="${HOSTNAME:-barcode-central-server}"
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] ✓ Successfully connected to Headscale mesh"
        TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "unknown")
        echo "[$(date)] Assigned Tailscale IP: $TAILSCALE_IP"
    else
        echo "[$(date)] ERROR: Failed to connect with authkey"
        exit 1
    fi
else
    # No authkey - manual registration required
    echo "[$(date)] No authkey provided - manual registration required"
    
    tailscale up \
        --accept-routes=true \
        --login-server="$HEADSCALE_URL" \
        --hostname="${HOSTNAME:-barcode-central-server}"
    
    echo "[$(date)] ========================================"
    echo "[$(date)] MANUAL REGISTRATION REQUIRED"
    echo "[$(date)] ========================================"
    echo "[$(date)] "
    echo "[$(date)] Check the logs above for a registration URL like:"
    echo "[$(date)] https://headscale.example.com/register/NODEKEY"
    echo "[$(date)] "
    echo "[$(date)] Then run the automated joining script:"
    echo "[$(date)]   ./scripts/join-headscale-mesh.sh"
    echo "[$(date)] "
    echo "[$(date)] Or manually register with:"
    echo "[$(date)]   docker exec headscale headscale nodes register --user barcode-central --key NODEKEY"
    echo "[$(date)] ========================================"
fi

# Launch iptables configuration in background
echo "[$(date)] Launching iptables configuration..."
/tailscale-iptables.sh &

# Keep container running
echo "[$(date)] ✓ Tailscale startup complete"
echo "[$(date)] Container is now monitoring Tailscale connection..."
exec tail -f /dev/null
```

---

## 3. Tailscale IPTables Configuration Script

**File**: `tailscale-iptables.sh`  
**Created by**: `setup.sh` (when Headscale is enabled)  
**Permissions**: `755` (executable)  
**Called by**: `tailscale-startup.sh` (background process)

### Complete Script Content

```bash
#!/bin/sh
set -e

echo "[$(date)] ========================================"
echo "[$(date)] Tailscale IPTables Configuration"
echo "[$(date)] ========================================"

# Wait for Tailscale to initialize its iptables chains
echo "[$(date)] Waiting for Tailscale iptables initialization..."
sleep 5

# Wait for ts-input chain to exist (created by Tailscale)
RETRIES=10
while [ $RETRIES -gt 0 ]; do
    if iptables -L ts-input -n >/dev/null 2>&1; then
        echo "[$(date)] ✓ Tailscale iptables chains detected"
        break
    fi
    echo "[$(date)] Waiting for ts-input chain... ($RETRIES retries left)"
    sleep 2
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -eq 0 ]; then
    echo "[$(date)] WARNING: ts-input chain not found, iptables rules may not work"
    echo "[$(date)] Continuing anyway..."
fi

echo "[$(date)] Configuring iptables for Docker network access..."

# ============================================================================
# INPUT RULES - Allow Docker networks through Tailscale's ts-input chain
# ============================================================================

# Allow headscale-network (172.29.0.0/16)
if iptables -I ts-input 1 -s 172.29.0.0/16 -j ACCEPT 2>/dev/null; then
    echo "[$(date)] ✓ Added ts-input rule for headscale-network (172.29.0.0/16)"
else
    echo "[$(date)] ts-input rule for 172.29.0.0/16 may already exist"
fi

# Allow barcode-network (172.23.0.0/16)
if iptables -I ts-input 1 -s 172.23.0.0/16 -j ACCEPT 2>/dev/null; then
    echo "[$(date)] ✓ Added ts-input rule for barcode-network (172.23.0.0/16)"
else
    echo "[$(date)] ts-input rule for 172.23.0.0/16 may already exist"
fi

# ============================================================================
# FORWARD RULES - Allow routing from Docker networks to Tailscale destinations
# ============================================================================

# Forward from headscale-network to Tailscale mesh (100.64.0.0/10)
if iptables -I FORWARD 1 -s 172.29.0.0/16 -d 100.64.0.0/10 -j ACCEPT 2>/dev/null; then
    echo "[$(date)] ✓ Added FORWARD rule: 172.29.0.0/16 → 100.64.0.0/10"
else
    echo "[$(date)] FORWARD rule 172.29.0.0/16 → 100.64.0.0/10 may already exist"
fi

# Forward from barcode-network to Tailscale mesh
if iptables -I FORWARD 1 -s 172.23.0.0/16 -d 100.64.0.0/10 -j ACCEPT 2>/dev/null; then
    echo "[$(date)] ✓ Added FORWARD rule: 172.23.0.0/16 → 100.64.0.0/10"
else
    echo "[$(date)] FORWARD rule 172.23.0.0/16 → 100.64.0.0/10 may already exist"
fi

# ============================================================================
# NAT RULES - Masquerade outgoing traffic for proper return routing
# ============================================================================

# NAT for headscale-network to Tailscale mesh
if iptables -t nat -A POSTROUTING -s 172.29.0.0/16 -d 100.64.0.0/10 -j MASQUERADE 2>/dev/null; then
    echo "[$(date)] ✓ Added NAT rule: 172.29.0.0/16 → 100.64.0.0/10"
else
    echo "[$(date)] NAT rule for 172.29.0.0/16 may already exist"
fi

# NAT for barcode-network to Tailscale mesh
if iptables -t nat -A POSTROUTING -s 172.23.0.0/16 -d 100.64.0.0/10 -j MASQUERADE 2>/dev/null; then
    echo "[$(date)] ✓ Added NAT rule: 172.23.0.0/16 → 100.64.0.0/10"
else
    echo "[$(date)] NAT rule for 172.23.0.0/16 may already exist"
fi

# ============================================================================
# VERIFICATION - Display configured rules
# ============================================================================

echo "[$(date)] ========================================"
echo "[$(date)] Verification: Active iptables rules"
echo "[$(date)] ========================================"

echo "[$(date)] "
echo "[$(date)] ts-input chain (first 10 rules):"
iptables -L ts-input -n -v --line-numbers 2>/dev/null | head -12 || echo "  (chain not found)"

echo "[$(date)] "
echo "[$(date)] FORWARD chain (Docker-related rules):"
iptables -L FORWARD -n -v --line-numbers 2>/dev/null | grep -E "172\.(29|23)" || echo "  (no Docker rules found)"

echo "[$(date)] "
echo "[$(date)] NAT POSTROUTING (masquerade rules):"
iptables -t nat -L POSTROUTING -n -v --line-numbers 2>/dev/null | grep -E "172\.(29|23)" || echo "  (no NAT rules found)"

echo "[$(date)] ========================================"
echo "[$(date)] ✓ IPTables configuration complete"
echo "[$(date)] ========================================"
```

---

## 4. Dockerfile Modifications

**File**: `Dockerfile`  
**Action**: Modify line 9  
**Changes**: Add networking tools for route management

### Change Required

**Current line 9**:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**Modified line 9**:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    iputils-ping \
    dnsutils \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
```

---

## Summary

This specification document provides:
1. ✅ Complete script content for all 3 routing scripts
2. ✅ Dockerfile modifications specified
3. ⏳ Setup.sh modifications (see [`HEADSCALE_ROUTING_ARCHITECTURE.md`](HEADSCALE_ROUTING_ARCHITECTURE.md) Section on Setup Script Integration)
4. ⏳ Automated mesh joining script (will create in next step)

**Next Step**: Create the `scripts/join-headscale-mesh.sh` script with complete implementation.

**Document Version**: 1.0  
**Status**: In Progress  
**Date**: 2025-11-26
