# Raspberry Pi Print Server Setup Guide

Complete guide for setting up Raspberry Pi devices as print servers for distributed Barcode Central deployment.

## Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Initial Setup](#initial-setup)
4. [Tailscale Client Installation](#tailscale-client-installation)
5. [Network Printer Configuration](#network-printer-configuration)
6. [USB Printer Support (CUPS)](#usb-printer-support-cups)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Each Raspberry Pi acts as a **print server gateway** that:
- Connects to the Headscale mesh network via Tailscale
- Advertises local printer subnets to the mesh
- Provides access to both network and USB printers
- Runs minimal services for security and reliability

```
┌─────────────────────────────────────────────┐
│         Raspberry Pi Print Server           │
├─────────────────────────────────────────────┤
│  Tailscale Client (100.64.0.10)            │
│  - Connects to Headscale                    │
│  - Advertises 192.168.1.0/24               │
├─────────────────────────────────────────────┤
│  CUPS (Optional - for USB printers)         │
│  - Exposes USB printers on network          │
│  - Port 631 (IPP)                           │
├─────────────────────────────────────────────┤
│  Local Network (192.168.1.0/24)            │
│  - Zebra ZT230: 192.168.1.100:9100         │
│  - Zebra GK420: 192.168.1.101:9100         │
│  - USB Printer via CUPS                     │
└─────────────────────────────────────────────┘
```

---

## Hardware Requirements

### Minimum Specifications
- **Model**: Raspberry Pi 3B+ or newer
- **RAM**: 1GB (2GB+ recommended)
- **Storage**: 16GB microSD card (Class 10 or better)
- **Network**: Ethernet connection (preferred) or WiFi
- **Power**: Official Raspberry Pi power supply (5V 3A for Pi 4)

### Recommended Setup
- **Model**: Raspberry Pi 4 (4GB RAM)
- **Storage**: 32GB microSD card or USB SSD
- **Network**: Gigabit Ethernet
- **Case**: With cooling (fan or heatsinks)
- **Power**: Official power supply with surge protection

### Optional Accessories
- USB hub (for multiple USB printers)
- UPS/battery backup
- Ethernet cable (Cat6)
- Case with GPIO access

---

## Initial Setup

### 1. Install Raspberry Pi OS

**Download Raspberry Pi Imager:**
- https://www.raspberrypi.com/software/

**Flash OS:**
```bash
# Use Raspberry Pi Imager to flash:
# - OS: Raspberry Pi OS Lite (64-bit) - No desktop needed
# - Configure WiFi/SSH in advanced options
# - Set hostname: warehouse-pi, office-pi, etc.
# - Enable SSH
# - Set username/password
```

**Advanced Options in Imager:**
- Hostname: `warehouse-pi` (or location-specific name)
- Enable SSH: Yes
- Username: `pi`
- Password: Strong password
- WiFi: Configure if needed (Ethernet preferred)
- Locale: Your timezone

### 2. First Boot Configuration

**SSH into the Pi:**
```bash
# From your computer
ssh pi@warehouse-pi.local
# Or use IP address: ssh pi@192.168.1.50
```

**Update System:**
```bash
# Update package lists
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    iptables \
    ca-certificates
```

**Configure Static IP (Optional but Recommended):**
```bash
# Edit dhcpcd.conf
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface eth0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# Restart networking
sudo systemctl restart dhcpcd
```

**Enable IP Forwarding:**
```bash
# Required for subnet routing
sudo nano /etc/sysctl.conf

# Uncomment or add:
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1

# Apply changes
sudo sysctl -p
```

### 3. Security Hardening

**Disable Password SSH (Use Keys):**
```bash
# On your computer, generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy key to Pi
ssh-copy-id pi@warehouse-pi.local

# On Pi, disable password authentication
sudo nano /etc/ssh/sshd_config

# Set these values:
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart ssh
```

**Configure Firewall:**
```bash
# Install UFW
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow Tailscale
sudo ufw allow 41641/udp

# Allow printer ports (if needed from local network)
sudo ufw allow from 192.168.1.0/24 to any port 9100
sudo ufw allow from 192.168.1.0/24 to any port 631

# Enable firewall
sudo ufw enable
```

**Automatic Security Updates:**
```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades

# Configure
sudo dpkg-reconfigure -plow unattended-upgrades

# Enable automatic updates
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Ensure these lines are uncommented:
# Unattended-Upgrade::Automatic-Reboot "true";
# Unattended-Upgrade::Automatic-Reboot-Time "03:00";
```

---

## Tailscale Client Installation

### 1. Install Tailscale

**Official Installation:**
```bash
# Add Tailscale repository
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/bullseye.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list

# Update and install
sudo apt update
sudo apt install -y tailscale

# Verify installation
tailscale version
```

### 2. Connect to Headscale

**Get Pre-Auth Key from VPS:**
```bash
# On your VPS (where Headscale is running)
docker exec headscale headscale preauthkeys create --reusable --expiration 90d

# Copy the generated key
```

**Connect Pi to Headscale:**
```bash
# On Raspberry Pi
sudo tailscale up \
    --login-server=http://headscale.example.com:8080 \
    --authkey=YOUR_PREAUTH_KEY_HERE \
    --advertise-routes=192.168.1.0/24 \
    --accept-routes \
    --hostname=warehouse-pi

# Verify connection
tailscale status
tailscale ip -4
```

**Enable Subnet Routing on Headscale Server:**
```bash
# On VPS
docker exec headscale headscale routes list
docker exec headscale headscale routes enable -r 1  # Enable route ID 1
```

### 3. Configure Tailscale Service

**Enable at Boot:**
```bash
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
```

**Create Systemd Override (Optional):**
```bash
# Create override directory
sudo mkdir -p /etc/systemd/system/tailscaled.service.d

# Create override file
sudo nano /etc/systemd/system/tailscaled.service.d/override.conf

# Add content:
[Service]
Environment="TS_DEBUG_FIREWALL_MODE=auto"
Restart=always
RestartSec=10

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart tailscaled
```

### 4. Verify Connectivity

**Test Mesh Network:**
```bash
# Check Tailscale status
tailscale status

# Ping VPS from Pi
ping -c 4 100.64.0.1

# From VPS, ping Pi
ping -c 4 100.64.0.10

# Test printer access from VPS
telnet 192.168.1.100 9100
```

---

## Network Printer Configuration

### 1. Verify Printer Connectivity

**From Raspberry Pi:**
```bash
# Ping printer
ping -c 4 192.168.1.100

# Test ZPL port
telnet 192.168.1.100 9100

# If telnet works, type:
^XA^FO50,50^A0N,50,50^FDTest^FS^XZ
# Then Ctrl+] and type 'quit'
```

### 2. Configure Printers in Barcode Central

**On VPS, edit printers.json:**
```json
{
  "printers": [
    {
      "id": "warehouse-zebra-zt230",
      "name": "Warehouse Zebra ZT230",
      "ip": "192.168.1.100",
      "port": 9100,
      "dpi": 203,
      "supported_sizes": ["4x6", "4x2"],
      "default_unit": "inches",
      "enabled": true,
      "location": "Warehouse A",
      "description": "Main warehouse printer via Tailscale mesh"
    },
    {
      "id": "warehouse-zebra-gk420",
      "name": "Warehouse Zebra GK420",
      "ip": "192.168.1.101",
      "port": 9100,
      "dpi": 203,
      "supported_sizes": ["4x6"],
      "default_unit": "inches",
      "enabled": true,
      "location": "Warehouse A",
      "description": "Secondary warehouse printer"
    }
  ]
}
```

### 3. Test Printing from VPS

**From Barcode Central container:**
```bash
# Enter container
docker exec -it barcode-central bash

# Test printer connectivity
echo "^XA^FO50,50^A0N,50,50^FDTest Print^FS^XZ" | nc 192.168.1.100 9100

# If successful, printer should print a test label
```

---

## USB Printer Support (CUPS)

### 1. Install CUPS

**Install CUPS and Drivers:**
```bash
# Install CUPS
sudo apt install -y cups cups-client

# Install printer drivers
sudo apt install -y printer-driver-all

# For Zebra printers specifically
sudo apt install -y printer-driver-gutenprint

# Add pi user to lpadmin group
sudo usermod -a -G lpadmin pi
```

### 2. Configure CUPS

**Enable Network Access:**
```bash
# Edit CUPS configuration
sudo nano /etc/cups/cupsd.conf

# Modify these sections:
# Listen on all interfaces
Port 631
Listen /run/cups/cups.sock

# Allow access from local network
<Location />
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.1.0/24
  Allow from 100.64.0.0/10
</Location>

<Location /admin>
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.1.0/24
  Allow from 100.64.0.0/10
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 192.168.1.0/24
  Allow from 100.64.0.0/10
</Location>

# Save and restart CUPS
sudo systemctl restart cups
```

**Enable CUPS Web Interface:**
```bash
# Access CUPS web interface
# From local network: http://192.168.1.50:631
# From Tailscale: http://100.64.0.10:631
```

### 3. Add USB Printer

**Via Web Interface:**
1. Navigate to http://100.64.0.10:631/admin
2. Click "Add Printer"
3. Select USB printer from list
4. Choose driver (or use "Generic" → "Generic Raw Queue")
5. Set printer name: `zebra-usb-01`
6. Check "Share This Printer"
7. Complete setup

**Via Command Line:**
```bash
# List connected USB printers
lpinfo -v

# Add printer (example for Zebra)
sudo lpadmin -p zebra-usb-01 \
    -E \
    -v usb://Zebra/ZT230 \
    -m everywhere \
    -L "Warehouse USB Printer" \
    -o printer-is-shared=true

# Enable printer
sudo cupsenable zebra-usb-01
sudo cupsaccept zebra-usb-01

# Set as default (optional)
sudo lpadmin -d zebra-usb-01

# Test print
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | lp -d zebra-usb-01
```

### 4. Configure Raw Socket for ZPL

**Create Raw Queue:**
```bash
# Add raw queue for ZPL
sudo lpadmin -p zebra-usb-raw \
    -E \
    -v usb://Zebra/ZT230 \
    -m raw \
    -L "Warehouse USB Printer (Raw ZPL)" \
    -o printer-is-shared=true

# This creates a raw socket that accepts ZPL directly
```

**Expose on Network Port:**
```bash
# Install socat for port forwarding
sudo apt install -y socat

# Create systemd service for port forwarding
sudo nano /etc/systemd/system/cups-raw-forward.service

# Add content:
[Unit]
Description=CUPS Raw Port Forwarding
After=cups.service

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP-LISTEN:9100,fork,reuseaddr EXEC:'/usr/bin/lp -d zebra-usb-raw'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable cups-raw-forward
sudo systemctl start cups-raw-forward
```

### 5. Configure in Barcode Central

**Add USB Printer to printers.json:**
```json
{
  "id": "warehouse-zebra-usb",
  "name": "Warehouse Zebra USB",
  "ip": "100.64.0.10",
  "port": 9100,
  "dpi": 203,
  "supported_sizes": ["4x6", "4x2"],
  "default_unit": "inches",
  "enabled": true,
  "location": "Warehouse A",
  "description": "USB printer via CUPS on Raspberry Pi"
}
```

---

## Monitoring & Maintenance

### 1. System Monitoring

**Install Monitoring Tools:**
```bash
# Install monitoring packages
sudo apt install -y \
    sysstat \
    iotop \
    nethogs \
    vnstat

# Enable sysstat
sudo systemctl enable sysstat
sudo systemctl start sysstat
```

**Create Monitoring Script:**
```bash
# Create monitoring script
sudo nano /usr/local/bin/pi-monitor.sh

# Add content:
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
echo ""
echo "=== Network Connections ==="
ss -tuln | grep -E ':(9100|631|41641)'
echo ""
echo "=== CUPS Status ==="
lpstat -t 2>/dev/null || echo "CUPS not installed"

# Make executable
sudo chmod +x /usr/local/bin/pi-monitor.sh

# Run it
/usr/local/bin/pi-monitor.sh
```

### 2. Health Check Script

**Create Health Check:**
```bash
# Create health check script
sudo nano /usr/local/bin/health-check.sh

# Add content:
#!/bin/bash
LOG_FILE="/var/log/pi-health.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check Tailscale
if ! tailscale status &>/dev/null; then
    log_message "ERROR: Tailscale is down"
    sudo systemctl restart tailscaled
else
    log_message "OK: Tailscale is running"
fi

# Check temperature
TEMP=$(vcgencmd measure_temp | grep -o '[0-9.]*')
if (( $(echo "$TEMP > 80" | bc -l) )); then
    log_message "WARNING: High temperature: ${TEMP}°C"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log_message "WARNING: Disk usage at ${DISK_USAGE}%"
fi

# Check printer connectivity
if ! ping -c 1 -W 2 192.168.1.100 &>/dev/null; then
    log_message "WARNING: Cannot reach printer 192.168.1.100"
fi

log_message "Health check completed"

# Make executable
sudo chmod +x /usr/local/bin/health-check.sh
```

**Schedule Health Checks:**
```bash
# Add to crontab
crontab -e

# Add line:
*/15 * * * * /usr/local/bin/health-check.sh
```

### 3. Log Rotation

**Configure Log Rotation:**
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/pi-health

# Add content:
/var/log/pi-health.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 4. Backup Configuration

**Create Backup Script:**
```bash
# Create backup script
sudo nano /usr/local/bin/backup-config.sh

# Add content:
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pi-config-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_FILE" \
    /etc/tailscale \
    /etc/cups \
    /etc/network \
    /etc/dhcpcd.conf \
    /etc/sysctl.conf \
    /home/pi/.ssh

echo "Backup created: $BACKUP_FILE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/pi-config-*.tar.gz | tail -n +11 | xargs -r rm

# Make executable
sudo chmod +x /usr/local/bin/backup-config.sh

# Schedule weekly backups
crontab -e
# Add: 0 2 * * 0 /usr/local/bin/backup-config.sh
```

---

## Troubleshooting

### Common Issues

**1. Tailscale Won't Connect**
```bash
# Check Tailscale status
sudo tailscale status

# Check logs
sudo journalctl -u tailscaled -f

# Restart Tailscale
sudo systemctl restart tailscaled

# Re-authenticate
sudo tailscale up --login-server=http://headscale.example.com:8080
```

**2. Subnet Routes Not Working**
```bash
# On Pi, verify routes are advertised
tailscale status

# On VPS, check routes
docker exec headscale headscale routes list

# Enable routes if needed
docker exec headscale headscale routes enable -r <route-id>

# Verify IP forwarding
sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1
```

**3. Cannot Reach Printers**
```bash
# From Pi, test printer
ping 192.168.1.100
telnet 192.168.1.100 9100

# Check firewall
sudo ufw status

# Check routing
ip route show

# From VPS, test via Tailscale
ping 192.168.1.100
```

**4. CUPS Issues**
```bash
# Check CUPS status
sudo systemctl status cups

# Check CUPS logs
sudo tail -f /var/log/cups/error_log

# Restart CUPS
sudo systemctl restart cups

# Test printer
lpstat -t
```

**5. High Temperature**
```bash
# Check temperature
vcgencmd measure_temp

# If over 80°C:
# - Ensure proper ventilation
# - Add heatsinks or fan
# - Reduce CPU frequency (if needed)
```

### Diagnostic Commands

```bash
# System information
uname -a
cat /etc/os-release

# Network interfaces
ip addr show
ip route show

# Tailscale diagnostics
tailscale status
tailscale netcheck
tailscale ping 100.64.0.1

# CUPS diagnostics
lpstat -t
lpstat -p
lpinfo -v

# System resources
htop
df -h
free -h
vcgencmd measure_temp

# Network connections
ss -tuln
netstat -tuln

# Logs
sudo journalctl -u tailscaled -f
sudo journalctl -u cups -f
tail -f /var/log/syslog
```

---

## Quick Reference

### Essential Commands

```bash
# Tailscale
sudo tailscale status
sudo tailscale up --login-server=http://headscale.example.com:8080
sudo tailscale down
sudo systemctl restart tailscaled

# CUPS
lpstat -t
sudo systemctl restart cups
lpadmin -p printer-name -E

# System
sudo reboot
sudo shutdown -h now
vcgencmd measure_temp
df -h
free -h

# Monitoring
/usr/local/bin/pi-monitor.sh
/usr/local/bin/health-check.sh
tail -f /var/log/pi-health.log
```

### Configuration Files

```
/etc/tailscale/          # Tailscale config
/etc/cups/cupsd.conf     # CUPS configuration
/etc/dhcpcd.conf         # Network configuration
/etc/sysctl.conf         # Kernel parameters
/etc/ufw/                # Firewall rules
```

---

## Next Steps

1. Complete initial setup for each Raspberry Pi
2. Install and configure Tailscale
3. Test printer connectivity
4. Set up CUPS if using USB printers
5. Configure monitoring and backups
6. Document location-specific configurations

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24  
**Tested On**: Raspberry Pi 4 Model B (4GB), Raspberry Pi OS Lite (64-bit)