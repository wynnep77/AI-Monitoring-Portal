import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Monitor, Cpu, HardDrive, Settings, Server, RefreshCw, Plus, Trash2, Download, Brain } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './index.css';

// Use empty base URL since nginx proxies /api to backend
const API_BASE = process.env.REACT_APP_API_URL || '';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('localhost');
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [showAddServer, setShowAddServer] = useState(false);
  const [testMode, setTestMode] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [apiStatus, setApiStatus] = useState('Unknown');
  const [exportPeriod, setExportPeriod] = useState(1);

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
    setApiError(null);
    setApiStatus('Fetching...');
    try {
      let response;
      const url = testMode ? `${API_BASE}/api/test` : `${API_BASE}/api/overview`;
      console.log('Fetching from:', url);
      
      if (testMode) {
        response = await axios.get(`${API_BASE}/api/test`);
      } else {
        response = await axios.get(`${API_BASE}/api/overview`, {
          params: { server_name: selectedServer }
        });
      }
      console.log('Response:', response.data);
      setOverview(response.data);
      setApiStatus('Connected');
    } catch (error) {
      console.error('Error fetching overview:', error);
      setApiError(error.message);
      setApiStatus('Error');
      if (error.response) {
        setApiError(`HTTP ${error.response.status}: ${error.response.statusText}`);
      } else if (error.request) {
        setApiError('No response from server - check if backend is running');
      }
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

  // Export all metrics to CSV
  const exportAllMetrics = async () => {
    try {
      const [gpuData, cpuData, storageData] = await Promise.all([
        axios.get(`${API_BASE}/api/gpu/historical`, { params: { server_name: selectedServer, hours: exportPeriod } }),
        axios.get(`${API_BASE}/api/cpu/historical`, { params: { server_name: selectedServer, hours: exportPeriod } }),
        axios.get(`${API_BASE}/api/storage/historical`, { params: { server_name: selectedServer, hours: exportPeriod } })
      ]);

      let csv = 'Type,Timestamp,Server,Value1,Value2,Value3,Value4,Value5\n';
      
      // GPU data
      if (gpuData.data.metrics) {
        gpuData.data.metrics.forEach(m => {
          csv += `GPU,${m.timestamp},${selectedServer},${m.gpu_id},${m.utilization},${m.memory_used},${m.memory_total},${m.temperature},${m.power_usage}\n`;
        });
      }
      
      // CPU data
      if (cpuData.data.metrics) {
        cpuData.data.metrics.forEach(m => {
          csv += `CPU,${m.timestamp},${selectedServer},${m.cpu_percent},${m.memory_percent},${m.memory_used},${m.memory_total},${m.load_avg_1m},${m.load_avg_5m}\n`;
        });
      }
      
      // Storage data
      if (storageData.data.metrics) {
        storageData.data.metrics.forEach(m => {
          csv += `Storage,${m.timestamp},${selectedServer},${m.device},${m.total},${m.used},${m.free},${m.percent},${m.read_bytes}\n`;
        });
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `all-metrics-${exportPeriod}hrs-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting metrics:', error);
      alert('Failed to export metrics');
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
              <div className={`text-sm px-3 py-1 rounded ${apiStatus === 'Connected' ? 'bg-green-600' : apiStatus === 'Error' ? 'bg-red-600' : 'bg-gray-600'}`}>
                API: {apiStatus}
              </div>
              <select
                value={exportPeriod}
                onChange={(e) => setExportPeriod(parseInt(e.target.value))}
                className="glossy-button px-3 py-1"
              >
                <option value={1}>1h</option>
                <option value={6}>6h</option>
                <option value={24}>24h</option>
                <option value={48}>48h</option>
              </select>
              <button
                onClick={exportAllMetrics}
                className="glossy-button flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export All
              </button>
              <button
                onClick={() => setTestMode(!testMode)}
                className={`glossy-button flex items-center gap-2 ${testMode ? 'bg-yellow-600' : ''}`}
              >
                <Monitor className="w-4 h-4" />
                {testMode ? 'Test Mode: ON' : 'Test Mode: OFF'}
              </button>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg-px-8 py-8">
        {/* Main Content */}
        <main className="flex-1">
            {/* Error Display */}
            {apiError && (
              <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
                <h3 className="text-white font-semibold mb-2">API Error</h3>
                <p className="text-red-200">{apiError}</p>
                <p className="text-red-300 text-sm mt-2">API URL: {API_BASE}</p>
              </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
              {[
                { id: 'overview', label: 'Overview', icon: Monitor },
                { id: 'gpu', label: 'GPU', icon: Monitor },
                { id: 'cpu', label: 'CPU', icon: Cpu },
                { id: 'storage', label: 'Storage', icon: HardDrive },
                { id: 'ollama', label: 'Ollama', icon: Brain },
                { id: 'servers', label: 'Servers', icon: Server },
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
            {activeTab === 'ollama' && (
              <OllamaTab serverName={selectedServer} API_BASE={API_BASE} />
            )}
            {activeTab === 'servers' && (
              <ServersTab
                servers={servers}
                selectedServer={selectedServer}
                setSelectedServer={setSelectedServer}
                onAddServer={addServer}
                onDeleteServer={deleteServer}
                showAddServer={showAddServer}
                setShowAddServer={setShowAddServer}
              />
            )}
            {activeTab === 'settings' && (
              <SettingsTab
                onCleanup={cleanupData}
                autoRefresh={autoRefresh}
                setAutoRefresh={setAutoRefresh}
                refreshInterval={refreshInterval}
                setRefreshInterval={setRefreshInterval}
              />
            )}
          </main>
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
    </div>
  );
}

// GPU Tab Component
function GPUTab({ serverName, API_BASE }) {
  const [gpuData, setGpuData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [selectedGpu, setSelectedGpu] = useState(null);
  const [timeRange, setTimeRange] = useState(1); // Default to 1 hour

  useEffect(() => {
    fetchGpuData();
  }, [serverName]);

  useEffect(() => {
    if (selectedGpu !== null) {
      fetchHistoricalData();
    }
  }, [selectedGpu, timeRange, serverName]);

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

  const exportGpuData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/gpu/historical`, {
        params: { server_name: serverName, gpu_id: selectedGpu, hours: timeRange }
      });
      
      let csv = 'Timestamp,GPU ID,Name,Utilization,Memory Used,Memory Total,Temperature,Power Usage,Fan Speed\n';
      if (response.data.metrics) {
        response.data.metrics.forEach(m => {
          csv += `${m.timestamp},${m.gpu_id},${m.gpu_name},${m.utilization},${m.memory_used},${m.memory_total},${m.temperature},${m.power_usage},${m.fan_speed}\n`;
        });
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gpu-metrics-${timeRange}hrs-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting GPU data:', error);
      alert('Failed to export GPU data');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">GPU Performance</h2>
      
      {gpuData && gpuData.gpus && gpuData.gpus.length > 0 ? (
        <div>
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

          <div className="glossy-card p-4 flex gap-4 items-center">
            <div className="flex-1">
              <label className="text-sm text-navy-300 block mb-2">Time Range</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(parseInt(e.target.value))}
                className="glossy-input w-full"
              >
                <option value={1}>Last 1 Hour</option>
                <option value={6}>Last 6 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={48}>Last 48 Hours</option>
              </select>
            </div>
            <button
              onClick={exportGpuData}
              className="glossy-button flex items-center gap-2 mt-6"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>

          {selectedGpu !== null && (
            <div>
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

              {/* Historical Graph */}
              {historicalData && historicalData.length > 0 && (
                <div className="glossy-card p-6 mt-4">
                  <h3 className="text-lg font-semibold text-white mb-4">GPU Utilization History</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                      <XAxis 
                        dataKey="timestamp" 
                        stroke="#94a3b8"
                        tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                      />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f' }}
                        labelStyle={{ color: '#e2e8f0' }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="utilization" stroke="#3b82f6" name="Utilization %" />
                      <Line type="monotone" dataKey="temperature" stroke="#ef4444" name="Temperature °C" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="glossy-card p-6 text-navy-200">No GPUs detected</div>
      )}
    </div>
  );
}

// CPU Tab Component
function CPUTab({ serverName, API_BASE }) {
  const [cpuData, setCpuData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [timeRange, setTimeRange] = useState(1);

  useEffect(() => {
    fetchCpuData();
  }, [serverName]);

  useEffect(() => {
    fetchHistoricalData();
  }, [timeRange, serverName]);

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

  const fetchHistoricalData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/cpu/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      setHistoricalData(response.data.metrics);
    } catch (error) {
      console.error('Error fetching historical CPU data:', error);
    }
  };

  const exportCpuData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/cpu/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      
      let csv = 'Timestamp,CPU Percent,Memory Percent,Memory Used,Memory Total,Load 1m,Load 5m,Load 15m\n';
      if (response.data.metrics) {
        response.data.metrics.forEach(m => {
          csv += `${m.timestamp},${m.cpu_percent},${m.memory_percent},${m.memory_used},${m.memory_total},${m.load_avg_1m},${m.load_avg_5m},${m.load_avg_15m}\n`;
        });
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cpu-metrics-${timeRange}hrs-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CPU data:', error);
      alert('Failed to export CPU data');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">CPU Performance</h2>
      
      <div className="glossy-card p-4 flex gap-4 items-center">
        <div className="flex-1">
          <label className="text-sm text-navy-300 block mb-2">Time Range</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="glossy-input w-full"
          >
            <option value={1}>Last 1 Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
          </select>
        </div>
        <button
          onClick={exportCpuData}
          className="glossy-button flex items-center gap-2 mt-6"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>
      
      {cpuData ? (
        <>
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

          {/* Historical Graph */}
          {historicalData && historicalData.length > 0 && (
            <div className="glossy-card p-6 mt-4">
              <h3 className="text-lg font-semibold text-white mb-4">CPU Utilization History</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="cpu_percent" stroke="#3b82f6" name="CPU %" />
                  <Line type="monotone" dataKey="memory_percent" stroke="#10b981" name="Memory %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      ) : (
        <div className="glossy-card p-6 text-navy-200">Unable to retrieve CPU metrics</div>
      )}
    </div>
  );
}

// Storage Tab Component
function StorageTab({ serverName, API_BASE }) {
  const [storageData, setStorageData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [timeRange, setTimeRange] = useState(1);

  useEffect(() => {
    fetchStorageData();
  }, [serverName]);

  useEffect(() => {
    fetchHistoricalData();
  }, [timeRange, serverName]);

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

  const fetchHistoricalData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/storage/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      setHistoricalData(response.data.metrics);
    } catch (error) {
      console.error('Error fetching historical storage data:', error);
    }
  };

  const exportStorageData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/storage/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      
      let csv = 'Timestamp,Device,Mountpoint,Total,Used,Free,Percent,Read Bytes,Write Bytes\n';
      if (response.data.metrics) {
        response.data.metrics.forEach(m => {
          csv += `${m.timestamp},${m.device},${m.mountpoint},${m.total},${m.used},${m.free},${m.percent},${m.read_bytes},${m.write_bytes}\n`;
        });
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `storage-metrics-${timeRange}hrs-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting storage data:', error);
      alert('Failed to export storage data');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Storage Performance</h2>
      
      <div className="glossy-card p-4 flex gap-4 items-center">
        <div className="flex-1">
          <label className="text-sm text-navy-300 block mb-2">Time Range</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="glossy-input w-full"
          >
            <option value={1}>Last 1 Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
          </select>
        </div>
        <button
          onClick={exportStorageData}
          className="glossy-button flex items-center gap-2 mt-6"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>
      
      {storageData && storageData.length > 0 ? (
        <>
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

          {/* Historical Graph */}
          {historicalData && historicalData.length > 0 && (
            <div className="glossy-card p-6 mt-4">
              <h3 className="text-lg font-semibold text-white mb-4">Storage Usage History</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="percent" stroke="#3b82f6" name="Usage %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      ) : (
        <div className="glossy-card p-6 text-navy-200">Unable to retrieve storage metrics</div>
      )}
    </div>
  );
}

// Settings Tab Component
function SettingsTab({
  onCleanup,
  autoRefresh,
  setAutoRefresh,
  refreshInterval,
  setRefreshInterval
}) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Settings</h2>
      
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

// Servers Tab Component
function ServersTab({
  servers,
  selectedServer,
  setSelectedServer,
  onAddServer,
  onDeleteServer,
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
      <h2 className="text-2xl font-bold text-white">Servers</h2>

      {/* Server Selection */}
      <div className="glossy-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Select Server</h3>
        <div className="space-y-2">
          <button
            onClick={() => setSelectedServer('localhost')}
            className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
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
              className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
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

      {/* Add Server */}
      <div className="glossy-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Add Server</h3>
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
    </div>
  );
}

// Ollama Tab Component
function OllamaTab({ serverName, API_BASE }) {
  const [ollamaData, setOllamaData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [timeRange, setTimeRange] = useState(1);

  useEffect(() => {
    fetchOllamaData();
  }, [serverName]);

  useEffect(() => {
    fetchHistoricalData();
  }, [timeRange, serverName]);

  const fetchOllamaData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/ollama/current`, {
        params: { server_name: serverName }
      });
      setOllamaData(response.data);
    } catch (error) {
      console.error('Error fetching Ollama data:', error);
    }
  };

  const fetchHistoricalData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/ollama/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      setHistoricalData(response.data.metrics);
    } catch (error) {
      console.error('Error fetching historical Ollama data:', error);
    }
  };

  const exportOllamaData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/ollama/historical`, {
        params: { server_name: serverName, hours: timeRange }
      });
      
      let csv = 'Timestamp,Model,Requests,Input Tokens,Output Tokens,Total Tokens\n';
      if (response.data.metrics) {
        response.data.metrics.forEach(m => {
          csv += `${m.timestamp},${m.model},${m.requests},${m.input_tokens},${m.output_tokens},${m.total_tokens}\n`;
        });
      }

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ollama-metrics-${timeRange}hrs-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting Ollama data:', error);
      alert('Failed to export Ollama data');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Ollama LLM Monitoring</h2>
      
      <div className="glossy-card p-4 flex gap-4 items-center">
        <div className="flex-1">
          <label className="text-sm text-navy-300 block mb-2">Time Range</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="glossy-input w-full"
          >
            <option value={1}>Last 1 Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
          </select>
        </div>
        <button
          onClick={exportOllamaData}
          className="glossy-button flex items-center gap-2 mt-6"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>
      
      {ollamaData && ollamaData.models ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ollamaData.models.map((model, idx) => (
              <div key={idx} className="glossy-card p-6">
                <div className="text-sm text-navy-300 uppercase tracking-wide mb-2">
                  Model
                </div>
                <div className="text-xl font-bold text-white mb-4">{model.name}</div>
                <div className="space-y-2 text-sm text-navy-200">
                  <div>Requests: {model.requests}</div>
                  <div>Input Tokens: {model.input_tokens}</div>
                  <div>Output Tokens: {model.output_tokens}</div>
                  <div>Total Tokens: {model.total_tokens}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Historical Graph */}
          {historicalData && historicalData.length > 0 && (
            <div className="glossy-card p-6 mt-4">
              <h3 className="text-lg font-semibold text-white mb-4">Token Generation History</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="input_tokens" stroke="#3b82f6" name="Input Tokens" />
                  <Line type="monotone" dataKey="output_tokens" stroke="#10b981" name="Output Tokens" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      ) : (
        <div className="glossy-card p-6 text-navy-200">Unable to retrieve Ollama metrics</div>
      )}
    </div>
  );
}

export default App;
