# Setup.sh Refactoring Architecture Plan

## Executive Summary

This document outlines the comprehensive architectural redesign of `setup.sh` to properly separate headscale/headscale-ui services onto their own domain with dedicated reverse proxy configuration, while maintaining security, ease of use, and re-runnability.

## Current Issues Identified

### 1. **Port Configuration Issues**
- Headscale internal port incorrectly assumed as 3000 (actually 8080)
- Headscale-UI port configuration unclear (actually uses 3000 for the UI container)
- No clear separation between internal Docker ports and external exposed ports

### 2. **Domain Architecture Issues**
- Headscale and barcode app share the same domain in current setup
- No proper separation for headscale services
- Headscale-UI routing mixed with main app routing

### 3. **Nginx Configuration Issues**
- Single nginx config tries to handle both apps
- No separate server blocks for different domains
- Port 80 only configuration (no SSL preparation)
- Missing proper upstream definitions

### 4. **Security Concerns**
- Unnecessary port exposure to external world
- No firewall configuration guidance
- Mixed internal/external port bindings
- No clear security boundaries

### 5. **Re-runnability Issues**
- Credentials not always preserved
- API keys not auto-configured
- No state detection for partial configurations
- Difficult to reconfigure without starting over

## New Architecture Design

### Domain Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└────────────────┬────────────────────────┬───────────────────────┘
                 │                        │
                 │ HTTPS/HTTP             │ HTTPS/HTTP
                 │                        │
    ┌────────────▼──────────────┐  ┌─────▼──────────────────────┐
    │  print.example.com        │  │  headscale.example.com     │
    │  (Barcode Central)        │  │  (Headscale + UI)          │
    └───────────────────────────┘  └────────────────────────────┘
```

**Key Principle**: Headscale and Headscale-UI share ONE domain, separate from the barcode app.

### Port Architecture

#### Modern Default Ports

```yaml
# Barcode Central App
HTTP_PORT: 5000          # Internal container port
EXTERNAL_PORT: 5000      # Host exposed port (default, user prompted)

# Headscale Services (shared domain: headscale.example.com)
HEADSCALE_HTTP_PORT: 8080        # Internal HTTP API port (container)
HEADSCALE_GRPC_PORT: 50443       # Internal gRPC port (not exposed)
HEADSCALE_METRICS_PORT: 9090     # Internal metrics port (not exposed)
HEADSCALE_WIREGUARD_PORT: 41641  # WireGuard port (UDP) - Tailscale standard

HEADSCALE_UI_PORT: 8080          # Internal UI container port

# External Exposure (when using nginx - user prompted for each)
HEADSCALE_EXTERNAL_HTTP: 8080    # Host port for headscale HTTP (default, user prompted)
HEADSCALE_UI_EXTERNAL: 8081      # Host port for headscale-ui (default, user prompted)
HEADSCALE_WIREGUARD_EXTERNAL: 41641  # WireGuard (standard port, user prompted)
```

**Port Configuration Philosophy**:
- All ports are **prompted to the user** with sensible defaults
- User can change any port to avoid conflicts
- Ports are **preserved on re-run** of setup.sh
- WireGuard port 41641 is the Tailscale/Headscale standard but can be changed

#### Port Exposure Strategy

**With Traefik (Recommended)**:
- Traefik handles all external ports (80, 443)
- Services communicate via Docker internal networks
- No host port exposure needed except WireGuard (41641/udp by default)

**With Nginx (Host-based)**:
- Nginx on host accesses services via exposed host ports (localhost only)
- Barcode app: localhost:5000 (default, user prompted)
- Headscale: localhost:8080 (default, user prompted)
- Headscale-UI: localhost:8081 (default, user prompted)
- WireGuard: 41641/udp (default, user prompted)

**LAN-only (Direct Exposure)**:
- Direct port exposure: 5000 for barcode app (default, user prompted)
- Headscale services optional (if mesh VPN needed)
- All ports configurable by user

### Nginx Configuration Architecture

#### Two Separate Nginx Configurations

**1. Barcode Central Nginx Config** (`config/nginx/barcode-central.conf`)
```nginx
# HTTP only (port 80) - SSL configured later by user with certbot
server {
    listen 80;
    server_name print.example.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /api/health {
        proxy_pass http://localhost:5000;
        access_log off;
    }
}
```

**2. Headscale Nginx Config** (`config/nginx/headscale.conf`)
```nginx
# HTTP only (port 80) - SSL configured later by user with certbot
# Upstream definitions
upstream headscale_backend {
    server localhost:${HEADSCALE_EXTERNAL_HTTP};
}

upstream headscale_ui_backend {
    server localhost:${HEADSCALE_UI_EXTERNAL};
}

# Main server block
server {
    listen 80;
    server_name headscale.example.com;
    
    # Headscale UI at /web path
    location /web {
        proxy_pass http://headscale_ui_backend/web/;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for UI
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Headscale API at root
    location / {
        proxy_pass http://headscale_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Headscale
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_buffering off;
        proxy_redirect http:// https://;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=15552000; includeSubDomains" always;
    }
}
```

### Traefik Configuration Architecture

#### Traefik with Separate Domains

**docker-compose.yml labels for Barcode Central**:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.barcode.rule=Host(`print.example.com`)"
  - "traefik.http.routers.barcode.entrypoints=websecure"
  - "traefik.http.routers.barcode.tls=true"
  - "traefik.http.routers.barcode.tls.certresolver=letsencrypt"
  - "traefik.http.services.barcode.loadbalancer.server.port=5000"
```

**docker-compose.yml labels for Headscale**:
```yaml
headscale:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.headscale.rule=Host(`headscale.example.com`)"
    - "traefik.http.routers.headscale.entrypoints=websecure"
    - "traefik.http.routers.headscale.tls=true"
    - "traefik.http.routers.headscale.tls.certresolver=letsencrypt"
    - "traefik.http.services.headscale.loadbalancer.server.port=8080"
    - "traefik.http.routers.headscale.priority=1"

headscale-ui:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.headscale-ui.rule=Host(`headscale.example.com`) && PathPrefix(`/web`)"
    - "traefik.http.routers.headscale-ui.entrypoints=websecure"
    - "traefik.http.routers.headscale-ui.tls=true"
    - "traefik.http.routers.headscale-ui.tls.certresolver=letsencrypt"
    - "traefik.http.services.headscale-ui.loadbalancer.server.port=3000"
    - "traefik.http.routers.headscale-ui.priority=100"
```

### Docker Compose Port Exposure Strategy

#### With Traefik (No Host Port Exposure)
```yaml
services:
  app:
    # No ports exposed - Traefik accesses via Docker network
    networks:
      - barcode-network
  
  headscale:
    ports:
      - "41641:41641/udp"  # Only WireGuard exposed
    networks:
      - headscale-network
  
  headscale-ui:
    # No ports exposed - Traefik accesses via Docker network
    networks:
      - headscale-network
  
  traefik:
    ports:
      - "80:80"
      - "443:443"
    networks:
      - barcode-network
      - headscale-network
```

#### With Nginx (Host Port Exposure)
```yaml
services:
  app:
    ports:
      - "5000:5000"  # Nginx on host accesses this
  
  headscale:
    ports:
      - "${HEADSCALE_EXTERNAL_HTTP:-8080}:8080"      # HTTP API
      - "${HEADSCALE_WIREGUARD_EXTERNAL:-41641}:41641/udp"  # WireGuard
    # Note: GRPC and metrics not exposed externally
  
  headscale-ui:
    ports:
      - "${HEADSCALE_UI_EXTERNAL:-8081}:8080"  # UI port
```

#### LAN-only (Direct Exposure)
```yaml
services:
  app:
    ports:
      - "5000:5000"
  
  # Headscale optional for LAN-only
```

### Security Architecture

#### Firewall Configuration

**Note**: Setup.sh will **advise** the user on firewall configuration but will **not automatically configure** the firewall. Users must manually run firewall commands.

**With Traefik**:
```bash
# Only expose Traefik and WireGuard
ufw allow 80/tcp      # HTTP (redirects to HTTPS)
ufw allow 443/tcp     # HTTPS
ufw allow ${HEADSCALE_WIREGUARD_EXTERNAL}/udp   # WireGuard (if headscale enabled)
ufw enable
```

**With Nginx**:
```bash
# Expose nginx and WireGuard
ufw allow 80/tcp      # HTTP (for both domains)
ufw allow 443/tcp     # HTTPS (after certbot)
ufw allow ${HEADSCALE_WIREGUARD_EXTERNAL}/udp   # WireGuard (if headscale enabled)
ufw enable

# Application ports NOT exposed externally (accessed via localhost by nginx)
```

**LAN-only**:
```bash
# Only expose application port
ufw allow ${HTTP_PORT}/tcp
# Optionally headscale if needed
ufw allow ${HEADSCALE_EXTERNAL_HTTP}/tcp
ufw allow ${HEADSCALE_WIREGUARD_EXTERNAL}/udp
ufw enable
```

#### Docker Network Isolation

```yaml
networks:
  barcode-network:
    name: barcode-network
    driver: bridge
    internal: false  # Needs external access
  
  headscale-network:
    name: headscale-network
    driver: bridge
    internal: false  # Needs external access for WireGuard
  
  # Traefik bridges both networks when enabled
```

### Credential and API Key Management

#### Credential Preservation Strategy

**Files to Preserve**:
1. `.env` - Main configuration (SECRET_KEY, passwords)
2. `config/headscale/.credentials` - Headscale UI credentials
3. `config/headscale/.api-key` - Headscale API key (auto-generated)
4. `data/headscale/db.sqlite` - Headscale database

**Preservation Logic**:
```bash
# On setup.sh re-run:
1. Check if .env exists
2. Parse existing values
3. Offer to keep or regenerate each credential
4. ALWAYS preserve SECRET_KEY (maintains sessions)
5. ALWAYS preserve Headscale API key if exists
6. Offer to regenerate passwords if needed
```

#### API Key Auto-Configuration

**Headscale API Key Flow**:
```bash
# During setup.sh:
1. Generate docker-compose.yml with headscale
2. Start headscale container
3. Auto-generate API key: docker exec headscale headscale apikeys create
4. Save to config/headscale/.api-key
5. Update .env with HEADSCALE_API_KEY
6. Restart headscale-ui to pick up new key
```

**Implementation**:
```bash
generate_headscale_api_key() {
    if [ -f "config/headscale/.api-key" ]; then
        print_info "Headscale API key already exists"
        HEADSCALE_API_KEY=$(cat config/headscale/.api-key)
    else
        print_info "Generating Headscale API key..."
        # Start headscale temporarily if not running
        docker compose up -d headscale
        sleep 5
        
        # Generate API key
        HEADSCALE_API_KEY=$(docker exec headscale headscale apikeys create --expiration 90d | grep -oP '(?<=key: ).*')
        
        # Save for future runs
        echo "$HEADSCALE_API_KEY" > config/headscale/.api-key
        chmod 600 config/headscale/.api-key
        
        print_success "API key generated and saved"
    fi
    
    # Update .env
    sed -i "s|^HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$HEADSCALE_API_KEY|" .env
}
```

### Setup.sh Flow Redesign

#### New Interactive Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Detect Existing Configuration                           │
│ - Check for .env, credentials, API keys                         │
│ - Offer to preserve or reconfigure                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Network Access Type                                     │
│ 1) LAN-only (simple, no reverse proxy)                          │
│ 2) External access (requires domain)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Domain Configuration (if external)                      │
│ - Barcode Central domain: print.example.com                     │
│ - Headscale domain (if enabled): headscale.example.com          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Reverse Proxy Choice (if external)                      │
│ 1) Traefik (automatic SSL, Docker-native)                       │
│ 2) Nginx (manual SSL with certbot, host-based)                  │
│ 3) None (manual configuration)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Headscale Mesh VPN                                      │
│ - Enable headscale? (y/N)                                       │
│ - If yes: Configure headscale domain                            │
│ - Enable headscale-ui? (Y/n)                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Port Configuration                                      │
│ - Barcode app port [5000] (always prompt user)                  │
│ - Headscale HTTP port [8080] (if nginx, prompt user)            │
│ - Headscale UI port [8081] (if nginx, prompt user)              │
│ - WireGuard port [41641] (if headscale, prompt user)            │
│ - All ports preserved on re-run                                 │
│ - User can change any port to avoid conflicts                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Credentials                                             │
│ - Preserve existing or generate new                             │
│ - Barcode Central: username/password                            │
│ - Headscale UI: username/password (if enabled)                  │
│ - SECRET_KEY (always preserve if exists)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Review & Confirm                                        │
│ - Show complete configuration                                   │
│ - Confirm before generating files                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Generate Configuration Files                            │
│ - .env                                                           │
│ - docker-compose.yml                                            │
│ - config/nginx/barcode-central.conf (if nginx)                  │
│ - config/nginx/headscale.conf (if nginx + headscale)            │
│ - config/headscale/config.yaml (if headscale)                   │
│ - config/headscale/acl.json (if headscale)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 10: Post-Setup Instructions                                │
│ - DNS configuration                                              │
│ - Firewall setup                                                 │
│ - Nginx deployment (if nginx)                                   │
│ - SSL certificate setup (certbot commands)                      │
│ - Docker compose up                                              │
│ - Headscale API key generation (if headscale)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration File Generation

#### .env File Structure

```bash
# Barcode Central Configuration
# Generated by setup.sh on $(date)

# ============================================================================
# Application Settings
# ============================================================================
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO

# Security
SECRET_KEY=${SECRET_KEY}
LOGIN_USER=${LOGIN_USER}
LOGIN_PASSWORD=${LOGIN_PASSWORD}

# Session
SESSION_COOKIE_SECURE=${USE_SSL}
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Network
HTTP_PORT=${HTTP_PORT}

# ============================================================================
# Reverse Proxy Configuration
# ============================================================================
REVERSE_PROXY=${REVERSE_PROXY}  # traefik, nginx, or none
DOMAIN=${DOMAIN}
$([ "$USE_SSL" = true ] && echo "ACME_EMAIL=${ACME_EMAIL}")

# ============================================================================
# Headscale Configuration (if enabled)
# ============================================================================
$(if [ "$USE_HEADSCALE" = true ]; then
cat << EOF
HEADSCALE_ENABLED=true
HEADSCALE_DOMAIN=${HEADSCALE_DOMAIN}
HEADSCALE_HTTP_PORT=${HEADSCALE_HTTP_PORT}
HEADSCALE_EXTERNAL_HTTP=${HEADSCALE_EXTERNAL_HTTP}
HEADSCALE_WIREGUARD_PORT=${HEADSCALE_WIREGUARD_PORT}
HEADSCALE_SERVER_URL=http://${HEADSCALE_DOMAIN}:${HEADSCALE_EXTERNAL_HTTP}

# Headscale UI (if enabled)
$(if [ "$USE_HEADSCALE_UI" = true ]; then
cat << EOF
HEADSCALE_UI_ENABLED=true
HEADSCALE_UI_PORT=${HEADSCALE_UI_PORT}
HEADSCALE_UI_EXTERNAL=${HEADSCALE_UI_EXTERNAL}
HEADSCALE_UI_USER=${HEADSCALE_UI_USER}
HEADSCALE_UI_PASSWORD=${HEADSCALE_UI_PASSWORD}
HEADSCALE_API_KEY=${HEADSCALE_API_KEY}
EOF
fi)
EOF
fi)

# ============================================================================
# Docker Compose Profiles
# ============================================================================
COMPOSE_PROFILES=${PROFILES}
```

#### docker-compose.yml Generation Logic

**Key Changes**:
1. Conditional port exposure based on reverse proxy choice
2. Separate networks for barcode and headscale
3. Traefik labels only when Traefik selected
4. Proper internal port mapping

```yaml
# Port exposure logic:
# - With Traefik: No host ports except WireGuard
# - With Nginx: Expose to localhost for nginx access
# - LAN-only: Direct exposure
```

### Re-runnability Features

#### State Detection

```bash
detect_existing_state() {
    local state="new"
    
    if [ -f .env ]; then
        state="existing"
        print_info "Detected existing configuration"
        
        # Check what's configured
        if grep -q "HEADSCALE_ENABLED=true" .env; then
            EXISTING_HEADSCALE=true
        fi
        
        if grep -q "REVERSE_PROXY=traefik" .env; then
            EXISTING_TRAEFIK=true
        fi
    fi
    
    if [ -f config/headscale/.api-key ]; then
        EXISTING_API_KEY=true
    fi
    
    echo "$state"
}
```

#### Reconfiguration Options

```bash
# On re-run, offer:
1. Keep all existing configuration (quick restart)
2. Reconfigure specific components (selective update)
3. Complete reconfiguration (fresh start, preserve credentials)
4. Factory reset (delete everything, start fresh)
```

### Post-Setup Automation

#### Automatic API Key Generation

```bash
# After docker-compose up:
if [ "$USE_HEADSCALE" = true ] && [ ! -f config/headscale/.api-key ]; then
    print_info "Waiting for headscale to start..."
    sleep 10
    
    print_info "Generating Headscale API key..."
    generate_headscale_api_key
    
    print_info "Updating configuration..."
    docker compose restart headscale-ui
    
    print_success "Headscale API key configured automatically"
fi
```

#### SSL Certificate Guidance

```bash
# For nginx deployments:
print_info "To enable SSL with Let's Encrypt:"
echo ""
echo "1. Install certbot:"
echo "   sudo apt-get install certbot python3-certbot-nginx"
echo ""
echo "2. Obtain certificates:"
echo "   sudo certbot --nginx -d ${DOMAIN}"
if [ "$USE_HEADSCALE" = true ]; then
    echo "   sudo certbot --nginx -d ${HEADSCALE_DOMAIN}"
fi
echo ""
echo "3. Certbot will automatically update nginx configs for HTTPS"
echo "4. Test renewal: sudo certbot renew --dry-run"
```

## Implementation Checklist

### Phase 1: Core Refactoring
- [ ] Refactor domain configuration logic (separate domains)
- [ ] Implement new port management system
- [ ] Create nginx config generation for both services
- [ ] Update docker-compose.yml generation logic
- [ ] Implement state detection and preservation

### Phase 2: Security & Networking
- [ ] Implement proper Docker network separation
- [ ] Add firewall configuration script
- [ ] Update port exposure logic based on reverse proxy choice
- [ ] Add security validation checks

### Phase 3: Automation
- [ ] Implement automatic API key generation
- [ ] Add credential preservation logic
- [ ] Create re-run detection and options
- [ ] Add post-setup automation scripts

### Phase 4: Documentation & Testing
- [ ] Update all documentation
- [ ] Create testing scenarios
- [ ] Add troubleshooting guides
- [ ] Create migration guide from old setup

## Testing Scenarios

### Scenario 1: Fresh Install - LAN Only
```bash
./setup.sh
# Choose: LAN-only, no headscale
# Expected: Working barcode app on port 5000
```

### Scenario 2: Fresh Install - Traefik + Headscale
```bash
./setup.sh
# Choose: External, Traefik, SSL, Headscale with UI
# Expected: Two domains with SSL, headscale API key auto-generated
```

### Scenario 3: Fresh Install - Nginx + Headscale
```bash
./setup.sh
# Choose: External, Nginx, Headscale with UI
# Expected: Two nginx configs, proper port exposure, SSL guidance
```

### Scenario 4: Re-run - Preserve Everything
```bash
./setup.sh
# Existing config detected
# Choose: Keep all settings
# Expected: No changes, quick validation
```

### Scenario 5: Re-run - Add Headscale
```bash
./setup.sh
# Existing config without headscale
# Choose: Enable headscale
# Expected: Headscale added, credentials preserved, API key generated
```

### Scenario 6: Re-run - Change Ports
```bash
./setup.sh
# Port conflict detected
# Choose: Change ports
# Expected: New ports configured, services restart successfully
```

## Migration Path

### From Current Setup to New Architecture

```bash
# 1. Backup existing configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup

# 2. Stop services
docker compose down

# 3. Run new setup.sh
./setup.sh
# It will detect existing config and offer to preserve credentials

# 4. Review generated configs
cat config/nginx/barcode-central.conf
cat config/nginx/headscale.conf  # if headscale enabled

# 5. Deploy nginx configs (if using nginx)
sudo cp config/nginx/*.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/barcode-central /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/headscale /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 6. Start services
docker compose up -d

# 7. Verify
docker compose ps
curl http://localhost:5000/api/health
curl http://localhost:8999/health  # if headscale
```

## Success Criteria

### Must Have
- ✅ Separate domains for barcode app and headscale
- ✅ Proper nginx configuration with /web routing for headscale-ui
- ✅ Correct port mappings (8080 for headscale, 3000 for headscale-ui)
- ✅ Port 80 only nginx configs (SSL added later by user)
- ✅ Credential preservation on re-run
- ✅ Automatic API key generation
- ✅ Re-runnable without data loss
- ✅ Clear security boundaries

### Should Have
- ✅ Firewall configuration automation
- ✅ SSL certificate guidance
- ✅ Port conflict detection and resolution
- ✅ State detection and smart defaults
- ✅ Comprehensive error handling

### Nice to Have
- ✅ Automatic SSL setup with certbot
- ✅ Health check validation
- ✅ Monitoring setup guidance
- ✅ Backup/restore scripts

## Next Steps

1. **Review this architecture** with stakeholders
2. **Validate technical approach** with team
3. **Create detailed implementation tasks** for each phase
4. **Begin Phase 1 implementation** in code mode
5. **Test each scenario** thoroughly
6. **Update documentation** as implementation progresses

## Related Files

- `setup.sh` - Main setup script (to be refactored)
- `docker-compose.yml` - Container orchestration (to be regenerated)
- `config/nginx/barcode-central.conf` - Barcode app nginx config (new)
- `config/nginx/headscale.conf` - Headscale nginx config (new)
- `scripts/configure-firewall.sh` - Firewall automation (to be updated)
- `scripts/generate-headscale-api-key.sh` - API key generation (to be automated)
