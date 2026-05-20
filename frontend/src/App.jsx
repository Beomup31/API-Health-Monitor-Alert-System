import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import EndpointDetail from './components/EndpointDetail';
import Login from './components/Login';
import { Activity, LogOut } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Do not show the navbar on the login page
  const showNavbar = token && location.pathname !== '/login';

  return (
    <div className="min-h-screen bg-gray-100">
      {showNavbar && (
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center gap-2">
                <Activity className="h-6 w-6 text-blue-600" />
                <span className="font-semibold text-xl tracking-tight text-gray-900">
                  API Health Monitor
                </span>
              </div>
              <div className="flex items-center">
                <button onClick={handleLogout} className="flex items-center gap-2 text-gray-500 hover:text-red-600 transition">
                  <LogOut size={18} /> Logout
                </button>
              </div>
            </div>
          </div>
        </nav>
      )}

      <main className={showNavbar ? "max-w-7xl mx-auto py-6 sm:px-6 lg:px-8" : ""}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/endpoints/:id" element={<ProtectedRoute><EndpointDetail /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
