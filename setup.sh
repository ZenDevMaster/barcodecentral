#!/bin/bash
# Barcode Central - Interactive Setup Script
# This script configures your deployment with an easy-to-use wizard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
DEPLOYMENT_TYPE=""
DOMAIN=""
ACME_EMAIL=""
HEADSCALE_DOMAIN=""
LOGIN_USER=""
LOGIN_PASSWORD=""
SECRET_KEY=""
HTTP_PORT="5000"
HTTPS_PORT="443"
HEADSCALE_PORT="8080"
USE_TRAEFIK=false
USE_HEADSCALE=false

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
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

generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
    openssl rand -hex 32 2>/dev/null || \
    head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-64
}

generate_password() {
    python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(20)))" 2>/dev/null || \
    openssl rand -base64 20 2>/dev/null || \
    head -c 20 /dev/urandom | base64 | tr -d '/+=' | cut -c1-20
}

# Main setup wizard
clear
print_header "Welcome to Barcode Central Setup!"
echo "This wizard will configure your deployment."
echo ""
echo "Press Enter to continue..."
read

# Step 1: Deployment Type
clear
print_header "[1/8] Deployment Type"
echo "Choose your deployment scenario:"
echo ""
echo "1) Basic       - HTTP only, local printers, simple setup"
echo "2) Production  - HTTPS with Traefik, automatic SSL certificates"
echo "3) Distributed - Full stack with Traefik + Headscale mesh network"
echo ""
read -p "Enter choice [1-3]: " deploy_choice

case $deploy_choice in
    1)
        DEPLOYMENT_TYPE="basic"
        print_info "Selected: Basic deployment"
        ;;
    2)
        DEPLOYMENT_TYPE="production"
        USE_TRAEFIK=true
        print_info "Selected: Production deployment with Traefik"
        ;;
    3)
        DEPLOYMENT_TYPE="distributed"
        USE_TRAEFIK=true
        USE_HEADSCALE=true
        print_info "Selected: Distributed deployment with Traefik + Headscale"
        ;;
    *)
        print_error "Invalid choice. Defaulting to Basic."
        DEPLOYMENT_TYPE="basic"
        ;;
esac

echo ""
sleep 1

# Step 2: Domain Configuration (if using Traefik)
if [ "$USE_TRAEFIK" = true ]; then
    clear
    print_header "[2/8] Domain Configuration"
    echo "Traefik requires a domain name for automatic HTTPS."
    echo ""
    read -p "Enter your domain (e.g., print.example.com): " DOMAIN
    
    while [ -z "$DOMAIN" ]; do
        print_error "Domain cannot be empty"
        read -p "Enter your domain: " DOMAIN
    done
    
    echo ""
    read -p "Enter email for Let's Encrypt notifications: " ACME_EMAIL
    
    while [ -z "$ACME_EMAIL" ]; do
        print_error "Email cannot be empty"
        read -p "Enter email: " ACME_EMAIL
    done
    
    print_success "Domain configured: $DOMAIN"
    echo ""
    sleep 1
else
    print_info "[2/8] Skipping domain configuration (not using Traefik)"
    sleep 1
fi

# Step 3: Headscale Configuration
if [ "$USE_HEADSCALE" = true ]; then
    clear
    print_header "[3/8] Headscale Configuration"
    echo "Headscale coordinates the mesh network for distributed printers."
    echo ""
    read -p "Enter Headscale subdomain (e.g., headscale.example.com): " HEADSCALE_DOMAIN
    
    if [ -z "$HEADSCALE_DOMAIN" ]; then
        HEADSCALE_DOMAIN="headscale.${DOMAIN}"
        print_info "Using default: $HEADSCALE_DOMAIN"
    fi
    
    print_success "Headscale configured: $HEADSCALE_DOMAIN"
    echo ""
    sleep 1
else
    print_info "[3/8] Skipping Headscale configuration"
    sleep 1
fi

# Step 4: Application Credentials
clear
print_header "[4/8] Application Credentials"
echo "Configure admin access for Barcode Central."
echo ""
read -p "Admin username [admin]: " LOGIN_USER
LOGIN_USER=${LOGIN_USER:-admin}

echo ""
echo "Generate secure password automatically? (recommended)"
read -p "Auto-generate password? [Y/n]: " auto_pass

if [[ "$auto_pass" =~ ^[Nn]$ ]]; then
    read -sp "Enter admin password: " LOGIN_PASSWORD
    echo ""
    read -sp "Confirm password: " LOGIN_PASSWORD_CONFIRM
    echo ""
    
    while [ "$LOGIN_PASSWORD" != "$LOGIN_PASSWORD_CONFIRM" ] || [ -z "$LOGIN_PASSWORD" ]; do
        print_error "Passwords don't match or are empty"
        read -sp "Enter admin password: " LOGIN_PASSWORD
        echo ""
        read -sp "Confirm password: " LOGIN_PASSWORD_CONFIRM
        echo ""
    done
else
    LOGIN_PASSWORD=$(generate_password)
    print_success "Generated secure password"
fi

echo ""
print_info "Generating secret key..."
SECRET_KEY=$(generate_secret)
print_success "Secret key generated"

echo ""
sleep 1

# Step 5: Network Configuration
clear
print_header "[5/8] Network Configuration"
echo "Configure network ports for your deployment."
echo ""

if [ "$USE_TRAEFIK" = false ]; then
    read -p "HTTP port [5000]: " HTTP_PORT
    HTTP_PORT=${HTTP_PORT:-5000}
fi

if [ "$USE_HEADSCALE" = true ]; then
    read -p "Headscale port [8080]: " HEADSCALE_PORT
    HEADSCALE_PORT=${HEADSCALE_PORT:-8080}
fi

print_success "Network configuration complete"
echo ""
sleep 1

# Step 6: Review Configuration
clear
print_header "[6/8] Review Configuration"
echo "Please review your configuration:"
echo ""
echo "Deployment Type:    $DEPLOYMENT_TYPE"
echo "Admin Username:     $LOGIN_USER"
echo "Admin Password:     ${LOGIN_PASSWORD:0:4}****${LOGIN_PASSWORD: -4}"

if [ "$USE_TRAEFIK" = true ]; then
    echo "Domain:             $DOMAIN"
    echo "SSL Email:          $ACME_EMAIL"
    echo "HTTPS Port:         $HTTPS_PORT"
fi

if [ "$USE_HEADSCALE" = true ]; then
    echo "Headscale Domain:   $HEADSCALE_DOMAIN"
    echo "Headscale Port:     $HEADSCALE_PORT"
fi

if [ "$USE_TRAEFIK" = false ]; then
    echo "HTTP Port:          $HTTP_PORT"
fi

echo ""
read -p "Is this configuration correct? [Y/n]: " confirm

if [[ "$confirm" =~ ^[Nn]$ ]]; then
    print_error "Setup cancelled. Please run ./setup.sh again."
    exit 1
fi

# Step 7: Generate Files
clear
print_header "[7/8] Generating Configuration Files"

# Create .env file
print_info "Creating .env file..."
cat > .env << EOF
# Barcode Central Configuration
# Generated by setup.sh on $(date)

# ============================================================================
# Application Settings
# ============================================================================
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO

# Security
SECRET_KEY=$SECRET_KEY
LOGIN_USER=$LOGIN_USER
LOGIN_PASSWORD=$LOGIN_PASSWORD

# Session
SESSION_COOKIE_SECURE=$([ "$USE_TRAEFIK" = true ] && echo "true" || echo "false")
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

EOF

# Add Traefik configuration if enabled
if [ "$USE_TRAEFIK" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Traefik Configuration
# ============================================================================
DOMAIN=$DOMAIN
ACME_EMAIL=$ACME_EMAIL

EOF
fi

# Add Headscale configuration if enabled
if [ "$USE_HEADSCALE" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Headscale Configuration
# ============================================================================
HEADSCALE_DOMAIN=$HEADSCALE_DOMAIN
HEADSCALE_SERVER_URL=http://$HEADSCALE_DOMAIN:$HEADSCALE_PORT
# TAILSCALE_AUTHKEY will be generated after first deployment

EOF
fi

# Add Docker Compose profiles
cat >> .env << EOF
# ============================================================================
# Docker Compose Profiles
# ============================================================================
COMPOSE_PROFILES=$([ "$USE_TRAEFIK" = true ] && echo -n "traefik" || echo -n "")$([ "$USE_HEADSCALE" = true ] && echo ",headscale" || echo "")

EOF

chmod 600 .env
print_success "Created .env file"

# Generate docker-compose.yml
print_info "Generating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
# Barcode Central - Docker Compose Configuration
# Generated by setup.sh

version: '3.8'

services:
  # Main Application (Always Enabled)
  app:
    build:
      context: .
      dockerfile: Dockerfile
    
    container_name: barcode-central
    restart: unless-stopped
    
    ports:
      - "${HTTP_PORT:-5000}:5000"
    
    env_file:
      - .env
    
    volumes:
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    networks:
      - barcode-network

  # Traefik Reverse Proxy (Optional)
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    
    profiles:
      - traefik
    
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--log.level=INFO"
      - "--accesslog=true"
    
    ports:
      - "80:80"
      - "443:443"
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
      - ./traefik-logs:/var/log/traefik
    
    networks:
      - barcode-network
    
    labels:
      - "traefik.enable=true"

  # Update app service with Traefik labels when Traefik is enabled
  app-traefik:
    extends:
      service: app
    
    profiles:
      - traefik
    
    ports: []  # Remove direct port exposure
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.barcode.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.barcode.entrypoints=websecure"
      - "traefik.http.routers.barcode.tls=true"
      - "traefik.http.routers.barcode.tls.certresolver=letsencrypt"
      - "traefik.http.services.barcode.loadbalancer.server.port=5000"
      - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
      - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
      - "traefik.http.middlewares.security-headers.headers.frameDeny=true"
      - "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true"
      - "traefik.http.routers.barcode.middlewares=security-headers"

  # Headscale Coordination Server (Optional)
  headscale:
    image: headscale/headscale:0.22
    container_name: headscale
    restart: unless-stopped
    
    profiles:
      - headscale
    
    command: headscale serve
    
    ports:
      - "${HEADSCALE_PORT:-8080}:8080"
      - "41641:41641/udp"
    
    volumes:
      - ./headscale/config:/etc/headscale
      - ./headscale/data:/var/lib/headscale
    
    networks:
      - barcode-network
    
    healthcheck:
      test: ["CMD", "headscale", "health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Tailscale Client (Optional - for mesh network)
  tailscale:
    image: tailscale/tailscale:latest
    container_name: barcode-central-tailscale
    restart: unless-stopped
    
    profiles:
      - headscale
    
    hostname: barcode-central-server
    
    environment:
      - TS_AUTHKEY=${TAILSCALE_AUTHKEY}
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_USERSPACE=true
      - TS_ACCEPT_DNS=true
      - TS_EXTRA_ARGS=--login-server=http://headscale:8080
    
    volumes:
      - ./tailscale/state:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
    
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    
    networks:
      - barcode-network
    
    depends_on:
      - headscale

networks:
  barcode-network:
    name: barcode-network
    driver: bridge

EOF

print_success "Created docker-compose.yml"

# Create required directories
print_info "Creating required directories..."
mkdir -p logs previews
touch history.json printers.json

if [ "$USE_TRAEFIK" = true ]; then
    mkdir -p letsencrypt traefik-logs
fi

if [ "$USE_HEADSCALE" = true ]; then
    mkdir -p headscale/config headscale/data tailscale/state
    
    # Create Headscale configuration
    if [ ! -f headscale/config/config.yaml ]; then
        print_info "Creating Headscale configuration..."
        cat > headscale/config/config.yaml << HEADSCALE_EOF
server_url: http://$HEADSCALE_DOMAIN:$HEADSCALE_PORT
listen_addr: 0.0.0.0:8080
metrics_listen_addr: 0.0.0.0:9090

private_key_path: /var/lib/headscale/private.key
noise:
  private_key_path: /var/lib/headscale/noise_private.key

ip_prefixes:
  - 100.64.0.0/10

db_type: sqlite3
db_path: /var/lib/headscale/db.sqlite

dns_config:
  override_local_dns: true
  nameservers:
    - 1.1.1.1
    - 8.8.8.8
  magic_dns: true
  base_domain: headscale.local

acl_policy_path: /etc/headscale/acl.json

derp:
  server:
    enabled: false
  urls:
    - https://controlplane.tailscale.com/derpmap/default

log:
  level: info
  format: text
HEADSCALE_EOF
    fi
    
    # Create ACL policy
    if [ ! -f headscale/config/acl.json ]; then
        cat > headscale/config/acl.json << ACL_EOF
{
  "acls": [
    {
      "action": "accept",
      "src": ["barcode-central-server"],
      "dst": ["*:9100", "*:631"]
    },
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["barcode-central-server:5000"]
    }
  ],
  "groups": {
    "group:printers": []
  },
  "hosts": {
    "barcode-central-server": "100.64.0.1"
  }
}
ACL_EOF
    fi
fi

print_success "Created all required directories"

# Set permissions
chmod 755 logs previews
chmod 644 history.json printers.json 2>/dev/null || true

print_success "Set file permissions"

# Step 8: Next Steps
clear
print_header "[8/8] Setup Complete!"
echo ""
print_success "Configuration files generated successfully!"
echo ""
echo "Your credentials:"
echo "  Username: $LOGIN_USER"
echo "  Password: $LOGIN_PASSWORD"
echo ""
print_warning "IMPORTANT: Save these credentials securely!"
echo ""
echo "Next steps:"
echo ""

if [ "$USE_TRAEFIK" = true ]; then
    echo "1. Configure DNS:"
    echo "   Create A record: $DOMAIN → $(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
    if [ "$USE_HEADSCALE" = true ]; then
        echo "   Create A record: $HEADSCALE_DOMAIN → $(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
    fi
    echo ""
fi

echo "2. Configure firewall:"
echo "   Run: ./scripts/configure-firewall.sh"
echo "   Or manually open ports:"
if [ "$USE_TRAEFIK" = true ]; then
    echo "   - 80/tcp (HTTP)"
    echo "   - 443/tcp (HTTPS)"
else
    echo "   - $HTTP_PORT/tcp (HTTP)"
fi
if [ "$USE_HEADSCALE" = true ]; then
    echo "   - $HEADSCALE_PORT/tcp (Headscale API)"
    echo "   - 41641/udp (WireGuard)"
fi
echo ""

echo "3. Start the application:"
echo "   docker compose up -d"
echo ""

echo "4. Check status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""

if [ "$USE_HEADSCALE" = true ]; then
    echo "5. Generate Tailscale auth key (after deployment):"
    echo "   ./scripts/generate-authkey.sh"
    echo ""
    echo "6. Setup Raspberry Pi print servers:"
    echo "   See: raspberry-pi-setup.sh"
    echo ""
fi

if [ "$USE_TRAEFIK" = true ]; then
    echo "Access your application at: https://$DOMAIN"
else
    echo "Access your application at: http://localhost:$HTTP_PORT"
fi

echo ""
print_info "For detailed documentation, see:"
echo "  - QUICKSTART.md"
echo "  - PRODUCTION_DEPLOYMENT_GUIDE.md"
echo ""

print_success "Setup complete! Happy printing! 🖨️"