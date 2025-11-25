# Quick Fix: Headscale UI 502 Bad Gateway

## Your Current Situation

✅ nginx is configured correctly (proxying to localhost:3009)
✅ headscale-ui container is running
✅ Port 3009 is exposed correctly
❌ Getting 502 Bad Gateway error
❌ headscale container shows as "unhealthy"

## The Problem

The 502 error means headscale-ui **cannot connect to the headscale backend**. This is almost always because:
1. **HEADSCALE_API_KEY is missing or invalid** (90% of cases)
2. Headscale container is unhealthy

## Quick Fix (5 minutes)

### Step 1: Check Headscale Health
```bash
cd /opt/barcodecentral
docker compose ps
```

If headscale shows "unhealthy", check its logs:
```bash
docker compose logs headscale | tail -50
```

### Step 2: Generate API Key
```bash
# Generate a new API key
docker compose exec headscale headscale apikeys create

# You'll get output like:
# 2024-11-25T05:00:00Z INF API key created key=hs_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy the key that starts with `hs_`**

### Step 3: Add API Key to .env
```bash
# Edit .env file
nano .env

# Find the line that says:
# HEADSCALE_API_KEY=

# Replace it with your actual key:
HEADSCALE_API_KEY=hs_your_actual_key_here

# Save and exit (Ctrl+X, Y, Enter)
```

### Step 4: Restart headscale-ui
```bash
docker compose restart headscale-ui

# Wait 10 seconds for it to start
sleep 10
```

### Step 5: Test
```bash
# Test from the server
curl -I http://localhost:3009/

# Should return HTTP 200 or 401 (auth required), NOT 502

# Test from your browser
# https://barcode.zendrian.com/headscale-admin/
```

## If Still Getting 502

### Run the Diagnostic Script
```bash
./diagnose_headscale_ui_502.sh
```

This will tell you exactly what's wrong.

### Common Issues

#### Issue 1: Headscale Won't Start
```bash
# Check logs
docker compose logs headscale

# Common causes:
# - Port 8999 already in use
# - Configuration file error
# - Database corruption

# Fix: Restart headscale
docker compose restart headscale
```

#### Issue 2: API Key Not Working
```bash
# Verify the key is set correctly
docker compose exec headscale-ui env | grep "^KEY="

# Should show: KEY=hs_your_key_here
# If empty or wrong, fix .env and restart
```

#### Issue 3: Network Issues
```bash
# Test if headscale-ui can reach headscale
docker compose exec headscale-ui curl http://headscale:8080/health

# Should return: {"status":"ok"}
# If not, there's a Docker network issue
```

## Verification Checklist

After applying the fix, verify:

- [ ] `docker compose ps` shows headscale as "healthy"
- [ ] `docker compose ps` shows headscale-ui as "Up"
- [ ] `curl -I http://localhost:3009/` returns 200 or 401 (not 502)
- [ ] `docker compose logs headscale-ui` shows no errors
- [ ] Browser shows Headscale UI login page (not 502)

## Expected Result

After the fix, you should see:
- **Browser**: Headscale UI login page at https://barcode.zendrian.com/headscale-admin/
- **Login**: Use credentials from `.env` file (HEADSCALE_UI_USER and HEADSCALE_UI_PASSWORD)
- **Dashboard**: Headscale admin interface

## Still Need Help?

If you're still getting 502 after following these steps:

1. Run the diagnostic script:
   ```bash
   ./diagnose_headscale_ui_502.sh
   ```

2. Check the full logs:
   ```bash
   docker compose logs headscale-ui > headscale-ui.log
   docker compose logs headscale > headscale.log
   ```

3. Verify environment variables:
   ```bash
   cat .env | grep HEADSCALE
   ```

4. Check Docker networks:
   ```bash
   docker network inspect barcode-network
   docker network inspect headscale-network
   ```

## Summary

The fix is simple:
1. Generate API key: `docker compose exec headscale headscale apikeys create`
2. Add to .env: `HEADSCALE_API_KEY=hs_your_key`
3. Restart: `docker compose restart headscale-ui`
4. Test: `curl -I http://localhost:3009/`

This should resolve the 502 error in 90% of cases.