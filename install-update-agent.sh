#!/bin/bash

# Install Update Agent as a systemd service
# This script sets up the auto-update agent to run as a system service

set -e

echo "=========================================="
echo "Update Agent Installation"
echo "=========================================="
echo ""

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📁 Installation directory: $SCRIPT_DIR"

# Update the service file with the correct path
sed "s|/path/to/gpu-monitor-dashboard|$SCRIPT_DIR|g" update-agent.service > /tmp/update-agent.service

# Copy the service file to systemd directory
echo "📋 Installing systemd service..."
sudo cp /tmp/update-agent.service /etc/systemd/system/gpu-monitor-update-agent.service

# Make the update agent script executable
echo "🔧 Making update agent executable..."
chmod +x "$SCRIPT_DIR/update_agent.py"

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start the service
echo "🚀 Enabling and starting update agent service..."
sudo systemctl enable gpu-monitor-update-agent
sudo systemctl start gpu-monitor-update-agent

# Check service status
echo ""
echo "✅ Update agent installed and started!"
echo ""
echo "Service status:"
sudo systemctl status gpu-monitor-update-agent --no-pager

echo ""
echo "To view logs:"
echo "   sudo journalctl -u gpu-monitor-update-agent -f"
echo ""
echo "To stop the service:"
echo "   sudo systemctl stop gpu-monitor-update-agent"
echo ""
echo "To start the service:"
echo "   sudo systemctl start gpu-monitor-update-agent"
echo ""
echo "To disable the service:"
echo "   sudo systemctl disable gpu-monitor-update-agent"
echo ""
