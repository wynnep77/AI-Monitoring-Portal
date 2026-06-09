#!/bin/bash

# GPU Monitor Dashboard Deployment Script (React + FastAPI)
# This script deploys the React frontend and FastAPI backend using Docker

set -e

echo "=========================================="
echo "GPU Monitor Dashboard Deployment"
echo "React + FastAPI Architecture"
echo "=========================================="
echo ""

# Function to run command with sudo if needed
run_sudo() {
    if [ "$EUID" -ne 0 ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose is installed"

# Function to check if a port is available
is_port_available() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Find available backend port starting from 8001
BACKEND_PORT=8001
while ! is_port_available $BACKEND_PORT; do
    echo "⚠️  Port $BACKEND_PORT is in use, trying next port..."
    BACKEND_PORT=$((BACKEND_PORT + 1))
    if [ $BACKEND_PORT -gt 8100 ]; then
        echo "❌ Could not find available port in range 8001-8100"
        exit 1
    fi
done

echo "✅ Using backend port: $BACKEND_PORT"

# Update docker-compose.yml with the available port
sed -i "s/\"8001:8000\"/\"$BACKEND_PORT:8000\"/g" docker-compose.yml
sed -i "s/REACT_APP_API_URL=http:\/\/localhost:8001/REACT_APP_API_URL=http:\/\/localhost:$BACKEND_PORT/g" docker-compose.yml

# Create data directory
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "✅ Data directory created"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose up -d --build

# Install monitoring agent
echo "📋 Installing automated monitoring agent..."
if [ -f "install-monitoring-agent.sh" ]; then
    run_sudo chmod +x install-monitoring-agent.sh
    run_sudo ./install-monitoring-agent.sh
else
    echo "⚠️  Monitoring agent installation script not found, skipping..."
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "The dashboard is now running:"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:$BACKEND_PORT"
echo "📚 API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "To view monitoring agent logs:"
echo "   journalctl -u gpu-monitoring-agent -f"
echo ""
echo "To stop the application:"
echo "   docker-compose down"
echo ""
echo "The monitoring agent will automatically report issues to GitHub."
echo ""
