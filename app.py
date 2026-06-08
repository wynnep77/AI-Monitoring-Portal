import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from database import init_db, get_db, MonitoredServer, cleanup_old_data
from monitors import GPUMonitor, CPUMonitor, StorageMonitor
from config import settings

# Initialize database
init_db()

# Page configuration
st.set_page_config(
    page_title="GPU Monitor Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for VMware vCenter-like styling with dark theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #00B4D8;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #262730;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
        border: 1px solid #3E4147;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stButton>button {
        background-color: #00B4D8;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #0096B4;
    }
    div[data-testid="stExpander"] {
        background-color: #1E2127;
        border: 1px solid #3E4147;
        border-radius: 8px;
    }
    .stSelectbox > div > div > div {
        background-color: #1E2127;
    }
    .stSlider > div > div > div {
        background-color: #1E2127;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'servers' not in st.session_state:
    st.session_state.servers = []
if 'selected_server' not in st.session_state:
    st.session_state.selected_server = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5

# Initialize monitors
gpu_monitor = GPUMonitor()
cpu_monitor = CPUMonitor()
storage_monitor = StorageMonitor()

def load_servers():
    """Load monitored servers from database"""
    db = next(get_db())
    try:
        servers = db.query(MonitoredServer).all()
        return servers
    finally:
        db.close()

def add_server(name, host, port, is_local):
    """Add a new server to monitor"""
    db = next(get_db())
    try:
        server = MonitoredServer(
            name=name,
            host=host,
            port=port,
            is_local=1 if is_local else 0
        )
        db.add(server)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error adding server: {e}")
        return False
    finally:
        db.close()

def remove_server(server_id):
    """Remove a server from monitoring"""
    db = next(get_db())
    try:
        server = db.query(MonitoredServer).filter(MonitoredServer.id == server_id).first()
        if server:
            db.delete(server)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        st.error(f"Error removing server: {e}")
        return False
    finally:
        db.close()

# Sidebar - simplified to just server selection
with st.sidebar:
    st.markdown('<div class="main-header">🖥️ Servers</div>', unsafe_allow_html=True)
    
    servers = load_servers()
    
    # Display existing servers
    if servers:
        st.subheader("Active Servers")
        for server in servers:
            if st.button(f"🖥️ {server.name}", key=f"select_{server.id}", use_container_width=True):
                st.session_state.selected_server = server.name
                st.rerun()
    else:
        st.info("No servers configured. Add a server in Settings.")

# Main content
st.markdown('<div class="main-header">🖥️ GPU Monitor Dashboard</div>', unsafe_allow_html=True)

# Default to localhost if no server selected
current_server = st.session_state.selected_server if st.session_state.selected_server else "localhost"

# Server selector in main area
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.info(f"📍 Currently Monitoring: **{current_server}**")
with col2:
    if st.button("🔄 Refresh Now", key="refresh_now"):
        st.rerun()
with col3:
    last_update = datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last update: {last_update}")

# Collect current metrics
gpu_metrics = gpu_monitor.get_all_gpu_info(current_server)
cpu_metrics = cpu_monitor.get_cpu_info(current_server)
storage_metrics = storage_monitor.get_storage_info(current_server)

# Store metrics in database
if gpu_metrics:
    gpu_monitor.collect_metrics(current_server)
if cpu_metrics:
    cpu_monitor.collect_metrics(current_server)
if storage_metrics:
    storage_monitor.collect_metrics(current_server)

# Dashboard tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🎮 GPU Performance", "💻 CPU Performance", "💾 Storage Performance", "⚙️ Settings"])

with tab1:
    st.subheader("System Overview")
    
    # GPU Overview
    if gpu_metrics:
        st.markdown("### GPU Status")
        gpu_cols = st.columns(len(gpu_metrics))
        for i, gpu in enumerate(gpu_metrics):
            with gpu_cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">GPU {gpu['gpu_id']}</div>
                    <div class="metric-value">{gpu['gpu_name']}</div>
                    <div style="margin-top: 0.5rem;">
                        <small>Utilization: {gpu['utilization']}%</small><br>
                        <small>Memory: {gpu['memory_used']:.1f}/{gpu['memory_total']:.1f} GB</small><br>
                        <small>Temperature: {gpu['temperature']}°C</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No GPUs detected on this server")
    
    # CPU Overview
    if cpu_metrics:
        st.markdown("### CPU & Memory Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-value">{cpu_metrics['cpu_percent']:.1f}%</div>
                <small>Cores: {cpu_metrics['cpu_count']}</small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Memory Usage</div>
                <div class="metric-value">{cpu_metrics['memory_percent']:.1f}%</div>
                <small>{cpu_metrics['memory_used']:.1f}/{cpu_metrics['memory_total']:.1f} GB</small>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Load Average</div>
                <div class="metric-value">{cpu_metrics['load_avg_1m']:.2f}</div>
                <small>1m: {cpu_metrics['load_avg_1m']:.2f} | 5m: {cpu_metrics['load_avg_5m']:.2f} | 15m: {cpu_metrics['load_avg_15m']:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Storage Overview
    if storage_metrics:
        st.markdown("### Storage Status")
        for storage in storage_metrics:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{storage['device']} ({storage['mountpoint']})</div>
                <div class="metric-value">{storage['percent']:.1f}%</div>
                <small>{storage['used']:.1f} GB used of {storage['total']:.1f} GB</small>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("GPU Performance Details")
    
    if gpu_metrics:
        # GPU selector
        gpu_options = [f"GPU {gpu['gpu_id']} - {gpu['gpu_name']}" for gpu in gpu_metrics]
        selected_gpu = st.selectbox("Select GPU", gpu_options)
        gpu_id = int(selected_gpu.split(" - ")[0].split(" ")[1])
        
        # Get historical data
        time_range = st.selectbox("Time Range", ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"])
        hours_map = {"Last 1 Hour": 1, "Last 6 Hours": 6, "Last 24 Hours": 24, "Last 7 Days": 168}
        hours = hours_map[time_range]
        
        historical_gpu = gpu_monitor.get_historical_metrics(current_server, gpu_id, hours)
        
        if historical_gpu:
            df = pd.DataFrame(historical_gpu)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('GPU Utilization', 'Memory Usage', 'Temperature', 'Power Usage'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # GPU Utilization
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['utilization'], name='Utilization %', line=dict(color='#1E88E5')),
                row=1, col=1
            )
            
            # Memory Usage
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['memory_used'], name='Memory Used (GB)', line=dict(color='#43A047')),
                row=1, col=2
            )
            
            # Temperature
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['temperature'], name='Temperature (°C)', line=dict(color='#FB8C00')),
                row=2, col=1
            )
            
            # Power Usage
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['power_usage'], name='Power (W)', line=dict(color='#E53935')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data available for this GPU")
        
        # Current GPU details
        gpu_info = next((g for g in gpu_metrics if g['gpu_id'] == gpu_id), None)
        if gpu_info:
            st.markdown("### Current GPU Details")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("GPU Name", gpu_info['gpu_name'])
                st.metric("Utilization", f"{gpu_info['utilization']}%")
                st.metric("Memory Used", f"{gpu_info['memory_used']:.2f} GB")
            with col2:
                st.metric("Memory Total", f"{gpu_info['memory_total']:.2f} GB")
                st.metric("Temperature", f"{gpu_info['temperature']}°C")
                st.metric("Power Usage", f"{gpu_info['power_usage']:.2f} W")
    else:
        st.warning("No GPUs detected on this server")

with tab3:
    st.subheader("CPU Performance Details")
    
    if cpu_metrics:
        # Get historical data
        time_range = st.selectbox("Time Range", ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"], key="cpu_time_range")
        hours_map = {"Last 1 Hour": 1, "Last 6 Hours": 6, "Last 24 Hours": 24, "Last 7 Days": 168}
        hours = hours_map[time_range]
        
        historical_cpu = cpu_monitor.get_historical_metrics(current_server, hours)
        
        if historical_cpu:
            df = pd.DataFrame(historical_cpu)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('CPU Utilization', 'Memory Usage', 'Load Average (1m)', 'Load Average (5m/15m)'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # CPU Utilization
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['cpu_percent'], name='CPU %', line=dict(color='#1E88E5')),
                row=1, col=1
            )
            
            # Memory Usage
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['memory_percent'], name='Memory %', line=dict(color='#43A047')),
                row=1, col=2
            )
            
            # Load Average 1m
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['load_avg_1m'], name='Load 1m', line=dict(color='#FB8C00')),
                row=2, col=1
            )
            
            # Load Average 5m/15m
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['load_avg_5m'], name='Load 5m', line=dict(color='#E53935')),
                row=2, col=2
            )
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['load_avg_15m'], name='Load 15m', line=dict(color='#8E24AA')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=True, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data available for CPU")
        
        # Current CPU details
        st.markdown("### Current CPU Details")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU Cores", cpu_metrics['cpu_count'])
            st.metric("CPU Usage", f"{cpu_metrics['cpu_percent']:.1f}%")
        with col2:
            st.metric("Memory Used", f"{cpu_metrics['memory_used']:.2f} GB")
            st.metric("Memory Total", f"{cpu_metrics['memory_total']:.2f} GB")
    else:
        st.warning("Unable to retrieve CPU metrics")

with tab4:
    st.subheader("Storage Performance Details")
    
    if storage_metrics:
        # Storage selector
        storage_options = [f"{s['device']} ({s['mountpoint']})" for s in storage_metrics]
        selected_storage = st.selectbox("Select Storage", storage_options)
        selected_device = selected_storage.split(" (")[0]
        
        # Get historical data
        time_range = st.selectbox("Time Range", ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"], key="storage_time_range")
        hours_map = {"Last 1 Hour": 1, "Last 6 Hours": 6, "Last 24 Hours": 24, "Last 7 Days": 168}
        hours = hours_map[time_range]
        
        historical_storage = storage_monitor.get_historical_metrics(current_server, selected_device, hours)
        
        if historical_storage:
            df = pd.DataFrame(historical_storage)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Storage Usage %', 'I/O Operations'),
                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            )
            
            # Storage Usage
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['percent'], name='Usage %', line=dict(color='#1E88E5')),
                row=1, col=1
            )
            
            # I/O Operations
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['read_bytes'], name='Read Bytes', line=dict(color='#43A047')),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['write_bytes'], name='Write Bytes', line=dict(color='#E53935')),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data available for this storage device")
        
        # Current storage details
        storage_info = next((s for s in storage_metrics if s['device'] == selected_device), None)
        if storage_info:
            st.markdown("### Current Storage Details")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Device", storage_info['device'])
                st.metric("Mount Point", storage_info['mountpoint'])
            with col2:
                st.metric("Total Space", f"{storage_info['total']:.2f} GB")
                st.metric("Used Space", f"{storage_info['used']:.2f} GB ({storage_info['percent']:.1f}%)")
    else:
        st.warning("Unable to retrieve storage metrics")

with tab5:
    st.subheader("Settings")
    
    # Server management
    st.markdown("### Monitored Servers")
    
    with st.expander("Add New Server", expanded=False):
        new_server_name = st.text_input("Server Name", key="new_server_name")
        new_server_host = st.text_input("Host/IP", key="new_server_host", value="localhost")
        new_server_port = st.number_input("Port", key="new_server_port", value=22, min_value=1, max_value=65535)
        is_local = st.checkbox("Local Server", value=True, key="is_local")
        
        if st.button("Add Server", key="add_server_btn"):
            if new_server_name:
                if add_server(new_server_name, new_server_host, new_server_port, is_local):
                    st.success(f"Server '{new_server_name}' added successfully!")
                    st.rerun()
            else:
                st.error("Please enter a server name")
    
    # Display existing servers with delete option
    if servers:
        st.markdown("### Active Servers")
        for server in servers:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"🖥️ {server.name} ({server.host}:{server.port})")
            with col2:
                if st.button("🗑️", key=f"delete_{server.id}"):
                    if remove_server(server.id):
                        st.success(f"Server '{server.name}' removed")
                        st.rerun()
    
    st.divider()
    
    # Refresh settings
    st.markdown("### Refresh Settings")
    st.session_state.auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
    st.session_state.refresh_interval = st.slider("Refresh Interval (seconds)", 1, 60, st.session_state.refresh_interval)
    
    st.divider()
    
    # Data management
    st.markdown("### Data Management")
    if st.button("🧹 Cleanup Old Data"):
        cleanup_old_data()
        st.success("Old data cleaned up successfully!")
    
    st.markdown("### GPU Detection Status")
    if gpu_monitor.initialized:
        if gpu_monitor.use_smi_fallback:
            st.warning("⚠️ Using nvidia-smi fallback mode (NVML not available)")
        else:
            st.success("✅ NVML initialized successfully")
    else:
        st.error("❌ GPU monitoring not initialized")
        if gpu_monitor.init_error:
            st.caption(f"Error: {gpu_monitor.init_error}")

# Auto refresh
if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
