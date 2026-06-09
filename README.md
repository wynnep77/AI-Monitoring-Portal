# GPU Monitor Dashboard

A comprehensive web-based monitoring application for real-time GPU, CPU, and storage performance tracking. Built with React and FastAPI, featuring a professional Navy and White glossy UI.

## Features

- **Real-time GPU Monitoring**: Track NVIDIA GPU performance including utilization, memory, temperature, and power consumption
- **CPU Performance Monitoring**: Monitor CPU usage, memory utilization, and load averages
- **Storage Performance**: Track disk usage and I/O operations across all mounted filesystems
- **Multi-Server Support**: Add and monitor multiple servers from a single dashboard
- **Historical Data**: Store performance data for up to 1 year with configurable sampling rates
- **Professional UI**: Navy and White glossy theme with modern React components
- **RESTful API**: FastAPI backend with automatic API documentation
- **Docker Deployment**: Fully containerized deployment with automated setup scripts
- **Auto-Update Agent**: Automatically checks for and applies updates from GitHub

## Supported GPU Models

- NVIDIA RTX Pro 6000
- NVIDIA H200 NVL
- NVIDIA B300
- Other NVIDIA GPUs with NVML support

## Prerequisites

- NVIDIA GPU with drivers installed
- Docker and Docker Compose (for containerized deployment)
- Node.js 18+ (for local frontend development)
- Python 3.8+ (for local backend development)

## Quick Start

### Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/wynnep77/AI-Monitoring-Portal.git
cd AI-Monitoring-Portal
```

2. Run the installation script (installs Docker, NVIDIA Container Toolkit, and dependencies):
```bash
sudo chmod +x install-ubuntu.sh
sudo ./install-ubuntu.sh
```

3. Run the deployment script:
```bash
chmod +x deploy-react.sh
./deploy-react.sh
```

4. Access the dashboard at `http://localhost:3000`
5. Access the API documentation at `http://localhost:8001/docs` (or the port shown in deployment output)

### Manual Docker Deployment

```bash
# Build and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Native Deployment (No Docker)

This method runs the application directly on the host system without Docker. It provides direct GPU access and is simpler to troubleshoot.

1. Clone the repository:
```bash
git clone https://github.com/wynnep77/AI-Monitoring-Portal.git
cd AI-Monitoring-Portal
```

2. Run the native deployment script:
```bash
chmod +x deploy-native.sh
sudo ./deploy-native.sh
```

3. The service will start automatically. Access the dashboard at `http://localhost:3000`

**Service management:**
```bash
# Check status
sudo systemctl status gpu-monitor-native

# View logs
sudo journalctl -u gpu-monitor-native -f

# Stop
sudo systemctl stop gpu-monitor-native

# Start
sudo systemctl start gpu-monitor-native

# Restart
sudo systemctl restart gpu-monitor-native
```

### Local Development

#### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend
npm install
npm start
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to `http://localhost:8000`.

## Architecture

The application is split into two main components:

### Backend (FastAPI)
- RESTful API for GPU, CPU, and Storage monitoring
- Real-time metrics collection
- Historical data storage and retrieval
- Server management endpoints
- Automatic API documentation via Swagger UI

### Frontend (React)
- Modern React application with Tailwind CSS
- Navy and White glossy professional theme
- Real-time data visualization
- Server management interface
- Responsive design

## API Endpoints

### Health & Status
- `GET /` - API information
- `GET /health` - Health check

### Server Management
- `GET /api/servers` - List all servers
- `POST /api/servers` - Add new server
- `DELETE /api/servers/{id}` - Delete server

### GPU Monitoring
- `GET /api/gpu/current` - Current GPU metrics
- `GET /api/gpu/historical` - Historical GPU data

### CPU Monitoring
- `GET /api/cpu/current` - Current CPU metrics
- `GET /api/cpu/historical` - Historical CPU data

### Storage Monitoring
- `GET /api/storage/current` - Current storage metrics
- `GET /api/storage/historical` - Historical storage data

### Data Management
- `POST /api/data/cleanup` - Clean up old data

### Overview
- `GET /api/overview` - Combined overview of all metrics

## Configuration

Edit the `.env` file to customize:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `GPU_MONITOR_INTERVAL`: GPU monitoring interval in seconds (default: 5)
- `CPU_MONITOR_INTERVAL`: CPU monitoring interval in seconds (default: 5)
- `STORAGE_MONITOR_INTERVAL`: Storage monitoring interval in seconds (default: 30)
- `DATA_RETENTION_DAYS`: How long to keep historical data (default: 365 days)

## Usage

### Adding a Server

1. Navigate to the "Settings" tab
2. Click "Add New Server"
3. Enter server details:
   - Server Name: A friendly name for the server
   - Host/IP: The server's hostname or IP address
   - Port: SSH port (default: 22)
   - Local Server: Check if monitoring the local machine
4. Click "Add Server"

### Monitoring Performance

The dashboard provides five main tabs:

1. **Overview**: Quick summary of all system metrics
2. **GPU**: Detailed GPU metrics with historical data
3. **CPU**: CPU and memory utilization with historical data
4. **Storage**: Disk usage and I/O metrics
5. **Settings**: Server management and configuration

### Historical Data

Select time ranges for historical data:
- Last 1 Hour
- Last 6 Hours
- Last 24 Hours
- Last 7 Days

### Data Cleanup

Click "Cleanup Old Data" in the Settings tab to remove data older than the retention period (default: 365 days).

## Project Structure

```
gpu-monitor-dashboard/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend Docker image
│   └── monitors/              # Monitoring modules (shared)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── index.js          # React entry point
│   │   └── index.css         # Tailwind CSS styles
│   ├── public/
│   │   └── index.html        # HTML template
│   ├── package.json          # Node.js dependencies
│   ├── tailwind.config.js    # Tailwind configuration
│   ├── Dockerfile            # Frontend Docker image
│   └── nginx.conf            # Nginx configuration
├── monitors/                   # Shared monitoring modules
│   ├── gpu_monitor.py         # GPU monitoring
│   ├── cpu_monitor.py         # CPU monitoring
│   └── storage_monitor.py     # Storage monitoring
├── database.py                 # Database models
├── config.py                   # Configuration settings
├── docker-compose.yml          # Docker Compose configuration
├── deploy-react.sh            # Docker deployment script
├── deploy-native.sh           # Native deployment script
├── install-ubuntu.sh          # Ubuntu installation script
├── cleanup.sh                 # Cleanup script
└── README.md                  # This file
```

## Troubleshooting

### GPU Not Detected

If the dashboard shows "No GPUs detected" but you have NVIDIA GPUs:

1. **Verify NVIDIA drivers on host:**
   ```bash
   nvidia-smi
   ```
   This should show your GPU information.

2. **Check backend container logs:**
   ```bash
   docker-compose logs backend
   ```
   Look for NVML initialization errors or nvidia-smi output.

3. **Check NVIDIA Container Toolkit:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi
   ```
   This should show GPU information from within a container.

4. **Verify NVIDIA runtime is configured:**
   ```bash
   docker info | grep -i runtime
   ```
   You should see "nvidia" in the runtimes list.

5. **Test GPU access manually:**
   ```bash
   docker exec -it gpu-monitor-backend nvidia-smi
   ```

### Frontend Not Connecting to Backend

1. **Check if backend is running:**
   ```bash
   docker-compose ps
   ```

2. **Check backend logs:**
   ```bash
   docker-compose logs backend
   ```

3. **Verify API is accessible:**
   ```bash
   curl http://localhost:8000/health
   ```

### Database Errors

- Ensure the `data` directory has write permissions
- Check that SQLite is properly installed
- Verify the `DATABASE_URL` in `.env` is correct

### Port Already in Use

If ports 3000 or 8000 are already in use, modify the ports in `docker-compose.yml`.

### High Memory Usage

If the database grows too large:
- Reduce `DATA_RETENTION_DAYS` in `.env`
- Run "Cleanup Old Data" from the Settings tab
- Adjust sampling rates in configuration

## License

MIT License

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.
