#!/bin/bash
# Barcode Central - Interactive Setup Script
# Configures deployment with logical real-world scenarios

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
USE_SSL=false
USE_HEADSCALE=false
EXTERNAL_ACCESS=false

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

# Step 1: LAN-only or External Access
clear
print_header "[1/7] Network Access"
echo "How will you access Barcode Central?"
echo ""
echo "1) LAN only - Access from local network only"
echo "   • Simple HTTP setup (port 5000)"
echo "   • Printers on same network or via direct IP"
echo "   • You can still add your own reverse proxy (nginx, etc.)"
echo "   • No SSL configuration needed"
echo ""
echo "2) External access - Access from internet"
echo "   • Requires domain name (FQDN)"
echo "   • Optional Traefik reverse proxy with automatic SSL"
echo "   • Can be combined with Headscale for remote printers"
echo ""
read -p "Enter choice [1-2]: " access_choice

case $access_choice in
    1)
        DEPLOYMENT_TYPE="lan-only"
        EXTERNAL_ACCESS=false
        print_info "Selected: LAN-only deployment"
        ;;
    2)
        EXTERNAL_ACCESS=true
        print_info "Selected: External access deployment"
        ;;
    *)
        print_error "Invalid choice. Defaulting to LAN-only."
        DEPLOYMENT_TYPE="lan-only"
        EXTERNAL_ACCESS=false
        ;;
esac

echo ""
sleep 1

# Step 2: Domain Configuration (if external access)
if [ "$EXTERNAL_ACCESS" = true ]; then
    clear
    print_header "[2/7] Domain Configuration"
    echo "Enter your fully qualified domain name (FQDN)."
    echo "Example: print.example.com"
    echo ""
    read -p "Domain (FQDN): " DOMAIN
    
    while [ -z "$DOMAIN" ]; do
        print_error "Domain cannot be empty for external access"
        read -p "Domain (FQDN): " DOMAIN
    done
    
    print_success "Domain configured: $DOMAIN"
    echo ""
    sleep 1
    
    # Step 3: Traefik Configuration
    clear
    print_header "[3/7] Reverse Proxy (Traefik)"
    echo "Do you want to use Traefik as a reverse proxy?"
    echo ""
    echo "Traefik provides:"
    echo "  • Automatic routing to your application"
    echo "  • Optional automatic SSL/HTTPS with Let's Encrypt"
    echo "  • Security headers"
    echo "  • Easy configuration"
    echo ""
    echo "If you choose 'no', you can use your own reverse proxy (nginx, etc.)"
    echo ""
    read -p "Use Traefik? [Y/n]: " use_traefik_choice
    
    if [[ ! "$use_traefik_choice" =~ ^[Nn]$ ]]; then
        USE_TRAEFIK=true
        DEPLOYMENT_TYPE="external-traefik"
        print_success "Traefik enabled"
        
        # Step 4: SSL Configuration
        echo ""
        echo "Do you want automatic SSL/HTTPS with Let's Encrypt?"
        echo ""
        echo "Requirements:"
        echo "  • Domain must point to this server's public IP"
        echo "  • Ports 80 and 443 must be accessible from internet"
        echo "  • Valid email address for Let's Encrypt notifications"
        echo ""
        read -p "Enable automatic SSL? [Y/n]: " use_ssl_choice
        
        if [[ ! "$use_ssl_choice" =~ ^[Nn]$ ]]; then
            USE_SSL=true
            
            echo ""
            read -p "Email for Let's Encrypt notifications: " ACME_EMAIL
            
            while [ -z "$ACME_EMAIL" ]; then
                print_error "Email cannot be empty"
                read -p "Email: " ACME_EMAIL
            done
            
            print_success "SSL enabled with Let's Encrypt"
        else
            print_info "SSL disabled - Traefik will use HTTP only"
        fi
    else
        DEPLOYMENT_TYPE="external-manual"
        print_info "Traefik disabled - you can configure your own reverse proxy"
    fi
else
    print_info "[2/7] Skipping domain configuration (LAN-only)"
    print_info "[3/7] Skipping Traefik configuration (LAN-only)"
fi

echo ""
sleep 1

# Step 5: Headscale Mesh VPN
clear
print_header "[4/7] Headscale Mesh VPN (Optional)"
echo "Do you want to enable Headscale for distributed printing?"
echo ""
echo "Headscale is a self-hosted mesh VPN that allows you to:"
echo "  • Connect printers on remote networks securely"
echo "  • Access printers at different physical locations"
echo "  • Create a secure mesh network for distributed printing"
echo "  • Use Raspberry Pis as print servers at remote sites"
echo ""
echo "Choose 'yes' if you have printers at multiple locations."
echo "Choose 'no' if all printers are on the same network as this server."
echo ""
read -p "Enable Headscale mesh VPN? [y/N]: " use_headscale_choice

if [[ "$use_headscale_choice" =~ ^[Yy]$ ]]; then
    USE_HEADSCALE=true
    
    echo ""
    if [ "$EXTERNAL_ACCESS" = true ]; then
        echo "Headscale needs a domain name."
        read -p "Use same domain ($DOMAIN) for Headscale? [Y/n]: " same_domain
        
        if [[ "$same_domain" =~ ^[Nn]$ ]]; then
            read -p "Enter Headscale domain (e.g., headscale.example.com): " HEADSCALE_DOMAIN
        else
            HEADSCALE_DOMAIN="$DOMAIN"
        fi
    else
        echo "Headscale needs to be accessible from remote locations."
        read -p "Enter Headscale domain or IP (e.g., headscale.example.com or 1.2.3.4): " HEADSCALE_DOMAIN
        
        while [ -z "$HEADSCALE_DOMAIN" ]; then
            print_error "Headscale domain/IP cannot be empty"
            read -p "Enter Headscale domain or IP: " HEADSCALE_DOMAIN
        done
    fi
    
    echo ""
    read -p "Headscale port [8080]: " HEADSCALE_PORT
    HEADSCALE_PORT=${HEADSCALE_PORT:-8080}
    
    print_success "Headscale enabled: $HEADSCALE_DOMAIN:$HEADSCALE_PORT"
else
    print_info "Headscale disabled - all printers must be on local network"
fi

echo ""
sleep 1

# Step 6: Application Credentials
clear
print_header "[5/7] Application Credentials"
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

# Step 7: Port Configuration
clear
print_header "[6/7] Port Configuration"

if [ "$USE_TRAEFIK" = false ]; then
    echo "Configure the HTTP port for the application."
    echo ""
    read -p "HTTP port [5000]: " HTTP_PORT
    HTTP_PORT=${HTTP_PORT:-5000}
    print_success "Application will be accessible on port $HTTP_PORT"
else
    print_info "Traefik will handle ports 80 (HTTP) and 443 (HTTPS)"
    HTTP_PORT="5000"  # Internal port
fi

echo ""
sleep 1

# Step 8: Review Configuration
clear
print_header "[7/7] Review Configuration"
echo "Please review your configuration:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deployment Type:    $DEPLOYMENT_TYPE"
echo "Admin Username:     $LOGIN_USER"
echo "Admin Password:     ${LOGIN_PASSWORD:0:4}****${LOGIN_PASSWORD: -4}"

if [ "$EXTERNAL_ACCESS" = true ]; then
    echo ""
    echo "External Access:"
    echo "  Domain:           $DOMAIN"
    if [ "$USE_TRAEFIK" = true ]; then
        echo "  Traefik:          Enabled"
        if [ "$USE_SSL" = true ]; then
            echo "  SSL:              Enabled (Let's Encrypt)"
            echo "  SSL Email:        $ACME_EMAIL"
            echo "  Access URL:       https://$DOMAIN"
        else
            echo "  SSL:              Disabled"
            echo "  Access URL:       http://$DOMAIN"
        fi
    else
        echo "  Traefik:          Disabled (manual reverse proxy)"
        echo "  Port:             $HTTP_PORT"
    fi
else
    echo ""
    echo "LAN Access:"
    echo "  Port:             $HTTP_PORT"
    echo "  Access URL:       http://localhost:$HTTP_PORT"
fi

if [ "$USE_HEADSCALE" = true ]; then
    echo ""
    echo "Headscale Mesh VPN:"
    echo "  Domain:           $HEADSCALE_DOMAIN"
    echo "  Port:             $HEADSCALE_PORT"
    echo "  WireGuard Port:   41641/udp"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Is this configuration correct? [Y/n]: " confirm

if [[ "$confirm" =~ ^[Nn]$ ]]; then
    print_error "Setup cancelled. Please run ./setup.sh again."
    exit 1
fi

# Generate Files
clear
print_header "Generating Configuration Files"

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
SESSION_COOKIE_SECURE=$([ "$USE_SSL" = true ] && echo "true" || echo "false")
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Network
HTTP_PORT=$HTTP_PORT

EOF

# Add Traefik configuration if enabled
if [ "$USE_TRAEFIK" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Traefik Configuration
# ============================================================================
DOMAIN=$DOMAIN
$([ "$USE_SSL" = true ] && echo "ACME_EMAIL=$ACME_EMAIL" || echo "# SSL disabled")

EOF
fi

# Add Headscale configuration if enabled
if [ "$USE_HEADSCALE" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Headscale Configuration
# ============================================================================
HEADSCALE_DOMAIN=$HEADSCALE_DOMAIN
HEADSCALE_PORT=$HEADSCALE_PORT
HEADSCALE_SERVER_URL=http://$HEADSCALE_DOMAIN:$HEADSCALE_PORT
# TAILSCALE_AUTHKEY will be generated after first deployment

EOF
fi

# Add Docker Compose profiles
PROFILES=""
[ "$USE_TRAEFIK" = true ] && PROFILES="traefik"
[ "$USE_HEADSCALE" = true ] && PROFILES="${PROFILES:+$PROFILES,}headscale"

cat >> .env << EOF
# ============================================================================
# Docker Compose Profiles
# ============================================================================
COMPOSE_PROFILES=$PROFILES

EOF

chmod 600 .env
print_success "Created .env file"

# Generate docker-compose.yml
print_info "Generating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSE_EOF'
# Barcode Central - Docker Compose Configuration
# Generated by setup.sh

version: '3.8'

services:
  # Main Application
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
    
    labels:
      - "com.barcodecentral.service=app"

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
      - headscale-network
    
    depends_on:
      - headscale

networks:
  barcode-network:
    name: barcode-network
    driver: bridge
  
  headscale-network:
    name: headscale-network
    driver: bridge

COMPOSE_EOF

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

# Final instructions
clear
print_header "Setup Complete!"
echo ""
print_success "Configuration files generated successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Your credentials:"
echo "  Username: $LOGIN_USER"
echo "  Password: $LOGIN_PASSWORD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_warning "IMPORTANT: Save these credentials securely!"
echo ""
echo "Next steps:"
echo ""

# DNS configuration
if [ "$EXTERNAL_ACCESS" = true ]; then
    echo "1. Configure DNS:"
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
    echo "   Create A record: $DOMAIN → $SERVER_IP"
    if [ "$USE_HEADSCALE" = true ] && [ "$HEADSCALE_DOMAIN" != "$DOMAIN" ]; then
        echo "   Create A record: $HEADSCALE_DOMAIN → $SERVER_IP"
    fi
    echo ""
fi

# Firewall configuration
echo "2. Configure firewall:"
echo "   Run: ./scripts/configure-firewall.sh"
echo "   Or manually open ports:"
if [ "$USE_TRAEFIK" = true ]; then
    echo "   - 80/tcp (HTTP)"
    if [ "$USE_SSL" = true ]; then
        echo "   - 443/tcp (HTTPS)"
    fi
else
    echo "   - $HTTP_PORT/tcp (HTTP)"
fi
if [ "$USE_HEADSCALE" = true ]; then
    echo "   - $HEADSCALE_PORT/tcp (Headscale API)"
    echo "   - 41641/udp (WireGuard)"
fi
echo ""

# Start application
echo "3. Start the application:"
echo "   docker compose up -d"
echo ""

echo "4. Check status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""

# Headscale-specific instructions
if [ "$USE_HEADSCALE" = true ]; then
    echo "5. Setup Headscale mesh network:"
    echo "   a) Generate auth key:"
    echo "      ./scripts/generate-authkey.sh"
    echo ""
    echo "   b) Setup Raspberry Pi print servers at each location:"
    echo "      On each Raspberry Pi, run:"
    echo "      curl -sSL https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh | bash"
    echo ""
    echo "   c) Enable subnet routes:"
    echo "      ./scripts/enable-routes.sh"
    echo ""
    echo "   d) Verify connectivity:"
    echo "      docker exec -it barcode-central ping <raspberry-pi-tailscale-ip>"
    echo "      docker exec -it barcode-central ping <printer-ip>"
    echo ""
fi

# Access URL
if [ "$USE_TRAEFIK" = true ]; then
    if [ "$USE_SSL" = true ]; then
        echo "Access your application at: https://$DOMAIN"
    else
        echo "Access your application at: http://$DOMAIN"
    fi
else
    if [ "$EXTERNAL_ACCESS" = true ]; then
        echo "Access your application at: http://$DOMAIN:$HTTP_PORT"
    else
        echo "Access your application at: http://localhost:$HTTP_PORT"
    fi
fi

echo ""
print_info "For detailed documentation, see:"
echo "  - QUICKSTART.md"
echo "  - PRODUCTION_DEPLOYMENT_GUIDE.md"
if [ "$USE_HEADSCALE" = true ]; then
    echo "  - RASPBERRY_PI_SETUP.md"
fi
echo ""

print_success "Setup complete! Happy printing! 🖨️"