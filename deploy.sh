#!/bin/bash

# GPU Monitor Dashboard Deployment Script
# This script automates the deployment of the GPU Monitor Dashboard

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Deployment"
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    echo "Or run: sudo ./install-ubuntu.sh (for Ubuntu systems)"
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    echo "Or run: sudo ./install-ubuntu.sh (for Ubuntu systems)"
    exit 1
fi

echo "✅ Docker Compose is installed"

# Check if NVIDIA Docker Runtime is available
if docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA Docker Runtime is available"
else
    echo "⚠️  NVIDIA Docker Runtime may not be properly configured"
    echo "   GPU monitoring may not work correctly"
    echo "   Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
fi

echo ""

# Create data directory if it doesn't exist
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

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the container
echo "🚀 Starting GPU Monitor Dashboard..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "The GPU Monitor Dashboard is now running on:"
echo "🌐 http://localhost:8000"
echo ""
echo "To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "To stop the dashboard:"
echo "   docker-compose down"
echo ""
echo "To restart the dashboard:"
echo "   docker-compose restart"
echo ""
