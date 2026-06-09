#!/bin/bash

# GPU Monitor Dashboard Ubuntu Installation Script
# This script installs all dependencies and deploys the GPU Monitor Dashboard on Ubuntu

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Ubuntu Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system packages
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
pip3 install --upgrade pip --break-system-packages
pip3 install requests --break-system-packages

# Install Docker
echo "🐳 Installing Docker..."
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

# Install NVIDIA Container Toolkit
echo "🎮 Installing NVIDIA Container Toolkit..."
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

# Verify NVIDIA drivers
echo "🔍 Verifying NVIDIA drivers..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA drivers detected"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
else
    echo "⚠️  NVIDIA drivers not detected. Please install NVIDIA drivers first."
    echo "   Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
fi

# Add current user to docker group (if not root)
if [ -n "$SUDO_USER" ]; then
    echo "👤 Adding user $SUDO_USER to docker group..."
    usermod -aG docker $SUDO_USER
    echo "⚠️  Please log out and log back in for group changes to take effect"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clone the repository (if not already done):"
echo "   git clone https://github.com/wynnep77/AI-Monitoring-Portal.git"
echo "   cd AI-Monitoring-Portal"
echo ""
echo "2. Run the deployment script:"
echo "   chmod +x deploy.sh"
echo "   ./deploy.sh"
echo ""
echo "3. Access the dashboard at:"
echo "   http://localhost:8000"
echo ""
