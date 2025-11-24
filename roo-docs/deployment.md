# Barcode Central - Deployment Guide

## Overview

This document provides comprehensive deployment strategies for the Barcode Central application, covering development setup in WSL, Docker containerization, and production deployment considerations.

## Deployment Environments

### 1. Development Environment (WSL + venv)
- **Purpose**: Local development and testing
- **Platform**: Windows Subsystem for Linux (Ubuntu)
- **Python**: Virtual environment (venv)
- **Server**: Flask development server
- **Port**: 5000

### 2. Production Environment (Docker)
- **Purpose**: Production deployment
- **Platform**: Docker container
- **Python**: System Python in container
- **Server**: Gunicorn + Flask
- **Port**: 8000

---

## Development Setup (WSL)

### Prerequisites

**System Requirements**:
- Windows 10/11 with WSL2 enabled
- Ubuntu 20.04+ in WSL
- Python 3.9 or higher
- Git

**Install WSL** (if not already installed):
```bash
# In Windows PowerShell (Administrator)
wsl --install -d Ubuntu-22.04
```

**Install Python and dependencies**:
```bash
# In WSL terminal
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip git
```

### Project Setup

**1. Clone or create project directory**:
```bash
cd ~/Projects
mkdir -p app.barcodecentral
cd app.barcodecentral
```

**2. Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Create directory structure**:
```bash
mkdir -p templates_zpl static/css static/js static/ace templates previews roo-docs
```

**5. Configure environment**:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Example .env for development**:
```env
# Authentication
LOGIN_USER=admin
LOGIN_PASSWORD=dev_password_123

# Flask Configuration
FLASK_SECRET_KEY=dev_secret_key_change_in_production_minimum_32_chars
FLASK_ENV=development
FLASK_DEBUG=True

# Application Settings
SESSION_TIMEOUT=3600
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Preview Settings
PREVIEW_CLEANUP_DAYS=7
PREVIEW_CLEANUP_ENABLED=True

# History Settings
HISTORY_MAX_ENTRIES=1000
HISTORY_ROTATION_ENABLED=True

# Labelary API
LABELARY_API_URL=http://api.labelary.com/v1/printers
LABELARY_DEFAULT_DPI=203
LABELARY_TIMEOUT=10

# Printer Settings
PRINTER_CONNECTION_TIMEOUT=5
PRINTER_STATUS_CACHE_TTL=300
```

**6. Create initial configuration files**:

**printers.json**:
```json
{
  "printers": [
    {
      "name": "Test Printer",
      "ip": "192.168.1.100",
      "port": 9100,
      "supported_sizes": ["4x6", "4x3", "2x1"],
      "dpi": 203,
      "description": "Development test printer",
      "enabled": true,
      "default": true
    }
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-11-24T01:45:00Z",
    "updated_by": "admin"
  }
}
```

**history.json**:
```json
{
  "entries": [],
  "metadata": {
    "version": "1.0",
    "total_entries": 0,
    "oldest_entry": null,
    "newest_entry": null,
    "last_rotation": null
  }
}
```

**7. Run development server**:
```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run Flask development server
python app.py

# Or use Flask CLI
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```

**8. Access application**:
- Open browser: `http://localhost:5000`
- Login with credentials from `.env`

### Development Workflow

**Starting development session**:
```bash
cd ~/Projects/app.barcodecentral
source venv/bin/activate
python app.py
```

**Stopping development server**:
- Press `Ctrl+C` in terminal

**Updating dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Running tests** (if implemented):
```bash
source venv/bin/activate
pytest tests/
```

---

## Docker Deployment

### Dockerfile

**Create Dockerfile in project root**:
```dockerfile
# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p templates_zpl static templates previews roo-docs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app:app"]
```

### Docker Compose

**Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  barcode-central:
    build: .
    container_name: barcode-central
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # Persistent data
      - ./templates_zpl:/app/templates_zpl
      - ./previews:/app/previews
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./.env:/app/.env
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    networks:
      - barcode-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  barcode-network:
    driver: bridge
```

### Building and Running

**Build Docker image**:
```bash
docker build -t barcode-central:latest .
```

**Run with Docker Compose**:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

**Run with Docker directly**:
```bash
docker run -d \
  --name barcode-central \
  -p 8000:8000 \
  -v $(pwd)/templates_zpl:/app/templates_zpl \
  -v $(pwd)/previews:/app/previews \
  -v $(pwd)/printers.json:/app/printers.json \
  -v $(pwd)/history.json:/app/history.json \
  -v $(pwd)/.env:/app/.env \
  --restart unless-stopped \
  barcode-central:latest
```

### Docker Management

**View logs**:
```bash
docker logs -f barcode-central
```

**Access container shell**:
```bash
docker exec -it barcode-central /bin/bash
```

**Update application**:
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

**Backup data**:
```bash
# Backup configuration and history
docker exec barcode-central tar czf /tmp/backup.tar.gz \
  /app/printers.json \
  /app/history.json \
  /app/templates_zpl \
  /app/previews

# Copy backup to host
docker cp barcode-central:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

---

## Requirements File

**requirements.txt**:
```txt
# Core Framework
Flask==2.3.3
Flask-Login==0.6.2
Werkzeug==2.3.7

# Environment Management
python-dotenv==1.0.0

# HTTP Client
requests==2.31.0

# Template Engine (included with Flask)
Jinja2==3.1.2

# Production Server
gunicorn==21.2.0

# Utilities
python-dateutil==2.8.2

# Optional: Testing
pytest==7.4.2
pytest-flask==1.2.0

# Optional: Code Quality
flake8==6.1.0
black==23.9.1
```

---

## Environment Configuration

### Development (.env)

```env
# Authentication
LOGIN_USER=admin
LOGIN_PASSWORD=dev_password_123

# Flask Configuration
FLASK_SECRET_KEY=dev_secret_key_change_in_production
FLASK_ENV=development
FLASK_DEBUG=True

# Session Settings
SESSION_TIMEOUT=3600
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Application Settings
PREVIEW_CLEANUP_DAYS=7
PREVIEW_CLEANUP_ENABLED=True
HISTORY_MAX_ENTRIES=1000
HISTORY_ROTATION_ENABLED=True

# External Services
LABELARY_API_URL=http://api.labelary.com/v1/printers
LABELARY_DEFAULT_DPI=203
LABELARY_TIMEOUT=10

# Printer Settings
PRINTER_CONNECTION_TIMEOUT=5
PRINTER_STATUS_CACHE_TTL=300
```

### Production (.env)

```env
# Authentication - USE STRONG PASSWORDS
LOGIN_USER=admin
LOGIN_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD_MIN_12_CHARS

# Flask Configuration - GENERATE SECURE SECRET KEY
FLASK_SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING_MIN_32_CHARS
FLASK_ENV=production
FLASK_DEBUG=False

# Session Settings - SECURE COOKIES
SESSION_TIMEOUT=3600
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict

# Application Settings
PREVIEW_CLEANUP_DAYS=7
PREVIEW_CLEANUP_ENABLED=True
HISTORY_MAX_ENTRIES=1000
HISTORY_ROTATION_ENABLED=True

# External Services
LABELARY_API_URL=http://api.labelary.com/v1/printers
LABELARY_DEFAULT_DPI=203
LABELARY_TIMEOUT=10

# Printer Settings
PRINTER_CONNECTION_TIMEOUT=5
PRINTER_STATUS_CACHE_TTL=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

### Generating Secure Keys

**Generate Flask secret key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Generate strong password**:
```bash
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(16)))"
```

---

## Volume Mapping Strategy

### Development (WSL)

**Directory structure**:
```
~/Projects/app.barcodecentral/
├── app.py
├── requirements.txt
├── .env
├── printers.json
├── history.json
├── templates_zpl/
│   ├── shipping_label.zpl.j2
│   └── product_label.zpl.j2
├── static/
│   ├── css/
│   ├── js/
│   └── ace/
├── templates/
│   ├── base.html
│   ├── login.html
│   └── index.html
├── previews/
│   └── (generated preview images)
└── roo-docs/
    ├── architecture.md
    ├── endpoints.md
    ├── data_structures.md
    └── deployment.md
```

**All files are directly accessible in WSL filesystem**

### Production (Docker)

**Volume mappings**:
```yaml
volumes:
  # Template files (editable)
  - ./templates_zpl:/app/templates_zpl

  # Preview images (generated, can be cleaned)
  - ./previews:/app/previews

  # Configuration files (persistent)
  - ./printers.json:/app/printers.json
  - ./history.json:/app/history.json
  - ./.env:/app/.env

  # Optional: Logs
  - ./logs:/app/logs
```

**Benefits**:
- Configuration changes without container rebuild
- Template updates without restart
- Data persistence across container restarts
- Easy backup of critical data

**Host directory structure**:
```
/opt/barcode-central/
├── .env
├── printers.json
├── history.json
├── templates_zpl/
├── previews/
└── logs/
```

---

## Port Exposure and Networking

### Development

**Port Configuration**:
- Flask dev server: `5000`
- Accessible from: `localhost:5000` or `127.0.0.1:5000`
- WSL to Windows: `<WSL-IP>:5000`

**Find WSL IP**:
```bash
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1
```

**Access from Windows**:
- Use WSL IP: `http://172.x.x.x:5000`
- Or use hostname: `http://$(hostname).local:5000`

### Production (Docker)

**Port Configuration**:
- Container internal: `8000`
- Host mapping: `8000:8000`
- Accessible from: `http://<server-ip>:8000`

**Firewall Configuration** (if needed):
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

**Reverse Proxy** (optional, recommended):

**Nginx configuration**:
```nginx
server {
    listen 80;
    server_name barcode.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optional: SSL configuration
    # listen 443 ssl;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
}
```

---

## Network Configuration

### Printer Network Access

**Requirements**:
- Printers must be on same network or routable network
- Port 9100 must be accessible (TCP)
- No firewall blocking between app and printers

**Test printer connectivity**:
```bash
# From WSL or Docker container
nc -zv 192.168.1.100 9100

# Or using telnet
telnet 192.168.1.100 9100
```

**Docker network configuration**:
```yaml
networks:
  barcode-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Host network mode** (if bridge doesn't work):
```yaml
services:
  barcode-central:
    network_mode: host
    # Note: port mapping not needed in host mode
```

---

## Security Considerations

### Development

**Security checklist**:
- [ ] Use weak passwords (acceptable for dev)
- [ ] Disable HTTPS (acceptable for dev)
- [ ] Enable debug mode
- [ ] Use local network only
- [ ] Don't expose to internet

### Production

**Security checklist**:
- [ ] Use strong passwords (12+ characters)
- [ ] Generate secure Flask secret key (32+ characters)
- [ ] Enable secure session cookies
- [ ] Disable debug mode
- [ ] Use HTTPS (via reverse proxy)
- [ ] Implement firewall rules
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Access logging
- [ ] Rate limiting (optional)

**Additional security measures**:

**1. File permissions**:
```bash
# Restrict .env file
chmod 600 .env

# Restrict configuration files
chmod 644 printers.json history.json

# Restrict directories
chmod 755 templates_zpl previews
```

**2. Docker security**:
```yaml
services:
  barcode-central:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"  # Non-root user
```

**3. Network isolation**:
```yaml
networks:
  barcode-network:
    internal: true  # No external access
```

---

## Monitoring and Logging

### Application Logs

**Development**:
```bash
# Flask dev server logs to console
python app.py
```

**Production (Docker)**:
```bash
# View container logs
docker logs -f barcode-central

# View last 100 lines
docker logs --tail 100 barcode-central

# Follow logs with timestamps
docker logs -f --timestamps barcode-central
```

### Log Configuration

**Add to .env**:
```env
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

**Log rotation** (in Docker):
```yaml
services:
  barcode-central:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Monitoring

**Health check endpoint**: `GET /health`

**Monitor with curl**:
```bash
# Check health
curl http://localhost:8000/health

# Monitor continuously
watch -n 30 'curl -s http://localhost:8000/health | jq'
```

**Docker health status**:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Backup and Recovery

### Backup Strategy

**What to backup**:
1. Configuration files (`.env`, `printers.json`)
2. History data (`history.json`)
3. Template files (`templates_zpl/`)
4. Preview images (`previews/`) - optional

**Backup script**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/barcode-central"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

tar czf "$BACKUP_FILE" \
  .env \
  printers.json \
  history.json \
  templates_zpl/ \
  previews/

echo "Backup created: $BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete
```

**Automated backups** (cron):
```bash
# Add to crontab
0 2 * * * /opt/barcode-central/backup.sh
```

### Recovery

**Restore from backup**:
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore.sh <backup_file>"
  exit 1
fi

# Stop application
docker-compose down

# Extract backup
tar xzf "$BACKUP_FILE" -C /opt/barcode-central/

# Start application
docker-compose up -d

echo "Restore completed"
```

---

## Troubleshooting

### Common Issues

**1. Port already in use**:
```bash
# Find process using port
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>

# Or use different port
flask run --port 5001
```

**2. Permission denied on files**:
```bash
# Fix file permissions
chmod 644 printers.json history.json
chmod 755 templates_zpl previews
```

**3. Docker container won't start**:
```bash
# Check logs
docker logs barcode-central

# Check configuration
docker-compose config

# Rebuild container
docker-compose build --no-cache
```

**4. Can't connect to printer**:
```bash
# Test connectivity
nc -zv 192.168.1.100 9100

# Check firewall
sudo ufw status

# Check Docker network
docker network inspect barcode-network
```

**5. Preview generation fails**:
```bash
# Test Labelary API
curl -X POST http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/ \
  --data-binary "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" \
  -o test.png

# Check internet connectivity
ping api.labelary.com
```

---

## Performance Tuning

### Gunicorn Configuration

**Optimal worker count**:
```
workers = (2 * CPU_cores) + 1
```

**Example for 4-core system**:
```bash
gunicorn --workers 9 --bind 0.0.0.0:8000 app:app
```

**Advanced configuration** (`gunicorn.conf.py`):
```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"
```

### Resource Limits (Docker)

```yaml
services:
  barcode-central:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
```

---

## Scaling Considerations

### Current Limitations

- Single server deployment
- File-based storage (not distributed)
- Synchronous print operations
- Limited to ~1000 history entries

### Future Scaling Options

**1. Database backend**:
- Replace JSON files with SQLite/PostgreSQL
- Better query performance
- Unlimited history entries

**2. Async processing**:
- Use Celery for print queue
- Background preview generation
- Better handling of slow printers

**3. Load balancing**:
- Multiple application instances
- Shared storage (NFS/S3)
- Redis for session storage

**4. Caching**:
- Redis for printer status
- Template metadata cache
- Preview image cache

---

## Maintenance Tasks

### Daily

- Monitor application logs
- Check disk space (previews directory)
- Verify printer connectivity

### Weekly

- Review history entries
- Backup configuration and data
- Update printer configurations if needed

### Monthly

- Update dependencies
- Review and rotate logs
- Archive old backups
- Security updates

### Quarterly

- Review and update templates
- Performance analysis
- Security audit

---

## Conclusion

This deployment guide provides comprehensive instructions for setting up Barcode Central in both development (WSL + venv) and production (Docker) environments. Follow the security best practices and maintenance schedules to ensure reliable operation.

For additional support, refer to:
- [`architecture.md`](architecture.md) - System architecture
- [`endpoints.md`](endpoints.md) - API documentation
- [`data_structures.md`](data_structures.md) - Data formats