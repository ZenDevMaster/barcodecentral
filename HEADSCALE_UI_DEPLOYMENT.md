# Headscale UI Deployment Guide

## Quick Start

This guide shows how to deploy Headscale with its web admin interface integrated into your Barcode Central deployment.

## Prerequisites

- Barcode Central already deployed (or being deployed)
- Headscale enabled in your deployment
- Domain name configured (for external access)

## Deployment Steps

### Step 1: Run Setup Script

```bash
./setup.sh
```

When prompted about Headscale:

```
Do you want to enable Headscale mesh VPN? [y/N]: y
Do you want to enable Headscale Web Admin UI? [Y/n]: y
```

The setup script will:
- Generate secure credentials for the UI
- Configure docker-compose with Headscale UI service
- Set up routing (Traefik or nginx)
- Create necessary environment variables

### Step 2: Deploy Services

```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                STATUS              PORTS
barcode-central     Up (healthy)        0.0.0.0:5000->5000/tcp
headscale           Up (healthy)        0.0.0.0:8080->8080/tcp, 0.0.0.0:41641->41641/udp
headscale-ui        Up                  3000/tcp
traefik             Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Step 3: Generate Headscale API Key

```bash
# Run the API key generation script
./scripts/generate-headscale-api-key.sh
```

This will output:
```
✓ API Key generated successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Key: hs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Add this to your .env file:
HEADSCALE_API_KEY=hs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 4: Update Environment File

```bash
# Edit .env file
nano .env

# Add the API key (at the bottom of the Headscale section)
HEADSCALE_API_KEY=hs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Save and exit (Ctrl+X, Y, Enter).

### Step 5: Restart Headscale UI

```bash
# Restart the UI to pick up the API key
docker compose restart headscale-ui

# Check logs to verify it started correctly
docker compose logs -f headscale-ui
```

Look for:
```
Successfully connected to Headscale API
Server listening on port 3000
```

### Step 6: Access the Web Interface

**With Traefik (HTTPS):**
```
https://your-domain.com/headscale-admin/
```

**Without Traefik (HTTP):**
```
http://your-domain.com:5000/headscale-admin/
```

**Login Credentials:**
- Username: (from setup.sh, default: `admin`)
- Password: (generated during setup, check `.env` file)

To view your credentials:
```bash
grep HEADSCALE_UI .env
```

## Post-Deployment Configuration

### 1. Create Headscale User/Namespace

```bash
# Create a namespace for your devices
docker exec headscale headscale namespaces create default

# Verify
docker exec headscale headscale namespaces list
```

### 2. Generate Pre-Auth Keys (for devices)

Via Web UI:
1. Navigate to "API Keys" section
2. Click "Create Pre-Auth Key"
3. Set expiration (e.g., 90 days)
4. Enable "Reusable" if needed
5. Copy the generated key

Via CLI:
```bash
docker exec headscale headscale preauthkeys create --reusable --expiration 90d --namespace default
```

### 3. Configure ACL Policies

Via Web UI:
1. Navigate to "ACL" section
2. Edit the policy JSON
3. Save changes

Via CLI:
```bash
# Edit the ACL file
nano headscale/config/acl.json

# Reload Headscale
docker compose restart headscale
```

## Common Tasks

### View Connected Devices

**Web UI:** Navigate to "Machines" section

**CLI:**
```bash
docker exec headscale headscale nodes list
```

### Approve Routes

**Web UI:** Navigate to "Routes" section, click "Approve"

**CLI:**
```bash
# List routes
docker exec headscale headscale routes list

# Approve a route
docker exec headscale headscale routes enable -r <route-id>
```

### Manage Users

**Web UI:** Navigate to "Users" section

**CLI:**
```bash
# List users
docker exec headscale headscale users list

# Create user
docker exec headscale headscale users create <username>

# Delete user
docker exec headscale headscale users destroy <username>
```

### Rotate API Key

```bash
# Generate new key
./scripts/generate-headscale-api-key.sh

# Update .env with new key
nano .env

# Restart UI
docker compose restart headscale-ui

# Revoke old key (optional)
docker exec headscale headscale apikeys expire <old-key-id>
```

## Troubleshooting

### UI Not Accessible

**Check if container is running:**
```bash
docker compose ps headscale-ui
```

**Check logs:**
```bash
docker compose logs headscale-ui
```

**Common issues:**
- API key not set or invalid
- Headscale service not running
- Reverse proxy misconfiguration

### Authentication Fails

**Verify credentials:**
```bash
grep HEADSCALE_UI .env
```

**Reset password:**
```bash
# Edit .env and change HEADSCALE_UI_PASSWORD
nano .env

# Restart UI
docker compose restart headscale-ui
```

### API Connection Error

**Test Headscale API:**
```bash
# From host
curl http://localhost:8080/health

# From UI container
docker exec headscale-ui curl http://headscale:8080/health
```

**Check network connectivity:**
```bash
docker exec headscale-ui ping headscale
```

### 404 Error on /headscale-admin

**Traefik:** Check labels are correct
```bash
docker inspect headscale-ui | grep traefik
```

**Nginx:** Verify location block exists
```bash
cat nginx.conf | grep -A 10 "location /headscale-admin"
```

## Security Recommendations

### 1. Use Strong Passwords

```bash
# Generate a strong password
openssl rand -base64 32
```

### 2. Enable IP Whitelisting (Optional)

**Traefik:**
```yaml
- "traefik.http.middlewares.headscale-ui-ipwhitelist.ipwhitelist.sourcerange=192.168.1.0/24,10.0.0.0/8"
- "traefik.http.routers.headscale-ui.middlewares=headscale-ui-stripprefix,headscale-ui-headers,security-headers,headscale-ui-ipwhitelist"
```

**Nginx:**
```nginx
location /headscale-admin/ {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    # ... rest of config
}
```

### 3. Rotate API Keys Regularly

Set a reminder to rotate API keys every 90 days:
```bash
# Add to crontab
0 0 1 */3 * /path/to/scripts/generate-headscale-api-key.sh
```

### 4. Enable Audit Logging

Edit `headscale/config/config.yaml`:
```yaml
log:
  level: info
  format: json  # Better for parsing
```

### 5. Regular Backups

```bash
# Backup Headscale database
docker exec headscale cp /var/lib/headscale/db.sqlite /var/lib/headscale/db.sqlite.backup

# Copy to host
docker cp headscale:/var/lib/headscale/db.sqlite.backup ./backups/
```

## Monitoring

### Health Checks

```bash
# Check all services
docker compose ps

# Check Headscale health
curl http://localhost:8080/health

# Check UI health
curl http://localhost:3000/
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f headscale-ui

# Last 100 lines
docker compose logs --tail=100 headscale-ui
```

### Resource Usage

```bash
# Container stats
docker stats headscale headscale-ui

# Disk usage
docker system df
```

## Updating

### Update Headscale UI

```bash
# Pull latest image
docker compose pull headscale-ui

# Restart with new image
docker compose up -d headscale-ui

# Verify
docker compose logs headscale-ui
```

### Update Headscale

```bash
# Pull latest image
docker compose pull headscale

# Restart
docker compose up -d headscale

# Verify
docker exec headscale headscale version
```

## Integration with Barcode Central

The Headscale UI is fully integrated with your Barcode Central deployment:

1. **Single Domain**: Both apps accessible from same domain
2. **Unified SSL**: One certificate covers both apps
3. **Shared Network**: Services can communicate internally
4. **Coordinated Deployment**: Managed via same docker-compose file

### Accessing Both Interfaces

```
Main App:        https://print.example.com/
Headscale Admin: https://print.example.com/headscale-admin/
```

### Managing Print Servers

1. Set up Raspberry Pi print servers at remote locations
2. Connect them to Headscale mesh network
3. Configure printers in Barcode Central using Tailscale IPs
4. Monitor connectivity via Headscale UI

## Support

For issues or questions:

1. Check logs: `docker compose logs`
2. Review documentation: `HEADSCALE_UI_INTEGRATION_PLAN.md`
3. Headscale docs: https://headscale.net/
4. Headscale UI repo: https://github.com/gurucomputing/headscale-ui

## Next Steps

After deploying Headscale UI:

1. ✅ Set up Raspberry Pi print servers (see `RASPBERRY_PI_SETUP.md`)
2. ✅ Configure ACL policies for your network
3. ✅ Add printers to Barcode Central
4. ✅ Test printing across mesh network
5. ✅ Set up monitoring and backups

---

**Congratulations!** Your Headscale web admin interface is now deployed and integrated with Barcode Central. 🎉