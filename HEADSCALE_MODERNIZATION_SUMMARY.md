# Headscale Configuration Modernization Summary

## Overview
Updated the headscale configuration in `setup.sh` to use the latest configuration format from the official headscale repository and modern Docker best practices.

## Changes Made

### 1. Dynamic Configuration Fetching (setup.sh lines 865-946)

**Before:**
- Hardcoded outdated configuration format
- Used old field names (`db_type`, `db_path`, `ip_prefixes`)
- Static configuration that would become outdated

**After:**
- Downloads latest `config-example.yaml` from official headscale GitHub repository
- Customizes only required fields using `sed`:
  - `server_url`
  - `listen_addr` → `0.0.0.0:8080`
  - `metrics_listen_addr` → `0.0.0.0:9090`
  - `grpc_listen_addr` → `0.0.0.0:50443`
  - `unix_socket` → `/var/run/headscale/headscale.sock`
  - `base_domain` → `headscale.local`
  - `policy.path` → `/etc/headscale/acl.json`
- Fallback to basic modern config if download fails

### 2. Docker Compose Modernization (setup.sh lines 726-755)

#### Image Version
**Before:** `headscale/headscale:v0.27.1` (pinned old version)
**After:** `headscale/headscale:latest` (always up-to-date)

#### Security Enhancements
**Added:**
- `read_only: true` - Read-only root filesystem for security
- `tmpfs: [/var/run/headscale]` - Temporary filesystem for runtime files

#### Port Bindings
**Before:**
```yaml
ports:
  - "${HEADSCALE_PORT:-8080}:8080"
  - "41641:41641/udp"
```

**After:**
```yaml
ports:
  - "0.0.0.0:${HEADSCALE_PORT:-8080}:8080"  # API/HTTP
  - "0.0.0.0:9090:9090"                      # Metrics (NEW)
  - "41641:41641/udp"                        # WireGuard
```

**Changes:**
- Explicitly bind to `0.0.0.0` for external access (as per documentation)
- Added metrics port `9090` exposure
- WireGuard port remains unchanged

#### Health Check
**Before:** `["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]`
**After:** `["CMD", "headscale", "health"]`

**Benefits:**
- Uses official headscale health check command
- More reliable and faster
- No dependency on external tools (wget)
- Follows official documentation recommendation

### 3. Configuration Format Updates

#### Modern Database Configuration
**Old format:**
```yaml
db_type: sqlite3
db_path: /var/lib/headscale/db.sqlite
```

**New format:**
```yaml
database:
  type: sqlite
  sqlite:
    path: /var/lib/headscale/db.sqlite
    write_ahead_log: true
```

#### Modern IP Prefixes
**Old format:**
```yaml
ip_prefixes:
  - 100.64.0.0/10
```

**New format:**
```yaml
prefixes:
  v4: 100.64.0.0/10
  v6: fd7a:115c:a1e0::/48
```

#### Policy Configuration
**Old format:**
```yaml
policy:
  path: /etc/headscale/acl.json
```

**New format:**
```yaml
policy:
  mode: file
  path: /etc/headscale/acl.json
```

## Benefits

### 1. Always Up-to-Date Configuration
- Fetches latest config from official source on each setup
- Automatically includes new features and improvements
- Reduces technical debt

### 2. Enhanced Security
- Read-only filesystem prevents container modifications
- tmpfs for runtime files (no persistent writable storage)
- Follows container security best practices

### 3. Better Monitoring
- Metrics port (9090) exposed for Prometheus/monitoring
- Proper health check endpoint

### 4. Improved Reliability
- Official health check command
- Modern configuration format with better validation
- WAL mode enabled for SQLite (better concurrent performance)

### 5. External Access Support
- Proper `0.0.0.0` binding for external network access
- Supports both LAN and internet deployments

## Testing the Configuration

To verify the changes work correctly:

```bash
# Run setup
./setup.sh

# Enable headscale when prompted
# After setup completes, start the services
docker compose up -d

# Verify headscale is running with new config
docker compose ps

# Check health
curl http://localhost:8080/health

# Verify metrics endpoint
curl http://localhost:9090/metrics

# Check logs for any issues
docker compose logs headscale

# Test health check command directly
docker exec headscale headscale health
```

## Compatibility Notes

- The new configuration is compatible with headscale v0.23.0+
- Existing data in `/var/lib/headscale` will be preserved
- ACL format remains unchanged (backward compatible)
- Clients using the mesh network will continue working without changes

## Files Modified

1. **setup.sh** - Lines 726-755, 865-946
   - Docker Compose generation section
   - Headscale configuration creation section

## Migration Path

For existing deployments:

1. **Backup existing configuration:**
   ```bash
   cp config/headscale/config.yaml config/headscale/config.yaml.backup
   ```

2. **Run setup.sh:**
   - Configuration download will be skipped if file exists
   - To force update, delete old config first:
     ```bash
     rm config/headscale/config.yaml
     ./setup.sh
     ```

3. **Regenerate docker-compose.yml:**
   ```bash
   ./setup.sh
   ```

4. **Restart services:**
   ```bash
   docker compose down
   docker compose up -d
   ```

## Reference Documentation

- Official headscale config: https://github.com/juanfont/headscale/blob/main/config-example.yaml
- Docker deployment: https://headscale.net/running-headscale-container/
- Health checks: https://headscale.net/ref/health/

## Related Issues Fixed

1. ✅ Outdated configuration format
2. ✅ Missing read-only filesystem security
3. ✅ Incorrect health check command
4. ✅ Missing metrics port exposure
5. ✅ Improper port binding for external access
6. ✅ Old Docker image version
7. ✅ Missing tmpfs for runtime files