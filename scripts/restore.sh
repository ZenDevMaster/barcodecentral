#!/bin/bash
# Restore Barcode Central data from backup
# Usage: ./scripts/restore.sh <backup_file.tar.gz>

set -e

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "ERROR: No backup file specified!"
    echo ""
    echo "Usage: ./scripts/restore.sh <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh backups/backup_*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "Restoring Barcode Central Data"
echo "=========================================="
echo "Backup file: $BACKUP_FILE"
echo ""

# Confirm restoration
read -p "This will overwrite existing data. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find the backup directory (should be only one)
BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "backup_*" | head -n 1)

if [ -z "$BACKUP_DIR" ]; then
    echo "ERROR: Invalid backup file structure"
    exit 1
fi

# Stop the application if running
echo "Stopping application..."
docker-compose down 2>/dev/null || true

# Restore files
echo "Restoring files..."

if [ -f "$BACKUP_DIR/history.json" ]; then
    cp "$BACKUP_DIR/history.json" ./
    echo "  ✓ history.json"
fi

if [ -f "$BACKUP_DIR/printers.json" ]; then
    cp "$BACKUP_DIR/printers.json" ./
    echo "  ✓ printers.json"
fi

if [ -d "$BACKUP_DIR/templates_zpl" ]; then
    rm -rf templates_zpl
    cp -r "$BACKUP_DIR/templates_zpl" ./
    echo "  ✓ templates_zpl/"
fi

if [ -f "$BACKUP_DIR/.env.backup" ]; then
    echo ""
    echo "Found .env.backup in backup"
    read -p "Restore .env file? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$BACKUP_DIR/.env.backup" ./.env
        echo "  ✓ .env"
    fi
fi

echo ""
echo "=========================================="
echo "Restore completed successfully!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  docker-compose up -d"
echo ""