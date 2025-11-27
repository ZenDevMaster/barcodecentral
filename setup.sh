#!/bin/bash
# Barcode Central - Interactive Setup Script (Refactored)
# Configures deployment with separate domain architecture for headscale

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
HEADSCALE_EXTERNAL_HTTP="8080"
HEADSCALE_UI_EXTERNAL="8081"
REVERSE_PROXY=""
USE_TRAEFIK=false
USE_NGINX=false
USE_SSL=false
USE_HEADSCALE=false
USE_HEADSCALE_UI=false
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

load_existing_config() {
    if [ -f .env ]; then
        print_info "Detected existing .env configuration"
        
        # Parse existing values from .env file
        EXISTING_SECRET_KEY=$(grep "^SECRET_KEY=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_LOGIN_USER=$(grep "^LOGIN_USER=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_LOGIN_PASSWORD=$(grep "^LOGIN_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_HTTP_PORT=$(grep "^HTTP_PORT=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_DOMAIN=$(grep "^DOMAIN=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_ACME_EMAIL=$(grep "^ACME_EMAIL=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_HEADSCALE_DOMAIN=$(grep "^HEADSCALE_DOMAIN=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_HEADSCALE_EXTERNAL_HTTP=$(grep "^HEADSCALE_EXTERNAL_HTTP=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_HEADSCALE_UI_EXTERNAL=$(grep "^HEADSCALE_UI_EXTERNAL=" .env 2>/dev/null | cut -d'=' -f2)
        EXISTING_REVERSE_PROXY=$(grep "^REVERSE_PROXY=" .env 2>/dev/null | cut -d'=' -f2)
        
        return 0
    fi
    return 1
}

# Main setup wizard
clear
print_header "Welcome to Barcode Central Setup!"
echo "This wizard will configure your deployment."
echo ""

# Load existing configuration if available
load_existing_config && echo ""

echo "Press Enter to continue..."
read

# Step 1: LAN-only or External Access
clear
print_header "[1/8] Network Access"
echo "How will you access Barcode Central?"
echo ""
echo "1) LAN only - Access from local network only"
echo "   • Simple HTTP setup"
echo "   • Printers on same network or via direct IP"
echo "   • You can still add your own reverse proxy later"
echo "   • No SSL configuration needed"
echo ""
echo "2) External access - Access from internet"
echo "   • Requires domain name (FQDN)"
echo "   • Optional reverse proxy (Traefik or Nginx) with SSL"
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
    print_header "[2/8] Barcode Central Domain Configuration"
    echo "Enter the domain name for Barcode Central."
    echo "Example: print.example.com"
    echo ""
    
    # Show existing domain if available
    if [ -n "$EXISTING_DOMAIN" ]; then
        print_info "Current domain: $EXISTING_DOMAIN"
        read -p "Domain (FQDN) [$EXISTING_DOMAIN]: " DOMAIN
        DOMAIN=${DOMAIN:-$EXISTING_DOMAIN}
    else
        read -p "Domain (FQDN): " DOMAIN
    fi
    
    while [ -z "$DOMAIN" ]; do
        print_error "Domain cannot be empty for external access"
        read -p "Domain (FQDN): " DOMAIN
    done
    
    print_success "Barcode Central domain configured: $DOMAIN"
    echo ""
    sleep 1
    
    # Step 3: Reverse Proxy Selection
    clear
    print_header "[3/8] Reverse Proxy Configuration"
    echo "Choose your reverse proxy setup:"
    echo ""
    echo "1) Traefik (Docker-native, automatic SSL with Let's Encrypt)"
    echo "   • Automatic HTTPS certificates"
    echo "   • Container-based routing via Docker networks"
    echo "   • No port exposure except 80/443"
    echo "   • Recommended for Docker deployments where there are no other systems sharing port 80/443"
    echo ""
    echo "2) Nginx (Host-based, manual SSL with certbot)"
    echo "   • Will create a sample nginx configuration for further setup with your existing Nginx installation"
    echo "   • Traditional nginx on host system"
    echo "   • Manual SSL setup with certbot"
    echo "   • Services exposed to localhost for nginx access"
    echo "   • More control, manual configuration"
    echo ""
    echo "3) None (Manual configuration)"
    echo "   • Configure your own reverse proxy"
    echo "   • Direct port exposure"
    echo ""
    
    # Show existing choice if available
    if [ -n "$EXISTING_REVERSE_PROXY" ]; then
        print_info "Current choice: $EXISTING_REVERSE_PROXY"
    fi
    
    read -p "Enter choice [1-3]: " proxy_choice
    
    case $proxy_choice in
        1)
            USE_TRAEFIK=true
            REVERSE_PROXY="traefik"
            DEPLOYMENT_TYPE="external-traefik"
            print_success "Traefik selected"
            
            # SSL Configuration for Traefik
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
                # Show existing email if available
                if [ -n "$EXISTING_ACME_EMAIL" ]; then
                    print_info "Current email: $EXISTING_ACME_EMAIL"
                    read -p "Email for Let's Encrypt notifications [$EXISTING_ACME_EMAIL]: " ACME_EMAIL
                    ACME_EMAIL=${ACME_EMAIL:-$EXISTING_ACME_EMAIL}
                else
                    read -p "Email for Let's Encrypt notifications: " ACME_EMAIL
                fi
                
                while [ -z "$ACME_EMAIL" ]; do
                    print_error "Email cannot be empty"
                    read -p "Email: " ACME_EMAIL
                done
                
                print_success "SSL enabled with Let's Encrypt"
            else
                print_info "SSL disabled - Traefik will use HTTP only"
            fi
            ;;
        2)
            USE_NGINX=true
            REVERSE_PROXY="nginx"
            DEPLOYMENT_TYPE="external-nginx"
            print_success "Nginx selected"
            print_info "Nginx configuration files will be generated"
            print_info "SSL setup with certbot will be explained in post-setup instructions"
            ;;
        3)
            REVERSE_PROXY="none"
            DEPLOYMENT_TYPE="external-manual"
            print_info "No reverse proxy - you will configure manually"
            ;;
        *)
            print_warning "Invalid choice, defaulting to Traefik"
            USE_TRAEFIK=true
            REVERSE_PROXY="traefik"
            DEPLOYMENT_TYPE="external-traefik"
            ;;
    esac
else
    print_info "[2/8] Skipping domain configuration (LAN-only)"
    print_info "[3/8] Skipping reverse proxy configuration (LAN-only)"
fi

echo ""
sleep 1

# Step 4: Headscale Mesh VPN
clear
print_header "[4/8] Headscale Mesh VPN (Optional)"
echo "Do you want to enable Headscale for distributed printing?"
echo ""
echo "Headscale is a self-hosted mesh VPN that allows you to:"
echo "  • Connect printers on remote networks securely"
echo "  • Access printers at different physical locations"
echo "  • Create a secure mesh network for distributed printing"
echo "  • Use a Raspberry Pi or another system that supports Tailscale running on the printer's LAN to give access to your Barcode Central server"
echo ""
echo "Choose 'yes' if you have printers at multiple locations."
echo "Choose 'no' if all printers are on the same network as this server."
echo ""
read -p "Enable Headscale mesh VPN? [y/N]: " use_headscale_choice

if [[ "$use_headscale_choice" =~ ^[Yy]$ ]]; then
    USE_HEADSCALE=true
    
    echo ""
    echo "Headscale needs its own domain name (separate from Barcode Central)."
    echo "Example: headscale.example.com"
    echo ""
    
    # Show existing Headscale domain if available
    if [ -n "$EXISTING_HEADSCALE_DOMAIN" ]; then
        print_info "Current Headscale domain: $EXISTING_HEADSCALE_DOMAIN"
        read -p "Headscale domain [$EXISTING_HEADSCALE_DOMAIN]: " HEADSCALE_DOMAIN
        HEADSCALE_DOMAIN=${HEADSCALE_DOMAIN:-$EXISTING_HEADSCALE_DOMAIN}
    else
        if [ "$EXTERNAL_ACCESS" = true ]; then
            read -p "Headscale domain (e.g., headscale.example.com): " HEADSCALE_DOMAIN
        else
            read -p "Headscale domain or IP (e.g., headscale.example.com or 192.168.1.10): " HEADSCALE_DOMAIN
        fi
    fi
    
    while [ -z "$HEADSCALE_DOMAIN" ]; do
        print_error "Headscale domain/IP cannot be empty"
        read -p "Headscale domain or IP: " HEADSCALE_DOMAIN
    done
    
    print_success "Headscale domain configured: $HEADSCALE_DOMAIN"
    
    # Headscale UI Option
    echo ""
    echo "Do you want to enable Headscale Web Admin UI?"
    echo "  • Manage users and machines via web interface"
    echo "  • Configure routes and ACLs visually"
    echo "  • Monitor network status in real-time"
    if [ "$USE_TRAEFIK" = true ]; then
        echo "  • Access at: https://$HEADSCALE_DOMAIN/web/"
    elif [ "$USE_NGINX" = true ]; then
        echo "  • Access at: http://$HEADSCALE_DOMAIN/web/"
    else
        echo "  • Access at: http://$HEADSCALE_DOMAIN:8081/web/"
    fi
    echo ""
    read -p "Enable Headscale Web Admin UI? [Y/n]: " use_headscale_ui_choice
    
    if [[ ! "$use_headscale_ui_choice" =~ ^[Nn]$ ]]; then
        USE_HEADSCALE_UI=true
        print_success "Headscale UI enabled"
    else
        USE_HEADSCALE_UI=false
        print_info "Headscale UI disabled"
    fi
    
    print_success "Headscale configured: $HEADSCALE_DOMAIN"
else
    USE_HEADSCALE=false
    USE_HEADSCALE_UI=false
    print_info "Headscale disabled - all printers must be on local network"
fi

echo ""
sleep 1

# Step 5: Port Configuration
clear
print_header "[5/8] Port Configuration"
echo "Configure ports for services."
echo "You can use defaults or change them to avoid conflicts."
echo ""

# Barcode Central HTTP Port
if [ -n "$EXISTING_HTTP_PORT" ]; then
    read -p "Barcode Central HTTP port [$EXISTING_HTTP_PORT]: " HTTP_PORT
    HTTP_PORT=${HTTP_PORT:-$EXISTING_HTTP_PORT}
else
    read -p "Barcode Central HTTP port [5000]: " HTTP_PORT
    HTTP_PORT=${HTTP_PORT:-5000}
fi
print_success "Barcode Central port: $HTTP_PORT"

# Headscale ports (if enabled and using nginx or no reverse proxy)
if [ "$USE_HEADSCALE" = true ]; then
    if [ "$USE_NGINX" = true ] || [ "$REVERSE_PROXY" = "none" ]; then
        echo ""
        print_info "Headscale port configuration (for nginx/manual access)"
        
        # Headscale HTTP Port
        if [ -n "$EXISTING_HEADSCALE_EXTERNAL_HTTP" ]; then
            read -p "Headscale HTTP port [$EXISTING_HEADSCALE_EXTERNAL_HTTP]: " HEADSCALE_EXTERNAL_HTTP
            HEADSCALE_EXTERNAL_HTTP=${HEADSCALE_EXTERNAL_HTTP:-$EXISTING_HEADSCALE_EXTERNAL_HTTP}
        else
            read -p "Headscale HTTP port [8080]: " HEADSCALE_EXTERNAL_HTTP
            HEADSCALE_EXTERNAL_HTTP=${HEADSCALE_EXTERNAL_HTTP:-8080}
        fi
        print_success "Headscale HTTP port: $HEADSCALE_EXTERNAL_HTTP"
        
        # Headscale UI Port (if enabled)
        if [ "$USE_HEADSCALE_UI" = true ]; then
            if [ -n "$EXISTING_HEADSCALE_UI_EXTERNAL" ]; then
                read -p "Headscale UI port [$EXISTING_HEADSCALE_UI_EXTERNAL]: " HEADSCALE_UI_EXTERNAL
                HEADSCALE_UI_EXTERNAL=${HEADSCALE_UI_EXTERNAL:-$EXISTING_HEADSCALE_UI_EXTERNAL}
            else
                read -p "Headscale UI port [8081]: " HEADSCALE_UI_EXTERNAL
                HEADSCALE_UI_EXTERNAL=${HEADSCALE_UI_EXTERNAL:-8081}
            fi
            print_success "Headscale UI port: $HEADSCALE_UI_EXTERNAL"
        fi
    fi
fi

echo ""
sleep 1

# Step 6: Application Credentials
clear
print_header "[6/8] Application Credentials"
echo "Configure admin access for Barcode Central."
echo ""

# Check for existing credentials
if [ -n "$EXISTING_LOGIN_USER" ] && [ -n "$EXISTING_LOGIN_PASSWORD" ]; then
    print_info "Found existing credentials"
    echo ""
    
    # Username
    read -p "Admin username [$EXISTING_LOGIN_USER]: " LOGIN_USER
    LOGIN_USER=${LOGIN_USER:-$EXISTING_LOGIN_USER}
    
    echo ""
    # Password - offer to keep existing
    echo "Password options:"
    echo "1) Keep existing password (recommended)"
    echo "2) Generate new secure password"
    echo "3) Enter custom password"
    read -p "Choice [1-3]: " pass_choice
    
    case $pass_choice in
        1)
            LOGIN_PASSWORD="$EXISTING_LOGIN_PASSWORD"
            print_success "Keeping existing password"
            ;;
        2)
            LOGIN_PASSWORD=$(generate_password)
            print_success "Generated new secure password"
            ;;
        3)
            echo ""
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
            print_success "Custom password set"
            ;;
        *)
            LOGIN_PASSWORD="$EXISTING_LOGIN_PASSWORD"
            print_info "Keeping existing password (invalid choice)"
            ;;
    esac
else
    # No existing credentials - first time setup
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
fi

echo ""
# Secret key - always preserve if exists to maintain sessions
if [ -n "$EXISTING_SECRET_KEY" ]; then
    SECRET_KEY="$EXISTING_SECRET_KEY"
    print_success "Using existing secret key (preserves active sessions)"
else
    print_info "Generating secret key..."
    SECRET_KEY=$(generate_secret)
    print_success "Secret key generated"
fi

# Headscale UI credentials (if enabled)
if [ "$USE_HEADSCALE_UI" = true ]; then
    echo ""
    print_info "Headscale UI will use the same credentials as Barcode Central"
    HEADSCALE_UI_USER="$LOGIN_USER"
    HEADSCALE_UI_PASSWORD="$LOGIN_PASSWORD"
fi

echo ""
sleep 1

# Step 7: Review Configuration
clear
print_header "[7/8] Review Configuration"
echo "Please review your configuration:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deployment Type:    $DEPLOYMENT_TYPE"
echo "Admin Username:     $LOGIN_USER"
echo "Admin Password:     ${LOGIN_PASSWORD:0:4}****${LOGIN_PASSWORD: -4}"

if [ "$EXTERNAL_ACCESS" = true ]; then
    echo ""
    echo "Barcode Central:"
    echo "  Domain:           $DOMAIN"
    echo "  Port:             $HTTP_PORT"
    echo "  Reverse Proxy:    $REVERSE_PROXY"
    if [ "$USE_TRAEFIK" = true ]; then
        if [ "$USE_SSL" = true ]; then
            echo "  SSL:              Enabled (Let's Encrypt)"
            echo "  SSL Email:        $ACME_EMAIL"
            echo "  Access URL:       https://$DOMAIN"
        else
            echo "  SSL:              Disabled"
            echo "  Access URL:       http://$DOMAIN"
        fi
    elif [ "$USE_NGINX" = true ]; then
        echo "  SSL:              Manual setup with certbot"
        echo "  Access URL:       http://$DOMAIN (HTTPS after certbot)"
    else
        echo "  Access URL:       http://$DOMAIN:$HTTP_PORT"
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
    if [ "$USE_NGINX" = true ] || [ "$REVERSE_PROXY" = "none" ]; then
        echo "  HTTP Port:        $HEADSCALE_EXTERNAL_HTTP"
        if [ "$USE_HEADSCALE_UI" = true ]; then
            echo "  UI Port:          $HEADSCALE_UI_EXTERNAL"
        fi
    fi
    echo "  STUN Port:        3478/udp"
    if [ "$USE_HEADSCALE_UI" = true ]; then
        echo "  UI Enabled:       Yes"
        if [ "$USE_TRAEFIK" = true ]; then
            echo "  UI Access:        https://$HEADSCALE_DOMAIN/web/"
        elif [ "$USE_NGINX" = true ]; then
            echo "  UI Access:        http://$HEADSCALE_DOMAIN/web/"
        else
            echo "  UI Access:        http://$HEADSCALE_DOMAIN:$HEADSCALE_UI_EXTERNAL/web/"
        fi
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Is this configuration correct? [Y/n]: " confirm

if [[ "$confirm" =~ ^[Nn]$ ]]; then
    print_error "Setup cancelled. Please run ./setup.sh again."
    exit 1
fi

# Step 8: Generate Configuration Files
clear
print_header "[8/8] Generating Configuration Files"

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

# Add reverse proxy configuration
if [ "$EXTERNAL_ACCESS" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Reverse Proxy Configuration
# ============================================================================
REVERSE_PROXY=$REVERSE_PROXY
DOMAIN=$DOMAIN
$([ "$USE_SSL" = true ] && echo "ACME_EMAIL=$ACME_EMAIL")

EOF
fi

# Add Headscale configuration if enabled
if [ "$USE_HEADSCALE" = true ]; then
    cat >> .env << EOF
# ============================================================================
# Headscale Configuration
# ============================================================================
HEADSCALE_ENABLED=true
HEADSCALE_DOMAIN=$HEADSCALE_DOMAIN
HEADSCALE_EXTERNAL_HTTP=$HEADSCALE_EXTERNAL_HTTP
HEADSCALE_SERVER_URL=http://$HEADSCALE_DOMAIN:$HEADSCALE_EXTERNAL_HTTP

EOF

    # Add Headscale UI configuration if enabled
    if [ "$USE_HEADSCALE_UI" = true ]; then
        cat >> .env << EOF
# Headscale UI
HEADSCALE_UI_ENABLED=true
HEADSCALE_UI_EXTERNAL=$HEADSCALE_UI_EXTERNAL
HEADSCALE_UI_USER=$HEADSCALE_UI_USER
HEADSCALE_UI_PASSWORD=$HEADSCALE_UI_PASSWORD
# HEADSCALE_API_KEY=  # Will be auto-generated after first deployment

EOF
    fi
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
COMPOSE_EOF

# Add Headscale routing capabilities if enabled
if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    # Enable route manipulation for Tailscale routing
    cap_add:
      - NET_ADMIN
    
    # Use routing wrapper script
    entrypoint: ["/docker-entrypoint-wrapper.sh"]
    command: ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
COMPOSE_EOF
fi

# Add ports based on reverse proxy choice
if [ "$USE_TRAEFIK" = true ]; then
    # Traefik: no host port exposure
    cat >> docker-compose.yml << COMPOSE_EOF
    # No ports exposed - Traefik accesses via Docker network
    
COMPOSE_EOF
else
    # Nginx or no reverse proxy: expose to host
    cat >> docker-compose.yml << COMPOSE_EOF
    ports:
      - "${HTTP_PORT:-5000}:5000"
    
COMPOSE_EOF
fi

cat >> docker-compose.yml << 'COMPOSE_EOF'
    env_file:
      - .env
COMPOSE_EOF

if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    environment:
      - ADVERTISED_ROUTES=${ADVERTISED_ROUTES:-}
COMPOSE_EOF
fi
    
cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    volumes:
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
COMPOSE_EOF

if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'
      # Routing wrapper script for Tailscale
      - ./docker-entrypoint-wrapper.sh:/docker-entrypoint-wrapper.sh:ro
COMPOSE_EOF
fi

cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    networks:
      - barcode-network
COMPOSE_EOF

if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'
      - headscale-network
    
    depends_on:
      tailscale:
        condition: service_started
COMPOSE_EOF
fi

# Add Traefik labels if enabled
if [ "$USE_TRAEFIK" = true ]; then
    cat >> docker-compose.yml << COMPOSE_EOF
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.barcode.rule=Host(\`${DOMAIN}\`)"
      - "traefik.http.routers.barcode.entrypoints=websecure"
      - "traefik.http.routers.barcode.tls=true"
      - "traefik.http.routers.barcode.tls.certresolver=letsencrypt"
      - "traefik.http.services.barcode.loadbalancer.server.port=5000"
      - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
      - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
      - "traefik.http.middlewares.security-headers.headers.frameDeny=true"
      - "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true"
      - "traefik.http.routers.barcode.middlewares=security-headers"
COMPOSE_EOF
fi

# Add Traefik service if enabled
if [ "$USE_TRAEFIK" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'

  # Traefik Reverse Proxy
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    
    profiles:
      - traefik
    
COMPOSE_EOF

    if [ "$USE_SSL" = true ]; then
        cat >> docker-compose.yml << COMPOSE_EOF
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
COMPOSE_EOF
    else
        cat >> docker-compose.yml << 'COMPOSE_EOF'
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=INFO"
      - "--accesslog=true"
COMPOSE_EOF
    fi

    cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    ports:
      - "80:80"
COMPOSE_EOF

    if [ "$USE_SSL" = true ]; then
        cat >> docker-compose.yml << 'COMPOSE_EOF'
      - "443:443"
COMPOSE_EOF
    fi

    cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
      - ./traefik-logs:/var/log/traefik
    
    networks:
      - barcode-network
COMPOSE_EOF

    if [ "$USE_HEADSCALE" = true ]; then
        cat >> docker-compose.yml << 'COMPOSE_EOF'
      - headscale-network
COMPOSE_EOF
    fi
fi

# Add Headscale services if enabled
if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'

  # Headscale Coordination Server
  headscale:
    image: headscale/headscale:latest
    container_name: headscale
    restart: unless-stopped
    read_only: true
    
    command: serve
    
    tmpfs:
      - /var/run/headscale
    
COMPOSE_EOF

    # Headscale port exposure based on reverse proxy choice
    if [ "$USE_TRAEFIK" = true ]; then
        # Traefik: only STUN exposed for DERP
        cat >> docker-compose.yml << 'COMPOSE_EOF'
    ports:
      - "3478:3478/udp"
    
COMPOSE_EOF
    else
        # Nginx or none: expose HTTP and STUN
        cat >> docker-compose.yml << COMPOSE_EOF
    ports:
      - "0.0.0.0:\${HEADSCALE_EXTERNAL_HTTP:-8080}:8080"
      - "0.0.0.0:9090:9090"
      - "3478:3478/udp"
    
COMPOSE_EOF
    fi

    cat >> docker-compose.yml << 'COMPOSE_EOF'
    volumes:
      - ./config/headscale:/etc/headscale:ro
      - ./data/headscale:/var/lib/headscale
    
    networks:
      - headscale-network
COMPOSE_EOF

    if [ "$USE_TRAEFIK" = true ]; then
        cat >> docker-compose.yml << 'COMPOSE_EOF'
      - barcode-network
COMPOSE_EOF
    fi

    cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    healthcheck:
      test: ["CMD", "headscale", "health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
COMPOSE_EOF

    # Add Traefik labels for Headscale if Traefik is enabled
    if [ "$USE_TRAEFIK" = true ]; then
        cat >> docker-compose.yml << COMPOSE_EOF
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.headscale.rule=Host(\`${HEADSCALE_DOMAIN}\`)"
      - "traefik.http.routers.headscale.entrypoints=websecure"
      - "traefik.http.routers.headscale.tls=true"
      - "traefik.http.routers.headscale.tls.certresolver=letsencrypt"
      - "traefik.http.services.headscale.loadbalancer.server.port=8080"
      - "traefik.http.routers.headscale.priority=1"
COMPOSE_EOF
    fi

    # Add Headscale UI if enabled
    if [ "$USE_HEADSCALE_UI" = true ]; then
        cat >> docker-compose.yml << 'COMPOSE_EOF'

  # Headscale Web Admin UI
  headscale-ui:
    image: ghcr.io/gurucomputing/headscale-ui:latest
    container_name: headscale-ui
    restart: unless-stopped
    
    environment:
      - TZ=UTC
      - HS_SERVER=http://headscale:8080
      - SCRIPT_NAME=/web
      - KEY=${HEADSCALE_API_KEY}
      - AUTH_TYPE=Basic
      - BASIC_AUTH_USER=${HEADSCALE_UI_USER}
      - BASIC_AUTH_PASS=${HEADSCALE_UI_PASSWORD}
    
COMPOSE_EOF

        # UI port exposure based on reverse proxy choice
        if [ "$USE_TRAEFIK" = true ]; then
            # Traefik: no port exposure
            cat >> docker-compose.yml << 'COMPOSE_EOF'
    # No ports exposed - Traefik accesses via Docker network
    
COMPOSE_EOF
        else
            # Nginx or none: expose UI port
            cat >> docker-compose.yml << COMPOSE_EOF
    ports:
      - "\${HEADSCALE_UI_EXTERNAL:-8081}:8080"
    
COMPOSE_EOF
        fi

        cat >> docker-compose.yml << 'COMPOSE_EOF'
    networks:
      - headscale-network
COMPOSE_EOF

        if [ "$USE_TRAEFIK" = true ]; then
            cat >> docker-compose.yml << 'COMPOSE_EOF'
      - barcode-network
COMPOSE_EOF
        fi

        cat >> docker-compose.yml << 'COMPOSE_EOF'
    
    depends_on:
      - headscale
COMPOSE_EOF

        # Add Traefik labels for Headscale UI if Traefik is enabled
        if [ "$USE_TRAEFIK" = true ]; then
            cat >> docker-compose.yml << COMPOSE_EOF
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.headscale-ui.rule=Host(\`${HEADSCALE_DOMAIN}\`) && PathPrefix(\`/web\`)"
      - "traefik.http.routers.headscale-ui.entrypoints=websecure"
      - "traefik.http.routers.headscale-ui.tls=true"
      - "traefik.http.routers.headscale-ui.tls.certresolver=letsencrypt"
      - "traefik.http.services.headscale-ui.loadbalancer.server.port=8080"
      - "traefik.http.routers.headscale-ui.priority=100"
      - "traefik.http.routers.headscale-ui.middlewares=security-headers"
COMPOSE_EOF
        fi
    fi

    # Add Tailscale client
    cat >> docker-compose.yml << 'COMPOSE_EOF'

  # Tailscale Client (for mesh network)
  tailscale:
    image: tailscale/tailscale:latest
    container_name: barcode-central-tailscale
    restart: unless-stopped
    
    hostname: barcode-central-server
    
    # Use startup script for initialization
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
      # Mount startup and iptables configuration scripts
      - ./tailscale-startup.sh:/tailscale-startup.sh:ro
      - ./tailscale-iptables.sh:/tailscale-iptables.sh:ro
    
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
      - SYS_MODULE
    
    networks:
      - barcode-network
      - headscale-network
    
    depends_on:
      - headscale
COMPOSE_EOF
fi

# Add networks section
cat >> docker-compose.yml << 'COMPOSE_EOF'

networks:
  barcode-network:
    name: barcode-network
    driver: bridge
COMPOSE_EOF

if [ "$USE_HEADSCALE" = true ]; then
    cat >> docker-compose.yml << 'COMPOSE_EOF'
  
  headscale-network:
    name: headscale-network
    driver: bridge
COMPOSE_EOF
fi

print_success "Created docker-compose.yml"

# Create required directories
print_info "Creating required directories..."
mkdir -p logs previews config data
mkdir -p config/headscale config/nginx config/traefik
mkdir -p data/headscale data/letsencrypt data/tailscale
touch history.json printers.json

# Initialize JSON files if empty
if [ ! -s history.json ]; then
    echo "[]" > history.json
fi

if [ ! -s printers.json ]; then
    echo "{\"printers\": []}" > printers.json
fi

# Create Headscale configuration if enabled
if [ "$USE_HEADSCALE" = true ]; then
    if [ ! -f config/headscale/config.yaml ]; then
        print_info "Downloading latest Headscale configuration template..."
        
        if curl -sSL https://raw.githubusercontent.com/juanfont/headscale/main/config-example.yaml -o config/headscale/config.yaml; then
            print_success "Downloaded latest config template"
            
            print_info "Customizing configuration for your setup..."
            
            # Customize required fields using sed
            # Determine correct server_url based on reverse proxy configuration
            # NOTE: We assume HTTPS for Traefik (with SSL) and Nginx (after certbot setup)
            #       Change to http:// if you're not putting SSL termination in front of Headscale
            if [ "$USE_TRAEFIK" = true ] && [ "$USE_SSL" = true ]; then
                HEADSCALE_SERVER_URL="https://$HEADSCALE_DOMAIN"
            elif [ "$USE_TRAEFIK" = true ]; then
                HEADSCALE_SERVER_URL="http://$HEADSCALE_DOMAIN"
            elif [ "$USE_NGINX" = true ]; then
                # Nginx: Assume HTTPS after certbot setup
                HEADSCALE_SERVER_URL="https://$HEADSCALE_DOMAIN"
            else
                HEADSCALE_SERVER_URL="http://$HEADSCALE_DOMAIN:$HEADSCALE_EXTERNAL_HTTP"
            fi
            
            sed -i "s|^server_url:.*|server_url: $HEADSCALE_SERVER_URL|" config/headscale/config.yaml
            sed -i "s|^listen_addr:.*|listen_addr: 0.0.0.0:8080|" config/headscale/config.yaml
            sed -i "s|^metrics_listen_addr:.*|metrics_listen_addr: 0.0.0.0:9090|" config/headscale/config.yaml
            sed -i "s|^grpc_listen_addr:.*|grpc_listen_addr: 0.0.0.0:50443|" config/headscale/config.yaml
            
            # Add TLS configuration (empty when using reverse proxy)
            sed -i 's|^tls_cert_path:.*|tls_cert_path: ""|' config/headscale/config.yaml
            sed -i 's|^tls_key_path:.*|tls_key_path: ""|' config/headscale/config.yaml
            sed -i "s|^unix_socket:.*|unix_socket: /var/run/headscale/headscale.sock|" config/headscale/config.yaml
            sed -i "s|^  base_domain:.*|  base_domain: headscale.local|" config/headscale/config.yaml
            sed -i 's|^  path: ""|  path: /etc/headscale/acl.json|' config/headscale/config.yaml
            
            print_success "Customized Headscale configuration"
        else
            print_warning "Failed to download config template, creating basic config..."
            # Fallback to basic config
            # Determine correct server_url based on reverse proxy configuration
            # NOTE: We assume HTTPS for Traefik (with SSL) and Nginx (after certbot setup)
            #       Change to http:// if you're not putting SSL termination in front of Headscale
            if [ "$USE_TRAEFIK" = true ] && [ "$USE_SSL" = true ]; then
                HEADSCALE_SERVER_URL="https://$HEADSCALE_DOMAIN"
            elif [ "$USE_TRAEFIK" = true ]; then
                HEADSCALE_SERVER_URL="http://$HEADSCALE_DOMAIN"
            elif [ "$USE_NGINX" = true ]; then
                # Nginx: Assume HTTPS after certbot setup
                HEADSCALE_SERVER_URL="https://$HEADSCALE_DOMAIN"
            else
                HEADSCALE_SERVER_URL="http://$HEADSCALE_DOMAIN:$HEADSCALE_EXTERNAL_HTTP"
            fi
            
            cat > config/headscale/config.yaml << HEADSCALE_EOF
# NOTE: server_url assumes HTTPS. Change to http:// if not using SSL termination
server_url: $HEADSCALE_SERVER_URL
listen_addr: 0.0.0.0:8080
metrics_listen_addr: 0.0.0.0:9090
grpc_listen_addr: 0.0.0.0:50443
grpc_allow_insecure: false

tls_cert_path: ""
tls_key_path: ""

noise:
  private_key_path: /var/lib/headscale/noise_private.key

prefixes:
  v4: 100.64.0.0/10
  v6: fd7a:115c:a1e0::/48

database:
  type: sqlite
  sqlite:
    path: /var/lib/headscale/db.sqlite
    write_ahead_log: true

unix_socket: /var/run/headscale/headscale.sock
unix_socket_permission: "0770"

log:
  level: info
  format: text

policy:
  mode: file
  path: /etc/headscale/acl.json

dns:
  magic_dns: true
  base_domain: headscale.local
  override_local_dns: true
  nameservers:
    global:
      - 1.1.1.1
      - 1.0.0.1

derp:
  server:
    enabled: false
  urls:
    - https://controlplane.tailscale.com/derpmap/default
HEADSCALE_EOF
            print_success "Created basic Headscale configuration"
        fi
    else
        print_info "Headscale configuration already exists, skipping"
    fi
    
    # Create ACL policy
    if [ ! -f config/headscale/acl.json ]; then
        print_info "Creating Headscale ACL policy..."
        cat > config/headscale/acl.json << ACL_EOF
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
        print_success "Created Headscale ACL policy"
    else
        print_info "Headscale ACL policy already exists, skipping"
    fi
fi
# Create routing and mesh joining scripts for Headscale
if [ "$USE_HEADSCALE" = true ]; then
    print_info "Creating Headscale routing scripts..."
    
    # Create app container routing wrapper
    cat > docker-entrypoint-wrapper.sh << 'WRAPPER_EOF'
#!/bin/bash
set -e

echo "[$(date)] Starting barcode-central with Tailscale routing configuration..."

# Check if running as root (needed for route configuration)
if [ "$(id -u)" -ne 0 ]; then
    echo "[$(date)] ERROR: This entrypoint must run as root to configure routes"
    echo "[$(date)] Continuing without routing configuration..."
    exec "$@"
fi

# Wait for Docker networking to stabilize
# This ensures DNS resolution is available
sleep 3

# Resolve tailscale container IP on shared network using Docker DNS
TAILSCALE_IP=$(getent hosts barcode-central-tailscale | awk '{ print $1 }')

if [ -n "$TAILSCALE_IP" ]; then
    echo "[$(date)] Configuring routes via Tailscale gateway: $TAILSCALE_IP"
    
    # Add route to Tailscale mesh network (100.64.0.0/10)
    # This is the standard Tailscale IP range
    if ip route add 100.64.0.0/10 via $TAILSCALE_IP 2>&1; then
        echo "[$(date)] ✓ Added route: 100.64.0.0/10 via $TAILSCALE_IP"
    else
        echo "[$(date)] Route 100.64.0.0/10 already exists or failed to add"
    fi
    
    # Add routes for advertised subnets (if configured via environment variable)
    # Format: ADVERTISED_ROUTES="192.168.11.0/24 10.0.1.0/24"
    if [ -n "$ADVERTISED_ROUTES" ]; then
        echo "[$(date)] Adding routes for advertised subnets..."
        for ROUTE in $ADVERTISED_ROUTES; do
            if ip route add $ROUTE via $TAILSCALE_IP 2>&1; then
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
    echo "[$(date)] WARNING: Could not resolve Tailscale container IP"
    echo "[$(date)] DNS lookup for 'barcode-central-tailscale' failed"
    echo "[$(date)] Continuing without Tailscale routing..."
fi

# Drop privileges and execute application as appuser
echo "[$(date)] Dropping privileges to appuser and starting application: $@"

# Use gosu if available, otherwise su-exec, otherwise fallback to su
if command -v gosu >/dev/null 2>&1; then
    exec gosu appuser "$@"
elif command -v su-exec >/dev/null 2>&1; then
    exec su-exec appuser "$@"
else
    exec su -s /bin/bash appuser -c "exec $*"
fi
WRAPPER_EOF
    
    chmod +x docker-entrypoint-wrapper.sh
    print_success "Created docker-entrypoint-wrapper.sh"
    
    # Create Tailscale startup script
    cat > tailscale-startup.sh << 'STARTUP_EOF'
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
sleep 3

# Check if tailscaled socket exists
if [ ! -S /var/run/tailscale/tailscaled.sock ]; then
    echo "[$(date)] WARNING: Tailscaled socket not found, waiting a bit longer..."
    sleep 2
fi

echo "[$(date)] ✓ Tailscale daemon initialization complete"

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
STARTUP_EOF
    
    chmod +x tailscale-startup.sh
    print_success "Created tailscale-startup.sh"
    
    # Create iptables configuration script
    cat > tailscale-iptables.sh << 'IPTABLES_EOF'
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
IPTABLES_EOF
    
    chmod +x tailscale-iptables.sh
    print_success "Created tailscale-iptables.sh"
    
    # Create automated mesh joining script (needs to be in scripts directory)
    mkdir -p scripts
    cat > scripts/join-headscale-mesh.sh << 'JOINMESH_EOF'
#!/bin/bash
# Automated Headscale Mesh Joining Script
# Joins barcode-central-tailscale container to Headscale mesh network

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Main script
clear
print_header "Headscale Mesh Joining - Automated Setup"

# Step 1: Check containers are running
print_info "Step 1/6: Checking container status..."

if ! docker ps | grep -q "headscale"; then
    print_error "Headscale container is not running"
    echo ""
    echo "Start containers with:"
    echo "  docker compose --profile headscale up -d"
    echo ""
    exit 1
fi
print_success "Headscale container is running"

if ! docker ps | grep -q "barcode-central-tailscale"; then
    print_error "Tailscale container is not running"
    echo ""
    echo "Start containers with:"
    echo "  docker compose --profile headscale up -d"
    echo ""
    exit 1
fi
print_success "Tailscale container is running"

if ! docker ps | grep -q "barcode-central"; then
    print_warning "App container is not running (optional for this step)"
else
    print_success "App container is running"
fi

echo ""

# Step 2: Create user in Headscale
print_info "Step 2/6: Creating Headscale user..."

USER_OUTPUT=$(docker exec headscale headscale users create barcode-central 2>&1 || true)
if echo "$USER_OUTPUT" | grep -q "already exists"; then
    print_info "User 'barcode-central' already exists (OK)"
elif echo "$USER_OUTPUT" | grep -q "User created"; then
    print_success "Created user 'barcode-central'"
else
    print_warning "Unexpected output creating user, continuing anyway..."
    echo "  Output: $USER_OUTPUT"
fi

echo ""

# Step 3: Extract node key from Tailscale logs
print_info "Step 3/6: Extracting node registration key..."
print_info "Monitoring Tailscale container logs for registration URL..."

NODE_KEY=""
TIMEOUT=30
ELAPSED=0

while [ -z "$NODE_KEY" ] && [ $ELAPSED -lt $TIMEOUT ]; do
    # Look for registration URL pattern in logs
    # Format: https://headscale.example.com/register/nodekey:ABCD1234...
    REG_URL=$(docker logs barcode-central-tailscale 2>&1 | \
        grep -oP 'https?://[^/]+/register/\K[a-zA-Z0-9:_-]+' | \
        tail -1 || true)
    
    if [ -n "$REG_URL" ]; then
        NODE_KEY="$REG_URL"
        break
    fi
    
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -n "."
done
echo ""

if [ -z "$NODE_KEY" ]; then
    print_error "Could not find registration URL in logs"
    echo ""
    print_warning "Manual registration required:"
    echo ""
    echo "1. Check container logs:"
    echo "   docker logs barcode-central-tailscale"
    echo ""
    echo "2. Find a URL like:"
    echo "   https://headscale.example.com/register/nodekey:ABCD1234..."
    echo ""
    echo "3. Extract the node key (everything after /register/) and run:"
    echo "   docker exec headscale headscale nodes register \\"
    echo "     --user barcode-central \\"
    echo "     --key 'nodekey:ABCD1234...'"
    echo ""
    exit 1
fi

print_success "Found node key: ${NODE_KEY:0:30}..."
echo ""

# Step 4: Register node in Headscale
print_info "Step 4/6: Registering node in Headscale..."

if docker exec headscale headscale nodes register \
    --user barcode-central \
    --key "$NODE_KEY" 2>&1; then
    print_success "Node registered successfully"
else
    print_error "Node registration failed"
    echo ""
    echo "Try manual registration:"
    echo "  docker exec headscale headscale nodes register \\"
    echo "    --user barcode-central \\"
    echo "    --key '$NODE_KEY'"
    echo ""
    exit 1
fi

echo ""

# Step 5: Verify mesh connectivity
print_info "Step 5/6: Verifying mesh connectivity..."
sleep 3

if docker exec barcode-central-tailscale tailscale status 2>&1 | grep -q "100.64"; then
    TAILSCALE_IP=$(docker exec barcode-central-tailscale tailscale ip -4 2>/dev/null || echo "unknown")
    print_success "Tailscale mesh connected!"
    echo "  Tailscale IP: $TAILSCALE_IP"
else
    print_warning "Tailscale may not be fully connected yet"
    echo ""
    echo "Check status with:"
    echo "  docker exec barcode-central-tailscale tailscale status"
fi

echo ""

# Step 6: Configure Headscale UI API key (if enabled)
print_info "Step 6/6: Checking Headscale UI configuration..."

if grep -q "HEADSCALE_UI_ENABLED=true" .env 2>/dev/null; then
    print_info "Headscale UI is enabled, generating API key..."
    
    # Create API key - Headscale v0.27+ syntax: apikeys create -e 90d
    API_KEY=$(docker exec headscale headscale apikeys create -e 90d 2>&1 | \
        tail -1 | \
        tr -d '[:space:]' || true)
    
    # Validate API key (should be alphanumeric with dots/underscores, ~40+ chars)
    if [ -n "$API_KEY" ] && [ ${#API_KEY} -gt 20 ]; then
        print_success "API key generated: ${API_KEY:0:20}..."
        
        # Update .env file
        if grep -q "^HEADSCALE_API_KEY=" .env; then
            # Replace existing key
            sed -i "s|^HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$API_KEY|" .env
            print_success "Updated HEADSCALE_API_KEY in .env"
        elif grep -q "^# HEADSCALE_API_KEY=" .env; then
            # Uncomment and set
            sed -i "s|^# HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$API_KEY|" .env
            print_success "Set HEADSCALE_API_KEY in .env"
        else
            # Add new entry
            echo "HEADSCALE_API_KEY=$API_KEY" >> .env
            print_success "Added HEADSCALE_API_KEY to .env"
        fi
        
        # Restart Headscale UI to pick up new API key
        print_info "Restarting Headscale UI container..."
        if docker compose restart headscale-ui 2>/dev/null; then
            print_success "Headscale UI restarted"
        else
            print_warning "Could not restart Headscale UI (may need manual restart)"
        fi
    else
        print_warning "API key generation failed or returned invalid key"
        print_info "You may need to generate it manually:"
        echo "  docker exec headscale headscale apikeys create --expiration 90d"
    fi
else
    print_info "Headscale UI not enabled, skipping API key generation"
fi

# Final summary
print_header "✓ Headscale Mesh Setup Complete!"

echo "Your barcode-central server is now connected to the Headscale mesh network."
echo ""
echo "Next steps:"
echo ""
echo "1. Verify app container can reach Tailscale mesh:"
echo "   docker exec barcode-central ip route | grep 100.64"
echo ""
echo "2. Generate authkey for Raspberry Pi devices:"
echo "   ./scripts/generate-authkey.sh"
echo ""
echo "3. Setup Raspberry Pi print servers at each location:"
echo "   (On each Pi, run the raspberry-pi-setup.sh script)"
echo ""
echo "4. After Pi's are connected, enable their subnet routes:"
echo "   ./scripts/enable-routes.sh"
echo ""
echo "5. Test connectivity to remote printers:"
echo "   docker exec barcode-central ping -c 3 <printer-ip>"
echo ""

print_header "Setup Complete!"
JOINMESH_EOF
    
    chmod +x scripts/join-headscale-mesh.sh
    print_success "Created scripts/join-headscale-mesh.sh"
    
    print_success "Created all Headscale routing scripts"
fi


# Generate nginx configuration files if using nginx
if [ "$USE_NGINX" = true ]; then
    print_info "Generating nginx configuration files..."
    
    # Barcode Central nginx config
    cat > config/nginx/barcode-central.conf << NGINX_EOF
# Nginx configuration for Barcode Central
# Generated by setup.sh on $(date)

# Upstream server
upstream barcode_central {
    server localhost:$HTTP_PORT;
}

# HTTP server
server {
    listen 80;
    server_name $DOMAIN;
    
    # Client body size (for file uploads)
    client_max_body_size 10M;
    
    # Proxy settings
    location / {
        proxy_pass http://barcode_central;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /api/health {
        proxy_pass http://barcode_central;
        access_log off;
    }
}

# Logging
access_log /var/log/nginx/barcode-central-access.log;
error_log /var/log/nginx/barcode-central-error.log;
NGINX_EOF
    print_success "Created config/nginx/barcode-central.conf"
    
    # Headscale nginx config (if enabled)
    if [ "$USE_HEADSCALE" = true ]; then
        cat > config/nginx/headscale.conf << NGINX_EOF
# Nginx configuration for Headscale
# Generated by setup.sh on $(date)

# Upstream definitions
upstream headscale_backend {
    server localhost:$HEADSCALE_EXTERNAL_HTTP;
}

NGINX_EOF

        if [ "$USE_HEADSCALE_UI" = true ]; then
            cat >> config/nginx/headscale.conf << NGINX_EOF
upstream headscale_ui_backend {
    server localhost:$HEADSCALE_UI_EXTERNAL;
}

NGINX_EOF
        fi

        cat >> config/nginx/headscale.conf << 'NGINX_EOF'
# Main server block
server {
    listen 80;
NGINX_EOF

        cat >> config/nginx/headscale.conf << NGINX_EOF
    server_name $HEADSCALE_DOMAIN;
    
NGINX_EOF

        if [ "$USE_HEADSCALE_UI" = true ]; then
            cat >> config/nginx/headscale.conf << 'NGINX_EOF'
    # Headscale UI at /web path
    location /web {
        proxy_pass http://headscale_ui_backend$request_uri;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for UI
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
NGINX_EOF
        fi

        cat >> config/nginx/headscale.conf << 'NGINX_EOF'
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

# Logging
access_log /var/log/nginx/headscale-access.log;
error_log /var/log/nginx/headscale-error.log;
NGINX_EOF
        print_success "Created config/nginx/headscale.conf"
    fi
fi

# Set permissions and ownership
chmod 755 logs previews 2>/dev/null || true
chown -R 1000:1000 logs previews 2>/dev/null || true
chmod 644 history.json printers.json 2>/dev/null || true
chown 1000:1000 history.json printers.json 2>/dev/null || true

print_success "Set file permissions and ownership"
print_success "Created all required directories"

# Final instructions
clear
print_header "Setup Complete!"
echo ""
print_success "Configuration files generated successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Your credentials:"
echo "  Barcode Central:"
echo "    Username: $LOGIN_USER"
echo "    Password: $LOGIN_PASSWORD"
if [ "$USE_HEADSCALE_UI" = true ]; then
    echo ""
    echo "  Headscale UI:"
    echo "    Username: $HEADSCALE_UI_USER"
    echo "    Password: $HEADSCALE_UI_PASSWORD"
fi
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
    if [ "$USE_HEADSCALE" = true ]; then
        echo "   Create A record: $HEADSCALE_DOMAIN → $SERVER_IP"
    fi
    echo ""
fi

# Firewall configuration
STEP_NUM=2
if [ "$EXTERNAL_ACCESS" = false ]; then
    STEP_NUM=1
fi

echo "$STEP_NUM. Configure firewall (IMPORTANT - Manual step required):"
echo "   The following ports need to be opened:"
echo ""
if [ "$USE_TRAEFIK" = true ]; then
    echo "   sudo ufw allow 80/tcp      # HTTP"
    if [ "$USE_SSL" = true ]; then
        echo "   sudo ufw allow 443/tcp     # HTTPS"
    fi
elif [ "$USE_NGINX" = true ]; then
    echo "   sudo ufw allow 80/tcp      # HTTP"
    echo "   sudo ufw allow 443/tcp     # HTTPS (after certbot)"
else
    echo "   sudo ufw allow $HTTP_PORT/tcp   # Barcode Central"
fi

if [ "$USE_HEADSCALE" = true ]; then
    echo "   sudo ufw allow 3478/udp        # STUN (Headscale DERP)"
    if [ "$REVERSE_PROXY" = "none" ]; then
        echo "   sudo ufw allow $HEADSCALE_EXTERNAL_HTTP/tcp   # Headscale API"
        if [ "$USE_HEADSCALE_UI" = true ]; then
            echo "   sudo ufw allow $HEADSCALE_UI_EXTERNAL/tcp   # Headscale UI"
        fi
    fi
fi
echo "   sudo ufw enable"
echo ""
print_warning "NOTE: Application ports are NOT exposed externally when using nginx"
print_warning "      (nginx accesses services via localhost)"
echo ""

# Nginx deployment instructions
((STEP_NUM++))
if [ "$USE_NGINX" = true ]; then
    echo "$STEP_NUM. Deploy nginx configuration:"
    echo "   sudo cp config/nginx/barcode-central.conf /etc/nginx/sites-available/barcode-central"
    echo "   sudo ln -s /etc/nginx/sites-available/barcode-central /etc/nginx/sites-enabled/"
    if [ "$USE_HEADSCALE" = true ]; then
        echo "   sudo cp config/nginx/headscale.conf /etc/nginx/sites-available/headscale"
        echo "   sudo ln -s /etc/nginx/sites-available/headscale /etc/nginx/sites-enabled/"
    fi
    echo "   sudo nginx -t"
    echo "   sudo systemctl reload nginx"
    echo ""
    
    ((STEP_NUM++))
    echo "$STEP_NUM. Setup SSL with certbot:"
    echo "   sudo apt-get install certbot python3-certbot-nginx"
    echo "   sudo certbot --nginx -d $DOMAIN"
    if [ "$USE_HEADSCALE" = true ]; then
        echo "   sudo certbot --nginx -d $HEADSCALE_DOMAIN"
    fi
    echo "   sudo certbot renew --dry-run  # Test renewal"
    echo ""
    
    ((STEP_NUM++))
fi

echo "$STEP_NUM. Start the application:"
echo "   docker compose up -d"
echo ""

((STEP_NUM++))
echo "$STEP_NUM. Check status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""

# Headscale-specific instructions
if [ "$USE_HEADSCALE" = true ]; then
    ((STEP_NUM++))
    echo "$STEP_NUM. Setup Headscale mesh network:"
    echo "   a) Join barcode-central to mesh (automated):"
    echo "      ./scripts/join-headscale-mesh.sh"
    echo ""
    echo "   b) Generate pre-auth key for Raspberry Pi devices:"
    echo "      ./scripts/generate-authkey.sh"
    echo ""
    echo "   c) Setup Raspberry Pi print servers at each location:"
    echo "      On each Raspberry Pi, run:"
    echo "      curl -sSL https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh | bash"
    echo ""
    echo "   d) Enable subnet routes from Raspberry Pis:"
    echo "      ./scripts/enable-routes.sh"
    echo ""
    echo "   e) Verify connectivity:"
    echo "      docker exec barcode-central ping -c 3 <printer-ip>"
    echo ""
    
    if [ "$USE_HEADSCALE_UI" = true ]; then
        echo "   f) Access Headscale UI at:"
        if [ "$USE_TRAEFIK" = true ] && [ "$USE_SSL" = true ]; then
            echo "      https://$HEADSCALE_DOMAIN/web/"
        elif [ "$USE_TRAEFIK" = true ]; then
            echo "      http://$HEADSCALE_DOMAIN/web/"
        elif [ "$USE_NGINX" = true ]; then
            echo "      http://$HEADSCALE_DOMAIN/web/ (https after certbot)"
        else
            echo "      http://$HEADSCALE_DOMAIN:$HEADSCALE_UI_EXTERNAL/web/"
        fi
        echo ""
    fi
fi

# Access URL
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$USE_TRAEFIK" = true ]; then
    if [ "$USE_SSL" = true ]; then
        echo "Access your application at: https://$DOMAIN"
    else
        echo "Access your application at: http://$DOMAIN"
    fi
elif [ "$USE_NGINX" = true ]; then
    echo "Access your application at: http://$DOMAIN"
    echo "(https://$DOMAIN after certbot setup)"
elif [ "$EXTERNAL_ACCESS" = true ]; then
    echo "Access your application at: http://$DOMAIN:$HTTP_PORT"
else
    echo "Access your application at: http://localhost:$HTTP_PORT"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
print_info "For detailed documentation, see:"
echo "  - QUICKSTART.md"
echo "  - PRODUCTION_DEPLOYMENT_GUIDE.md"
echo "  - SETUP_REFACTORING_ARCHITECTURE.md"
if [ "$USE_HEADSCALE" = true ]; then
    echo "  - RASPBERRY_PI_SETUP.md"
fi
echo ""

print_success "Setup complete! Happy printing! 🖨️"