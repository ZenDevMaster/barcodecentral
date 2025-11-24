#!/bin/bash
# Build Docker image for Barcode Central
# Usage: ./scripts/build.sh [tag]

set -e

# Default tag
TAG="${1:-latest}"

echo "=========================================="
echo "Building Barcode Central Docker Image"
echo "=========================================="
echo "Tag: barcode-central:${TAG}"
echo ""

# Build the image
docker build -t "barcode-central:${TAG}" .

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo "Image: barcode-central:${TAG}"
echo ""
echo "To run the container:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"