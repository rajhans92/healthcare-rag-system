import { Link } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const stats = [
  { label: 'Active records', value: '03' },
  { label: 'Recent reports', value: '07' },
  { label: 'Access requests', value: '02' },
]

export default function PatientDashboard() {
  const { user } = useAuth()

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Patient portal</span>
          <h1>Welcome, {user?.first_name || 'Patient'}</h1>
        </div>
        <Link className="secondary-button" to="/chat">Ask clinical question</Link>
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
          <h2>Recent clinical summary</h2>
          <ul className="bullet-list">
            <li>Most recent encounter: OPD follow-up for respiratory symptoms.</li>
            <li>Primary diagnosis: Upper respiratory infection.</li>
            <li>Latest report: CBC uploaded and processed.</li>
          </ul>
        </section>

        <section className="panel-card">
          <h2>Quick actions</h2>
          <div className="action-stack">
            <Link to="/documents">View documents</Link>
            <Link to="/access">Manage access</Link>
            <Link to="/chat">Open chat</Link>
          </div>
        </section>
      </div>
    </div>
  )
}
