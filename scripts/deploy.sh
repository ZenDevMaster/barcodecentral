#!/bin/bash
# Deploy Barcode Central with Docker Compose
# Usage: ./scripts/deploy.sh [--build]

set -e

BUILD_FLAG=""
if [ "$1" = "--build" ]; then
    BUILD_FLAG="--build"
    echo "Building new image before deployment..."
fi

echo "=========================================="
echo "Deploying Barcode Central"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file from .env.production.example"
    echo ""
    echo "  cp .env.production.example .env"
    echo "  nano .env  # Edit with your configuration"
    echo ""
    exit 1
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Start containers
echo "Starting containers..."
docker-compose up -d $BUILD_FLAG

# Wait for health check
echo ""
echo "Waiting for application to be healthy..."
sleep 5

# Check health
for i in {1..30}; do
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        echo ""
        echo "=========================================="
        echo "Deployment successful!"
        echo "=========================================="
        echo "Application is running at: http://localhost:5000"
        echo ""
        echo "To view logs:"
        echo "  docker-compose logs -f"
        echo ""
        echo "To stop:"
        echo "  docker-compose down"
        echo ""
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "WARNING: Health check timeout. Check logs:"
echo "  docker-compose logs"
exit 1