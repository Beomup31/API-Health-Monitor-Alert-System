import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, CheckCircle2, XCircle, Activity, Trash2, ExternalLink } from 'lucide-react';
import apiClient from '../api/axios';
import AddEndpointModal from './AddEndpointModal';

const Dashboard = () => {
  const [endpoints, setEndpoints] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchEndpoints = async () => {
    try {
      const response = await apiClient.get('/endpoints/');
      const endpointsData = response.data;
      
      // Fetch latest log for each endpoint to determine status
      const endpointsWithStatus = await Promise.all(
        endpointsData.map(async (ep) => {
          try {
            const logsRes = await apiClient.get(`/endpoints/${ep.id}/logs?limit=50`);
            const logs = logsRes.data;
            const latestLog = logs.length > 0 ? logs[0] : null;
            
            // Calculate average response time
            const avgTime = logs.length > 0 
              ? logs.reduce((acc, log) => acc + (log.response_time_ms || 0), 0) / logs.length
              : 0;

            return { ...ep, latestLog, avgTime, totalLogs: logs.length };
          } catch (error) {
            console.error(`Error fetching logs for endpoint ${ep.id}:`, error);
            return { ...ep, latestLog: null, avgTime: 0, totalLogs: 0 };
          }
        })
      );
      
      setEndpoints(endpointsWithStatus);
    } catch (error) {
      console.error('Failed to fetch endpoints:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEndpoints();
    // Poll every 30 seconds
    const interval = setInterval(fetchEndpoints, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    if (window.confirm('Are you sure you want to delete this endpoint?')) {
      try {
        await apiClient.delete(`/endpoints/${id}`);
        fetchEndpoints();
      } catch (error) {
        console.error('Failed to delete endpoint:', error);
      }
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Activity className="animate-spin h-8 w-8 text-blue-500" /></div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Monitored Endpoints</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          <Plus size={18} /> Add Endpoint
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {endpoints.length === 0 ? (
            <li className="p-6 text-center text-gray-500">No endpoints configured yet. Add one to get started!</li>
          ) : (
            endpoints.map((endpoint) => (
              <li key={endpoint.id}>
                <Link to={`/endpoints/${endpoint.id}`} className="block hover:bg-gray-50 transition">
                  <div className="px-4 py-4 sm:px-6 flex items-center justify-between">
                    <div className="flex items-center flex-1 min-w-0">
                      <div className="flex-shrink-0">
                        {endpoint.latestLog ? (
                          endpoint.latestLog.is_success ? (
                            <CheckCircle2 className="h-8 w-8 text-green-500" />
                          ) : (
                            <XCircle className="h-8 w-8 text-red-500" />
                          )
                        ) : (
                          <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">N/A</div>
                        )}
                      </div>
                      <div className="ml-4 flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-blue-600 truncate">{endpoint.name}</p>
                          <div className="ml-2 flex-shrink-0 flex text-sm text-gray-500 gap-4">
                            <span>Avg: {endpoint.avgTime > 0 ? `${endpoint.avgTime.toFixed(0)}ms` : '-'}</span>
                            <button onClick={(e) => handleDelete(endpoint.id, e)} className="text-gray-400 hover:text-red-500">
                              <Trash2 size={18} />
                            </button>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <ExternalLink className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          <p className="truncate">{endpoint.url}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))
          )}
        </ul>
      </div>

      <AddEndpointModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={() => {
          setIsModalOpen(false);
          fetchEndpoints();
        }} 
      />
    </div>
  );
};

export default Dashboard;
