#!/bin/bash
# Raspberry Pi Print Server Setup
# Quick setup script for Raspberry Pi to connect to Headscale mesh network

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    print_warning "This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? [y/N]: " continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

clear
print_header "Raspberry Pi Print Server Setup"
echo "This script will configure your Raspberry Pi as a print server"
echo "for Barcode Central with Headscale mesh networking."
echo ""
echo "Press Enter to continue..."
read

# Gather configuration
clear
print_header "Configuration"

read -p "Location name (e.g., warehouse, office, remote): " LOCATION
while [ -z "$LOCATION" ]; do
    print_error "Location cannot be empty"
    read -p "Location name: " LOCATION
done

HOSTNAME="${LOCATION}-pi"
print_info "Hostname will be set to: $HOSTNAME"
echo ""

read -p "Headscale server URL (e.g., http://headscale.example.com:8080): " HEADSCALE_URL
while [ -z "$HEADSCALE_URL" ]; do
    print_error "Headscale URL cannot be empty"
    read -p "Headscale server URL: " HEADSCALE_URL
done

echo ""
read -p "Tailscale pre-auth key: " AUTH_KEY
while [ -z "$AUTH_KEY" ]; then
    print_error "Auth key cannot be empty"
    print_info "Generate one on your VPS with: ./scripts/generate-authkey.sh"
    read -p "Tailscale pre-auth key: " AUTH_KEY
done

echo ""
read -p "Local subnet to advertise (e.g., 192.168.1.0/24): " SUBNET
while [ -z "$SUBNET" ]; then
    print_error "Subnet cannot be empty"
    read -p "Local subnet: " SUBNET
done

# Confirm configuration
echo ""
print_header "Review Configuration"
echo "Location:        $LOCATION"
echo "Hostname:        $HOSTNAME"
echo "Headscale URL:   $HEADSCALE_URL"
echo "Auth Key:        ${AUTH_KEY:0:20}..."
echo "Subnet:          $SUBNET"
echo ""
read -p "Is this correct? [Y/n]: " confirm

if [[ "$confirm" =~ ^[Nn]$ ]]; then
    print_error "Setup cancelled"
    exit 1
fi

# Start installation
clear
print_header "Installing..."

# Update system
print_info "Updating system packages..."
sudo apt update
sudo apt upgrade -y
print_success "System updated"

# Install essential packages
print_info "Installing essential packages..."
sudo apt install -y curl wget git vim htop net-tools iptables ca-certificates ufw
print_success "Essential packages installed"

# Set hostname
print_info "Setting hostname to $HOSTNAME..."
sudo hostnamectl set-hostname $HOSTNAME
if ! grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts; then
    echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts
fi
print_success "Hostname set"

# Enable IP forwarding
print_info "Enabling IP forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p >/dev/null 2>&1
print_success "IP forwarding enabled"

# Configure firewall
print_info "Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 41641/udp
print_success "Firewall configured"

# Install Tailscale
print_info "Installing Tailscale..."
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt update
sudo apt install -y tailscale
print_success "Tailscale installed"

# Connect to Headscale
print_info "Connecting to Headscale mesh network..."
sudo tailscale up \
    --login-server="$HEADSCALE_URL" \
    --authkey="$AUTH_KEY" \
    --advertise-routes="$SUBNET" \
    --accept-routes \
    --hostname="$HOSTNAME"

if [ $? -eq 0 ]; then
    print_success "Connected to Headscale"
else
    print_error "Failed to connect to Headscale"
    echo "Check the Headscale URL and auth key"
    exit 1
fi

# Enable Tailscale at boot
sudo systemctl enable tailscaled
print_success "Tailscale enabled at boot"

# Create monitoring script
print_info "Creating monitoring script..."
sudo tee /usr/local/bin/pi-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== Raspberry Pi Print Server Status ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Temperature: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo ""
echo "=== Tailscale Status ==="
sudo tailscale status
echo ""
echo "=== Network Info ==="
echo "Tailscale IP: $(sudo tailscale ip -4 2>/dev/null || echo 'Not connected')"
echo "Local IP: $(hostname -I | awk '{print $1}')"
EOF

sudo chmod +x /usr/local/bin/pi-monitor.sh
print_success "Monitoring script created"

# Create health check script
print_info "Creating health check script..."
sudo tee /usr/local/bin/health-check.sh > /dev/null <<'EOF'
#!/bin/bash
LOG_FILE="/var/log/pi-health.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a "$LOG_FILE" >/dev/null
}

# Check Tailscale
if ! sudo tailscale status &>/dev/null; then
    log_message "ERROR: Tailscale is down"
    sudo systemctl restart tailscaled
else
    log_message "OK: Tailscale is running"
fi

# Check temperature
TEMP=$(vcgencmd measure_temp 2>/dev/null | grep -o '[0-9.]*' || echo "0")
if (( $(echo "$TEMP > 80" | bc -l 2>/dev/null || echo "0") )); then
    log_message "WARNING: High temperature: ${TEMP}°C"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log_message "WARNING: Disk usage at ${DISK_USAGE}%"
fi

log_message "Health check completed"
EOF

sudo chmod +x /usr/local/bin/health-check.sh
print_success "Health check script created"

# Schedule health checks
print_info "Scheduling health checks..."
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/health-check.sh") | crontab -
print_success "Health checks scheduled (every 15 minutes)"

# Get Tailscale IP
TAILSCALE_IP=$(sudo tailscale ip -4 2>/dev/null || echo "unknown")

# Setup complete
clear
print_header "Setup Complete!"
echo ""
print_success "Raspberry Pi print server configured successfully!"
echo ""
echo "Configuration:"
echo "  Hostname:      $HOSTNAME"
echo "  Location:      $LOCATION"
echo "  Tailscale IP:  $TAILSCALE_IP"
echo "  Local IP:      $(hostname -I | awk '{print $1}')"
echo "  Subnet:        $SUBNET"
echo ""
print_warning "IMPORTANT: Next steps on your VPS:"
echo ""
echo "1. Enable subnet routes:"
echo "   ./scripts/enable-routes.sh"
echo ""
echo "2. Verify connectivity from VPS:"
echo "   docker exec -it barcode-central ping $TAILSCALE_IP"
echo "   docker exec -it barcode-central ping <printer-ip>"
echo ""
echo "3. Add printers to Barcode Central:"
echo "   Edit printers.json with your printer IPs from subnet $SUBNET"
echo ""
print_info "Useful commands:"
echo "  sudo tailscale status       - Check Tailscale status"
echo "  /usr/local/bin/pi-monitor.sh - View system status"
echo "  sudo journalctl -u tailscaled -f - View Tailscale logs"
echo ""
print_success "Setup complete! 🎉"