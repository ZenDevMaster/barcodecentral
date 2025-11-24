#!/bin/bash
# Backup Barcode Central data files
# Usage: ./scripts/backup.sh

set -e

# Create backups directory if it doesn't exist
mkdir -p backups

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_${TIMESTAMP}"

echo "=========================================="
echo "Backing up Barcode Central Data"
echo "=========================================="
echo "Backup directory: ${BACKUP_DIR}"
echo ""

# Create temporary backup directory
mkdir -p "$BACKUP_DIR"

# Backup data files
echo "Backing up data files..."
[ -f history.json ] && cp history.json "$BACKUP_DIR/" && echo "  ✓ history.json"
[ -f printers.json ] && cp printers.json "$BACKUP_DIR/" && echo "  ✓ printers.json"

# Backup templates directory
if [ -d templates_zpl ]; then
    echo "Backing up ZPL templates..."
    cp -r templates_zpl "$BACKUP_DIR/"
    echo "  ✓ templates_zpl/"
fi

# Backup .env file (excluding sensitive data in production)
if [ -f .env ]; then
    echo "Backing up configuration..."
    cp .env "$BACKUP_DIR/.env.backup"
    echo "  ✓ .env (as .env.backup)"
fi

# Create compressed archive
echo ""
echo "Creating compressed archive..."
tar -czf "${BACKUP_DIR}.tar.gz" -C backups "backup_${TIMESTAMP}"

# Remove temporary directory
rm -rf "$BACKUP_DIR"

# Get archive size
SIZE=$(du -h "${BACKUP_DIR}.tar.gz" | cut -f1)

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "=========================================="
echo "Archive: ${BACKUP_DIR}.tar.gz"
echo "Size: ${SIZE}"
echo ""
echo "To restore from this backup:"
echo "  ./scripts/restore.sh ${BACKUP_DIR}.tar.gz"
echo ""

# Clean up old backups (keep last 10)
echo "Cleaning up old backups (keeping last 10)..."
cd backups
ls -t backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
cd ..
echo "Done!"