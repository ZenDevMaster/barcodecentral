# Setup Script Re-run Guide

## Overview

The `setup.sh` script now intelligently detects existing configuration when re-run, allowing you to preserve your current settings while making selective updates. This prevents accidental credential loss and saves time during reconfiguration.

## What Gets Detected

When you re-run `setup.sh`, it automatically detects and offers to preserve:

### Always Detected
- **SECRET_KEY** - Automatically preserved to maintain active user sessions
- **LOGIN_USER** - Admin username
- **LOGIN_PASSWORD** - Admin password
- **HTTP_PORT** - Application port

### Detected for External Access
- **DOMAIN** - Your FQDN (used for both Traefik and manual nginx setup)
- **ACME_EMAIL** - Let's Encrypt notification email (if SSL was enabled)

### Detected for Headscale
- **HEADSCALE_DOMAIN** - Headscale server domain/IP
- **HEADSCALE_PORT** - Headscale API port
- **HEADSCALE_UI_PORT** - Headscale UI host port (default: 3000)
- **HEADSCALE_UI_USER** - Headscale UI username (from config/headscale/.credentials)
- **HEADSCALE_UI_PASSWORD** - Headscale UI password (from config/headscale/.credentials)

## User Experience

### First Run
When running `setup.sh` for the first time, you'll see the standard setup wizard with no existing configuration detected.

### Re-run with Existing Configuration

#### Welcome Screen
```
Welcome to Barcode Central Setup!
This wizard will configure your deployment.

ℹ Detected existing .env configuration

Press Enter to continue...
```

#### Domain Configuration (Step 2)
```
[2/7] Domain Configuration
Enter your fully qualified domain name (FQDN).
Example: print.example.com

ℹ Current domain: print.example.com
Domain (FQDN) [print.example.com]: _
```
- Press Enter to keep existing domain
- Type new domain to change it

#### ACME Email (Step 3, if SSL enabled)
```
ℹ Current email: admin@example.com
Email for Let's Encrypt notifications [admin@example.com]: _
```

#### Headscale Configuration (Step 4, if enabled)
```
ℹ Current Headscale domain: headscale.example.com
Enter Headscale domain or IP [headscale.example.com]: _

Headscale port [8080]: _

Configure Headscale UI port (default: 3000)
Change this if port 3000 is already in use on your system.
Headscale UI port [3000]: _
```

#### Application Credentials (Step 5)
```
[5/7] Application Credentials
Configure admin access for Barcode Central.

ℹ Found existing credentials

Admin username [admin]: _

Password options:
1) Keep existing password (recommended)
2) Generate new secure password
3) Enter custom password
Choice [1-3]: _
```

**Password Options:**
1. **Keep existing** - Preserves your current password (recommended)
2. **Generate new** - Creates a new secure random password
3. **Custom** - Enter your own password with confirmation

**Secret Key:**
```
✓ Using existing secret key (preserves active sessions)
```
The secret key is automatically preserved to prevent invalidating active user sessions.

#### Port Configuration (Step 6)
```
[6/7] Port Configuration
Configure the HTTP port for the application.

HTTP port [5000]: _
```

## Best Practices

### When to Keep Existing Values
- **SECRET_KEY** - Always kept automatically (maintains sessions)
- **LOGIN_PASSWORD** - Keep if you remember it and it's secure
- **DOMAIN** - Keep unless you're changing your domain
- **HTTP_PORT** - Keep unless you have port conflicts

### When to Change Values
- **LOGIN_PASSWORD** - Change if you suspect it's compromised
- **DOMAIN** - Change if migrating to a new domain
- **HTTP_PORT** - Change if you have port conflicts
- **HEADSCALE_UI_PORT** - Change if port 3000 is already in use (e.g., by another service)
- **ACME_EMAIL** - Change if you want notifications at a different address

### Security Considerations

1. **Password Display**: Passwords are never displayed in full. When showing existing credentials, only masked versions are shown (e.g., `admi****word`)

2. **Secret Key Preservation**: The SECRET_KEY is automatically preserved to maintain session continuity. Changing it would log out all active users.

3. **Credential Files**: The `.env` file permissions are set to `600` (owner read/write only) for security.

4. **Headscale UI Credentials**: Stored separately in `config/headscale/.credentials` with `600` permissions.

## Common Scenarios

### Scenario 1: Changing Only the Domain
```bash
./setup.sh
# Keep all settings the same except:
# - Step 2: Enter new domain
# - Step 3: Confirm or update ACME email
# - Step 5: Choose option 1 (keep existing password)
```

### Scenario 2: Resetting Admin Password
```bash
./setup.sh
# Keep all settings the same except:
# - Step 5: Choose option 2 (generate new password) or 3 (custom password)
```

### Scenario 3: Changing Ports
```bash
./setup.sh
# Keep all settings the same except:
# - Step 4: Enter new Headscale UI port (if using Headscale)
# - Step 6: Enter new HTTP port
```

### Scenario 4: Adding Headscale to Existing Setup
```bash
./setup.sh
# Keep existing settings:
# - Step 1: Choose same access type
# - Step 2-3: Keep domain/SSL settings
# - Step 4: Enable Headscale (new)
# - Step 5: Keep existing credentials
```

## Troubleshooting

### "Detected existing configuration" but values aren't showing
- Ensure `.env` file exists in the project root
- Check that `.env` has proper format: `KEY=value`
- Verify file permissions allow reading

### Want to start fresh
```bash
# Backup existing configuration
cp .env .env.backup

# Remove .env to start fresh
rm .env

# Run setup
./setup.sh
```

### Accidentally changed a value
- Press Ctrl+C to cancel setup
- Run `./setup.sh` again
- The previous values will still be detected

## Technical Details

### Detection Mechanism
The script uses a `load_existing_config()` function that:
1. Checks for `.env` file existence
2. Parses specific configuration keys using `grep` and `cut`
3. Stores values in `EXISTING_*` variables
4. Presents these as defaults throughout the wizard

### Files Checked
- `.env` - Main configuration file
- `config/headscale/.credentials` - Headscale UI credentials (if Headscale was enabled)

### Preserved vs Generated
- **Always Preserved**: SECRET_KEY (if exists)
- **Offered as Default**: All other detected values
- **User Choice**: Password can be kept, regenerated, or custom

## Related Documentation
- [QUICKSTART.md](QUICKSTART.md) - Initial setup guide
- [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) - Production deployment
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment information