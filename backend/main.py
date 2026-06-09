from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Optional
import uvicorn

from database import init_db, get_db, MonitoredServer, cleanup_old_data
from monitors import GPUMonitor, CPUMonitor, StorageMonitor

# Initialize FastAPI app
app = FastAPI(
    title="GPU Monitor Dashboard API",
    description="Real-time GPU, CPU, and Storage Monitoring API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Initialize monitors with error handling
print("Initializing monitors...")
try:
    gpu_monitor = GPUMonitor()
    print(f"GPU Monitor initialized: {gpu_monitor.initialized}")
    if hasattr(gpu_monitor, 'use_smi_fallback'):
        print(f"GPU Monitor using SMI fallback: {gpu_monitor.use_smi_fallback}")
except Exception as e:
    print(f"Error initializing GPU monitor: {e}")
    gpu_monitor = None

try:
    cpu_monitor = CPUMonitor()
    print("CPU Monitor initialized successfully")
except Exception as e:
    print(f"Error initializing CPU monitor: {e}")
    cpu_monitor = None

try:
    storage_monitor = StorageMonitor()
    print("Storage Monitor initialized successfully")
except Exception as e:
    print(f"Error initializing storage monitor: {e}")
    storage_monitor = None

@app.get("/")
async def root():
    return {
        "message": "GPU Monitor Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "gpu_monitor_initialized": gpu_monitor.initialized if gpu_monitor else False,
        "gpu_monitor_smi_fallback": gpu_monitor.use_smi_fallback if gpu_monitor and hasattr(gpu_monitor, 'use_smi_fallback') else False,
        "cpu_monitor_available": cpu_monitor is not None,
        "storage_monitor_available": storage_monitor is not None
    }

@app.get("/api/diagnostics")
async def get_diagnostics():
    """Get diagnostic information about monitoring system"""
    diagnostics = {
        "timestamp": datetime.utcnow().isoformat(),
        "monitors": {},
        "environment": {}
    }
    
    # GPU Monitor diagnostics
    if gpu_monitor:
        diagnostics["monitors"]["gpu"] = {
            "initialized": gpu_monitor.initialized,
            "init_error": gpu_monitor.init_error if hasattr(gpu_monitor, 'init_error') else None,
            "use_smi_fallback": gpu_monitor.use_smi_fallback if hasattr(gpu_monitor, 'use_smi_fallback') else False
        }
        try:
            gpu_info = gpu_monitor.get_all_gpu_info("localhost")
            diagnostics["monitors"]["gpu"]["test_result"] = "success" if gpu_info else "no_gpus"
            diagnostics["monitors"]["gpu"]["gpu_count"] = len(gpu_info) if gpu_info else 0
        except Exception as e:
            diagnostics["monitors"]["gpu"]["test_result"] = f"error: {str(e)}"
    else:
        diagnostics["monitors"]["gpu"] = {"status": "not_initialized"}
    
    # CPU Monitor diagnostics
    if cpu_monitor:
        try:
            cpu_info = cpu_monitor.get_cpu_info("localhost")
            diagnostics["monitors"]["cpu"] = {
                "test_result": "success" if cpu_info else "no_data",
                "data": cpu_info
            }
        except Exception as e:
            diagnostics["monitors"]["cpu"] = {"test_result": f"error: {str(e)}"}
    else:
        diagnostics["monitors"]["cpu"] = {"status": "not_initialized"}
    
    # Storage Monitor diagnostics
    if storage_monitor:
        try:
            storage_info = storage_monitor.get_storage_info("localhost")
            diagnostics["monitors"]["storage"] = {
                "test_result": "success" if storage_info else "no_data",
                "volume_count": len(storage_info) if storage_info else 0
            }
        except Exception as e:
            diagnostics["monitors"]["storage"] = {"test_result": f"error: {str(e)}"}
    else:
        diagnostics["monitors"]["storage"] = {"status": "not_initialized"}
    
    # Environment diagnostics
    import os
    diagnostics["environment"] = {
        "host_proc": os.getenv('HOST_PROC'),
        "host_sys": os.getenv('HOST_SYS'),
        "nvidia_visible_devices": os.getenv('NVIDIA_VISIBLE_DEVICES'),
        "nvidia_driver_capabilities": os.getenv('NVIDIA_DRIVER_CAPABILITIES')
    }
    
    return diagnostics

@app.get("/api/test")
async def get_test_data():
    """Return test data to verify frontend can display data"""
    return {
        "gpu": [
            {
                "name": "NVIDIA RTX Pro 6000 (Test)",
                "utilization": 45.2,
                "memory_used": 12.5,
                "memory_total": 24.0,
                "temperature": 65
            }
        ],
        "cpu": {
            "cpu_percent": 35.5,
            "cpu_count": 16,
            "memory_percent": 42.3,
            "memory_used": 16.8,
            "memory_total": 64.0,
            "load_avg_1m": 2.5,
            "load_avg_5m": 2.1,
            "load_avg_15m": 1.8
        },
        "storage": [
            {
                "device": "/dev/sda1",
                "mountpoint": "/",
                "total": 500.0,
                "used": 250.5,
                "free": 249.5,
                "percent": 50.1
            }
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "test_mode": True
    }

# Server Management Endpoints
@app.get("/api/servers")
async def get_servers():
    """Get all monitored servers"""
    db = next(get_db())
    try:
        servers = db.query(MonitoredServer).all()
        return [
            {
                "id": server.id,
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "is_local": server.is_local
            }
            for server in servers
        ]
    finally:
        db.close()

@app.post("/api/servers")
async def add_server(server: dict):
    """Add a new server to monitor"""
    db = next(get_db())
    try:
        new_server = MonitoredServer(
            name=server.get("name"),
            host=server.get("host", "localhost"),
            port=server.get("port", 22),
            is_local=1 if server.get("is_local", True) else 0
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)
        return {
            "id": new_server.id,
            "name": new_server.name,
            "host": new_server.host,
            "port": new_server.port,
            "is_local": new_server.is_local
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.delete("/api/servers/{server_id}")
async def delete_server(server_id: int):
    """Delete a monitored server"""
    db = next(get_db())
    try:
        server = db.query(MonitoredServer).filter(MonitoredServer.id == server_id).first()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        db.delete(server)
        db.commit()
        return {"message": "Server deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

# GPU Monitoring Endpoints
@app.get("/api/gpu/current")
async def get_current_gpu_metrics(server_name: str = "localhost"):
    """Get current GPU metrics"""
    if not gpu_monitor:
        raise HTTPException(status_code=503, detail="GPU monitor not initialized")
    try:
        print(f"Fetching GPU metrics for {server_name}")
        gpu_metrics = gpu_monitor.get_all_gpu_info(server_name)
        print(f"GPU metrics result: {gpu_metrics}")
        if not gpu_metrics:
            return {"message": "No GPUs detected", "gpus": []}
        
        # Store metrics in database
        gpu_monitor.collect_metrics(server_name)
        
        return {"gpus": gpu_metrics}
    except Exception as e:
        print(f"Error fetching GPU metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gpu/historical")
async def get_historical_gpu_metrics(
    server_name: str = "localhost",
    gpu_id: Optional[int] = None,
    hours: int = 24
):
    """Get historical GPU metrics"""
    try:
        metrics = gpu_monitor.get_historical_metrics(server_name, gpu_id, hours)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CPU Monitoring Endpoints
@app.get("/api/cpu/current")
async def get_current_cpu_metrics(server_name: str = "localhost"):
    """Get current CPU metrics"""
    if not cpu_monitor:
        raise HTTPException(status_code=503, detail="CPU monitor not initialized")
    try:
        print(f"Fetching CPU metrics for {server_name}")
        cpu_metrics = cpu_monitor.get_cpu_info(server_name)
        print(f"CPU metrics result: {cpu_metrics}")
        if not cpu_metrics:
            return {"message": "Unable to retrieve CPU metrics", "cpu": None}
        
        # Store metrics in database
        cpu_monitor.collect_metrics(server_name)
        
        return {"cpu": cpu_metrics}
    except Exception as e:
        print(f"Error fetching CPU metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cpu/historical")
async def get_historical_cpu_metrics(
    server_name: str = "localhost",
    hours: int = 24
):
    """Get historical CPU metrics"""
    try:
        metrics = cpu_monitor.get_historical_metrics(server_name, hours)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Storage Monitoring Endpoints
@app.get("/api/storage/current")
async def get_current_storage_metrics(server_name: str = "localhost"):
    """Get current storage metrics"""
    if not storage_monitor:
        raise HTTPException(status_code=503, detail="Storage monitor not initialized")
    try:
        print(f"Fetching storage metrics for {server_name}")
        storage_metrics = storage_monitor.get_storage_info(server_name)
        print(f"Storage metrics result: {storage_metrics}")
        if not storage_metrics:
            return {"message": "Unable to retrieve storage metrics", "storage": []}
        
        # Store metrics in database
        storage_monitor.collect_metrics(server_name)
        
        return {"storage": storage_metrics}
    except Exception as e:
        print(f"Error fetching storage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/storage/historical")
async def get_historical_storage_metrics(
    server_name: str = "localhost",
    device: Optional[str] = None,
    hours: int = 24
):
    """Get historical storage metrics"""
    try:
        metrics = storage_monitor.get_historical_metrics(server_name, device, hours)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Data Management Endpoints
@app.post("/api/data/cleanup")
async def cleanup_data():
    """Clean up old data"""
    try:
        cleanup_old_data()
        return {"message": "Old data cleaned up successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Overview Endpoint
@app.get("/api/overview")
async def get_overview(server_name: str = "localhost"):
    """Get overview of all current metrics"""
    try:
        gpu_metrics = gpu_monitor.get_all_gpu_info(server_name)
        cpu_metrics = cpu_monitor.get_cpu_info(server_name)
        storage_metrics = storage_monitor.get_storage_info(server_name)
        
        # Store metrics
        if gpu_metrics:
            gpu_monitor.collect_metrics(server_name)
        if cpu_metrics:
            cpu_monitor.collect_metrics(server_name)
        if storage_metrics:
            storage_monitor.collect_metrics(server_name)
        
        return {
            "gpu": gpu_metrics if gpu_metrics else [],
            "cpu": cpu_metrics,
            "storage": storage_metrics if storage_metrics else [],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
