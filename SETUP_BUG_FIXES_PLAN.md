# Setup.sh Bug Fixes - Implementation Plan

## Overview
This document outlines the bugs identified in the recently deployed setup.sh and provides a detailed plan for fixing them.

## Bug Analysis

### Bug 1: Headscale config.yaml Configuration Issues

**Location:** Lines 1056-1058 in setup.sh

**Current Implementation:**
```bash
sed -i "s|^server_url:.*|server_url: http://$HEADSCALE_DOMAIN:$HEADSCALE_EXTERNAL_HTTP|" config/headscale/config.yaml
sed -i "s|^listen_addr:.*|listen_addr: 0.0.0.0:8080|" config/headscale/config.yaml
```

**Issues:**
- **1a:** `server_url` should match the external FQDN and port configuration based on reverse proxy setup
  - With Traefik + SSL: `https://$HEADSCALE_DOMAIN`
  - With Traefik (no SSL): `http://$HEADSCALE_DOMAIN`
  - With Nginx: `http://$HEADSCALE_DOMAIN` (will become https after certbot)
  - With no reverse proxy: `http://$HEADSCALE_DOMAIN:$HEADSCALE_EXTERNAL_HTTP`

- **1b:** `listen_addr` is hardcoded to `0.0.0.0:8080` but should match the docker internal port (which is 8080, so this is actually correct)

**Fix Strategy:**
- Update `server_url` logic to be conditional based on `$USE_TRAEFIK`, `$USE_SSL`, `$USE_NGINX`, and `$REVERSE_PROXY`
- Keep `listen_addr` as `0.0.0.0:8080` (internal docker port - this is correct)
- Also update the fallback config section (lines 1069-1113)

---

### Bug 2: Nginx Headscale Configuration - proxy_pass URL Handling

**Location:** Lines 1240-1242 in setup.sh

**Current Implementation:**
```nginx
location /web {
    proxy_pass http://headscale_ui_backend/web/;
```

**Issue:**
The proxy_pass directive ends with `/web/` which can cause double-encoding or path issues. According to Headscale documentation and nginx best practices, we should use a variable like `$request_uri`.

**Fix Strategy:**
Update to:
```nginx
location /web {
    proxy_pass http://headscale_ui_backend$request_uri;
```

This approach uses the request URI variable to properly handle the path without double-encoding issues.

---

### Bug 3: Missing TLS Configuration in Headscale Config

**Location:** Lines 1056-1063 and 1068-1113 in setup.sh

**Current Implementation:**
Missing `tls_cert_path` and `tls_key_path` settings

**Issue:**
According to Headscale documentation, when using a reverse proxy for TLS, these should be explicitly set to empty strings:
```yaml
tls_cert_path: ""
tls_key_path: ""
```

**Fix Strategy:**
Add these two lines after the `metrics_listen_addr` configuration in both:
1. The sed customization section (around line 1058)
2. The fallback config section (around line 1072)

---

### Bug 4: Help Text Updates

#### Bug 4.1: Reverse Proxy Option 1 Text
**Location:** Line 178 in setup.sh

**Current Text:**
```bash
echo "   • Recommended for Docker deployments"
```

**Required Text:**
```bash
echo "   • Recommended for Docker deployments where there are no other systems sharing port 80/443"
```

#### Bug 4.2: Reverse Proxy Option 2 Text
**Location:** Lines 180-184 in setup.sh

**Current Text:**
```bash
echo "2) Nginx (Host-based, manual SSL with certbot)"
echo "   • Traditional nginx on host system"
echo "   • Manual SSL setup with certbot"
echo "   • Services exposed to localhost for nginx access"
echo "   • More control, manual configuration"
```

**Required Update:**
Update to include the new description:
```bash
echo "2) Nginx (Host-based, manual SSL with certbot)"
echo "   • Will create a sample nginx configuration for further setup with your existing Nginx installation"
echo "   • Traditional nginx on host system"
echo "   • Manual SSL setup with certbot"
echo "   • Services exposed to localhost for nginx access"
echo "   • More control, manual configuration"
```

#### Bug 4.3: Headscale Description Text
**Location:** Line 276 in setup.sh

**Current Text:**
```bash
echo "  • Use Raspberry Pis as print servers at remote sites"
```

**Required Text:**
```bash
echo "  • Use a Raspberry Pi or another system that supports Tailscale running on the printer's LAN to give access to your Barcode Central server"
```

---

### Bug 5: Firewall Configuration - Port Requirements

**Location:** Lines 1344-1368 in setup.sh

**Current Implementation:**
References `HEADSCALE_WIREGUARD_PORT` variable (line 26: `HEADSCALE_WIREGUARD_PORT="41641"`)

**Issue:**
According to Headscale documentation (https://headscale.net/stable/setup/requirements/#ports-in-use), the required ports are:

| Port | Protocol | Public? | Purpose | Notes |
|------|----------|---------|---------|-------|
| 80 | tcp | yes | HTTP | Let's Encrypt HTTP-01 challenge (if using built-in ACME) |
| 443 | tcp | yes | HTTPS | Required for Tailscale clients; also used by embedded DERP |
| 3478 | udp | yes | STUN | Required if embedded DERP server is enabled |
| 50443 | tcp | yes | gRPC | Only if using remote-control Headscale |
| 9090 | tcp | **NO** | Metrics | Debug endpoint - should NOT be exposed publicly |

The "WireGuard port" (41641) reference appears to be outdated. Headscale uses the DERP protocol over HTTPS (port 443) and STUN (port 3478/udp) for NAT traversal, not a separate WireGuard port.

**Fix Strategy:**

1. **Remove the WireGuard port variable** from line 26
2. **Remove WireGuard port prompts** from lines 391-400
3. **Update docker-compose.yml generation** to remove WireGuard port exposure (lines 843, 852)
4. **Update firewall instructions** (lines 1344-1368) to reflect correct ports
5. **Update .env file generation** to remove `HEADSCALE_WIREGUARD_PORT` (line 633)
6. **Update the review screen** to remove WireGuard port display (line 557)

**Correct Firewall Instructions:**

When using **Traefik with SSL**:
```bash
sudo ufw allow 80/tcp       # HTTP (Let's Encrypt)
sudo ufw allow 443/tcp      # HTTPS (Barcode Central + Headscale)
sudo ufw allow 3478/udp     # STUN (Headscale DERP)
```

When using **Traefik without SSL**:
```bash
sudo ufw allow 80/tcp       # HTTP (Barcode Central + Headscale)
sudo ufw allow 3478/udp     # STUN (Headscale DERP)
```

When using **Nginx**:
```bash
sudo ufw allow 80/tcp       # HTTP
sudo ufw allow 443/tcp      # HTTPS (after certbot)
sudo ufw allow 3478/udp     # STUN (Headscale DERP)
```

When using **no reverse proxy**:
```bash
sudo ufw allow [HTTP_PORT]/tcp        # Barcode Central
sudo ufw allow [HEADSCALE_HTTP]/tcp   # Headscale API
sudo ufw allow 3478/udp               # STUN (Headscale DERP)
# Optional: sudo ufw allow 50443/tcp  # gRPC (if using remote CLI)
```

**Important Notes to Add:**
- Port 9090 (metrics) should NOT be exposed publicly - it's for internal monitoring only
- The embedded DERP server uses port 443 (HTTPS) and 3478 (STUN) for relay/NAT traversal
- If using an external reverse proxy, only expose ports 80/443 externally; Headscale will be accessed through the reverse proxy

---

## Implementation Order

### Phase 1: Simple Text Updates
1. ✅ **Bug 4.1** - Update reverse proxy option 1 help text
2. ✅ **Bug 4.2** - Update reverse proxy option 2 help text
3. ✅ **Bug 4.3** - Update Headscale description text

### Phase 2: Configuration File Updates
4. ✅ **Bug 3** - Add TLS configuration to both sed section and fallback config
5. ✅ **Bug 2** - Update nginx proxy_pass configuration
6. ✅ **Bug 1a** - Fix server_url with proper conditionals

### Phase 3: Port Configuration Overhaul
7. ✅ **Bug 5** - Remove WireGuard port references throughout the file:
   - Remove variable declaration
   - Remove user prompts
   - Update docker-compose generation
   - Update .env generation
   - Update firewall instructions
   - Update review screen
   - Add correct STUN port (3478/udp)

### Phase 4: Validation
8. ✅ Review all changes for consistency
9. ✅ Verify conditional logic flows correctly
10. ✅ Ensure all generated files will be syntactically correct

---

## Detailed Change Map

### File: setup.sh

| Line Range | Change Type | Description |
|------------|-------------|-------------|
| 26 | REMOVE | `HEADSCALE_WIREGUARD_PORT="41641"` variable |
| 178 | UPDATE | Add "where there are no other systems sharing port 80/443" |
| 180-184 | UPDATE | Add nginx sample configuration note |
| 276 | UPDATE | Update Raspberry Pi description |
| 391-400 | REMOVE | WireGuard port prompts |
| 557 | REMOVE | WireGuard port in review screen |
| 633 | REMOVE | HEADSCALE_WIREGUARD_PORT in .env |
| 843, 852 | UPDATE | Remove WireGuard port exposure, keep STUN 3478/udp |
| 1056-1063 | UPDATE | Add conditional server_url logic + TLS config |
| 1069-1113 | UPDATE | Add TLS config to fallback + update server_url |
| 1242 | UPDATE | Change proxy_pass to use $request_uri |
| 1344-1368 | UPDATE | Complete rewrite of firewall section with correct ports |

---

## Testing Checklist

After implementation, test the following scenarios:

### Scenario 1: Traefik with SSL + Headscale
- [ ] `server_url` should be `https://HEADSCALE_DOMAIN`
- [ ] Firewall shows: 80, 443, 3478/udp
- [ ] No WireGuard port references
- [ ] Nginx config not generated
- [ ] TLS config has empty strings

### Scenario 2: Traefik without SSL + Headscale  
- [ ] `server_url` should be `http://HEADSCALE_DOMAIN`
- [ ] Firewall shows: 80, 3478/udp
- [ ] No WireGuard port references

### Scenario 3: Nginx + Headscale
- [ ] `server_url` should be `http://HEADSCALE_DOMAIN`
- [ ] Nginx config uses `$request_uri` for /web proxy
- [ ] Firewall shows: 80, 443, 3478/udp
- [ ] No WireGuard port references

### Scenario 4: No Reverse Proxy + Headscale
- [ ] `server_url` should be `http://HEADSCALE_DOMAIN:8080`
- [ ] Firewall shows: HTTP_PORT, 8080, 3478/udp
- [ ] No WireGuard port references

### Scenario 5: No Headscale
- [ ] No headscale config generated
- [ ] No STUN port in firewall
- [ ] Standard Barcode Central setup works

---

## Risk Assessment

### Low Risk Changes
- Bug 4.1, 4.2, 4.3 (text updates only)
- Bug 3 (adding config that should have been there)

### Medium Risk Changes
- Bug 2 (nginx config change - affects URL routing)
- Bug 1a (server_url - affects Headscale connectivity)

### Higher Risk Changes
- Bug 5 (removing WireGuard port - multiple file locations)
  - Risk: Breaking existing installations if they relied on this port
  - Mitigation: This is a new deployment, so no backwards compatibility needed
  - The correct approach is STUN/DERP, not WireGuard port exposure

---

## Post-Implementation Actions

1. Update SETUP_REFACTORING_IMPLEMENTATION_SUMMARY.md with bug fix details
2. Update HEADSCALE_MODERNIZATION_SUMMARY.md with correct port requirements
3. Consider creating a SETUP_CHANGELOG.md to track versions
4. Test all deployment scenarios (Traefik, Nginx, None × Headscale, No Headscale)

---

## Questions for User

Before finalizing the implementation, please confirm:

1. **WireGuard Port Removal**: You mentioned the WireGuard port might have been updated or is no longer required. Based on Headscale's official documentation, the correct approach is:
   - DERP over HTTPS (port 443)
   - STUN for NAT traversal (port 3478/udp)
   - No separate WireGuard port exposure needed
   
   **Confirm**: Remove all WireGuard port (41641) references? ✓

2. **Bug 1b Listen Address**: The current `listen_addr: 0.0.0.0:8080` appears correct for the Docker internal port. Should we make any changes here, or is this already correct? 
   
   **Assessment**: This is correct - no changes needed.

3. **Server URL for Nginx**: Should it be `http://HEADSCALE_DOMAIN` initially (before certbot), or should we set it to `https://HEADSCALE_DOMAIN` in anticipation of certbot setup?
   
   **Recommendation**: Use `http://` initially, user updates to `https://` after certbot, or we document that they need to update the config after SSL setup.

---

## Implementation Ready

This plan is ready for implementation. The changes are well-scoped, risks are identified, and the testing strategy is clear. Proceed to Code mode for implementation.
