import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./monitoring.db"
    
    # Monitoring intervals (seconds)
    GPU_MONITOR_INTERVAL: int = 5
    CPU_MONITOR_INTERVAL: int = 5
    STORAGE_MONITOR_INTERVAL: int = 30
    
    # Data retention (days)
    DATA_RETENTION_DAYS: int = 365
    
    # Sampling rates for different time ranges
    HIGH_FREQUENCY_SAMPLING: int = 5  # seconds (last 24 hours)
    MEDIUM_FREQUENCY_SAMPLING: int = 60  # seconds (last 7 days)
    LOW_FREQUENCY_SAMPLING: int = 300  # seconds (older than 7 days)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure data directory exists
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
