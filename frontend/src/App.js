import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Monitor, Cpu, HardDrive, Settings, Server, RefreshCw, Plus, Trash2 } from 'lucide-react';
import './index.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('localhost');
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [showAddServer, setShowAddServer] = useState(false);

  // Fetch servers
  const fetchServers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/servers`);
      setServers(response.data);
    } catch (error) {
      console.error('Error fetching servers:', error);
    }
  };

  // Fetch overview data
  const fetchOverview = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/overview`, {
        params: { server_name: selectedServer }
      });
      setOverview(response.data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  };

  // Add server
  const addServer = async (serverData) => {
    try {
      await axios.post(`${API_BASE}/api/servers`, serverData);
      await fetchServers();
      setShowAddServer(false);
    } catch (error) {
      console.error('Error adding server:', error);
    }
  };

  // Delete server
  const deleteServer = async (serverId) => {
    try {
      await axios.delete(`${API_BASE}/api/servers/${serverId}`);
      await fetchServers();
    } catch (error) {
      console.error('Error deleting server:', error);
    }
  };

  // Cleanup data
  const cleanupData = async () => {
    try {
      await axios.post(`${API_BASE}/api/data/cleanup`);
      alert('Old data cleaned up successfully');
    } catch (error) {
      console.error('Error cleaning up data:', error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchServers();
    fetchOverview();
  }, [selectedServer]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchOverview, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, selectedServer]);

  return (
    <div className="min-h-screen bg-navy-950">
      {/* Header */}
      <header className="bg-navy-900 border-b border-navy-700 shadow-glossy-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Monitor className="w-8 h-8 text-white" />
              <h1 className="text-2xl font-bold text-white">GPU Monitor Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={fetchOverview}
                className="glossy-button flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <div className="glossy-card p-4">
              <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                <Server className="w-5 h-5" />
                Servers
              </h2>
              <div className="space-y-2">
                <button
                  onClick={() => setSelectedServer('localhost')}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedServer === 'localhost'
                      ? 'bg-white text-navy-900 font-medium'
                      : 'text-navy-200 hover:bg-navy-700'
                  }`}
                >
                  🖥️ Localhost
                </button>
                {servers.map((server) => (
                  <button
                    key={server.id}
                    onClick={() => setSelectedServer(server.name)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedServer === server.name
                        ? 'bg-white text-navy-900 font-medium'
                        : 'text-navy-200 hover:bg-navy-700'
                    }`}
                  >
                    🖥️ {server.name}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {/* Tabs */}
            <div className="flex gap-2 mb-6">
              {[
                { id: 'overview', label: 'Overview', icon: Monitor },
                { id: 'gpu', label: 'GPU', icon: Monitor },
                { id: 'cpu', label: 'CPU', icon: Cpu },
                { id: 'storage', label: 'Storage', icon: HardDrive },
                { id: 'settings', label: 'Settings', icon: Settings },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    activeTab === tab.id
                      ? 'bg-white text-navy-900 font-medium shadow-glossy'
                      : 'text-navy-200 hover:bg-navy-800'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <OverviewTab overview={overview} loading={loading} />
            )}
            {activeTab === 'gpu' && (
              <GPUTab serverName={selectedServer} API_BASE={API_BASE} />
            )}
            {activeTab === 'cpu' && (
              <CPUTab serverName={selectedServer} API_BASE={API_BASE} />
            )}
            {activeTab === 'storage' && (
              <StorageTab serverName={selectedServer} API_BASE={API_BASE} />
            )}
            {activeTab === 'settings' && (
              <SettingsTab
                servers={servers}
                onAddServer={addServer}
                onDeleteServer={deleteServer}
                onCleanup={cleanupData}
                autoRefresh={autoRefresh}
                setAutoRefresh={setAutoRefresh}
                refreshInterval={refreshInterval}
                setRefreshInterval={setRefreshInterval}
                showAddServer={showAddServer}
                setShowAddServer={setShowAddServer}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ overview, loading }) {
  if (loading) {
    return <div className="text-navy-200">Loading...</div>;
  }

  if (!overview) {
    return <div className="text-navy-200">No data available</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">System Overview</h2>
      
      {/* GPU Cards */}
      {overview.gpu && overview.gpu.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">GPU Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {overview.gpu.map((gpu) => (
              <div key={gpu.gpu_id} className="glossy-card p-6">
                <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                  GPU {gpu.gpu_id}
                </div>
                <div className="text-xl font-bold text-white mb-4">{gpu.gpu_name}</div>
                <div className="space-y-2 text-sm text-navy-200">
                  <div>Utilization: {gpu.utilization}%</div>
                  <div>Memory: {gpu.memory_used.toFixed(1)} / {gpu.memory_total.toFixed(1)} GB</div>
                  <div>Temperature: {gpu.temperature}°C</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CPU Card */}
      {overview.cpu && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">CPU & Memory</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glossy-card p-6">
              <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                CPU Usage
              </div>
              <div className="text-3xl font-bold text-white">
                {overview.cpu.cpu_percent.toFixed(1)}%
              </div>
              <div className="text-sm text-navy-200 mt-2">
                Cores: {overview.cpu.cpu_count}
              </div>
            </div>
            <div className="glossy-card p-6">
              <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                Memory Usage
              </div>
              <div className="text-3xl font-bold text-white">
                {overview.cpu.memory_percent.toFixed(1)}%
              </div>
              <div className="text-sm text-navy-200 mt-2">
                {overview.cpu.memory_used.toFixed(1)} / {overview.cpu.memory_total.toFixed(1)} GB
              </div>
            </div>
            <div className="glossy-card p-6">
              <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                Load Average
              </div>
              <div className="text-3xl font-bold text-white">
                {overview.cpu.load_avg_1m.toFixed(2)}
              </div>
              <div className="text-sm text-navy-200 mt-2">
                1m: {overview.cpu.load_avg_1m.toFixed(2)} | 5m: {overview.cpu.load_avg_5m.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Storage Cards */}
      {overview.storage && overview.storage.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Storage</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {overview.storage.map((storage, idx) => (
              <div key={idx} className="glossy-card p-6">
                <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                  {storage.device} ({storage.mountpoint})
                </div>
                <div className="text-3xl font-bold text-white mb-2">
                  {storage.percent.toFixed(1)}%
                </div>
                <div className="text-sm text-navy-200">
                  {storage.used.toFixed(1)} GB used of {storage.total.toFixed(1)} GB
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// GPU Tab Component
function GPUTab({ serverName, API_BASE }) {
  const [gpuData, setGpuData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [selectedGpu, setSelectedGpu] = useState(null);
  const [timeRange, setTimeRange] = useState(24);

  useEffect(() => {
    fetchGpuData();
  }, [serverName]);

  const fetchGpuData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/gpu/current`, {
        params: { server_name: serverName }
      });
      setGpuData(response.data);
      if (response.data.gpus && response.data.gpus.length > 0) {
        setSelectedGpu(response.data.gpus[0].gpu_id);
      }
    } catch (error) {
      console.error('Error fetching GPU data:', error);
    }
  };

  const fetchHistoricalData = async () => {
    if (selectedGpu === null) return;
    try {
      const response = await axios.get(`${API_BASE}/api/gpu/historical`, {
        params: { server_name: serverName, gpu_id: selectedGpu, hours: timeRange }
      });
      setHistoricalData(response.data.metrics);
    } catch (error) {
      console.error('Error fetching historical GPU data:', error);
    }
  };

  useEffect(() => {
    fetchHistoricalData();
  }, [selectedGpu, timeRange]);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">GPU Performance</h2>
      
      {gpuData && gpuData.gpus && gpuData.gpus.length > 0 ? (
        <>
          <div className="glossy-card p-4">
            <label className="text-sm text-navy-300 block mb-2">Select GPU</label>
            <select
              value={selectedGpu || ''}
              onChange={(e) => setSelectedGpu(parseInt(e.target.value))}
              className="glossy-input w-full"
            >
              {gpuData.gpus.map((gpu) => (
                <option key={gpu.gpu_id} value={gpu.gpu_id}>
                  GPU {gpu.gpu_id} - {gpu.gpu_name}
                </option>
              ))}
            </select>
          </div>

          <div className="glossy-card p-4">
            <label className="text-sm text-navy-300 block mb-2">Time Range</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              className="glossy-input w-full"
            >
              <option value={1}>Last 1 Hour</option>
              <option value={6}>Last 6 Hours</option>
              <option value={24}>Last 24 Hours</option>
              <option value={168}>Last 7 Days</option>
            </select>
          </div>

          {selectedGpu !== null && (
            <div className="glossy-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                GPU {selectedGpu} Details
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-navy-300">GPU Name</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.gpu_name}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-navy-300">Utilization</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.utilization}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-navy-300">Memory Used</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.memory_used.toFixed(2)} GB
                  </div>
                </div>
                <div>
                  <div className="text-sm text-navy-300">Memory Total</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.memory_total.toFixed(2)} GB
                  </div>
                </div>
                <div>
                  <div className="text-sm text-navy-300">Temperature</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.temperature}°C
                  </div>
                </div>
                <div>
                  <div className="text-sm text-navy-300">Power Usage</div>
                  <div className="text-white font-medium">
                    {gpuData.gpus.find(g => g.gpu_id === selectedGpu)?.power_usage.toFixed(2)} W
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="glossy-card p-6 text-navy-200">No GPUs detected</div>
      )}
    </div>
  );
}

// CPU Tab Component
function CPUTab({ serverName, API_BASE }) {
  const [cpuData, setCpuData] = useState(null);

  useEffect(() => {
    fetchCpuData();
  }, [serverName]);

  const fetchCpuData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/cpu/current`, {
        params: { server_name: serverName }
      });
      setCpuData(response.data.cpu);
    } catch (error) {
      console.error('Error fetching CPU data:', error);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">CPU Performance</h2>
      
      {cpuData ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glossy-card p-6">
            <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
              CPU Cores
            </div>
            <div className="text-3xl font-bold text-white">{cpuData.cpu_count}</div>
          </div>
          <div className="glossy-card p-6">
            <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
              CPU Usage
            </div>
            <div className="text-3xl font-bold text-white">
              {cpuData.cpu_percent.toFixed(1)}%
            </div>
          </div>
          <div className="glossy-card p-6">
            <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
              Memory Used
            </div>
            <div className="text-3xl font-bold text-white">
              {cpuData.memory_used.toFixed(2)} GB
            </div>
          </div>
          <div className="glossy-card p-6">
            <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
              Memory Total
            </div>
            <div className="text-3xl font-bold text-white">
              {cpuData.memory_total.toFixed(2)} GB
            </div>
          </div>
        </div>
      ) : (
        <div className="glossy-card p-6 text-navy-200">Unable to retrieve CPU metrics</div>
      )}
    </div>
  );
}

// Storage Tab Component
function StorageTab({ serverName, API_BASE }) {
  const [storageData, setStorageData] = useState(null);

  useEffect(() => {
    fetchStorageData();
  }, [serverName]);

  const fetchStorageData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/storage/current`, {
        params: { server_name: serverName }
      });
      setStorageData(response.data.storage);
    } catch (error) {
      console.error('Error fetching storage data:', error);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Storage Performance</h2>
      
      {storageData && storageData.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {storageData.map((storage, idx) => (
            <div key={idx} className="glossy-card p-6">
              <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                {storage.device}
              </div>
              <div className="text-lg font-semibold text-white mb-2">
                {storage.mountpoint}
              </div>
              <div className="text-3xl font-bold text-white mb-2">
                {storage.percent.toFixed(1)}%
              </div>
              <div className="text-sm text-navy-200">
                {storage.used.toFixed(1)} GB used of {storage.total.toFixed(1)} GB
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glossy-card p-6 text-navy-200">Unable to retrieve storage metrics</div>
      )}
    </div>
  );
}

// Settings Tab Component
function SettingsTab({
  servers,
  onAddServer,
  onDeleteServer,
  onCleanup,
  autoRefresh,
  setAutoRefresh,
  refreshInterval,
  setRefreshInterval,
  showAddServer,
  setShowAddServer
}) {
  const [newServer, setNewServer] = useState({ name: '', host: 'localhost', port: 22, is_local: true });

  const handleAddServer = (e) => {
    e.preventDefault();
    onAddServer(newServer);
    setNewServer({ name: '', host: 'localhost', port: 22, is_local: true });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Settings</h2>
      
      {/* Server Management */}
      <div className="glossy-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Monitored Servers</h3>
        
        <button
          onClick={() => setShowAddServer(!showAddServer)}
          className="glossy-button-primary flex items-center gap-2 mb-4"
        >
          <Plus className="w-4 h-4" />
          Add New Server
        </button>

        {showAddServer && (
          <form onSubmit={handleAddServer} className="space-y-4 mb-4 p-4 bg-navy-900 rounded-lg">
            <div>
              <label className="text-sm text-navy-300 block mb-2">Server Name</label>
              <input
                type="text"
                value={newServer.name}
                onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
                className="glossy-input w-full"
                required
              />
            </div>
            <div>
              <label className="text-sm text-navy-300 block mb-2">Host/IP</label>
              <input
                type="text"
                value={newServer.host}
                onChange={(e) => setNewServer({ ...newServer, host: e.target.value })}
                className="glossy-input w-full"
              />
            </div>
            <div>
              <label className="text-sm text-navy-300 block mb-2">Port</label>
              <input
                type="number"
                value={newServer.port}
                onChange={(e) => setNewServer({ ...newServer, port: parseInt(e.target.value) })}
                className="glossy-input w-full"
                min="1"
                max="65535"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_local"
                checked={newServer.is_local}
                onChange={(e) => setNewServer({ ...newServer, is_local: e.target.checked })}
                className="w-4 h-4"
              />
              <label htmlFor="is_local" className="text-white">Local Server</label>
            </div>
            <button type="submit" className="glossy-button-primary">
              Add Server
            </button>
          </form>
        )}

        <div className="space-y-2">
          {servers.map((server) => (
            <div key={server.id} className="flex items-center justify-between p-3 bg-navy-900 rounded-lg">
              <div className="text-white">
                🖥️ {server.name} ({server.host}:{server.port})
              </div>
              <button
                onClick={() => onDeleteServer(server.id)}
                className="text-red-400 hover:text-red-300"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Refresh Settings */}
      <div className="glossy-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Refresh Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="auto_refresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="auto_refresh" className="text-white">Auto Refresh</label>
          </div>
          <div>
            <label className="text-sm text-navy-300 block mb-2">Refresh Interval (seconds)</label>
            <input
              type="number"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              className="glossy-input w-full"
              min="1"
              max="60"
            />
          </div>
        </div>
      </div>

      {/* Data Management */}
      <div className="glossy-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Data Management</h3>
        <button onClick={onCleanup} className="glossy-button">
          🧹 Cleanup Old Data
        </button>
      </div>
    </div>
  );
}

export default App;
