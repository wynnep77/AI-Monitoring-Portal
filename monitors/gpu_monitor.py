import pynvml
import subprocess
import re
from datetime import datetime
from typing import List, Dict, Optional
from database import GPUMetric, get_db

class GPUMonitor:
    def __init__(self):
        self.initialized = False
        self.init_error = None
        self.use_smi_fallback = False
        print("=" * 60)
        print("Initializing GPU Monitor")
        print("=" * 60)
        
        # Check if nvidia-smi is available
        print("Checking nvidia-smi availability...")
        try:
            result = subprocess.run(['which', 'nvidia-smi'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"nvidia-smi found at: {result.stdout.strip()}")
            else:
                print("nvidia-smi not found in PATH")
        except Exception as e:
            print(f"Error checking nvidia-smi: {e}")
        
        # Try nvidia-smi directly
        print("Testing nvidia-smi command...")
        try:
            result = subprocess.run(['nvidia-smi', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"nvidia-smi version: {result.stdout.strip()}")
            else:
                print(f"nvidia-smi failed: {result.stderr}")
        except Exception as e:
            print(f"nvidia-smi command failed: {e}")
        
        # Try NVML initialization
        print("Attempting NVML initialization...")
        try:
            pynvml.nvmlInit()
            self.initialized = True
            print("✅ NVML initialized successfully")
            device_count = pynvml.nvmlDeviceGetCount()
            print(f"✅ Found {device_count} GPU(s) via NVML")
        except Exception as e:
            self.init_error = str(e)
            print(f"❌ Failed to initialize NVML: {e}")
            print("Attempting to check GPU availability via nvidia-smi...")
            if self._check_nvidia_smi():
                print("✅ GPUs available via nvidia-smi, using fallback method")
                self.use_smi_fallback = True
                self.initialized = True
            else:
                print("❌ No GPUs detected via nvidia-smi")
        
        # If NVML initialized but can't get GPU count, force fallback
        if self.initialized and not self.use_smi_fallback:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count == 0:
                    print("⚠️  NVML reports 0 GPUs, trying nvidia-smi fallback")
                    if self._check_nvidia_smi():
                        print("✅ GPUs available via nvidia-smi, switching to fallback method")
                        self.use_smi_fallback = True
            except Exception as e:
                print(f"⚠️  Error getting GPU count via NVML: {e}, trying nvidia-smi fallback")
                if self._check_nvidia_smi():
                    print("✅ GPUs available via nvidia-smi, switching to fallback method")
                    self.use_smi_fallback = True
        
        print("=" * 60)
    
    def _check_nvidia_smi(self) -> bool:
        """Check GPU availability using nvidia-smi command"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_names = result.stdout.strip().split('\n')
                print(f"GPUs detected via nvidia-smi: {gpu_names}")
                return True
            else:
                print(f"nvidia-smi failed with return code: {result.returncode}")
                print(f"Error: {result.stderr}")
                return False
        except FileNotFoundError:
            print("nvidia-smi command not found. NVIDIA drivers may not be installed.")
            return False
        except subprocess.TimeoutExpired:
            print("nvidia-smi command timed out.")
            return False
        except Exception as e:
            print(f"Error running nvidia-smi: {e}")
            return False
    
    def _get_gpu_info_smi(self, gpu_id: int) -> Optional[Dict]:
        """Get GPU info using nvidia-smi as fallback"""
        try:
            # Get GPU name
            name_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            if name_result.returncode != 0:
                return None
            gpu_name = name_result.stdout.strip()
            
            # Get utilization
            util_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            utilization = int(util_result.stdout.strip()) if util_result.returncode == 0 else 0
            
            # Get memory info
            mem_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            if mem_result.returncode == 0:
                mem_used, mem_total = map(int, mem_result.stdout.strip().split(','))
                mem_used_gb = mem_used / 1024
                mem_total_gb = mem_total / 1024
            else:
                mem_used_gb = 0
                mem_total_gb = 0
            
            # Get temperature
            temp_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            temperature = int(temp_result.stdout.strip()) if temp_result.returncode == 0 else 0
            
            # Get power usage
            power_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            power_usage = float(power_result.stdout.strip()) if power_result.returncode == 0 else 0.0
            
            # Get fan speed
            fan_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=fan.speed', '--format=csv,noheader,nounits', '--id', str(gpu_id)],
                capture_output=True, text=True, timeout=5
            )
            fan_speed = int(fan_result.stdout.strip()) if fan_result.returncode == 0 else 0
            
            return {
                "gpu_id": gpu_id,
                "gpu_name": gpu_name,
                "utilization": utilization,
                "memory_used": mem_used_gb,
                "memory_total": mem_total_gb,
                "temperature": temperature,
                "power_usage": power_usage,
                "fan_speed": fan_speed
            }
        except Exception as e:
            print(f"Error getting GPU {gpu_id} info via nvidia-smi: {e}")
            return None
    
    def get_gpu_count(self) -> int:
        """Get number of GPUs"""
        if not self.initialized:
            return 0
        if self.use_smi_fallback:
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=count', '--format=csv,noheader'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return int(result.stdout.strip())
            except:
                pass
            return 0
        try:
            return pynvml.nvmlDeviceGetCount()
        except:
            return 0
    
    def get_gpu_info(self, gpu_id: int) -> Dict:
        """Get detailed information for a specific GPU"""
        if not self.initialized:
            return None
        
        if self.use_smi_fallback:
            return self._get_gpu_info_smi(gpu_id)
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Power info (may not be available on all GPUs)
            power_usage = 0.0
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            except pynvml.NVMLError as e:
                if str(e) != "Not Supported":
                    print(f"Warning: Could not get power usage for GPU {gpu_id}: {e}")
            
            # Fan speed (may not be available on all GPUs)
            fan_speed = 0
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError as e:
                if str(e) != "Not Supported":
                    print(f"Warning: Could not get fan speed for GPU {gpu_id}: {e}")
            
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
        except pynvml.NVMLError as e:
            if str(e) == "Not Supported":
                print(f"Warning: Some metrics not supported for GPU {gpu_id}, using fallback")
                # Try fallback method for this GPU
                return self._get_gpu_info_smi(gpu_id)
            print(f"Error getting GPU {gpu_id} info: {e}")
            return None
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
