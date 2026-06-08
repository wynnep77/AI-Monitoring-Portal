#!/bin/bash

# Cleanup script for GPU Monitor Dashboard
# This script helps resolve container configuration issues

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Cleanup"
echo "=========================================="
echo ""

# Stop and remove the container
echo "🛑 Stopping and removing container..."
docker-compose down

# Remove the container completely (including volumes)
echo "🗑️  Removing container and volumes..."
docker rm -f gpu-monitor-dashboard 2>/dev/null || true

# Remove the image
echo "🗑️  Removing Docker image..."
docker rmi gpu-monitor-dashboard_gpu-monitor 2>/dev/null || true

# Prune dangling images
echo "🧹 Pruning dangling images..."
docker image prune -f

# Clean up Docker system
echo "🧹 Cleaning up Docker system..."
docker system prune -f

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To redeploy:"
echo "   ./deploy.sh"
echo ""
