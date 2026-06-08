from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings, DATA_DIR
import sqlite3

# Create database engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GPUMetric(Base):
    __tablename__ = "gpu_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True)
    gpu_id = Column(Integer, index=True)
    gpu_name = Column(String)
    utilization = Column(Float)
    memory_used = Column(Float)
    memory_total = Column(Float)
    temperature = Column(Float)
    power_usage = Column(Float)
    fan_speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_server_gpu_timestamp', 'server_name', 'gpu_id', 'timestamp'),
    )

class CPUMetric(Base):
    __tablename__ = "cpu_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True)
    cpu_percent = Column(Float)
    cpu_count = Column(Integer)
    memory_percent = Column(Float)
    memory_used = Column(Float)
    memory_total = Column(Float)
    load_avg_1m = Column(Float)
    load_avg_5m = Column(Float)
    load_avg_15m = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_server_timestamp', 'server_name', 'timestamp'),
    )

class StorageMetric(Base):
    __tablename__ = "storage_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True)
    device = Column(String)
    mountpoint = Column(String)
    total = Column(Float)
    used = Column(Float)
    free = Column(Float)
    percent = Column(Float)
    read_bytes = Column(Float)
    write_bytes = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_server_device_timestamp', 'server_name', 'device', 'timestamp'),
    )

class MonitoredServer(Base):
    __tablename__ = "monitored_servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    host = Column(String)
    port = Column(Integer, default=22)
    is_local = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def cleanup_old_data():
    """Remove data older than retention period"""
    from sqlalchemy import delete
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.DATA_RETENTION_DAYS)
        
        # Delete old GPU metrics
        db.execute(delete(GPUMetric).where(GPUMetric.timestamp < cutoff_date))
        
        # Delete old CPU metrics
        db.execute(delete(CPUMetric).where(CPUMetric.timestamp < cutoff_date))
        
        # Delete old storage metrics
        db.execute(delete(StorageMetric).where(StorageMetric.timestamp < cutoff_date))
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
