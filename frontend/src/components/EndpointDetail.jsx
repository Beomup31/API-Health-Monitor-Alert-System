import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowLeft, Activity, CheckCircle2, XCircle } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import apiClient from '../api/axios';

const EndpointDetail = () => {
  const { id } = useParams();
  const [endpoint, setEndpoint] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [epRes, logsRes] = await Promise.all([
        apiClient.get(`/endpoints/${id}`),
        apiClient.get(`/endpoints/${id}/logs?limit=50`)
      ]);
      setEndpoint(epRes.data);
      
      // Format data for chart, reversing it so oldest is first on the left
      const formattedLogs = logsRes.data.reverse().map(log => ({
        ...log,
        time: format(parseISO(log.timestamp), 'HH:mm:ss'),
        responseTime: log.response_time_ms ? Math.round(log.response_time_ms) : 0,
      }));
      setLogs(formattedLogs);
    } catch (error) {
      console.error('Failed to fetch endpoint details:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [id]);

  if (loading) return <div className="flex justify-center py-20"><Activity className="animate-spin h-8 w-8 text-blue-500" /></div>;
  if (!endpoint) return <div className="text-center py-20 text-gray-500">Endpoint not found</div>;

  const latestLog = logs.length > 0 ? logs[logs.length - 1] : null;
  const avgResponseTime = logs.length > 0 
    ? Math.round(logs.reduce((acc, log) => acc + log.responseTime, 0) / logs.length)
    : 0;
  const uptimeCount = logs.filter(log => log.is_success).length;
  const uptimePercentage = logs.length > 0 ? Math.round((uptimeCount / logs.length) * 100) : 0;

  return (
    <div>
      <div className="mb-6">
        <Link to="/" className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-500">
          <ArrowLeft className="mr-1 h-4 w-4" /> Back to Dashboard
        </Link>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">{endpoint.name}</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">{endpoint.url}</p>
          </div>
          <div>
            {latestLog && (
              <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${latestLog.is_success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {latestLog.is_success ? <CheckCircle2 className="mr-1 h-4 w-4" /> : <XCircle className="mr-1 h-4 w-4" />}
                {latestLog.is_success ? 'Operational' : 'Failing'}
              </span>
            )}
          </div>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-3">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Average Response Time</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{avgResponseTime} ms</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Uptime (Last 50 checks)</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{uptimePercentage}%</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Check Interval</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">Every {endpoint.check_interval_minutes} min</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg p-6">
        <h4 className="text-base font-medium text-gray-900 mb-4">Response Time History</h4>
        <div className="h-72 w-full">
          {logs.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={logs} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="time" stroke="#6B7280" fontSize={12} tickMargin={10} />
                <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `${value}ms`} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  formatter={(value) => [`${value} ms`, 'Response Time']}
                  labelStyle={{ color: '#374151', fontWeight: 'bold', marginBottom: '4px' }}
                />
                <Line type="monotone" dataKey="responseTime" stroke="#3B82F6" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              No ping data available yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EndpointDetail;
