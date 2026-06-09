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

# Check Python version
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Ensure pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "📦 pip3 not found, installing..."
    python3 -m ensurepip --upgrade
    if [ $? -ne 0 ]; then
        echo "📦 Installing pip via get-pip.py..."
        curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        python3 /tmp/get-pip.py
        rm /tmp/get-pip.py
    fi
fi

echo "✅ pip3 is installed"

# Install Python dependencies (requests should already be installed by install-ubuntu.sh)
echo "📦 Checking Python dependencies (requests)..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "📦 Installing requests package..."
    pip3 install requests --quiet
else
    echo "✅ requests already installed"
fi

# Copy systemd service file
echo "📋 Installing systemd service..."
sed "s|/root/AI-Monitoring-Portal|$REPO_DIR|g" monitoring-agent.service > /etc/systemd/system/gpu-monitoring-agent.service

# Update ExecStart to use python3
sed -i 's|/usr/bin/python3|/usr/bin/python3.12|g' /etc/systemd/system/gpu-monitoring-agent.service

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
