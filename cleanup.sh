#!/bin/bash

# Cleanup script for GPU Monitor Dashboard
# This script helps resolve container configuration issues and cleans up native deployment

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Cleanup"
echo "=========================================="
echo ""

# Check if docker-compose.yml exists (Docker deployment)
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Cleaning up Docker deployment..."
    
    # Stop and remove containers
    echo "🛑 Stopping and removing containers..."
    docker-compose down

    # Remove containers completely (including volumes)
    echo "🗑️  Removing containers and volumes..."
    docker rm -f gpu-monitor-backend 2>/dev/null || true
    docker rm -f gpu-monitor-frontend 2>/dev/null || true

    # Remove images
    echo "🗑️  Removing Docker images..."
    docker rmi gpu-monitor-dashboard-backend 2>/dev/null || true
    docker rmi gpu-monitor-dashboard-frontend 2>/dev/null || true

    # Prune dangling images
    echo "🧹 Pruning dangling images..."
    docker image prune -f

    # Clean up Docker system
    echo "🧹 Cleaning up Docker system..."
    docker system prune -f
fi

# Check if native deployment is running (systemd service)
if systemctl is-active --quiet gpu-monitor-native; then
    echo "🐍 Cleaning up native deployment..."
    
    # Stop the service
    echo "🛑 Stopping native service..."
    sudo systemctl stop gpu-monitor-native
    
    # Disable the service
    echo "🗑️  Disabling native service..."
    sudo systemctl disable gpu-monitor-native
    
    # Remove the service file
    echo "🗑️  Removing service file..."
    sudo rm -f /etc/systemd/system/gpu-monitor-native.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    echo "✅ Native deployment cleaned up"
fi

# Clean up virtual environment if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing virtual environment..."
    rm -rf venv
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To redeploy Docker:"
echo "   ./deploy-react.sh"
echo ""
echo "To redeploy native:"
echo "   ./deploy-native.sh"
echo ""
