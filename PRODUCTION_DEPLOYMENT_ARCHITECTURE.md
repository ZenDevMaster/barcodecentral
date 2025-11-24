# Barcode Central - Production Deployment Architecture

## Executive Summary

This document outlines a production-ready deployment architecture for Barcode Central designed for:
- **Central VPS deployment** with public HTTPS access
- **Distributed printer networks** across multiple physical locations worldwide
- **Secure mesh networking** via Headscale/Tailscale for printer connectivity
- **Raspberry Pi print servers** for local printer management
- **Optional Traefik** reverse proxy with automatic HTTPS

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS (443)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    VPS / Cloud Server                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Traefik (Optional)                                       │  │
│  │  - Automatic HTTPS (Let's Encrypt)                        │  │
│  │  - SSL Termination                                        │  │
│  │  - Request routing                                        │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │  Barcode Central Application                             │  │
│  │  - Flask web interface                                    │  │
│  │  - Template management                                    │  │
│  │  - Print job orchestration                                │  │
│  │  - History tracking                                       │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │  Headscale Server (Optional)                             │  │
│  │  - Coordination server for mesh network                   │  │
│  │  - ACL management                                         │  │
│  │  - Subnet routing                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Tailscale Client: 100.64.0.1                                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ Tailscale Mesh Network
                           │ (Encrypted WireGuard)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼───────┐  ┌──────▼───────┐
│  Location A    │  │  Location B  │  │  Location C  │
│  (Warehouse)   │  │  (Office)    │  │  (Remote)    │
└────────────────┘  └──────────────┘  └──────────────┘
│                   │                 │
│ Raspberry Pi      │ Raspberry Pi    │ Raspberry Pi
│ Print Server      │ Print Server    │ Print Server
│ 100.64.0.10       │ 100.64.0.20     │ 100.64.0.30
│                   │                 │
│ Advertises:       │ Advertises:     │ Advertises:
│ 192.168.1.0/24    │ 10.0.0.0/24     │ 172.16.0.0/24
│                   │                 │
│ ┌──────────────┐  │ ┌────────────┐  │ ┌────────────┐
│ │ Zebra ZT230  │  │ │ Zebra GK420│  │ │ Zebra ZT410│
│ │ 192.168.1.100│  │ │ 10.0.0.100 │  │ │ 172.16.0.100│
│ │ Port 9100    │  │ │ Port 9100  │  │ │ Port 9100  │
│ └──────────────┘  │ └────────────┘  │ └────────────┘
│                   │                 │
│ ┌──────────────┐  │ ┌────────────┐  │ ┌────────────┐
│ │ USB Printer  │  │ │ USB Printer│  │ │ USB Printer│
│ │ via CUPS     │  │ │ via CUPS   │  │ │ via CUPS   │
│ │ localhost:631│  │ │ localhost  │  │ │ localhost  │
│ └──────────────┘  │ └────────────┘  │ └────────────┘
└───────────────────┘ └────────────────┘ └────────────┘
```

## Deployment Scenarios

### Scenario 1: Simple VPS Deployment (Current)
**Use Case**: Single location, all printers on same network as VPS

```yaml
# docker-compose.yml (current)
services:
  app:
    image: barcode-central:latest
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
```

**Pros**: Simple, no additional infrastructure
**Cons**: Limited to local network printers

### Scenario 2: VPS + Traefik (Recommended for Public Access)
**Use Case**: Public HTTPS access with automatic SSL

```yaml
# docker-compose.traefik.yml
services:
  traefik:
    image: traefik:v2.10
    # Automatic HTTPS with Let's Encrypt
  
  app:
    image: barcode-central:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.barcode.rule=Host(`print.example.com`)"
```

**Pros**: Automatic HTTPS, professional setup
**Cons**: Requires domain name

### Scenario 3: VPS + Headscale + Distributed Printers (Full Solution)
**Use Case**: Central server with printers at multiple physical locations

```yaml
# docker-compose.full.yml
services:
  headscale:
    image: headscale/headscale:latest
    # Mesh network coordinator
  
  app:
    image: barcode-central:latest
    # Connects to Headscale mesh
  
  # Raspberry Pi at each location runs Tailscale client
  # and advertises local printer subnets
```

**Pros**: Secure global printer access, scalable
**Cons**: More complex setup, requires Raspberry Pis

## Network Architecture

### Headscale/Tailscale Mesh Network

**Why Headscale?**
- Self-hosted alternative to Tailscale's coordination server
- Full control over your mesh network
- No external dependencies
- Free and open source

**Network Design:**

1. **VPS (Coordination + Application)**
   - Headscale server: Coordinates mesh network
   - Barcode Central: Main application
   - Tailscale IP: `100.64.0.1`

2. **Location A - Warehouse**
   - Raspberry Pi: `100.64.0.10`
   - Advertises subnet: `192.168.1.0/24`
   - Printers: `192.168.1.100-110`

3. **Location B - Office**
   - Raspberry Pi: `100.64.0.20`
   - Advertises subnet: `10.0.0.0/24`
   - Printers: `10.0.0.100-110`

4. **Location C - Remote Site**
   - Raspberry Pi: `100.64.0.30`
   - Advertises subnet: `172.16.0.0/24`
   - Printers: `172.16.0.100-110`

**Printer Configuration in Barcode Central:**

```json
{
  "printers": [
    {
      "id": "warehouse-zebra-01",
      "name": "Warehouse Zebra ZT230",
      "ip": "192.168.1.100",
      "port": 9100,
      "location": "Warehouse A",
      "description": "Accessible via Tailscale mesh"
    },
    {
      "id": "office-zebra-01",
      "name": "Office Zebra GK420",
      "ip": "10.0.0.100",
      "port": 9100,
      "location": "Office B",
      "description": "Accessible via Tailscale mesh"
    }
  ]
}
```

## Raspberry Pi Print Server Setup

### Hardware Requirements
- Raspberry Pi 3B+ or newer (4GB RAM recommended)
- MicroSD card (16GB minimum)
- Power supply
- Network connection (Ethernet preferred)

### Software Stack
```
┌─────────────────────────────────────┐
│  Raspberry Pi OS Lite (64-bit)      │
├─────────────────────────────────────┤
│  Tailscale Client                   │
│  - Connects to Headscale            │
│  - Advertises local subnet          │
├─────────────────────────────────────┤
│  CUPS (Optional - for USB printers) │
│  - Exposes USB printers on network  │
│  - Creates virtual network printers │
├─────────────────────────────────────┤
│  Monitoring (Optional)               │
│  - Node Exporter for metrics        │
│  - Health check scripts             │
└─────────────────────────────────────┘
```

### USB Printer Support via CUPS

**CUPS Configuration:**
```bash
# Install CUPS on Raspberry Pi
sudo apt-get install cups

# Configure CUPS to accept network connections
sudo cupsctl --remote-any
sudo systemctl restart cups

# Add USB printer and share on network
lpadmin -p zebra-usb -E -v usb://Zebra/ZT230 -m everywhere

# Printer becomes accessible at:
# http://raspberrypi.local:631/printers/zebra-usb
# Or via IPP: ipp://100.64.0.10:631/printers/zebra-usb
```

**Barcode Central Integration:**
For USB printers via CUPS, you have two options:

1. **IPP Protocol** (Recommended):
   - Use CUPS IPP endpoint
   - More reliable for USB printers
   - Requires minor code modification

2. **Raw TCP/IP** (Current):
   - Configure CUPS to expose raw socket
   - Works with existing code
   - Less reliable for USB

## Deployment Files Structure

```
barcode-central/
├── docker-compose.yml                    # Basic deployment
├── docker-compose.traefik.yml           # With Traefik reverse proxy
├── docker-compose.headscale.yml         # With Headscale mesh
├── docker-compose.full.yml              # Complete stack
├── .env.production                       # Production config
├── .env.traefik                         # Traefik config
├── .env.headscale                       # Headscale config
│
├── deployment/
│   ├── vps/
│   │   ├── deploy-basic.sh              # Basic VPS deployment
│   │   ├── deploy-traefik.sh            # With Traefik
│   │   ├── deploy-full.sh               # Full stack
│   │   └── README.md
│   │
│   ├── raspberry-pi/
│   │   ├── setup-print-server.sh        # Pi setup script
│   │   ├── install-tailscale.sh         # Tailscale client
│   │   ├── configure-cups.sh            # USB printer support
│   │   ├── config/
│   │   │   ├── tailscale.conf
│   │   │   └── cups.conf
│   │   └── README.md
│   │
│   └── headscale/
│       ├── config.yaml                   # Headscale config
│       ├── acl.json                      # Access control
│       ├── setup.sh                      # Initial setup
│       └── README.md
│
├── docs/
│   ├── PRODUCTION_DEPLOYMENT_ARCHITECTURE.md  # This file
│   ├── DEPLOYMENT_GUIDE_FULL.md              # Complete guide
│   ├── RASPBERRY_PI_SETUP.md                 # Pi configuration
│   ├── HEADSCALE_SETUP.md                    # Mesh network setup
│   ├── TRAEFIK_SETUP.md                      # Reverse proxy setup
│   └── NETWORK_TOPOLOGY.md                   # Network diagrams
│
└── monitoring/
    ├── docker-compose.monitoring.yml     # Prometheus + Grafana
    ├── prometheus.yml
    └── grafana-dashboards/
```

## Security Considerations

### VPS Security
1. **Firewall Configuration**
   ```bash
   # Only expose necessary ports
   ufw allow 443/tcp    # HTTPS (Traefik)
   ufw allow 41641/udp  # Headscale (WireGuard)
   ufw enable
   ```

2. **Application Security**
   - Strong SECRET_KEY
   - Secure LOGIN credentials
   - HTTPS only (via Traefik)
   - Rate limiting (via Traefik)

3. **Container Security**
   - Non-root user in containers
   - Read-only root filesystem where possible
   - Resource limits
   - Regular updates

### Mesh Network Security
1. **Headscale ACLs**
   ```json
   {
     "acls": [
       {
         "action": "accept",
         "src": ["100.64.0.1"],
         "dst": ["100.64.0.0/16:9100"]
       }
     ]
   }
   ```

2. **Subnet Routing**
   - Only advertise printer subnets
   - No full network access
   - Principle of least privilege

3. **Raspberry Pi Hardening**
   - Disable SSH password auth
   - Use SSH keys only
   - Automatic security updates
   - Minimal installed packages

## Scalability & High Availability

### Horizontal Scaling (Future)
```yaml
# docker-compose.ha.yml
services:
  app:
    deploy:
      replicas: 3
    
  traefik:
    # Load balances across replicas
  
  redis:
    # Shared session storage
  
  postgres:
    # Shared database (instead of JSON files)
```

### Backup Strategy
1. **Application Data**
   - Automated daily backups
   - Offsite storage (S3/B2)
   - Retention: 30 days

2. **Headscale Data**
   - Database backups
   - Configuration backups
   - Node registration data

3. **Raspberry Pi**
   - SD card images
   - Configuration backups
   - Automated via cron

## Monitoring & Observability

### Application Monitoring
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    # Metrics collection
  
  grafana:
    # Visualization
  
  loki:
    # Log aggregation
  
  node-exporter:
    # System metrics
```

### Key Metrics
- Print job success rate
- Printer connectivity status
- Response times
- Error rates
- Mesh network latency

### Alerting
- Printer offline alerts
- Failed print jobs
- High error rates
- Disk space warnings
- Certificate expiration

## Cost Analysis

### Infrastructure Costs (Monthly)

**Scenario 1: Basic VPS**
- VPS (2 vCPU, 4GB RAM): $10-20
- Domain: $1-2
- **Total: ~$15/month**

**Scenario 2: VPS + Traefik**
- VPS (2 vCPU, 4GB RAM): $10-20
- Domain: $1-2
- SSL: Free (Let's Encrypt)
- **Total: ~$15/month**

**Scenario 3: Full Stack (3 locations)**
- VPS (4 vCPU, 8GB RAM): $20-40
- Domain: $1-2
- 3x Raspberry Pi 4 (4GB): $180 one-time
- 3x Power supplies: $30 one-time
- 3x SD cards: $30 one-time
- **Monthly: ~$25**
- **Initial: ~$265**

## Implementation Phases

### Phase 1: Basic Production Deployment (Week 1)
- [ ] Deploy to VPS with docker-compose
- [ ] Configure domain and DNS
- [ ] Set up basic monitoring
- [ ] Test with local printers
- [ ] Documentation

### Phase 2: Add Traefik (Week 2)
- [ ] Deploy Traefik container
- [ ] Configure Let's Encrypt
- [ ] Set up automatic HTTPS
- [ ] Test SSL certificates
- [ ] Update documentation

### Phase 3: Headscale Mesh Network (Week 3-4)
- [ ] Deploy Headscale server
- [ ] Configure ACLs
- [ ] Set up first Raspberry Pi
- [ ] Test printer connectivity
- [ ] Document setup process

### Phase 4: Scale to Multiple Locations (Week 5-6)
- [ ] Deploy additional Raspberry Pis
- [ ] Configure subnet routing
- [ ] Test cross-location printing
- [ ] Set up monitoring
- [ ] Create runbooks

### Phase 5: USB Printer Support (Week 7)
- [ ] Install CUPS on Raspberry Pis
- [ ] Configure USB printer sharing
- [ ] Test USB printer connectivity
- [ ] Update application if needed
- [ ] Documentation

## Next Steps

1. **Review this architecture** with your team
2. **Choose deployment scenario** based on your needs
3. **Prepare infrastructure** (VPS, domain, Raspberry Pis)
4. **Follow implementation phases** step by step
5. **Test thoroughly** before production use

## Related Documentation

- [`DEPLOYMENT_GUIDE_FULL.md`](DEPLOYMENT_GUIDE_FULL.md) - Complete deployment instructions
- [`RASPBERRY_PI_SETUP.md`](RASPBERRY_PI_SETUP.md) - Raspberry Pi configuration
- [`HEADSCALE_SETUP.md`](HEADSCALE_SETUP.md) - Mesh network setup
- [`TRAEFIK_SETUP.md`](TRAEFIK_SETUP.md) - Reverse proxy configuration
- [`NETWORK_TOPOLOGY.md`](NETWORK_TOPOLOGY.md) - Detailed network diagrams

## Support & Questions

For questions or issues:
1. Check the documentation in `docs/`
2. Review deployment scripts in `deployment/`
3. Open GitHub issue for bugs
4. Consult community forums for general questions

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24  
**Status**: Architecture Design Complete