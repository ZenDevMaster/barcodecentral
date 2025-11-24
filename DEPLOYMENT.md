# Barcode Central - Deployment Guide

This guide covers deploying Barcode Central using Docker and Docker Compose for production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Building the Image](#building-the-image)
6. [Running with Docker Compose](#running-with-docker-compose)
7. [Environment Variables](#environment-variables)
8. [Volume Mounts](#volume-mounts)
9. [Backup and Restore](#backup-and-restore)
10. [Monitoring and Logs](#monitoring-and-logs)
11. [Updating the Application](#updating-the-application)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)
14. [Alternative Deployment Methods](#alternative-deployment-methods)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **curl**: For health checks (usually pre-installed)

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 1GB for application, additional space for logs and data
- **OS**: Linux, macOS, or Windows with WSL2

### Installation

#### Ubuntu/Debian
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Other Systems
- **macOS**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Windows**: Install [Docker Desktop with WSL2](https://docs.docker.com/desktop/windows/wsl/)

---

## Quick Start

For a rapid deployment:

```bash
# 1. Clone or navigate to the project directory
cd /path/to/barcode-central

# 2. Create environment file
cp .env.production.example .env
nano .env  # Edit with your configuration

# 3. Deploy
./scripts/deploy.sh --build
```

The application will be available at `http://localhost:5000`

---

## Initial Setup

### 1. Prepare Environment Configuration

Create your production environment file:

```bash
cp .env.production.example .env
```

Edit `.env` with your configuration:

```bash
nano .env
```

**Critical settings to change:**

```env
# Generate a secure secret key
SECRET_KEY=your-random-secret-key-here

# Set strong credentials
LOGIN_USER=your-admin-username
LOGIN_PASSWORD=your-secure-password
```

**Generate a secure secret key:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Secure the Environment File

```bash
chmod 600 .env
```

### 3. Initialize Data Files

Create empty data files if they don't exist:

```bash
# Create printers configuration
echo '[]' > printers.json

# Create history file
echo '[]' > history.json

# Ensure templates directory exists
mkdir -p templates_zpl
```

---

## Configuration

### Environment Variables

See [Environment Variables](#environment-variables) section below for detailed configuration options.

### Application Settings

Key configuration files:

- **`.env`**: Environment variables (credentials, settings)
- **`gunicorn.conf.py`**: Production server configuration
- **`docker-compose.yml`**: Container orchestration
- **`Dockerfile`**: Container image definition

---

## Building the Image

### Using the Build Script

```bash
./scripts/build.sh
```

Or with a custom tag:

```bash
./scripts/build.sh v1.0.0
```

### Manual Build

```bash
docker build -t barcode-central:latest .
```

### Build Options

For development builds with different configurations:

```bash
# Build without cache
docker build --no-cache -t barcode-central:latest .

# Build with specific platform
docker build --platform linux/amd64 -t barcode-central:latest .
```

---

## Running with Docker Compose

### Start the Application

```bash
# Using the deployment script (recommended)
./scripts/deploy.sh

# Or manually
docker-compose up -d
```

### Stop the Application

```bash
docker-compose down
```

### Restart the Application

```bash
docker-compose restart
```

### View Running Containers

```bash
docker-compose ps
```

### Access the Application

Open your browser to:
- **Local**: http://localhost:5000
- **Network**: http://your-server-ip:5000

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `a1b2c3d4e5f6...` |
| `LOGIN_USER` | Admin username | `admin` |
| `LOGIN_PASSWORD` | Admin password | `SecurePass123!` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `FLASK_DEBUG` | Debug mode | `0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SESSION_COOKIE_SECURE` | HTTPS-only cookies | `false` |

### Example Production Configuration

```env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-generated-secret-key-here
LOGIN_USER=admin
LOGIN_PASSWORD=YourSecurePassword123!
LOG_LEVEL=INFO
SESSION_COOKIE_SECURE=false
```

---

## Volume Mounts

Docker Compose mounts the following directories for data persistence:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./templates_zpl` | `/app/templates_zpl` | ZPL label templates |
| `./history.json` | `/app/history.json` | Print job history |
| `./printers.json` | `/app/printers.json` | Printer configurations |
| `./previews` | `/app/previews` | Generated label previews |
| `./logs` | `/app/logs` | Application logs |

### Data Persistence

All data is stored on the host system, ensuring:
- Data survives container restarts
- Easy backup and restore
- Direct file access when needed

---

## Backup and Restore

### Creating Backups

#### Using the Backup Script (Recommended)

```bash
./scripts/backup.sh
```

This creates a timestamped backup in `backups/backup_YYYYMMDD_HHMMSS.tar.gz`

#### Manual Backup

```bash
# Create backup directory
mkdir -p backups

# Backup data files
tar -czf backups/manual_backup.tar.gz \
    history.json \
    printers.json \
    templates_zpl/ \
    .env
```

### Restoring from Backup

#### Using the Restore Script (Recommended)

```bash
./scripts/restore.sh backups/backup_20240101_120000.tar.gz
```

#### Manual Restore

```bash
# Stop the application
docker-compose down

# Extract backup
tar -xzf backups/backup_20240101_120000.tar.gz

# Copy files to current directory
cp -r backup_20240101_120000/* .

# Start the application
docker-compose up -d
```

### Automated Backups

Set up a cron job for automated backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/barcode-central && ./scripts/backup.sh
```

---

## Monitoring and Logs

### View Logs

```bash
# All logs (follow mode)
docker-compose logs -f

# Application logs only
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Logs since specific time
docker-compose logs --since 2024-01-01T00:00:00 app
```

### Access Log Files

Logs are stored in the `logs/` directory:

```bash
# Application logs
tail -f logs/app.log

# Gunicorn access logs
tail -f logs/gunicorn-access.log

# Gunicorn error logs
tail -f logs/gunicorn-error.log
```

### Health Check

Check application health:

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "barcode-central"
}
```

### Container Status

```bash
# Check container health
docker ps

# Inspect container
docker inspect barcode-central

# View resource usage
docker stats barcode-central
```

---

## Updating the Application

### Update Process

1. **Backup current data:**
   ```bash
   ./scripts/backup.sh
   ```

2. **Pull latest code:**
   ```bash
   git pull origin main
   ```

3. **Rebuild and deploy:**
   ```bash
   ./scripts/deploy.sh --build
   ```

### Rolling Back

If issues occur:

```bash
# Stop current version
docker-compose down

# Restore from backup
./scripts/restore.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz

# Start previous version
docker-compose up -d
```

### Zero-Downtime Updates

For production environments:

1. Build new image with different tag
2. Update docker-compose.yml to use new tag
3. Run `docker-compose up -d` (will recreate containers)

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
- Missing `.env` file
- Invalid environment variables
- Port 5000 already in use
- Insufficient permissions

**Solutions:**
```bash
# Check if port is in use
sudo lsof -i :5000

# Check file permissions
ls -la .env

# Verify environment file
cat .env
```

### Application Not Accessible

**Check container status:**
```bash
docker-compose ps
```

**Verify network:**
```bash
# Test from host
curl http://localhost:5000/api/health

# Check container network
docker network inspect barcode-central_barcode-network
```

### Health Check Failing

**Check application logs:**
```bash
docker-compose logs app | grep -i error
```

**Verify health endpoint:**
```bash
docker exec barcode-central curl http://localhost:5000/api/health
```

### Permission Issues

**Fix file permissions:**
```bash
# Ensure proper ownership
sudo chown -R $USER:$USER .

# Fix directory permissions
chmod 755 templates_zpl previews logs
chmod 644 *.json
chmod 600 .env
```

### Database/File Corruption

**Restore from backup:**
```bash
./scripts/restore.sh backups/latest_backup.tar.gz
```

### High Memory Usage

**Check resource usage:**
```bash
docker stats barcode-central
```

**Adjust worker count in `gunicorn.conf.py`:**
```python
workers = 2  # Reduce if needed
```

---

## Security Considerations

### Essential Security Measures

1. **Change Default Credentials**
   ```env
   LOGIN_USER=your-unique-username
   LOGIN_PASSWORD=your-strong-password
   ```

2. **Generate Strong Secret Key**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Secure Environment File**
   ```bash
   chmod 600 .env
   ```

4. **Use HTTPS in Production**
   - Set up reverse proxy (nginx/Apache)
   - Enable SSL/TLS certificates
   - Set `SESSION_COOKIE_SECURE=true`

5. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

6. **Regular Updates**
   - Keep Docker updated
   - Update base images regularly
   - Monitor security advisories

7. **Network Isolation**
   - Use Docker networks
   - Limit container exposure
   - Implement network policies

### Additional Recommendations

- Enable audit logging
- Implement rate limiting
- Use secrets management (Docker secrets, Vault)
- Regular security scans
- Backup encryption

---

## Alternative Deployment Methods

### Without Docker

See [`barcode-central.service`](barcode-central.service) for systemd service configuration.

#### Manual Installation

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.production.example .env
nano .env

# Run with gunicorn
gunicorn --config gunicorn.conf.py app:app
```

#### Systemd Service

```bash
# Copy service file
sudo cp barcode-central.service /etc/systemd/system/

# Edit paths in service file
sudo nano /etc/systemd/system/barcode-central.service

# Enable and start
sudo systemctl enable barcode-central
sudo systemctl start barcode-central

# Check status
sudo systemctl status barcode-central
```

### With Nginx Reverse Proxy

See [`nginx.conf`](nginx.conf) for nginx configuration example.

```bash
# Install nginx
sudo apt-get install nginx

# Copy configuration
sudo cp nginx.conf /etc/nginx/sites-available/barcode-central
sudo ln -s /etc/nginx/sites-available/barcode-central /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

---

## Support and Resources

### Documentation

- [Architecture Documentation](roo-docs/architecture.md)
- [API Endpoints](roo-docs/endpoints.md)
- [Data Structures](roo-docs/data_structures.md)

### Getting Help

- Check logs: `docker-compose logs -f`
- Review troubleshooting section above
- Verify configuration files
- Check Docker and system resources

### Useful Commands

```bash
# Quick reference
docker-compose ps              # List containers
docker-compose logs -f         # Follow logs
docker-compose restart         # Restart services
docker-compose down            # Stop services
docker-compose up -d           # Start services
./scripts/backup.sh            # Create backup
./scripts/deploy.sh --build    # Deploy with rebuild
```

---

## License

See project LICENSE file for details.