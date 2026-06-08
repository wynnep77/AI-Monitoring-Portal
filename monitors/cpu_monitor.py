import psutil
from datetime import datetime
from typing import List, Dict
from database import CPUMetric, get_db

class CPUMonitor:
    def __init__(self):
        pass
    
    def get_cpu_info(self, server_name: str = "localhost") -> Dict:
        """Get current CPU and memory information"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Load average (Unix-like systems only)
            try:
                load_avg = psutil.getloadavg()
                load_avg_1m, load_avg_5m, load_avg_15m = load_avg
            except (AttributeError, OSError):
                # Windows or system without load average
                load_avg_1m = load_avg_5m = load_avg_15m = 0.0
            
            return {
                "server_name": server_name,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory.percent,
                "memory_used": memory.used / (1024**3),  # GB
                "memory_total": memory.total / (1024**3),  # GB
                "load_avg_1m": load_avg_1m,
                "load_avg_5m": load_avg_5m,
                "load_avg_15m": load_avg_15m
            }
        except Exception as e:
            print(f"Error getting CPU info: {e}")
            return None
    
    def collect_metrics(self, server_name: str = "localhost") -> CPUMetric:
        """Collect and store CPU metrics"""
        cpu_info = self.get_cpu_info(server_name)
        
        if not cpu_info:
            return None
        
        db = next(get_db())
        try:
            metric = CPUMetric(
                server_name=cpu_info["server_name"],
                cpu_percent=cpu_info["cpu_percent"],
                cpu_count=cpu_info["cpu_count"],
                memory_percent=cpu_info["memory_percent"],
                memory_used=cpu_info["memory_used"],
                memory_total=cpu_info["memory_total"],
                load_avg_1m=cpu_info["load_avg_1m"],
                load_avg_5m=cpu_info["load_avg_5m"],
                load_avg_15m=cpu_info["load_avg_15m"],
                timestamp=datetime.utcnow()
            )
            db.add(metric)
            db.commit()
            return metric
        except Exception as e:
            db.rollback()
            print(f"Error storing CPU metrics: {e}")
            return None
        finally:
            db.close()
    
    def get_historical_metrics(self, server_name: str, hours: int = 24) -> List[Dict]:
        """Get historical CPU metrics"""
        from sqlalchemy import and_
        from datetime import timedelta
        
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            metrics = db.query(CPUMetric).filter(
                and_(
                    CPUMetric.server_name == server_name,
                    CPUMetric.timestamp >= cutoff_time
                )
            ).order_by(CPUMetric.timestamp.asc()).all()
            
            return [{
                "timestamp": m.timestamp,
                "cpu_percent": m.cpu_percent,
                "cpu_count": m.cpu_count,
                "memory_percent": m.memory_percent,
                "memory_used": m.memory_used,
                "memory_total": m.memory_total,
                "load_avg_1m": m.load_avg_1m,
                "load_avg_5m": m.load_avg_5m,
                "load_avg_15m": m.load_avg_15m
            } for m in metrics]
        finally:
            db.close()
