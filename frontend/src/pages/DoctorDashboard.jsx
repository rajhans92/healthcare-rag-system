import { Link } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const stats = [
  { label: 'Patients assigned', value: '12' },
  { label: 'Pending access', value: '04' },
  { label: 'Unread reviews', value: '08' },
]

export default function DoctorDashboard() {
  const { user } = useAuth()

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Doctor workspace</span>
          <h1>Welcome, Dr. {user?.last_name || 'Clinician'}</h1>
        </div>
        <Link className="secondary-button" to="/chat">Open patient chat</Link>
      </div>

      <div className="stats-grid">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <p>{stat.label}</p>
            <strong>{stat.value}</strong>
          </div>
        ))}
      </div>

      <div className="content-grid">
        <section className="panel-card">
          <h2>Assigned patients</h2>
          <ul className="bullet-list">
            <li>Patient 1024 — active care plan review</li>
            <li>Patient 1056 — labs pending signature</li>
            <li>Patient 1088 — follow-up medication review</li>
          </ul>
        </section>

        <section className="panel-card">
          <h2>Clinical actions</h2>
          <div className="action-stack">
            <Link to="/patients">Review patient records</Link>
            <Link to="/access">Approve access</Link>
            <Link to="/chat">Consult with patient context</Link>
          </div>
        </section>
      </div>
    </div>
  )
}
