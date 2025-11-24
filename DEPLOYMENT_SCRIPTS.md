# Deployment Scripts Documentation

Complete reference for all deployment and orchestration scripts for Barcode Central production deployment.

## Table of Contents

1. [VPS Deployment Scripts](#vps-deployment-scripts)
2. [Raspberry Pi Setup Scripts](#raspberry-pi-setup-scripts)
3. [Headscale Management Scripts](#headscale-management-scripts)
4. [Monitoring Scripts](#monitoring-scripts)
5. [Backup & Restore Scripts](#backup--restore-scripts)
6. [Maintenance Scripts](#maintenance-scripts)

---

## VPS Deployment Scripts

### 1. Basic Deployment Script

**File**: `deployment/vps/deploy-basic.sh`

```bash
#!/bin/bash
# Basic VPS Deployment Script for Barcode Central
# Deploys the application without Traefik or Headscale

set -e

echo "=== Barcode Central - Basic Deployment ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is not installed"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: Docker Compose is not installed"; exit 1; }

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.production.example to .env and configure it"
    exit 1
fi

# Create required directories
echo "Creating required directories..."
mkdir -p logs previews

# Create data files if they don't exist
touch history.json
touch printers.json

# Build image
echo "Building Docker image..."
docker compose build

# Start services
echo "Starting services..."
docker compose up -d

# Wait for health check
echo "Waiting for application to be healthy..."
sleep 10

# Check health
if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
    echo "✓ Application is healthy"
    echo "✓ Deployment successful!"
    echo ""
    echo "Access the application at: http://localhost:5000"
else
    echo "✗ Health check failed"
    echo "Check logs with: docker compose logs -f"
    exit 1
fi
```

### 2. Traefik Deployment Script

**File**: `deployment/vps/deploy-traefik.sh`

```bash
#!/bin/bash
# Traefik Deployment Script for Barcode Central
# Deploys with automatic HTTPS via Let's Encrypt

set -e

echo "=== Barcode Central - Traefik Deployment ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is not installed"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: Docker Compose is not installed"; exit 1; }

# Check environment files
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

if [ ! -f .env.traefik ]; then
    echo "Error: .env.traefik file not found"
    echo "Please copy .env.traefik.example to .env.traefik and configure it"
    exit 1
fi

# Source Traefik environment
source .env.traefik

# Validate required variables
if [ -z "$DOMAIN" ]; then
    echo "Error: DOMAIN not set in .env.traefik"
    exit 1
fi

if [ -z "$ACME_EMAIL" ]; then
    echo "Error: ACME_EMAIL not set in .env.traefik"
    exit 1
fi

echo "Domain: $DOMAIN"
echo "Email: $ACME_EMAIL"

# Create required directories
echo "Creating required directories..."
mkdir -p logs previews letsencrypt traefik-logs

# Set permissions for Let's Encrypt
chmod 600 letsencrypt 2>/dev/null || true

# Create data files
touch history.json
touch printers.json

# Build and start services
echo "Building and starting services..."
docker compose -f docker-compose.traefik.yml up -d --build

# Wait for services
echo "Waiting for services to start..."
sleep 15

# Check health
echo "Checking application health..."
if curl -f -k https://$DOMAIN/api/health >/dev/null 2>&1; then
    echo "✓ Application is healthy"
    echo "✓ Deployment successful!"
    echo ""
    echo "Access the application at: https://$DOMAIN"
else
    echo "⚠ Health check via HTTPS failed (this is normal if DNS isn't propagated yet)"
    echo "Check logs with: docker compose -f docker-compose.traefik.yml logs -f"
fi

echo ""
echo "Note: It may take a few minutes for Let's Encrypt to issue certificates"
echo "Monitor Traefik logs: docker compose -f docker-compose.traefik.yml logs -f traefik"
```

### 3. Full Stack Deployment Script

**File**: `deployment/vps/deploy-full.sh`

```bash
#!/bin/bash
# Full Stack Deployment Script
# Deploys Traefik + Headscale + Application

set -e

echo "=== Barcode Central - Full Stack Deployment ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is not installed"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: Docker Compose is not installed"; exit 1; }

# Check environment files
for file in .env .env.traefik .env.headscale; do
    if [ ! -f "$file" ]; then
        echo "Error: $file not found"
        echo "Please create all required environment files"
        exit 1
    fi
done

# Source environment files
source .env.traefik
source .env.headscale

# Validate configuration
if [ -z "$DOMAIN" ] || [ -z "$ACME_EMAIL" ]; then
    echo "Error: Missing Traefik configuration"
    exit 1
fi

# Create required directories
echo "Creating required directories..."
mkdir -p logs previews letsencrypt traefik-logs
mkdir -p headscale/config headscale/data
mkdir -p tailscale/state

# Copy Headscale configuration if not exists
if [ ! -f headscale/config/config.yaml ]; then
    echo "Error: headscale/config/config.yaml not found"
    echo "Please create Headscale configuration file"
    exit 1
fi

if [ ! -f headscale/config/acl.json ]; then
    echo "Error: headscale/config/acl.json not found"
    echo "Please create Headscale ACL file"
    exit 1
fi

# Create data files
touch history.json
touch printers.json

# Build and start services
echo "Building and starting services..."
docker compose -f docker-compose.full.yml up -d --build

# Wait for Headscale to start
echo "Waiting for Headscale to initialize..."
sleep 20

# Generate pre-auth key if needed
if [ -z "$TAILSCALE_AUTHKEY" ]; then
    echo "Generating Tailscale pre-auth key..."
    AUTHKEY=$(docker exec headscale headscale preauthkeys create --reusable --expiration 90d | grep -oP 'Key: \K.*')
    echo "Generated auth key: $AUTHKEY"
    echo "Add this to .env.headscale: TAILSCALE_AUTHKEY=$AUTHKEY"
    echo ""
    echo "Then restart the application container:"
    echo "docker compose -f docker-compose.full.yml restart app tailscale"
fi

# Check health
echo "Checking services..."
sleep 10

if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✓ Headscale is healthy"
else
    echo "⚠ Headscale health check failed"
fi

if curl -f -k https://$DOMAIN/api/health >/dev/null 2>&1; then
    echo "✓ Application is healthy"
else
    echo "⚠ Application health check failed (may need DNS propagation)"
fi

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Configure Raspberry Pi print servers (see RASPBERRY_PI_SETUP.md)"
echo "2. Enable subnet routes in Headscale"
echo "3. Add printers to printers.json"
echo ""
echo "Access points:"
echo "- Application: https://$DOMAIN"
echo "- Headscale: https://headscale.$DOMAIN"
```

### 4. Update Script

**File**: `deployment/vps/update.sh`

```bash
#!/bin/bash
# Update Script for Barcode Central
# Pulls latest code and rebuilds containers

set -e

echo "=== Barcode Central - Update ==="

# Determine which compose file to use
COMPOSE_FILE="docker-compose.yml"
if [ -f docker-compose.full.yml ] && docker compose -f docker-compose.full.yml ps >/dev/null 2>&1; then
    COMPOSE_FILE="docker-compose.full.yml"
elif [ -f docker-compose.traefik.yml ] && docker compose -f docker-compose.traefik.yml ps >/dev/null 2>&1; then
    COMPOSE_FILE="docker-compose.traefik.yml"
fi

echo "Using compose file: $COMPOSE_FILE"

# Backup before update
echo "Creating backup..."
./scripts/backup.sh

# Pull latest code (if using git)
if [ -d .git ]; then
    echo "Pulling latest code..."
    git pull
fi

# Rebuild and restart
echo "Rebuilding containers..."
docker compose -f $COMPOSE_FILE build --no-cache

echo "Restarting services..."
docker compose -f $COMPOSE_FILE up -d

# Wait for health check
echo "Waiting for application..."
sleep 10

# Verify health
if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
    echo "✓ Update successful!"
else
    echo "✗ Health check failed after update"
    echo "Check logs: docker compose -f $COMPOSE_FILE logs -f"
    exit 1
fi
```

---

## Raspberry Pi Setup Scripts

### 1. Automated Setup Script

**File**: `deployment/raspberry-pi/setup-print-server.sh`

```bash
#!/bin/bash
# Automated Raspberry Pi Print Server Setup
# Run this script on a fresh Raspberry Pi OS installation

set -e

echo "=== Raspberry Pi Print Server Setup ==="

# Configuration
read -p "Enter location name (e.g., warehouse, office): " LOCATION
read -p "Enter Headscale server URL (e.g., http://headscale.example.com:8080): " HEADSCALE_URL
read -p "Enter Tailscale pre-auth key: " AUTH_KEY
read -p "Enter local subnet to advertise (e.g., 192.168.1.0/24): " SUBNET

HOSTNAME="${LOCATION}-pi"

echo ""
echo "Configuration:"
echo "  Hostname: $HOSTNAME"
echo "  Headscale: $HEADSCALE_URL"
echo "  Subnet: $SUBNET"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Update system
echo "Updating system..."
sudo apt update
sudo apt upgrade -y

# Install essential packages
echo "Installing essential packages..."
sudo apt install -y \
    curl wget git vim htop \
    net-tools iptables ca-certificates \
    ufw

# Set hostname
echo "Setting hostname..."
sudo hostnamectl set-hostname $HOSTNAME
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts

# Enable IP forwarding
echo "Enabling IP forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p

# Configure firewall
echo "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 41641/udp
sudo ufw --force enable

# Install Tailscale
echo "Installing Tailscale..."
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt update
sudo apt install -y tailscale

# Connect to Headscale
echo "Connecting to Headscale..."
sudo tailscale up \
    --login-server=$HEADSCALE_URL \
    --authkey=$AUTH_KEY \
    --advertise-routes=$SUBNET \
    --accept-routes \
    --hostname=$HOSTNAME

# Enable Tailscale at boot
sudo systemctl enable tailscaled

# Create monitoring script
echo "Creating monitoring script..."
sudo tee /usr/local/bin/pi-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== Raspberry Pi Print Server Status ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Temperature: $(vcgencmd measure_temp)"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo ""
echo "=== Tailscale Status ==="
tailscale status
EOF

sudo chmod +x /usr/local/bin/pi-monitor.sh

# Create health check script
echo "Creating health check script..."
sudo tee /usr/local/bin/health-check.sh > /dev/null <<'EOF'
#!/bin/bash
LOG_FILE="/var/log/pi-health.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

if ! tailscale status &>/dev/null; then
    log_message "ERROR: Tailscale is down"
    sudo systemctl restart tailscaled
else
    log_message "OK: Tailscale is running"
fi

TEMP=$(vcgencmd measure_temp | grep -o '[0-9.]*')
if (( $(echo "$TEMP > 80" | bc -l) )); then
    log_message "WARNING: High temperature: ${TEMP}°C"
fi

log_message "Health check completed"
EOF

sudo chmod +x /usr/local/bin/health-check.sh

# Schedule health checks
echo "Scheduling health checks..."
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/health-check.sh") | crontab -

echo ""
echo "✓ Setup complete!"
echo ""
echo "Tailscale IP: $(tailscale ip -4)"
echo ""
echo "Next steps:"
echo "1. On Headscale server, enable subnet route:"
echo "   docker exec headscale headscale routes list"
echo "   docker exec headscale headscale routes enable -r <route-id>"
echo ""
echo "2. Test connectivity from VPS:"
echo "   ping $(tailscale ip -4)"
echo "   ping <printer-ip-in-subnet>"
echo ""
echo "3. Add printers to Barcode Central printers.json"
```

### 2. CUPS Installation Script

**File**: `deployment/raspberry-pi/install-cups.sh`

```bash
#!/bin/bash
# Install and configure CUPS for USB printer support

set -e

echo "=== Installing CUPS for USB Printers ==="

# Install CUPS
echo "Installing CUPS..."
sudo apt install -y cups cups-client printer-driver-all

# Add user to lpadmin group
sudo usermod -a -G lpadmin pi

# Configure CUPS for network access
echo "Configuring CUPS..."
sudo cp /etc/cups/cupsd.conf /etc/cups/cupsd.conf.backup

sudo tee /etc/cups/cupsd.conf > /dev/null <<'EOF'
Port 631
Listen /run/cups/cups.sock

Browsing On
BrowseLocalProtocols dnssd

DefaultAuthType Basic
WebInterface Yes

<Location />
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.0.0/16
  Allow from 10.0.0.0/8
  Allow from 172.16.0.0/12
  Allow from 100.64.0.0/10
</Location>

<Location /admin>
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.0.0/16
  Allow from 10.0.0.0/8
  Allow from 172.16.0.0/12
  Allow from 100.64.0.0/10
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.0.0/16
  Allow from 10.0.0.0/8
  Allow from 172.16.0.0/12
  Allow from 100.64.0.0/10
</Location>
EOF

# Restart CUPS
sudo systemctl restart cups
sudo systemctl enable cups

# Allow CUPS through firewall
sudo ufw allow from 192.168.0.0/16 to any port 631
sudo ufw allow from 10.0.0.0/8 to any port 631
sudo ufw allow from 100.64.0.0/10 to any port 631

echo ""
echo "✓ CUPS installed and configured!"
echo ""
echo "Access CUPS web interface:"
echo "  Local: http://$(hostname -I | awk '{print $1}'):631"
echo "  Tailscale: http://$(tailscale ip -4):631"
echo ""
echo "To add a USB printer:"
echo "1. Connect USB printer"
echo "2. Access CUPS web interface"
echo "3. Administration → Add Printer"
echo "4. Select USB printer and configure"
```

---

## Headscale Management Scripts

### 1. Headscale Setup Script

**File**: `deployment/headscale/setup.sh`

```bash
#!/bin/bash
# Initialize Headscale server

set -e

echo "=== Headscale Setup ==="

# Check if Headscale is running
if ! docker ps | grep -q headscale; then
    echo "Error: Headscale container is not running"
    echo "Start it with: docker compose -f docker-compose.headscale.yml up -d"
    exit 1
fi

# Wait for Headscale to be ready
echo "Waiting for Headscale to be ready..."
sleep 5

# Create first user/namespace
echo "Creating default namespace..."
docker exec headscale headscale namespaces create default || echo "Namespace may already exist"

# Generate pre-auth key
echo "Generating pre-auth key..."
AUTHKEY=$(docker exec headscale headscale preauthkeys create --reusable --expiration 90d --namespace default | grep -oP 'Key: \K.*' || echo "")

if [ -n "$AUTHKEY" ]; then
    echo ""
    echo "✓ Pre-auth key generated:"
    echo "$AUTHKEY"
    echo ""
    echo "Use this key when setting up Raspberry Pi print servers"
    echo "Add to .env.headscale: TAILSCALE_AUTHKEY=$AUTHKEY"
else
    echo "Failed to generate auth key"
    exit 1
fi

# List current nodes
echo ""
echo "Current nodes:"
docker exec headscale headscale nodes list

echo ""
echo "✓ Headscale setup complete!"
```

### 2. Route Management Script

**File**: `deployment/headscale/manage-routes.sh`

```bash
#!/bin/bash
# Manage Headscale subnet routes

set -e

echo "=== Headscale Route Management ==="

# Check if Headscale is running
if ! docker ps | grep -q headscale; then
    echo "Error: Headscale container is not running"
    exit 1
fi

# Function to list routes
list_routes() {
    echo "Current routes:"
    docker exec headscale headscale routes list
}

# Function to enable route
enable_route() {
    read -p "Enter route ID to enable: " ROUTE_ID
    docker exec headscale headscale routes enable -r $ROUTE_ID
    echo "✓ Route enabled"
}

# Function to disable route
disable_route() {
    read -p "Enter route ID to disable: " ROUTE_ID
    docker exec headscale headscale routes disable -r $ROUTE_ID
    echo "✓ Route disabled"
}

# Menu
while true; do
    echo ""
    echo "1) List routes"
    echo "2) Enable route"
    echo "3) Disable route"
    echo "4) Exit"
    echo ""
    read -p "Select option: " choice

    case $choice in
        1) list_routes ;;
        2) enable_route ;;
        3) disable_route ;;
        4) exit 0 ;;
        *) echo "Invalid option" ;;
    esac
done
```

---

## Monitoring Scripts

### 1. System Status Script

**File**: `deployment/monitoring/system-status.sh`

```bash
#!/bin/bash
# Check status of all components

echo "=== Barcode Central System Status ==="
echo ""

# Check Docker
echo "Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check application health
echo "Application Health:"
if curl -f http://localhost:5000/api/health 2>/dev/null; then
    echo "✓ Application is healthy"
else
    echo "✗ Application health check failed"
fi
echo ""

# Check Headscale (if running)
if docker ps | grep -q headscale; then
    echo "Headscale Nodes:"
    docker exec headscale headscale nodes list 2>/dev/null || echo "Failed to list nodes"
    echo ""
    
    echo "Headscale Routes:"
    docker exec headscale headscale routes list 2>/dev/null || echo "Failed to list routes"
    echo ""
fi

# Check disk space
echo "Disk Usage:"
df -h / | tail -1
echo ""

# Check memory
echo "Memory Usage:"
free -h | grep Mem
echo ""

# Check logs for errors
echo "Recent Errors (last 10):"
docker compose logs --tail=10 2>&1 | grep -i error || echo "No recent errors"
```

---

## Backup & Restore Scripts

These scripts already exist in the `scripts/` directory but are documented here for completeness.

### Backup Script
**File**: `scripts/backup.sh` (already exists)

### Restore Script
**File**: `scripts/restore.sh` (already exists)

---

## Maintenance Scripts

### 1. Cleanup Script

**File**: `deployment/maintenance/cleanup.sh`

```bash
#!/bin/bash
# Cleanup old Docker images, logs, and temporary files

echo "=== System Cleanup ==="

# Remove old Docker images
echo "Removing unused Docker images..."
docker image prune -a -f

# Remove old containers
echo "Removing stopped containers..."
docker container prune -f

# Remove old volumes
echo "Removing unused volumes..."
docker volume prune -f

# Clean old logs (keep last 30 days)
echo "Cleaning old logs..."
find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Clean old previews (keep last 7 days)
echo "Cleaning old previews..."
find previews/ -name "*.pdf" -mtime +7 -delete 2>/dev/null || true
find previews/ -name "*.png" -mtime +7 -delete 2>/dev/null || true

# Clean old backups (keep last 10)
echo "Cleaning old backups..."
ls -t backups/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm

echo "✓ Cleanup complete!"
```

### 2. Health Check Script

**File**: `deployment/maintenance/health-check.sh`

```bash
#!/bin/bash
# Comprehensive health check

set -e

echo "=== Health Check ==="

ERRORS=0

# Check application
if ! curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
    echo "✗ Application health check failed"
    ((ERRORS++))
else
    echo "✓ Application is healthy"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "✗ Disk usage critical: ${DISK_USAGE}%"
    ((ERRORS++))
else
    echo "✓ Disk usage OK: ${DISK_USAGE}%"
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "⚠ Memory usage high: ${MEM_USAGE}%"
else
    echo "✓ Memory usage OK: ${MEM_USAGE}%"
fi

# Check Docker containers
STOPPED=$(docker ps -a --filter "status=exited" --format "{{.Names}}" | wc -l)
if [ "$STOPPED" -gt 0 ]; then
    echo "⚠ $STOPPED stopped containers"
else
    echo "✓ All containers running"
fi

# Exit with error if any checks failed
if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "✗ Health check failed with $ERRORS errors"
    exit 1
else
    echo ""
    echo "✓ All health checks passed"
    exit 0
fi
```

---

## Script Installation

### Make Scripts Executable

```bash
# VPS scripts
chmod +x deployment/vps/*.sh

# Raspberry Pi scripts
chmod +x deployment/raspberry-pi/*.sh

# Headscale scripts
chmod +x deployment/headscale/*.sh

# Monitoring scripts
chmod +x deployment/monitoring/*.sh

# Maintenance scripts
chmod +x deployment/maintenance/*.sh
```

### Add to PATH (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:$HOME/barcode-central/deployment/vps"
export PATH="$PATH:$HOME/barcode-central/deployment/monitoring"
export PATH="$PATH:$HOME/barcode-central/deployment/maintenance"
```

---

## Usage Examples

### Deploy to VPS

```bash
# Basic deployment
./deployment/vps/deploy-basic.sh

# With Traefik
./deployment/vps/deploy-traefik.sh

# Full stack
./deployment/vps/deploy-full.sh
```

### Setup Raspberry Pi

```bash
# On Raspberry Pi
curl -O https://raw.githubusercontent.com/your-repo/barcode-central/main/deployment/raspberry-pi/setup-print-server.sh
chmod +x setup-print-server.sh
./setup-print-server.sh
```

### Manage Headscale

```bash
# Setup Headscale
./deployment/headscale/setup.sh

# Manage routes
./deployment/headscale/manage-routes.sh
```

### Monitoring

```bash
# Check system status
./deployment/monitoring/system-status.sh

# Run health check
./deployment/maintenance/health-check.sh
```

### Maintenance

```bash
# Cleanup old files
./deployment/maintenance/cleanup.sh

# Update application
./deployment/vps/update.sh
```

---

## Automation with Cron

### VPS Cron Jobs

```bash
# Edit crontab
crontab -e

# Add jobs:
# Backup daily at 2 AM
0 2 * * * cd /path/to/barcode-central && ./scripts/backup.sh

# Health check every 15 minutes
*/15 * * * * cd /path/to/barcode-central && ./deployment/maintenance/health-check.sh

# Cleanup weekly on Sunday at 3 AM
0 3 * * 0 cd /path/to/barcode-central && ./deployment/maintenance/cleanup.sh
```

### Raspberry Pi Cron Jobs

```bash
# Edit crontab
crontab -e

# Add jobs:
# Health check every 15 minutes
*/15 * * * * /usr/local/bin/health-check.sh

# Backup config weekly
0 2 * * 0 /usr/local/bin/backup-config.sh
```

---

## Next Steps

1. Copy scripts to appropriate directories
2. Make scripts executable
3. Test each script in a development environment
4. Customize scripts for your specific needs
5. Set up cron jobs for automation
6. Document any custom modifications

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24