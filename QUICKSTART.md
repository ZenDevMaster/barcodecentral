# Barcode Central - Quick Start Guide

Get up and running with Barcode Central in minutes with our **interactive setup wizard**!

---

## Prerequisites

Before you begin, ensure you have:

### For Docker Deployment (Recommended)
- **Docker** 20.10 or higher
- **Docker Compose** 2.0 or higher
- **Git** (to clone the repository)
- 2GB RAM minimum (4GB for distributed setup)
- 1GB disk space

### For Distributed Printer Setup (Optional)
- **Raspberry Pi** 3B+ or newer (one per location)
- **Network printers** with TCP/IP connectivity (port 9100)
- **Domain name** (for HTTPS with Traefik)

---

## 🚀 Quick Start with Interactive Setup (2 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/ZenDevMaster/barcodecentral.git
cd barcodecentral
```

### Step 2: Run Setup Wizard

```bash
./setup.sh
```

The interactive wizard will guide you through:
- ✅ Deployment type selection (Basic/Production/Distributed)
- ✅ Domain configuration (if using Traefik)
- ✅ Headscale mesh network setup (if distributed)
- ✅ Admin credentials
- ✅ Network ports
- ✅ Automatic file generation

**That's it!** The wizard creates all configuration files for you.

### Step 3: Deploy

```bash
docker compose up -d
```

### Step 4: Configure Firewall (if needed)

```bash
./scripts/configure-firewall.sh
```

### Step 5: Access the Application

**Basic deployment:**
```
http://localhost:5000
```

**Production deployment (with Traefik):**
```
https://your-domain.com
```

**Login with credentials from setup wizard**

### Step 6: Verify Deployment

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Check health
curl http://localhost:5000/api/health
```

---

## 🌐 Distributed Printer Setup (Optional)

If you chose "Distributed" deployment, set up Raspberry Pi print servers:

### On VPS: Generate Auth Key

```bash
./scripts/generate-authkey.sh
```

Copy the generated key.

### On Raspberry Pi: One-Liner Setup

```bash
curl -sSL https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh | bash
```

Or download and run:

```bash
wget https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh
chmod +x raspberry-pi-setup.sh
./raspberry-pi-setup.sh
```

Enter the auth key when prompted.

### On VPS: Enable Routes

```bash
./scripts/enable-routes.sh
```

Select option 1 to enable all routes.

### Verify Connectivity

```bash
# From VPS, ping Raspberry Pi
docker exec -it barcode-central ping 100.64.0.10

# Test printer access
docker exec -it barcode-central ping 192.168.1.100
```

---

## 📋 Manual Setup (Alternative)

If you prefer manual configuration:

### Step 1: Clone Repository

```bash
git clone https://github.com/ZenDevMaster/barcodecentral.git
cd barcodecentral
```

### Step 2: Create Environment File

```bash
# Copy example (blocked by .rooignore, create manually)
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
LOGIN_USER=admin
LOGIN_PASSWORD=your-secure-password
LOG_LEVEL=INFO
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
EOF
```

### Step 3: Create Directories

```bash
mkdir -p logs previews
touch history.json printers.json
```

### Step 4: Deploy

```bash
docker compose up -d --build
```

---

## Quick Start for Development (10 Minutes)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd app.barcodecentral
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows
```

### Step 3: Install Dependencies

```bash
# Install application dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-test.txt
```

### Step 4: Configure Environment

```bash
# Copy the development environment template
cp .env.example .env

# Edit the configuration
nano .env
```

**Development Configuration:**
```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
LOGIN_USER=admin
LOGIN_PASSWORD=admin
```

### Step 5: Run Development Server

```bash
# Make the script executable
chmod +x run_dev.sh

# Run the development server
./run_dev.sh
```

**Or run directly:**
```bash
python app.py
```

### Step 6: Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

**Login with:**
- Username: `admin`
- Password: `admin`

---

## First Steps After Installation

### 1. Create Your First Template

1. **Navigate to Dashboard** after logging in
2. **Click "Create New Template"**
3. **Enter template details:**
   - Name: `My First Label`
   - Description: `Test label template`
   - Label Size: `4x2` (4 inches wide, 2 inches tall)
4. **Add ZPL code:**
   ```zpl
   ^XA
   ^FO50,50^A0N,50,50^FDHello World!^FS
   ^FO50,120^BY3^BCN,100,Y,N,N^FD123456789^FS
   ^XZ
   ```
5. **Click "Save Template"**

### 2. Add Your First Printer

1. **Navigate to "Printers" section**
2. **Click "Add Printer"**
3. **Enter printer details:**
   - Name: `Warehouse Printer`
   - IP Address: `192.168.1.100` (your printer's IP)
   - Port: `9100` (default Zebra port)
   - Description: `Main warehouse label printer`
4. **Click "Test Connection"** to verify
5. **Click "Save Printer"**

### 3. Print Your First Label

1. **Navigate to "Print Label" section**
2. **Select your template** from dropdown
3. **Select your printer** from dropdown
4. **Enter quantity** (default: 1)
5. **Click "Generate Preview"** to see how it will look
6. **Review the preview**
7. **Click "Print"** to send to printer

### 4. View Print History

1. **Navigate to "History" page**
2. **View all your print jobs**
3. **Use search to filter** by template, printer, or date
4. **Click "Reprint"** to print again with same data
5. **Click "Export"** to download history data

---

## Common Tasks

### Creating a Template with Variables

Templates support Jinja2 variables for dynamic content:

```zpl
^XA
^FO50,50^A0N,50,50^FD{{ product_name }}^FS
^FO50,120^BY3^BCN,100,Y,N,N^FD{{ barcode }}^FS
^FO50,240^A0N,30,30^FDPrice: ${{ price }}^FS
^XZ
```

**When printing, you'll be prompted for:**
- `product_name`
- `barcode`
- `price`

### Testing Printer Connectivity

```bash
# From command line
telnet <printer-ip> 9100

# Or use netcat
nc -zv <printer-ip> 9100

# Or ping
ping <printer-ip>
```

### Viewing Logs

**Docker deployment:**
```bash
# Application logs
docker-compose logs -f app

# Or view log file
docker-compose exec app tail -f logs/app.log
```

**Development deployment:**
```bash
# View log file
tail -f logs/app.log
```

### Backing Up Data

```bash
# Create backup
./scripts/backup.sh

# Backups saved to: backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

### Restoring from Backup

```bash
# Restore from backup
./scripts/restore.sh backups/backup_20240101_120000.tar.gz
```

### Managing Headscale Routes

```bash
# List and enable routes
./scripts/enable-routes.sh

# Generate new auth key
./scripts/generate-authkey.sh

# Configure firewall
./scripts/configure-firewall.sh
```

---

## Troubleshooting

### Application Won't Start

**Check logs:**
```bash
# Docker
docker-compose logs app

# Development
cat logs/app.log
```

**Common issues:**
- `.env` file missing → Copy from `.env.example`
- Port 5000 already in use → Change port in `docker-compose.yml`
- Permission denied → Check file permissions

### Can't Connect to Printer

**Verify network connectivity:**
```bash
# Ping printer
ping <printer-ip>

# Test port
telnet <printer-ip> 9100
```

**Common issues:**
- Wrong IP address → Verify printer IP
- Firewall blocking → Check firewall rules
- Printer offline → Check printer power and network
- Wrong port → Zebra printers typically use port 9100

### Preview Generation Fails

**Common issues:**
- No internet connection → Labelary API requires internet
- Invalid ZPL syntax → Check ZPL code
- Unsupported label size → Use standard sizes (4x2, 4x6, etc.)

**Check preview directory:**
```bash
ls -la previews/
```

### Login Issues

**Reset credentials:**
1. Edit `.env` file
2. Change `LOGIN_USER` and `LOGIN_PASSWORD`
3. Restart application:
   ```bash
   # Docker
   docker-compose restart
   
   # Development
   # Stop and restart run_dev.sh
   ```

### Docker Container Issues

**Container won't start:**
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs --tail=100 app

# Rebuild container
docker-compose down
docker-compose up -d --build
```

**Container keeps restarting:**
```bash
# Check health status
docker inspect barcode-central | grep -A 10 Health

# View health check logs
docker-compose logs app | grep health
```

---

## Next Steps

### Learn More
- Read the [full documentation](README.md)
- Review [API documentation](roo-docs/endpoints.md)
- Check [architecture guide](roo-docs/architecture.md)
- See [deployment guide](DEPLOYMENT.md)

### Customize
- Create custom templates for your labels
- Configure multiple printers
- Set up automated backups
- Configure reverse proxy (Nginx)
- Set up HTTPS

### Advanced Usage
- Integrate with your existing systems via API
- Create custom scripts for bulk printing
- Set up monitoring and alerting
- Configure log rotation
- Optimize performance

---

## Getting Help

### Documentation
- **Main README:** [`README.md`](README.md:1)
- **API Reference:** [`roo-docs/endpoints.md`](roo-docs/endpoints.md:1)
- **Architecture:** [`roo-docs/architecture.md`](roo-docs/architecture.md:1)
- **Deployment:** [`DEPLOYMENT.md`](DEPLOYMENT.md:1)

### Troubleshooting
- Check application logs: `logs/app.log`
- Check Docker logs: `docker-compose logs -f`
- Review [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)
- Check [known limitations](LIMITATIONS.md)

### Support
- Review existing documentation
- Check logs for error messages
- Verify configuration files
- Test network connectivity

---

## Quick Reference

### Essential Commands

**Setup:**
```bash
# Interactive setup wizard
./setup.sh

# Configure firewall
./scripts/configure-firewall.sh

# Generate Headscale auth key
./scripts/generate-authkey.sh

# Enable subnet routes
./scripts/enable-routes.sh
```

**Docker:**
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Logs
docker compose logs -f

# Status
docker compose ps
```

**Raspberry Pi:**
```bash
# Setup print server
./raspberry-pi-setup.sh

# Check status
/usr/local/bin/pi-monitor.sh

# View Tailscale status
sudo tailscale status
```

**Development:**
```bash
# Start
./run_dev.sh

# Run tests
./run_tests.sh

# Backup
./scripts/backup.sh
```

### Essential URLs

- **Application:** http://localhost:5000
- **Login:** http://localhost:5000/login
- **Dashboard:** http://localhost:5000/
- **Health Check:** http://localhost:5000/api/health
- **API Base:** http://localhost:5000/api

### Essential Files

- **Configuration:** `.env`
- **Templates:** `templates_zpl/*.zpl.j2`
- **Printers:** `printers.json`
- **History:** `history.json`
- **Logs:** `logs/app.log`

---

## Success Checklist

- [ ] Application installed and running
- [ ] Can access login page
- [ ] Can log in successfully
- [ ] Dashboard loads correctly
- [ ] Created first template
- [ ] Added first printer
- [ ] Tested printer connection
- [ ] Generated preview successfully
- [ ] Printed first label
- [ ] Viewed print history
- [ ] Backup created successfully

**Congratulations! You're ready to use Barcode Central!** 🎉

---

**Need more help?** Check the [full documentation](README.md) or [troubleshooting guide](DEPLOYMENT.md#troubleshooting).