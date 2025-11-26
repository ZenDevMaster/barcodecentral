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
COMPOSE_EOF

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
    
    profiles:
      - headscale
    
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
    
    profiles:
      - headscale
    
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
      - ./data/tailscale:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
    
    cap_add:
      - NET_ADMIN
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
    
    if [ "$USE_HEADSCALE_UI" = true ]; then
        echo "   a) Wait for services to start (30 seconds)"
        echo "      sleep 30"
        echo ""
        echo "   b) Generate Headscale API key (automatic):"
        echo "      API_KEY=\$(docker exec headscale headscale apikeys create --expiration 90d | grep -oP '(?<=Created API key: ).*')"
        echo "      echo \"HEADSCALE_API_KEY=\$API_KEY\" >> .env"
        echo "      docker compose restart headscale-ui"
        echo ""
        echo "   c) Access Headscale UI:"
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
        echo "   d) Generate pre-auth key (in UI or via CLI):"
        echo "      ./scripts/generate-authkey.sh"
    else
        echo "   a) Generate auth key:"
        echo "      ./scripts/generate-authkey.sh"
    fi
    echo ""
    if [ "$USE_HEADSCALE_UI" = true ]; then
        echo "   e) Setup Raspberry Pi print servers at each location:"
    else
        echo "   b) Setup Raspberry Pi print servers at each location:"
    fi
    echo "      On each Raspberry Pi, run:"
    echo "      curl -sSL https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh | bash"
    echo ""
    if [ "$USE_HEADSCALE_UI" = true ]; then
        echo "   f) Enable subnet routes (in UI or via CLI):"
        echo "      ./scripts/enable-routes.sh"
        echo ""
        echo "   g) Verify connectivity:"
    else
        echo "   c) Enable subnet routes:"
        echo "      ./scripts/enable-routes.sh"
        echo ""
        echo "   d) Verify connectivity:"
    fi
    echo "      docker exec -it barcode-central-tailscale tailscale ping <raspberry-pi-hostname>"
    echo ""
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