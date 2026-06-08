#!/bin/bash

# GPU Monitor Dashboard Native Deployment Script (Linux/Ubuntu)
# This script deploys the application without Docker, running directly on the host system

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Native Deployment"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Some operations may require sudo. If installation fails, run with sudo."
fi

# Check and install Python3
if ! command -v python3 &> /dev/null; then
    echo "📦 Python3 not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y python3
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3
    else
        echo "❌ Cannot install Python3 automatically. Please install it manually."
        exit 1
    fi
else
    echo "✅ Python3 is installed"
fi

# Check and install pip3
if ! command -v pip3 &> /dev/null; then
    echo "📦 pip3 not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    else
        echo "📦 Installing pip via ensurepip..."
        python3 -m ensurepip --upgrade
    fi
else
    echo "✅ pip3 is installed"
fi

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create data directory
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "✅ Data directory created"
fi

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
fi

# Install systemd service
echo "📋 Installing systemd service..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sed "s|/path/to/gpu-monitor-dashboard|$SCRIPT_DIR|g" gpu-monitor-native.service > /tmp/gpu-monitor-native.service

sudo cp /tmp/gpu-monitor-native.service /etc/systemd/system/gpu-monitor-native.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start the service
echo "🚀 Enabling and starting GPU Monitor service..."
sudo systemctl enable gpu-monitor-native
sudo systemctl start gpu-monitor-native

echo ""
echo "=========================================="
echo "✅ Native Deployment Complete!"
echo "=========================================="
echo ""
echo "The GPU Monitor Dashboard is now running on:"
echo "🌐 http://localhost:8000"
echo ""
echo "Service management:"
echo "   Check status: sudo systemctl status gpu-monitor-native"
echo "   View logs: sudo journalctl -u gpu-monitor-native -f"
echo "   Stop: sudo systemctl stop gpu-monitor-native"
echo "   Start: sudo systemctl start gpu-monitor-native"
echo "   Restart: sudo systemctl restart gpu-monitor-native"
echo ""
echo "To run manually:"
echo "   source venv/bin/activate"
echo "   streamlit run app.py --server.port 8000"
echo ""
