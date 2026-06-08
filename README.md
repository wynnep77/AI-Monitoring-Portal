# GPU Monitor Dashboard

A comprehensive web-based monitoring application for real-time GPU, CPU, and storage performance tracking. Built with Streamlit and designed with a clean VMware vCenter-inspired interface.

## Features

- **Real-time GPU Monitoring**: Track NVIDIA GPU performance including utilization, memory, temperature, and power consumption
- **CPU Performance Monitoring**: Monitor CPU usage, memory utilization, and load averages
- **Storage Performance**: Track disk usage and I/O operations across all mounted filesystems
- **Multi-Server Support**: Add and monitor multiple servers from a single dashboard
- **Historical Data**: Store performance data for up to 1 year with configurable sampling rates
- **Clean UI**: VMware vCenter-inspired interface with real-time charts and metrics
- **Docker Deployment**: Fully containerized deployment with automated setup scripts
- **Auto-Update Agent**: Automatically checks for and applies updates from GitHub

## Supported GPU Models

- NVIDIA RTX Pro 6000
- NVIDIA H200 NVL
- NVIDIA B300
- Other NVIDIA GPUs with NVML support

## Prerequisites

- NVIDIA GPU with drivers installed
- For Windows: Docker Desktop with WSL2 support
- For Ubuntu: Docker, Docker Compose, and NVIDIA Container Toolkit (can be installed automatically via install script)

## Quick Start

### Windows Deployment

1. Clone the repository:
```bash
git clone <your-repo-url>
cd gpu-monitor-dashboard
```

2. Run the deployment script:
```powershell
.\deploy.ps1
```

3. Access the dashboard at `http://localhost:8000`

### Ubuntu Deployment (Recommended)

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
chmod +x deploy.sh
./deploy.sh
```

4. Access the dashboard at `http://localhost:8000`

### Linux/Ubuntu Manual Deployment

If you already have Docker and NVIDIA Container Toolkit installed:

1. Clone the repository:
```bash
git clone https://github.com/wynnep77/AI-Monitoring-Portal.git
cd AI-Monitoring-Portal
```

2. Make the deployment script executable:
```bash
chmod +x deploy.sh
```

3. Run the deployment script:
```bash
./deploy.sh
```

4. Access the dashboard at `http://localhost:8000`

## Manual Deployment

If you prefer manual deployment:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Run the application:
```bash
streamlit run app.py --server.port 8000
```

## Docker Deployment

### Build and Run with Docker Compose

```bash
docker-compose up -d
```

### Build and Run with Docker

```bash
docker build -t gpu-monitor-dashboard .
docker run -d -p 8000:8000 --gpus all -v $(pwd)/data:/app/data gpu-monitor-dashboard
```

## Configuration

Edit the `.env` file to customize:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `GPU_MONITOR_INTERVAL`: GPU monitoring interval in seconds (default: 5)
- `CPU_MONITOR_INTERVAL`: CPU monitoring interval in seconds (default: 5)
- `STORAGE_MONITOR_INTERVAL`: Storage monitoring interval in seconds (default: 30)
- `DATA_RETENTION_DAYS`: How long to keep historical data (default: 365 days)

## Usage

### Adding a Server

1. Click "Settings" in the sidebar
2. Expand "Add New Server"
3. Enter server details:
   - Server Name: A friendly name for the server
   - Host/IP: The server's hostname or IP address
   - Port: SSH port (default: 22)
   - Local Server: Check if monitoring the local machine
4. Click "Add Server"

### Monitoring Performance

The dashboard provides four main tabs:

1. **Overview**: Quick summary of all system metrics
2. **GPU Performance**: Detailed GPU metrics with historical charts
3. **CPU Performance**: CPU and memory utilization with historical data
4. **Storage Performance**: Disk usage and I/O metrics

### Historical Data

Select time ranges for historical data:
- Last 1 Hour
- Last 6 Hours
- Last 24 Hours
- Last 7 Days

Data is automatically sampled at different rates based on age:
- High frequency (5 seconds): Last 24 hours
- Medium frequency (60 seconds): Last 7 days
- Low frequency (300 seconds): Older than 7 days

### Data Cleanup

Click "Cleanup Old Data" in the sidebar to remove data older than the retention period (default: 365 days).

## Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Frontend               │
│  ┌──────────┬──────────┬──────────────┐  │
│  │ Overview │ GPU      │ CPU/Storage  │  │
│  └──────────┴──────────┴──────────────┘  │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         Monitoring Services              │
│  • GPUMonitor (NVML)                     │
│  • CPUMonitor (psutil)                   │
│  • StorageMonitor (psutil)               │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         SQLite Database                  │
│  • GPU Metrics                           │
│  • CPU Metrics                           │
│  • Storage Metrics                       │
│  • Monitored Servers                     │
└─────────────────────────────────────────┘
```

## Project Structure

```
gpu-monitor-dashboard/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── database.py                 # Database models and operations
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── install-ubuntu.sh           # Ubuntu installation script
├── deploy.sh                   # Linux deployment script
├── deploy.ps1                  # Windows deployment script
├── .env.example                # Environment variables template
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── monitors/
│   ├── __init__.py
│   ├── gpu_monitor.py         # GPU monitoring service
│   ├── cpu_monitor.py         # CPU monitoring service
│   └── storage_monitor.py     # Storage monitoring service
└── data/                      # Data directory (created at runtime)
    └── monitoring.db           # SQLite database
```

## Troubleshooting

### GPU Not Detected

If the dashboard shows "No GPUs detected" but you have NVIDIA GPUs:

1. **Verify NVIDIA drivers on host:**
   ```bash
   nvidia-smi
   ```
   This should show your GPU information.

2. **Check NVIDIA Container Toolkit:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi
   ```
   This should show GPU information from within a container.

3. **Verify NVIDIA runtime is configured:**
   ```bash
   docker info | grep -i runtime
   ```
   You should see "nvidia" in the runtimes list.

4. **Check container logs for GPU initialization errors:**
   ```bash
   docker-compose logs gpu-monitor
   ```
   Look for NVML initialization errors or nvidia-smi output.

5. **For Docker Compose users:**
   - Ensure `runtime: nvidia` is set in docker-compose.yml
   - If using Docker Swarm, use the deploy resources section instead
   - Restart the container after changes:
     ```bash
     docker-compose down
     docker-compose up -d
     ```

6. **Test GPU access manually:**
   ```bash
   docker exec -it gpu-monitor-dashboard nvidia-smi
   ```

7. **For Windows users:**
   - Ensure WSL2 is properly configured
   - Check Docker Desktop GPU settings are enabled
   - Verify NVIDIA WSL drivers are installed

### Database Errors

- Ensure the `data` directory has write permissions
- Check that SQLite is properly installed
- Verify the `DATABASE_URL` in `.env` is correct

### Port Already in Use

If port 8000 is already in use, modify the port in:
- `docker-compose.yml` (ports section)
- `.streamlit/config.toml` (server.port)
- Or stop the conflicting service

### High Memory Usage

If the database grows too large:
- Reduce `DATA_RETENTION_DAYS` in `.env`
- Run "Cleanup Old Data" from the sidebar
- Adjust sampling rates in configuration

## Development

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Adding New Monitors

1. Create a new monitor class in `monitors/`
2. Implement `collect_metrics()` and `get_historical_metrics()` methods
3. Add database model in `database.py`
4. Integrate into `app.py`

## Auto-Update Agent

The GPU Monitor Dashboard includes an auto-update agent that automatically checks for updates from GitHub and applies them.

### Features

- Automatically checks for updates every hour (configurable)
- Pulls latest changes from GitHub
- Restarts the application with the new version
- Logs all update activities
- Runs as a system service (Linux) or scheduled task (Windows)

### Installation

#### Ubuntu/Linux

```bash
# Install the update agent as a systemd service
sudo chmod +x install-update-agent.sh
sudo ./install-update-agent.sh
```

The agent will:
- Install as a systemd service named `gpu-monitor-update-agent`
- Start automatically on system boot
- Check for updates every hour (configurable via `UPDATE_CHECK_INTERVAL` environment variable)

#### Windows

```powershell
# Install the update agent as a scheduled task
.\install-update-agent.ps1
```

The agent will:
- Install as a Windows Scheduled Task named `GPU-Monitor-Update-Agent`
- Run with SYSTEM privileges
- Check for updates every hour

### Configuration

The update check interval can be configured by setting the `UPDATE_CHECK_INTERVAL` environment variable (in seconds):

**Linux (systemd):**
Edit `/etc/systemd/system/gpu-monitor-update-agent.service` and modify:
```
Environment="UPDATE_CHECK_INTERVAL=3600"
```
Then reload: `sudo systemctl daemon-reload && sudo systemctl restart gpu-monitor-update-agent`

**Windows:**
Modify the trigger interval in the scheduled task settings or edit the `install-update-agent.ps1` script before installation.

### Management

#### Linux

```bash
# Check service status
sudo systemctl status gpu-monitor-update-agent

# View logs
sudo journalctl -u gpu-monitor-update-agent -f

# Stop the service
sudo systemctl stop gpu-monitor-update-agent

# Start the service
sudo systemctl start gpu-monitor-update-agent

# Disable the service
sudo systemctl disable gpu-monitor-update-agent

# Enable the service
sudo systemctl enable gpu-monitor-update-agent
```

#### Windows

```powershell
# Check task status
Get-ScheduledTask -TaskName 'GPU-Monitor-Update-Agent'

# View task history
Get-ScheduledTaskInfo -TaskName 'GPU-Monitor-Update-Agent'

# Stop the task
Stop-ScheduledTask -TaskName 'GPU-Monitor-Update-Agent'

# Start the task
Start-ScheduledTask -TaskName 'GPU-Monitor-Update-Agent'

# Remove the task
Unregister-ScheduledTask -TaskName 'GPU-Monitor-Update-Agent' -Confirm:$false
```

### Manual Update

To manually trigger an update check:

```bash
# Run the update agent manually
python3 update_agent.py
```

The agent will check for updates, apply them if available, and restart the application.

### Logs

Update agent logs are stored in:
- **Linux**: Systemd journal (`journalctl -u gpu-monitor-update-agent`)
- **Windows**: `update_agent.log` in the application directory
- **Both**: `update_agent.log` in the application directory (when run manually)

## License

MIT License

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.
