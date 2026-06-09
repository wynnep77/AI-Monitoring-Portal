import psutil
import os
from datetime import datetime
from typing import List, Dict
from database import StorageMetric, get_db

class StorageMonitor:
    def __init__(self):
        # Configure psutil to use host proc/sys if running in Docker
        host_proc = os.getenv('HOST_PROC')
        host_sys = os.getenv('HOST_SYS')
        if host_proc:
            psutil.PROCFS_PATH = host_proc
        if host_sys:
            psutil.SYSFS_PATH = host_sys
    
    def get_storage_info(self, server_name: str = "localhost") -> List[Dict]:
        """Get current storage information for all mounted filesystems"""
        storage_infos = []
        
        try:
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Get disk I/O stats
                    try:
                        disk_io = psutil.disk_io_counters(perdisk=True)
                        device_name = partition.device.split('/')[-1]
                        if device_name in disk_io:
                            read_bytes = disk_io[device_name].read_bytes
                            write_bytes = disk_io[device_name].write_bytes
                        else:
                            read_bytes = 0
                            write_bytes = 0
                    except:
                        read_bytes = 0
                        write_bytes = 0
                    
                    storage_info = {
                        "server_name": server_name,
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total": usage.total / (1024**3),  # GB
                        "used": usage.used / (1024**3),  # GB
                        "free": usage.free / (1024**3),  # GB
                        "percent": usage.percent,
                        "read_bytes": read_bytes,
                        "write_bytes": write_bytes
                    }
                    storage_infos.append(storage_info)
                except Exception as e:
                    print(f"Error getting storage info for {partition.mountpoint}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error getting storage partitions: {e}")
        
        return storage_infos
    
    def collect_metrics(self, server_name: str = "localhost") -> List[StorageMetric]:
        """Collect and store storage metrics"""
        storage_infos = self.get_storage_info(server_name)
        metrics = []
        
        db = next(get_db())
        try:
            for storage_info in storage_infos:
                metric = StorageMetric(
                    server_name=storage_info["server_name"],
                    device=storage_info["device"],
                    mountpoint=storage_info["mountpoint"],
                    total=storage_info["total"],
                    used=storage_info["used"],
                    free=storage_info["free"],
                    percent=storage_info["percent"],
                    read_bytes=storage_info["read_bytes"],
                    write_bytes=storage_info["write_bytes"],
                    timestamp=datetime.utcnow()
                )
                db.add(metric)
                metrics.append(metric)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error storing storage metrics: {e}")
        finally:
            db.close()
        
        return metrics
    
    def get_historical_metrics(self, server_name: str, device: str = None, 
                               hours: int = 24) -> List[Dict]:
        """Get historical storage metrics"""
        from sqlalchemy import and_
        from datetime import timedelta
        
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = db.query(StorageMetric).filter(
                and_(
                    StorageMetric.server_name == server_name,
                    StorageMetric.timestamp >= cutoff_time
                )
            )
            
            if device:
                query = query.filter(StorageMetric.device == device)
            
            query = query.order_by(StorageMetric.timestamp.asc())
            
            metrics = query.all()
            return [{
                "timestamp": m.timestamp,
                "device": m.device,
                "mountpoint": m.mountpoint,
                "total": m.total,
                "used": m.used,
                "free": m.free,
                "percent": m.percent,
                "read_bytes": m.read_bytes,
                "write_bytes": m.write_bytes
            } for m in metrics]
        finally:
            db.close()
