import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import './App.css'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import AdminDashboard from './pages/AdminDashboard'
import ChatPage from './pages/ChatPage'
import DocumentsPage from './pages/DocumentsPage'
import AccessPage from './pages/AccessPage'

function AppContent() {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <span className="brand-mark">+</span>
          <div>
            <strong>Clinician AI</strong>
            <small>Healthcare RAG</small>
          </div>
        </div>

        {user ? (
          <nav className="topnav">
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/chat">Chat</Link>
            <Link to="/documents">Documents</Link>
            <Link to="/access">Access</Link>
            {user.role === 'ADMIN' ? <Link to="/admin">Admin</Link> : null}
            <button type="button" className="ghost-button" onClick={logout}>
              Logout
            </button>
          </nav>
        ) : (
          <nav className="topnav">
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </nav>
        )}
      </header>

      <main className="page-body">
        <Routes>
          <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
          <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/access" element={<AccessPage />} />
          </Route>

          <Route path="*" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  )
}
