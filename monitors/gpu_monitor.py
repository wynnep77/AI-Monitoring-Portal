import pynvml
from datetime import datetime
from typing import List, Dict, Optional
from database import GPUMetric, get_db

class GPUMonitor:
    def __init__(self):
        self.initialized = False
        try:
            pynvml.nvmlInit()
            self.initialized = True
        except Exception as e:
            print(f"Failed to initialize NVML: {e}")
    
    def get_gpu_count(self) -> int:
        """Get number of GPUs"""
        if not self.initialized:
            return 0
        try:
            return pynvml.nvmlDeviceGetCount()
        except:
            return 0
    
    def get_gpu_info(self, gpu_id: int) -> Dict:
        """Get detailed information for a specific GPU"""
        if not self.initialized:
            return None
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Power info (may not be available on all GPUs)
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            except:
                power_usage = 0.0
            
            # Fan speed (may not be available on all GPUs)
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except:
                fan_speed = 0.0
            
            return {
                "gpu_id": gpu_id,
                "gpu_name": name.decode('utf-8') if isinstance(name, bytes) else name,
                "utilization": utilization.gpu,
                "memory_used": memory_info.used / (1024**3),  # GB
                "memory_total": memory_info.total / (1024**3),  # GB
                "temperature": temperature,
                "power_usage": power_usage,
                "fan_speed": fan_speed
            }
        except Exception as e:
            print(f"Error getting GPU {gpu_id} info: {e}")
            return None
    
    def get_all_gpu_info(self, server_name: str = "localhost") -> List[Dict]:
        """Get information for all GPUs"""
        gpu_count = self.get_gpu_count()
        gpus = []
        
        for gpu_id in range(gpu_count):
            gpu_info = self.get_gpu_info(gpu_id)
            if gpu_info:
                gpu_info["server_name"] = server_name
                gpus.append(gpu_info)
        
        return gpus
    
    def collect_metrics(self, server_name: str = "localhost") -> List[GPUMetric]:
        """Collect and store GPU metrics"""
        gpu_infos = self.get_all_gpu_info(server_name)
        metrics = []
        
        db = next(get_db())
        try:
            for gpu_info in gpu_infos:
                metric = GPUMetric(
                    server_name=gpu_info["server_name"],
                    gpu_id=gpu_info["gpu_id"],
                    gpu_name=gpu_info["gpu_name"],
                    utilization=gpu_info["utilization"],
                    memory_used=gpu_info["memory_used"],
                    memory_total=gpu_info["memory_total"],
                    temperature=gpu_info["temperature"],
                    power_usage=gpu_info["power_usage"],
                    fan_speed=gpu_info["fan_speed"],
                    timestamp=datetime.utcnow()
                )
                db.add(metric)
                metrics.append(metric)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error storing GPU metrics: {e}")
        finally:
            db.close()
        
        return metrics
    
    def get_historical_metrics(self, server_name: str, gpu_id: Optional[int] = None, 
                               hours: int = 24) -> List[Dict]:
        """Get historical GPU metrics"""
        from sqlalchemy import and_
        from datetime import timedelta
        
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = db.query(GPUMetric).filter(
                and_(
                    GPUMetric.server_name == server_name,
                    GPUMetric.timestamp >= cutoff_time
                )
            )
            
            if gpu_id is not None:
                query = query.filter(GPUMetric.gpu_id == gpu_id)
            
            query = query.order_by(GPUMetric.timestamp.asc())
            
            metrics = query.all()
            return [{
                "timestamp": m.timestamp,
                "gpu_id": m.gpu_id,
                "gpu_name": m.gpu_name,
                "utilization": m.utilization,
                "memory_used": m.memory_used,
                "memory_total": m.memory_total,
                "temperature": m.temperature,
                "power_usage": m.power_usage,
                "fan_speed": m.fan_speed
            } for m in metrics]
        finally:
            db.close()
    
    def shutdown(self):
        """Cleanup NVML"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
