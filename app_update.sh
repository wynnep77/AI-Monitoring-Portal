#!/bin/bash

# GPU Monitor Dashboard Update Script
# This script combines installation and deployment for the GPU Monitor Dashboard
# Use this script to update and deploy the application

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Update"
echo "=========================================="
echo ""

# Check if running as root for installation steps
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Some installation steps may require sudo. If installation fails, run with sudo."
fi

# Update system packages (if running as root)
if [ "$EUID" -eq 0 ]; then
    echo "📦 Updating system packages..."
    apt-get update -y

    # Install basic dependencies
    echo "🔧 Installing basic dependencies..."
    apt-get install -y \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    # Install Python packages globally
    echo "📦 Installing Python packages globally..."
    pip3 install requests --break-system-packages
fi

# Install Docker (if running as root and not installed)
if [ "$EUID" -eq 0 ]; then
    echo "🐳 Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Set up the stable repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker Engine
        apt-get update -y
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        # Start and enable Docker
        systemctl start docker
        systemctl enable docker
        
        echo "✅ Docker installed successfully"
    else
        echo "✅ Docker already installed"
    fi

    # Install NVIDIA Container Toolkit (if running as root)
    echo "🎮 Checking NVIDIA Container Toolkit..."
    if ! command -v nvidia-container-toolkit &> /dev/null; then
        # Add NVIDIA repository
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
          sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
          tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        
        # Install NVIDIA Container Toolkit
        apt-get update -y
        apt-get install -y nvidia-container-toolkit
        
        # Configure Docker to use NVIDIA runtime
        nvidia-ctk runtime configure --runtime=docker
        systemctl restart docker
        
        echo "✅ NVIDIA Container Toolkit installed successfully"
    else
        echo "✅ NVIDIA Container Toolkit already installed"
    fi

    # Add current user to docker group (if not root)
    if [ -n "$SUDO_USER" ]; then
        echo "👤 Adding user $SUDO_USER to docker group..."
        usermod -aG docker $SUDO_USER
        echo "⚠️  Please log out and log back in for group changes to take effect"
    fi
fi

# Check Python3 (if not running as root)
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

# Check pip3 (if not running as root)
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
    echo "Or run this script with sudo (for Ubuntu systems)"
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    echo "Or run this script with sudo (for Ubuntu systems)"
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

# Stop and remove existing containers to avoid containerconfig errors
echo "🛑 Stopping and removing existing containers..."
docker-compose down 2>/dev/null || true
docker rm -f gpu-monitor-backend 2>/dev/null || true
docker rm -f gpu-monitor-frontend 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the container
echo "🚀 Starting GPU Monitor Dashboard..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✅ Update Complete!"
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
