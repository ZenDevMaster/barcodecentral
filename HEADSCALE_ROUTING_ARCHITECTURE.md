# Headscale Mesh Network Routing Architecture

## Executive Summary

This document outlines the complete architecture for enabling Docker container-to-remote-printer communication via Tailscale mesh networking, addressing the critical issues in the current setup and implementing a fully automated solution.

---

## Current Problems Identified

### 1. API Key Generation Failure
```bash
# This command fails silently due to grep pattern mismatch
API_KEY=$(docker exec headscale headscale apikeys create --expiration 90d | grep -oP '(?<=Created API key: ).*')
echo $API_KEY  # Returns empty!
```

**Root Cause**: The output format from headscale doesn't match the grep pattern, causing silent failure.

**Solution**: Extract the key correctly and automate the entire process in a dedicated script.

### 2. Manual Mesh Joining Process
Current process requires manual intervention:
- Wait for containers to start
- Extract registration URL from logs
- Manually register node in Headscale

**Solution**: Automated mesh joining script that polls for readiness and auto-registers.

### 3. Missing Network Routing
The barcode-central container cannot communicate with remote printers because:
- No routes configured to Tailscale mesh network (100.64.0.0/10)
- No routes configured to remote subnets (e.g., 192.168.11.0/24)
- Tailscale iptables rules block Docker network traffic

**Solution**: Implement comprehensive routing and firewall configuration.

---

## Proposed Architecture

### Network Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Docker Host (VPS)                                               │
│                                                                  │
│  ┌────────────────────┐         ┌──────────────────────┐       │
│  │ barcode-central    │────────►│ barcode-central-     │       │
│  │ (app container)    │  DNS    │ tailscale            │       │
│  │                    │  lookup │ (mesh gateway)       │       │
│  │ Routes added:      │         │                      │       │
│  │ 100.64.0.0/10 via  │         │ Tailscale IP:        │       │
│  │ barcode-central-   │         │ 100.64.0.1           │       │
│  │ tailscale          │         │                      │       │
│  │                    │         │ iptables configured  │       │
│  │ 192.168.11.0/24 via│         │ to allow Docker      │       │
│  │ barcode-central-   │         │ network traffic      │       │
│  │ tailscale          │         │                      │       │
│  └────────────────────┘         └──────────────────────┘       │
│         │                                │                      │
│         │                                │                      │
│  ┌──────▼────────────────────────────────▼──────┐              │
│  │  headscale-network (172.29.0.0/16)           │              │
│  │  barcode-network (172.23.0.0/16)             │              │
│  └──────────────────────────────────────────────┘              │
│                                    │                            │
│                          ┌─────────▼──────────┐                │
│                          │ headscale          │                │
│                          │ (coordinator)      │                │
│                          └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                          Tailscale Mesh (100.64.0.0/10)
                                    │
                    ┌───────────────▼────────────────┐
                    │ Raspberry Pi (skulabelpi)      │
                    │ Tailscale IP: 100.64.0.2       │
                    │ Advertises: 192.168.11.0/24    │
                    └───────────────┬────────────────┘
                                    │
                          Physical LAN (192.168.11.0/24)
                                    │
                            ┌───────▼────────┐
                            │ Zebra Printer  │
                            │ 192.168.11.12  │
                            │ Port 9100      │
                            └────────────────┘
```

### Key Design Decisions

#### 1. DNS-Based Container Resolution
**Decision**: Use Docker's built-in DNS instead of hardcoded IPs

**Rationale**:
- Docker provides automatic DNS resolution for container names
- More flexible - survives container recreation with different IPs
- Aligns with Docker best practices
- Simplifies configuration

**Implementation**:
```bash
# In docker-entrypoint-wrapper.sh
TAILSCALE_IP=$(getent hosts barcode-central-tailscale | awk '{ print $1 }')
ip route add 100.64.0.0/10 via $TAILSCALE_IP
```

#### 2. Network Subnet Configuration
**Decision**: Use Docker-managed networks with automatic IP assignment

**Rationale**:
- Docker handles IP assignment and prevents conflicts
- Networks are isolated and secure by default
- No need to hardcode subnet ranges in configuration

**Implementation**:
```yaml
networks:
  barcode-network:
    name: barcode-network
    driver: bridge
  headscale-network:
    name: headscale-network
    driver: bridge
```

#### 3. Script-Based Configuration
**Decision**: Use separate shell scripts for complex startup logic

**Rationale**:
- Better maintainability - easier to debug and modify
- Reusable - can be run manually for troubleshooting
- Testable - can be tested outside Docker environment
- Clear separation of concerns

**Scripts to Create**:
1. `docker-entrypoint-wrapper.sh` - App container routing
2. `tailscale-startup.sh` - Tailscale initialization
3. `tailscale-iptables.sh` - Firewall configuration
4. `scripts/join-headscale-mesh.sh` - Automated mesh joining

#### 4. Post-Deployment Automation
**Decision**: Provide separate script for mesh joining after deployment

**Rationale**:
- Containers need to be running before joining can occur
- Allows users to verify container health first
- Provides clear checkpoint in deployment process
- Easier to retry if it fails

---

## Implementation Components

### Component 1: App Container Routing Script

**File**: `docker-entrypoint-wrapper.sh`

**Purpose**: Configure routes in app container to direct Tailscale traffic through tailscale container

**Key Functions**:
- Wait for Docker networking to stabilize
- Resolve tailscale container IP via DNS
- Add routes for Tailscale mesh (100.64.0.0/10)
- Add routes for advertised subnets (configurable via ENV)
- Execute original application command

**Requirements**:
- Container must have `NET_ADMIN` capability
- Must run before application starts (entrypoint wrapper)

### Component 2: Tailscale Startup Script

**File**: `tailscale-startup.sh`

**Purpose**: Initialize Tailscale daemon and configure connection

**Key Functions**:
- Start tailscaled in background
- Wait for daemon readiness
- Connect to Headscale with proper flags:
  - `--accept-routes=true` (critical for subnet routing)
  - `--login-server=http://headscale:8080`
  - `--authkey=${TAILSCALE_AUTHKEY}` (if available)
  - `--advertise-routes` (if needed)
- Log registration URL if authkey not provided
- Keep container running

### Component 3: Tailscale Firewall Script

**File**: `tailscale-iptables.sh`

**Purpose**: Configure iptables to allow Docker network traffic through Tailscale

**Key Functions**:
- Wait for Tailscale to initialize iptables chains
- Add Docker network subnets to ts-input chain (ACCEPT)
- Add FORWARD rules for Docker → Tailscale mesh
- Add FORWARD rules for Docker → advertised subnets
- Configure NAT/MASQUERADE for return traffic

**Requirements**:
- Container must have `NET_ADMIN` capability
- Must run after Tailscale initializes but before traffic flows

### Component 4: Automated Mesh Joining Script

**File**: `scripts/join-headscale-mesh.sh`

**Purpose**: Automate the process of joining barcode-central-tailscale to Headscale mesh

**Process Flow**:
```
1. Wait for containers to be healthy
   ├─ Check headscale container is running
   ├─ Check tailscale container is running
   └─ Verify headscale API responds

2. Create default user/namespace in Headscale
   └─ docker exec headscale headscale users create barcode-central

3. Monitor tailscale logs for registration URL
   ├─ docker logs -f barcode-central-tailscale
   ├─ Extract node key from URL
   └─ Timeout after 60 seconds

4. Register node in Headscale
   ├─ docker exec headscale headscale nodes register \
   │    --user barcode-central \
   │    --key <extracted-node-key>
   └─ Verify registration successful

5. Verify mesh connectivity
   ├─ Check tailscale status shows connected
   └─ Confirm Tailscale IP assigned

6. Generate and configure API key (if Headscale UI enabled)
   ├─ Create API key with proper command
   ├─ Update .env file
   └─ Restart headscale-ui container
```

**Error Handling**:
- Timeout if containers don't start within threshold
- Retry logic for transient failures
- Clear error messages for user intervention
- Rollback capability if needed

---

## Docker Compose Changes

### App Container Configuration

```yaml
  app:
    build:
      context: .
      dockerfile: Dockerfile
    
    container_name: barcode-central
    restart: unless-stopped
    
    # REQUIRED: Enable route manipulation
    cap_add:
      - NET_ADMIN
    
    # REQUIRED: Use wrapper script to configure routes
    entrypoint: ["/docker-entrypoint-wrapper.sh"]
    command: ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
    
    env_file:
      - .env
    
    environment:
      # Routes to configure (space-separated list of CIDR blocks)
      - ADVERTISED_ROUTES=${ADVERTISED_ROUTES:-}
    
    volumes:
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
      # REQUIRED: Mount routing script
      - ./docker-entrypoint-wrapper.sh:/docker-entrypoint-wrapper.sh:ro
    
    # REQUIRED: Both networks for routing + nginx access
    networks:
      - barcode-network      # For nginx reverse proxy
      - headscale-network    # For Tailscale routing
    
    depends_on:
      tailscale:
        condition: service_started
```

### Tailscale Container Configuration

```yaml
  tailscale:
    image: tailscale/tailscale:latest
    container_name: barcode-central-tailscale
    restart: unless-stopped
    
    profiles:
      - headscale
    
    hostname: barcode-central-server
    
    # Use startup script for complex initialization
    entrypoint: ["/tailscale-startup.sh"]
    
    environment:
      - TS_AUTHKEY=${TAILSCALE_AUTHKEY:-}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_USERSPACE=true
      - TS_ACCEPT_DNS=true
      - HEADSCALE_URL=http://headscale:8080
    
    volumes:
      - ./data/tailscale:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
      # REQUIRED: Mount startup and iptables scripts
      - ./tailscale-startup.sh:/tailscale-startup.sh:ro
      - ./tailscale-iptables.sh:/tailscale-iptables.sh:ro
    
    # REQUIRED: For iptables and routing
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    
    networks:
      - barcode-network
      - headscale-network
    
    depends_on:
      headscale:
        condition: service_healthy
```

### Dockerfile Changes

```dockerfile
FROM python:3.11-slim

# Install system dependencies including networking tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# ... rest of Dockerfile ...

# Note: NET_ADMIN capability added in docker-compose.yml
```

---

## Testing & Verification

### Test Plan

#### Phase 1: Container Startup
```bash
# Start containers
docker compose --profile headscale up -d

# Verify containers are running
docker compose ps

# Check container logs
docker compose logs headscale
docker compose logs tailscale
docker compose logs app
```

#### Phase 2: Mesh Joining
```bash
# Run automated mesh joining
./scripts/join-headscale-mesh.sh

# Verify Tailscale status
docker exec barcode-central-tailscale tailscale status

# Check routes in app container
docker exec barcode-central ip route | grep -E "(100.64|tailscale)"
```

#### Phase 3: Firewall Verification
```bash
# Check iptables rules in tailscale container
docker exec barcode-central-tailscale iptables -L ts-input -n -v

# Verify FORWARD rules
docker exec barcode-central-tailscale iptables -L FORWARD -n -v | grep "172.29\|172.23"

# Check NAT rules
docker exec barcode-central-tailscale iptables -t nat -L POSTROUTING -n -v
```

#### Phase 4: Connectivity Testing
```bash
# Test ping to Tailscale mesh
docker exec barcode-central ping -c 3 100.64.0.2

# Test ping to remote printer subnet
docker exec barcode-central ping -c 3 192.168.11.12

# Test printer port connectivity
docker exec barcode-central nc -zv 192.168.11.12 9100
```

---

## Troubleshooting Guide

### Issue: Routes not appearing in app container

**Symptoms**:
```bash
docker exec barcode-central ip route | grep 100.64
# No output
```

**Diagnosis**:
```bash
# Check if wrapper script ran
docker logs barcode-central | grep "Configuring routes"

# Check if NET_ADMIN capability exists
docker inspect barcode-central | grep -A 5 CapAdd

# Manually test DNS resolution
docker exec barcode-central getent hosts barcode-central-tailscale
```

**Solutions**:
1. Verify NET_ADMIN capability in docker-compose.yml
2. Check wrapper script is mounted and executable
3. Manually add routes for testing:
   ```bash
   docker exec barcode-central sh -c '
   TAILSCALE_IP=$(getent hosts barcode-central-tailscale | awk "{print \$1}")
   ip route add 100.64.0.0/10 via $TAILSCALE_IP
   '
   ```

### Issue: Tailscale iptables rules not working

**Symptoms**:
- Can ping Tailscale IPs from host
- Cannot ping from app container

**Diagnosis**:
```bash
# Check if ts-input chain has Docker network rules
docker exec barcode-central-tailscale iptables -L ts-input -n | grep "172.29\|172.23"

# Check logs
docker logs barcode-central-tailscale | grep iptables
```

**Solutions**:
1. Manually apply iptables rules:
   ```bash
   docker exec barcode-central-tailscale sh -c '
   iptables -I ts-input 1 -s 172.29.0.0/16 -j ACCEPT
   iptables -I ts-input 1 -s 172.23.0.0/16 -j ACCEPT
   '
   ```
2. Verify script ran after Tailscale initialized
3. Check script has execute permissions

### Issue: Mesh joining script cannot find node key

**Symptoms**:
```bash
./scripts/join-headscale-mesh.sh
# Error: Could not find registration URL
```

**Diagnosis**:
```bash
# Check tailscale container logs manually
docker logs barcode-central-tailscale | grep -i register

# Verify Tailscale is actually trying to connect
docker exec barcode-central-tailscale tailscale status
```

**Solutions**:
1. Ensure Tailscale container is fully started
2. Check Headscale is reachable: `docker exec barcode-central-tailscale ping headscale`
3. Manually register using URL from logs
4. Verify Headscale config has correct server_url

---

## Security Considerations

### 1. Network Isolation
- Docker networks provide isolation between services
- Only necessary containers share networks
- Tailscale traffic is encrypted end-to-end

### 2. Firewall Rules
Current iptables rules allow **all** Docker network traffic to Tailscale mesh.

**More Restrictive Alternative**:
```bash
# Only allow specific destination ports
iptables -I FORWARD 1 -s 172.29.0.0/16 -d 100.64.0.0/10 -p tcp --dport 9100 -j ACCEPT
iptables -I FORWARD 1 -s 172.29.0.0/16 -d 100.64.0.0/10 -p tcp --dport 631 -j ACCEPT
# Reject everything else
iptables -A FORWARD -s 172.29.0.0/16 -d 100.64.0.0/10 -j REJECT
```

### 3. Capabilities
Both app and tailscale containers require `NET_ADMIN`:
- Only granted to containers that need it
- Containers run as non-root user where possible
- Read-only filesystems where appropriate (headscale)

---

## Performance Considerations

### Expected Latency
- **Direct LAN print job**: ~50-100ms
- **Via Tailscale mesh**: ~200-400ms (depends on internet connection)
- **Recommended timeout**: 5-10 seconds for print operations

### Optimization Recommendations
1. Use regional DERP servers for lower latency
2. Enable direct connections where possible (NAT traversal)
3. Monitor Tailscale connection quality: `tailscale status`
4. Consider dedicated bandwidth for print operations

---

## Summary of Files to Create/Modify

### New Files Created:
1. `docker-entrypoint-wrapper.sh` - App container routing
2. `tailscale-startup.sh` - Tailscale initialization
3. `tailscale-iptables.sh` - Firewall configuration
4. `scripts/join-headscale-mesh.sh` - Automated mesh joining
5. `HEADSCALE_ROUTING_ARCHITECTURE.md` - This document

### Files Modified:
1. `setup.sh` - Add script generation, update instructions
2. `docker-compose.yml` - Template generation in setup.sh
3. `Dockerfile` - Add networking tools

### Files Unchanged (Already Correct):
1. `scripts/generate-authkey.sh` - Works as-is
2. `scripts/enable-routes.sh` - Works as-is

---

## Documentation Version
- **Version**: 1.0
- **Date**: 2025-11-26
- **Author**: Automated Architecture Planning
- **Status**: Ready for Implementation
