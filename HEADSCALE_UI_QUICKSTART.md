# Headscale UI - Quick Start Guide

## What is Headscale UI?

Headscale UI is a web-based admin interface for managing your Headscale mesh network. It provides an easy way to:
- Manage users and machines
- Configure routes and ACLs
- Monitor network status
- Generate pre-auth keys

## Quick Deployment

### 1. Run Setup

```bash
./setup.sh
```

When prompted:
- Enable Headscale: **Yes**
- Enable Headscale UI: **Yes**

### 2. Deploy Services

```bash
docker compose up -d
```

### 3. Generate API Key

```bash
./scripts/generate-headscale-api-key.sh
```

### 4. Restart UI

```bash
docker compose restart headscale-ui
```

### 5. Access the UI

**With Traefik (HTTPS):**
```
https://your-domain.com/headscale-admin/
```

**Without Traefik:**
```
http://your-domain.com:5000/headscale-admin/
```

## Credentials

View your credentials:
```bash
grep HEADSCALE_UI .env
```

Or check the saved credentials file:
```bash
cat config/headscale/.credentials
```

## Common Tasks

### Create a User/Namespace

**Via UI:**
1. Navigate to "Users" section
2. Click "Create User"
3. Enter username
4. Save

**Via CLI:**
```bash
docker exec headscale headscale users create default
```

### Generate Pre-Auth Key

**Via UI:**
1. Navigate to "API Keys" section
2. Click "Create Pre-Auth Key"
3. Set expiration (e.g., 90 days)
4. Enable "Reusable" if needed
5. Copy the key

**Via CLI:**
```bash
./scripts/generate-authkey.sh
```

### Approve Routes

**Via UI:**
1. Navigate to "Routes" section
2. Find the route to approve
3. Click "Approve"

**Via CLI:**
```bash
docker exec headscale headscale routes list
docker exec headscale headscale routes enable -r <route-id>
```

### View Connected Devices

**Via UI:**
Navigate to "Machines" section

**Via CLI:**
```bash
docker exec headscale headscale nodes list
```

## Backup Your Configuration

### Backup Config Folder

```bash
tar -czf barcode-central-config-$(date +%Y%m%d).tar.gz config/
```

This includes:
- Headscale configuration
- ACL policies
- Nginx/Traefik configs
- UI credentials

### Backup Data Folder

```bash
tar -czf barcode-central-data-$(date +%Y%m%d).tar.gz data/
```

This includes:
- Headscale database
- Private keys
- SSL certificates

## Troubleshooting

### UI Not Accessible

```bash
# Check if container is running
docker compose ps headscale-ui

# Check logs
docker compose logs headscale-ui
```

### Authentication Fails

```bash
# Verify credentials
cat config/headscale/.credentials

# Reset if needed - edit .env and restart
docker compose restart headscale-ui
```

### API Connection Error

```bash
# Test Headscale API
curl http://localhost:8080/health

# Check network connectivity
docker exec headscale-ui ping headscale
```

## Directory Structure

```
project/
├── config/
│   ├── headscale/
│   │   ├── config.yaml         # Headscale config
│   │   ├── acl.json            # ACL policies
│   │   └── .credentials        # UI credentials
│   └── nginx/
│       └── barcode-central.conf # Nginx config
├── data/
│   ├── headscale/              # Database & keys
│   ├── letsencrypt/            # SSL certificates
│   └── tailscale/              # Tailscale state
├── .env                        # Environment variables
└── docker-compose.yml          # Service definitions
```

## Security Best Practices

1. **Use Strong Passwords**: Auto-generated passwords are recommended
2. **Rotate API Keys**: Regenerate every 90 days
3. **Backup Regularly**: Backup `config/` and `data/` folders
4. **Enable HTTPS**: Use Traefik with Let's Encrypt
5. **Restrict Access**: Consider IP whitelisting for `/headscale-admin/`

## Next Steps

1. ✅ Create users/namespaces in Headscale UI
2. ✅ Generate pre-auth keys for devices
3. ✅ Set up Raspberry Pi print servers (see `RASPBERRY_PI_SETUP.md`)
4. ✅ Configure ACL policies for your network
5. ✅ Add printers to Barcode Central

## More Information

- **Full Documentation**: `HEADSCALE_UI_DEPLOYMENT.md`
- **Integration Plan**: `HEADSCALE_UI_INTEGRATION_PLAN.md`
- **Summary**: `HEADSCALE_UI_SUMMARY.md`
- **Raspberry Pi Setup**: `RASPBERRY_PI_SETUP.md`

## Support

For issues or questions:
1. Check logs: `docker compose logs headscale-ui`
2. Review documentation
3. Headscale docs: https://headscale.net/
4. Headscale UI repo: https://github.com/gurucomputing/headscale-ui