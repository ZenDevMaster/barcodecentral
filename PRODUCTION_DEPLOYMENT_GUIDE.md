# Production Deployment Guide - Complete Walkthrough

Step-by-step guide for deploying Barcode Central in production with distributed printer support.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: VPS Setup](#phase-1-vps-setup)
4. [Phase 2: Application Deployment](#phase-2-application-deployment)
5. [Phase 3: Headscale Mesh Network](#phase-3-headscale-mesh-network)
6. [Phase 4: Raspberry Pi Print Servers](#phase-4-raspberry-pi-print-servers)
7. [Phase 5: Testing & Verification](#phase-5-testing--verification)
8. [Phase 6: Production Hardening](#phase-6-production-hardening)
9. [Troubleshooting](#troubleshooting)

---

## Deployment Overview

This guide covers deploying Barcode Central with:
- **VPS**: Central application server with public HTTPS access
- **Traefik**: Automatic HTTPS with Let's Encrypt (optional)
- **Headscale**: Self-hosted mesh network coordination
- **Raspberry Pi**: Print servers at multiple locations
- **Distributed Printers**: Network and USB printers worldwide

**Estimated Time**: 4-6 hours for complete setup

---

## Prerequisites

### Required Resources

**VPS/Cloud Server:**
- 2+ vCPU
- 4GB+ RAM
- 20GB+ storage
- Ubuntu 22.04 LTS or similar
- Public IP address
- Root or sudo access

**Domain Name:**
- Domain for application (e.g., `print.example.com`)
- Subdomain for Headscale (e.g., `headscale.example.com`)
- DNS access to create A records

**Raspberry Pi (per location):**
- Raspberry Pi 4 (4GB RAM recommended)
- 32GB microSD card
- Ethernet connection
- Power supply

**Network Printers:**
- Zebra or compatible ZPL printers
- Network connectivity (TCP/IP)
- Known IP addresses and ports

### Required Knowledge

- Basic Linux command line
- Docker and Docker Compose
- Networking concepts (IP addresses, subnets, ports)
- SSH access and key management

### Tools Needed

- SSH client
- Text editor (nano, vim, or VS Code with Remote SSH)
- Web browser
- Terminal/command prompt

---

## Phase 1: VPS Setup

### Step 1.1: Initial Server Configuration

**Connect to VPS:**
```bash
ssh root@your-vps-ip
```

**Update System:**
```bash
apt update && apt upgrade -y
```

**Create Non-Root User:**
```bash
adduser barcode
usermod -aG sudo barcode
```

**Configure SSH Keys:**
```bash
# On your local machine
ssh-keygen -t ed25519 -C "barcode-central"
ssh-copy-id barcode@your-vps-ip

# On VPS, disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

**Configure Firewall:**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 41641/udp   # Headscale/WireGuard
sudo ufw enable
```

### Step 1.2: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker barcode

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Log out and back in for group changes
exit
ssh barcode@your-vps-ip
```

### Step 1.3: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/ZenDevMaster/barcodecentral.git
cd barcodecentral

# Or download and extract
wget https://github.com/ZenDevMaster/barcodecentral/archive/refs/heads/main.zip
unzip main.zip
cd barcodecentral-main
```

### Step 1.4: Configure DNS

**Create DNS A Records:**
```
Type  Name        Value           TTL
A     print       your-vps-ip     300
A     headscale   your-vps-ip     300
```

**Verify DNS Propagation:**
```bash
dig print.example.com +short
dig headscale.example.com +short
```

---

## Phase 2: Application Deployment

### Step 2.1: Choose Deployment Scenario

**Option A: Basic (No Traefik, No Headscale)**
- Simple deployment
- HTTP only
- Local printers only

**Option B: With Traefik (Recommended)**
- Automatic HTTPS
- Professional setup
- Still local printers only

**Option C: Full Stack (Complete Solution)**
- Traefik + HTTPS
- Headscale mesh network
- Distributed printers

**We'll proceed with Option C (Full Stack)**

### Step 2.2: Configure Environment Variables

**Create Main Environment File:**
```bash
cp .env.production.example .env
nano .env
```

**Edit `.env`:**
```env
# Security - CHANGE THESE!
SECRET_KEY=<generate-with-command-below>
LOGIN_USER=admin
LOGIN_PASSWORD=<your-secure-password>

# Application
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO

# Session
SESSION_COOKIE_SECURE=true
```

**Generate Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Create Traefik Environment File:**
```bash
cp .env.traefik.example .env.traefik
nano .env.traefik
```

**Edit `.env.traefik`:**
```env
DOMAIN=print.example.com
ACME_EMAIL=admin@example.com
```

**Create Headscale Environment File:**
```bash
cp .env.headscale.example .env.headscale
nano .env.headscale
```

**Edit `.env.headscale`:**
```env
HEADSCALE_SERVER_URL=http://headscale.example.com:8080
# TAILSCALE_AUTHKEY will be generated later
```

**Secure Environment Files:**
```bash
chmod 600 .env .env.traefik .env.headscale
```

### Step 2.3: Configure Headscale

**Create Configuration Directory:**
```bash
mkdir -p headscale/config headscale/data
```

**Create Headscale Config:**
```bash
nano headscale/config/config.yaml
```

**Add Configuration:**
```yaml
server_url: http://headscale.example.com:8080
listen_addr: 0.0.0.0:8080
metrics_listen_addr: 0.0.0.0:9090

private_key_path: /var/lib/headscale/private.key
noise:
  private_key_path: /var/lib/headscale/noise_private.key

ip_prefixes:
  - 100.64.0.0/10

db_type: sqlite3
db_path: /var/lib/headscale/db.sqlite

# DNS configuration (v0.27.1+ format)
dns:
  magic_dns: true
  base_domain: headscale.local
  override_local_dns: true
  nameservers:
    global:
      - 1.1.1.1
      - 8.8.8.8

# ACL policy (v0.27.1+ format)
policy:
  path: /etc/headscale/acl.json

derp:
  server:
    enabled: false
  urls:
    - https://controlplane.tailscale.com/derpmap/default

log:
  level: info
  format: text
```

**Create ACL Policy:**
```bash
nano headscale/config/acl.json
```

**Add ACL Configuration:**
```json
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
```

### Step 2.4: Deploy Full Stack

**Create Required Directories:**
```bash
mkdir -p logs previews letsencrypt traefik-logs tailscale/state
touch history.json printers.json
```

**Deploy:**
```bash
docker compose -f docker-compose.full.yml up -d --build
```

**Monitor Deployment:**
```bash
docker compose -f docker-compose.full.yml logs -f
```

**Wait for Services to Start (2-3 minutes)**

### Step 2.5: Generate Tailscale Auth Key

**Create Headscale Namespace:**
```bash
docker exec headscale headscale namespaces create default
```

**Generate Pre-Auth Key:**
```bash
docker exec headscale headscale preauthkeys create --reusable --expiration 90d --namespace default
```

**Copy the generated key and add to `.env.headscale`:**
```bash
nano .env.headscale
# Add: TAILSCALE_AUTHKEY=<your-key-here>
```

**Restart Application Containers:**
```bash
docker compose -f docker-compose.full.yml restart app tailscale
```

### Step 2.6: Verify Deployment

**Check Container Status:**
```bash
docker compose -f docker-compose.full.yml ps
```

**Test Application Health:**
```bash
curl http://localhost:5000/api/health
```

**Test HTTPS (may take a few minutes for certificate):**
```bash
curl https://print.example.com/api/health
```

**Access Web Interface:**
- Open browser to: `https://print.example.com`
- Login with credentials from `.env`

---

## Phase 3: Headscale Mesh Network

### Step 3.1: Verify Headscale

**Check Headscale Status:**
```bash
docker exec headscale headscale nodes list
```

**You should see the barcode-central-server node**

**Check Routes:**
```bash
docker exec headscale headscale routes list
```

### Step 3.2: Configure Headscale Access

**Access Headscale Web Interface:**
- URL: `https://headscale.example.com`
- Or: `http://your-vps-ip:8080`

**Verify API Access:**
```bash
curl http://localhost:8080/health
```

---

## Phase 4: Raspberry Pi Print Servers

### Step 4.1: Prepare Raspberry Pi

**Flash Raspberry Pi OS:**
1. Download Raspberry Pi Imager
2. Select "Raspberry Pi OS Lite (64-bit)"
3. Configure in advanced options:
   - Hostname: `warehouse-pi` (or location name)
   - Enable SSH
   - Set username: `pi`
   - Set password
   - Configure WiFi (if needed)
   - Set timezone

**Boot and Connect:**
```bash
ssh pi@warehouse-pi.local
```

### Step 4.2: Run Automated Setup

**Download Setup Script:**
```bash
curl -O https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/deployment/raspberry-pi/setup-print-server.sh
chmod +x setup-print-server.sh
```

**Run Setup:**
```bash
./setup-print-server.sh
```

**Provide Information When Prompted:**
- Location name: `warehouse`
- Headscale URL: `http://headscale.example.com:8080`
- Pre-auth key: (from earlier step)
- Local subnet: `192.168.1.0/24`

**Wait for Setup to Complete (5-10 minutes)**

### Step 4.3: Enable Subnet Routes

**On VPS, list routes:**
```bash
docker exec headscale headscale routes list
```

**Enable the route for your Raspberry Pi:**
```bash
docker exec headscale headscale routes enable -r <route-id>
```

### Step 4.4: Verify Connectivity

**From VPS, ping Raspberry Pi:**
```bash
# Get Pi's Tailscale IP
docker exec headscale headscale nodes list

# Ping it
docker exec -it barcode-central ping 100.64.0.10
```

**From VPS, test printer access:**
```bash
docker exec -it barcode-central ping 192.168.1.100
docker exec -it barcode-central bash
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | nc 192.168.1.100 9100
exit
```

### Step 4.5: Configure USB Printers (Optional)

**If you have USB printers, install CUPS:**
```bash
# On Raspberry Pi
curl -O https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/deployment/raspberry-pi/install-cups.sh
chmod +x install-cups.sh
./install-cups.sh
```

**Access CUPS Web Interface:**
- URL: `http://100.64.0.10:631` (via Tailscale)
- Add USB printers through the web interface

### Step 4.6: Repeat for Additional Locations

**For each additional location:**
1. Prepare new Raspberry Pi
2. Run setup script with location-specific values
3. Enable subnet routes in Headscale
4. Verify connectivity
5. Test printer access

---

## Phase 5: Testing & Verification

### Step 5.1: Configure Printers

**Edit printers.json on VPS:**
```bash
nano printers.json
```

**Add Your Printers:**
```json
{
  "printers": [
    {
      "id": "warehouse-zebra-01",
      "name": "Warehouse Zebra ZT230",
      "ip": "192.168.1.100",
      "port": 9100,
      "dpi": 203,
      "supported_sizes": ["4x6", "4x2"],
      "default_unit": "inches",
      "enabled": true,
      "location": "Warehouse A",
      "description": "Main warehouse printer via Tailscale"
    },
    {
      "id": "office-zebra-01",
      "name": "Office Zebra GK420",
      "ip": "10.0.0.100",
      "port": 9100,
      "dpi": 203,
      "supported_sizes": ["4x6"],
      "default_unit": "inches",
      "enabled": true,
      "location": "Office B",
      "description": "Office printer via Tailscale"
    }
  ]
}
```

**Restart Application:**
```bash
docker compose -f docker-compose.full.yml restart app
```

### Step 5.2: Test Printing

**Via Web Interface:**
1. Login to `https://print.example.com`
2. Go to Printers page
3. Test each printer
4. Verify test labels print successfully

**Via API:**
```bash
# Test printer connectivity
curl -X POST https://print.example.com/api/printers/warehouse-zebra-01/test \
  -H "Content-Type: application/json" \
  -u admin:your-password
```

### Step 5.3: Test Label Printing

**Create Test Print Job:**
1. Go to Print page
2. Select template
3. Fill in variables
4. Select printer
5. Generate preview
6. Print label
7. Verify label prints correctly

### Step 5.4: Monitor System

**Check Logs:**
```bash
# Application logs
docker compose -f docker-compose.full.yml logs -f app

# Headscale logs
docker compose -f docker-compose.full.yml logs -f headscale

# Traefik logs
docker compose -f docker-compose.full.yml logs -f traefik
```

**Check Metrics:**
```bash
# Container stats
docker stats

# Disk usage
df -h

# Memory usage
free -h
```

---

## Phase 6: Production Hardening

### Step 6.1: Security Checklist

**Application Security:**
- [x] Changed default LOGIN_USER and LOGIN_PASSWORD
- [x] Generated secure SECRET_KEY
- [x] Set FLASK_ENV=production
- [x] Set FLASK_DEBUG=0
- [x] Enabled HTTPS via Traefik
- [x] Configured firewall rules

**Server Security:**
- [x] Disabled SSH password authentication
- [x] Using SSH keys only
- [x] Configured UFW firewall
- [x] Running containers as non-root
- [x] Secured environment files (chmod 600)

**Network Security:**
- [x] Headscale ACLs configured
- [x] Subnet routing limited to printer networks
- [x] Raspberry Pis hardened
- [x] Firewall rules on all devices

### Step 6.2: Setup Monitoring

**Install Monitoring Stack (Optional):**
```bash
docker compose -f docker-compose.monitoring.yml up -d
```

**Access Grafana:**
- URL: `http://your-vps-ip:3000`
- Default login: admin/admin
- Change password on first login

**Configure Alerts:**
- Set up email notifications
- Configure alert rules for:
  - Application down
  - High error rate
  - Disk space low
  - Memory usage high

### Step 6.3: Setup Automated Backups

**Configure Backup Cron Job:**
```bash
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /home/barcode/barcodecentral && ./scripts/backup.sh

# Add weekly cleanup on Sunday at 3 AM
0 3 * * 0 cd /home/barcode/barcodecentral && ./deployment/maintenance/cleanup.sh
```

**Test Backup:**
```bash
./scripts/backup.sh
ls -lh backups/
```

**Test Restore:**
```bash
./scripts/restore.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

### Step 6.4: Setup Health Monitoring

**Create Health Check Cron:**
```bash
crontab -e

# Add health check every 15 minutes
*/15 * * * * cd /home/barcode/barcodecentral && ./deployment/maintenance/health-check.sh
```

### Step 6.5: Document Your Setup

**Create Local Documentation:**
```bash
nano PRODUCTION_NOTES.md
```

**Document:**
- Server IP addresses
- Domain names
- Raspberry Pi locations and IPs
- Printer IP addresses
- Network topology
- Custom configurations
- Emergency contacts
- Backup locations

---

## Troubleshooting

### Common Issues

**1. Cannot Access Application via HTTPS**

**Symptoms:** Browser shows "Connection refused" or certificate error

**Solutions:**
```bash
# Check Traefik logs
docker compose -f docker-compose.full.yml logs traefik

# Verify DNS
dig print.example.com +short

# Check certificate status
docker compose -f docker-compose.full.yml exec traefik cat /letsencrypt/acme.json

# Wait for certificate (can take 5-10 minutes)
# Check Traefik dashboard (if enabled)
```

**2. Cannot Reach Printers**

**Symptoms:** Print jobs fail, "Connection refused" errors

**Solutions:**
```bash
# From VPS, test Tailscale connectivity
docker exec -it barcode-central ping 100.64.0.10

# Test printer directly
docker exec -it barcode-central ping 192.168.1.100
docker exec -it barcode-central telnet 192.168.1.100 9100

# Check Headscale routes
docker exec headscale headscale routes list

# Enable routes if needed
docker exec headscale headscale routes enable -r <route-id>

# On Raspberry Pi, check Tailscale
ssh pi@warehouse-pi
tailscale status
```

**3. Raspberry Pi Not Connecting to Headscale**

**Symptoms:** Pi doesn't appear in `headscale nodes list`

**Solutions:**
```bash
# On Raspberry Pi
sudo tailscale status
sudo journalctl -u tailscaled -f

# Restart Tailscale
sudo systemctl restart tailscaled

# Re-authenticate
sudo tailscale up --login-server=http://headscale.example.com:8080 --authkey=<new-key>

# On VPS, generate new key if needed
docker exec headscale headscale preauthkeys create --reusable --expiration 90d
```

**4. High Memory Usage**

**Symptoms:** System slow, OOM errors

**Solutions:**
```bash
# Check memory
free -h
docker stats

# Restart containers
docker compose -f docker-compose.full.yml restart

# Add swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**5. Disk Space Full**

**Symptoms:** Cannot write files, application errors

**Solutions:**
```bash
# Check disk usage
df -h
du -sh /home/barcode/barcodecentral/*

# Run cleanup
./deployment/maintenance/cleanup.sh

# Clean Docker
docker system prune -a

# Remove old backups
ls -t backups/ | tail -n +6 | xargs -r rm
```

### Getting Help

**Check Logs:**
```bash
# All services
docker compose -f docker-compose.full.yml logs -f

# Specific service
docker compose -f docker-compose.full.yml logs -f app

# System logs
sudo journalctl -xe
```

**Run Diagnostics:**
```bash
# System status
./deployment/monitoring/system-status.sh

# Health check
./deployment/maintenance/health-check.sh
```

**Community Support:**
- GitHub Issues: https://github.com/ZenDevMaster/barcodecentral/issues
- Documentation: Check all .md files in repository
- Logs: Always include relevant logs when asking for help

---

## Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] All printers configured and tested
- [ ] Raspberry Pis connected to mesh network
- [ ] Subnet routes enabled in Headscale
- [ ] Test print jobs successful from all locations
- [ ] Automated backups configured
- [ ] Health monitoring setup
- [ ] Monitoring/alerting configured (if using)
- [ ] Documentation updated with custom configurations
- [ ] Team trained on system usage
- [ ] Emergency procedures documented
- [ ] Backup restore tested

---

## Maintenance Schedule

**Daily:**
- Automated backups (2 AM)
- Health checks (every 15 minutes)

**Weekly:**
- Review logs for errors
- Check disk space
- Verify all printers operational
- Run cleanup script (Sunday 3 AM)

**Monthly:**
- Update system packages
- Review and rotate logs
- Test backup restore procedure
- Review security settings
- Update documentation

**Quarterly:**
- Review and update ACL policies
- Audit user access
- Performance optimization
- Capacity planning

---

## Next Steps

1. **Optimize Performance**
   - Tune Gunicorn workers
   - Configure caching if needed
   - Optimize database queries

2. **Scale Horizontally**
   - Add more Raspberry Pis
   - Deploy to additional locations
   - Load balance if needed

3. **Enhance Monitoring**
   - Set up Prometheus + Grafana
   - Configure detailed alerts
   - Create custom dashboards

4. **Improve Reliability**
   - Set up redundancy
   - Configure failover
   - Implement high availability

---

**Congratulations!** You now have a production-ready Barcode Central deployment with distributed printer support.

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24  
**Deployment Time**: 4-6 hours  
**Difficulty**: Intermediate to Advanced