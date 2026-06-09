#!/bin/bash

# Installation script for the Automated Monitoring Agent
# This script installs the monitoring agent as a systemd service

set -e

echo "=========================================="
echo "Installing Automated Monitoring Agent"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get the repository directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Repository directory: $REPO_DIR"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install requests --quiet

# Copy systemd service file
echo "📋 Installing systemd service..."
sed "s|/root/AI-Monitoring-Portal|$REPO_DIR|g" monitoring-agent.service > /etc/systemd/system/gpu-monitoring-agent.service

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable and start the service
echo "🚀 Enabling and starting monitoring agent..."
systemctl enable gpu-monitoring-agent
systemctl start gpu-monitoring-agent

# Check service status
echo ""
echo "✅ Monitoring agent installed and started!"
echo ""
echo "Service status:"
systemctl status gpu-monitoring-agent --no-pager

echo ""
echo "To view logs:"
echo "   journalctl -u gpu-monitoring-agent -f"
echo ""
echo "To stop the service:"
echo "   sudo systemctl stop gpu-monitoring-agent"
echo ""
echo "To restart the service:"
echo "   sudo systemctl restart gpu-monitoring-agent"
echo ""
echo "The agent will monitor the application and report issues to GitHub."
echo "Check interval: 5 minutes (configurable via MONITOR_CHECK_INTERVAL)"
echo ""
