# Docker Compose Configurations for Production Deployment

This document contains all Docker Compose configurations for different deployment scenarios.

## Table of Contents

1. [Basic Deployment](#basic-deployment)
2. [Traefik Reverse Proxy](#traefik-reverse-proxy)
3. [Headscale Mesh Network](#headscale-mesh-network)
4. [Full Stack Deployment](#full-stack-deployment)
5. [Monitoring Stack](#monitoring-stack)

---

## Basic Deployment

**File**: `docker-compose.yml` (already exists)

This is the current simple deployment configuration.

---

## Traefik Reverse Proxy

**File**: `docker-compose.traefik.yml`

This configuration adds Traefik as a reverse proxy with automatic HTTPS via Let's Encrypt.

```yaml
# Docker Compose with Traefik Reverse Proxy
# Provides automatic HTTPS with Let's Encrypt
# 
# Prerequisites:
# 1. Domain name pointing to your VPS IP
# 2. Ports 80 and 443 open in firewall
# 3. Email address for Let's Encrypt
#
# Usage:
#   cp .env.traefik.example .env.traefik
#   # Edit .env.traefik with your domain and email
#   docker compose -f docker-compose.traefik.yml up -d

version: '3.8'

services:
  # Traefik Reverse Proxy
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    
    command:
      # Enable Docker provider
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      
      # Entry points
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      
      # HTTP to HTTPS redirect
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      
      # Let's Encrypt configuration
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      
      # Enable dashboard (optional - comment out for production)
      # - "--api.dashboard=true"
      # - "--api.insecure=true"
      
      # Logging
      - "--log.level=INFO"
      - "--accesslog=true"
    
    ports:
      - "80:80"
      - "443:443"
      # Dashboard (optional - comment out for production)
      # - "8080:8080"
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
      - ./traefik-logs:/var/log/traefik
    
    networks:
      - traefik-network
    
    labels:
      # Dashboard access (optional - comment out for production)
      # - "traefik.enable=true"
      # - "traefik.http.routers.dashboard.rule=Host(`traefik.${DOMAIN}`)"
      # - "traefik.http.routers.dashboard.service=api@internal"
      # - "traefik.http.routers.dashboard.entrypoints=websecure"
      # - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      # - "traefik.http.routers.dashboard.middlewares=auth"
      # - "traefik.http.middlewares.auth.basicauth.users=${TRAEFIK_DASHBOARD_AUTH}"

  # Barcode Central Application
  app:
    build:
      context: .
      dockerfile: Dockerfile
    
    container_name: barcode-central
    restart: unless-stopped
    
    # No need to expose ports - Traefik handles it
    expose:
      - "5000"
    
    env_file:
      - .env
    
    volumes:
      # Application data
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
    
    networks:
      - traefik-network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    labels:
      # Enable Traefik for this service
      - "traefik.enable=true"
      
      # Router configuration
      - "traefik.http.routers.barcode.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.barcode.entrypoints=websecure"
      - "traefik.http.routers.barcode.tls=true"
      - "traefik.http.routers.barcode.tls.certresolver=letsencrypt"
      
      # Service configuration
      - "traefik.http.services.barcode.loadbalancer.server.port=5000"
      
      # Security headers
      - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
      - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
      - "traefik.http.middlewares.security-headers.headers.stsPreload=true"
      - "traefik.http.middlewares.security-headers.headers.forceSTSHeader=true"
      - "traefik.http.middlewares.security-headers.headers.frameDeny=true"
      - "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true"
      - "traefik.http.middlewares.security-headers.headers.browserXssFilter=true"
      
      # Apply security headers
      - "traefik.http.routers.barcode.middlewares=security-headers"
      
      # Rate limiting (optional)
      # - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
      # - "traefik.http.middlewares.rate-limit.ratelimit.burst=50"
      # - "traefik.http.routers.barcode.middlewares=security-headers,rate-limit"

networks:
  traefik-network:
    name: traefik-network
    driver: bridge

volumes:
  letsencrypt:
    name: letsencrypt-data
```

### Environment File for Traefik

**File**: `.env.traefik.example`

```env
# Traefik Configuration
# Copy this file to .env.traefik and customize

# Your domain name
DOMAIN=print.example.com

# Email for Let's Encrypt notifications
ACME_EMAIL=admin@example.com

# Traefik Dashboard Authentication (optional)
# Generate with: echo $(htpasswd -nb admin your-password) | sed -e s/\\$/\\$\\$/g
# TRAEFIK_DASHBOARD_AUTH=admin:$$apr1$$xyz...

# Application environment variables (from .env)
# Include all variables from your main .env file here
SECRET_KEY=your-secret-key
LOGIN_USER=admin
LOGIN_PASSWORD=your-password
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO
```

---

## Headscale Mesh Network

**File**: `docker-compose.headscale.yml`

This configuration adds Headscale for mesh networking with distributed printers.

```yaml
# Docker Compose with Headscale Mesh Network
# Enables secure connectivity to printers across multiple locations
#
# Prerequisites:
# 1. Domain name for Headscale server
# 2. Port 8080 (HTTP) and 41641 (UDP) open in firewall
# 3. Raspberry Pis at remote locations with Tailscale client
#
# Usage:
#   cp .env.headscale.example .env.headscale
#   # Edit .env.headscale with your configuration
#   docker compose -f docker-compose.headscale.yml up -d

version: '3.8'

services:
  # Headscale Coordination Server
  headscale:
    image: headscale/headscale:v0.27.1
    container_name: headscale
    restart: unless-stopped
    
    command: headscale serve
    
    ports:
      - "8080:8080"    # HTTP API
      - "9090:9090"    # Metrics
      - "41641:41641/udp"  # WireGuard
    
    volumes:
      - ./headscale/config:/etc/headscale
      - ./headscale/data:/var/lib/headscale
    
    networks:
      - headscale-network
    
    environment:
      - TZ=UTC
    
    healthcheck:
      test: ["CMD", "headscale", "health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Barcode Central Application with Tailscale
  app:
    build:
      context: .
      dockerfile: Dockerfile
    
    container_name: barcode-central
    restart: unless-stopped
    
    # Network mode: Use Tailscale sidecar
    network_mode: "service:tailscale"
    
    env_file:
      - .env
    
    volumes:
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
    
    depends_on:
      - tailscale
      - headscale
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Tailscale Client for Application
  tailscale:
    image: tailscale/tailscale:latest
    container_name: barcode-central-tailscale
    restart: unless-stopped
    
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
      - headscale-network
    
    depends_on:
      - headscale

networks:
  headscale-network:
    name: headscale-network
    driver: bridge
```

### Headscale Configuration

**File**: `headscale/config/config.yaml`

```yaml
# Headscale Configuration
# Place this file in ./headscale/config/config.yaml

server_url: http://headscale.example.com:8080
listen_addr: 0.0.0.0:8080
metrics_listen_addr: 0.0.0.0:9090

# WireGuard configuration
private_key_path: /var/lib/headscale/private.key
noise:
  private_key_path: /var/lib/headscale/noise_private.key

# IP prefix for the Tailscale network
ip_prefixes:
  - 100.64.0.0/10

# Database
db_type: sqlite3
db_path: /var/lib/headscale/db.sqlite

# DNS configuration
dns_config:
  override_local_dns: true
  nameservers:
    - 1.1.1.1
    - 8.8.8.8
  domains: []
  magic_dns: true
  base_domain: headscale.local

# ACL policy file
acl_policy_path: /etc/headscale/acl.json

# DERP (relay) configuration
derp:
  server:
    enabled: false
  
  urls:
    - https://controlplane.tailscale.com/derpmap/default

# Logging
log:
  level: info
  format: text

# Ephemeral nodes
ephemeral_node_inactivity_timeout: 30m

# Node update check
disable_check_updates: false
```

### Headscale ACL Policy

**File**: `headscale/config/acl.json`

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["barcode-central-server"],
      "dst": ["*:9100"]
    },
    {
      "action": "accept",
      "src": ["barcode-central-server"],
      "dst": ["*:631"]
    },
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["barcode-central-server:5000"]
    }
  ],
  "groups": {
    "group:printers": [
      "warehouse-pi",
      "office-pi",
      "remote-pi"
    ]
  },
  "hosts": {
    "barcode-central-server": "100.64.0.1",
    "warehouse-pi": "100.64.0.10",
    "office-pi": "100.64.0.20",
    "remote-pi": "100.64.0.30"
  },
  "tagOwners": {
    "tag:printer-server": ["group:printers"]
  }
}
```

### Environment File for Headscale

**File**: `.env.headscale.example`

```env
# Headscale Configuration
# Copy this file to .env.headscale and customize

# Tailscale authentication key
# Generate with: headscale preauthkeys create --reusable --expiration 90d
TAILSCALE_AUTHKEY=your-preauth-key-here

# Headscale server URL
HEADSCALE_SERVER_URL=http://headscale.example.com:8080

# Application environment variables (from .env)
SECRET_KEY=your-secret-key
LOGIN_USER=admin
LOGIN_PASSWORD=your-password
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO
```

---

## Full Stack Deployment

**File**: `docker-compose.full.yml`

This combines Traefik, Headscale, and the application for a complete production setup.

```yaml
# Complete Production Stack
# Includes: Traefik (HTTPS) + Headscale (Mesh) + Application
#
# Prerequisites:
# 1. Domain name for both Traefik and Headscale
# 2. Ports 80, 443, 8080, 41641 open
# 3. Configured .env files
#
# Usage:
#   docker compose -f docker-compose.full.yml up -d

version: '3.8'

services:
  # Traefik Reverse Proxy
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    
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
      - traefik-network
      - headscale-network

  # Headscale Coordination Server
  headscale:
    image: headscale/headscale:v0.27.1
    container_name: headscale
    restart: unless-stopped
    
    command: headscale serve
    
    expose:
      - "8080"
      - "9090"
    
    ports:
      - "41641:41641/udp"
    
    volumes:
      - ./headscale/config:/etc/headscale
      - ./headscale/data:/var/lib/headscale
    
    networks:
      - headscale-network
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.headscale.rule=Host(`headscale.${DOMAIN}`)"
      - "traefik.http.routers.headscale.entrypoints=websecure"
      - "traefik.http.routers.headscale.tls=true"
      - "traefik.http.routers.headscale.tls.certresolver=letsencrypt"
      - "traefik.http.services.headscale.loadbalancer.server.port=8080"

  # Barcode Central Application
  app:
    build:
      context: .
      dockerfile: Dockerfile
    
    container_name: barcode-central
    restart: unless-stopped
    
    network_mode: "service:tailscale"
    
    env_file:
      - .env
    
    volumes:
      - ./printers.json:/app/printers.json
      - ./history.json:/app/history.json
      - ./templates_zpl:/app/templates_zpl
      - ./logs:/app/logs
      - ./previews:/app/previews
    
    depends_on:
      - tailscale
      - headscale
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Tailscale Client
  tailscale:
    image: tailscale/tailscale:latest
    container_name: barcode-central-tailscale
    restart: unless-stopped
    
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
      - traefik-network
      - headscale-network
    
    depends_on:
      - headscale
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.barcode.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.barcode.entrypoints=websecure"
      - "traefik.http.routers.barcode.tls=true"
      - "traefik.http.routers.barcode.tls.certresolver=letsencrypt"
      - "traefik.http.services.barcode.loadbalancer.server.port=5000"

networks:
  traefik-network:
    name: traefik-network
    driver: bridge
  
  headscale-network:
    name: headscale-network
    driver: bridge
```

---

## Monitoring Stack

**File**: `docker-compose.monitoring.yml`

Optional monitoring stack with Prometheus and Grafana.

```yaml
# Monitoring Stack for Barcode Central
# Includes: Prometheus, Grafana, Node Exporter
#
# Usage:
#   docker compose -f docker-compose.monitoring.yml up -d
#   Access Grafana at http://localhost:3000 (admin/admin)

version: '3.8'

services:
  # Prometheus - Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    
    ports:
      - "9090:9090"
    
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    
    networks:
      - monitoring-network

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    
    ports:
      - "3000:3000"
    
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    
    networks:
      - monitoring-network
    
    depends_on:
      - prometheus

  # Node Exporter - System Metrics
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    
    ports:
      - "9100:9100"
    
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    
    networks:
      - monitoring-network

networks:
  monitoring-network:
    name: monitoring-network
    driver: bridge

volumes:
  prometheus-data:
    name: prometheus-data
  grafana-data:
    name: grafana-data
```

### Prometheus Configuration

**File**: `monitoring/prometheus.yml`

```yaml
# Prometheus Configuration

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'barcode-central'

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Barcode Central Application
  - job_name: 'barcode-central'
    static_configs:
      - targets: ['app:5000']
    metrics_path: '/api/metrics'

  # Headscale
  - job_name: 'headscale'
    static_configs:
      - targets: ['headscale:9090']

  # Traefik
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
```

---

## Deployment Instructions

### 1. Basic Deployment
```bash
# Use existing docker-compose.yml
docker compose up -d
```

### 2. With Traefik
```bash
# Copy and configure environment
cp .env.traefik.example .env.traefik
nano .env.traefik

# Create required directories
mkdir -p letsencrypt traefik-logs

# Deploy
docker compose -f docker-compose.traefik.yml up -d
```

### 3. With Headscale
```bash
# Copy and configure environment
cp .env.headscale.example .env.headscale

# Create required directories
mkdir -p headscale/config headscale/data tailscale/state

# Copy configuration files
cp headscale/config/config.yaml.example headscale/config/config.yaml
cp headscale/config/acl.json.example headscale/config/acl.json

# Deploy
docker compose -f docker-compose.headscale.yml up -d

# Generate pre-auth key
docker exec headscale headscale preauthkeys create --reusable --expiration 90d

# Update .env.headscale with the key
```

### 4. Full Stack
```bash
# Combine all configurations
docker compose -f docker-compose.full.yml up -d
```

### 5. With Monitoring
```bash
# Deploy monitoring stack separately
docker compose -f docker-compose.monitoring.yml up -d

# Access Grafana at http://localhost:3000
```

---

## Next Steps

1. Choose your deployment scenario
2. Copy the appropriate docker-compose file
3. Configure environment variables
4. Deploy and test
5. Set up Raspberry Pi print servers (see RASPBERRY_PI_SETUP.md)

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24