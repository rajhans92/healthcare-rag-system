import { useAuth } from '../context/AuthContext'
import AdminDashboard from './AdminDashboard'
import PatientDashboard from './PatientDashboard'
import DoctorDashboard from './DoctorDashboard'

export default function DashboardPage() {
  const { user } = useAuth()

  if (!user) {
    return null
  }

  if (user.role === 'PATIENT') {
    return <PatientDashboard />
  }

  if (user.role === 'DOCTOR') {
    return <DoctorDashboard />
  }

  if (user.role === 'ADMIN') {
    return <AdminDashboard />
  }

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Admin</span>
          <h1>Operations dashboard</h1>
        </div>
      </div>
      <section className="panel-card">
        <h2>Platform administration</h2>
        <p>Monitor user activity, access requests, ingestion queues, and system health.</p>
      </section>
    </div>
  )
}
