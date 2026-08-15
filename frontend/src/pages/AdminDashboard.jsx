import { useEffect, useState } from 'react'

import api, { getApiErrorMessage } from '../services/api'

export default function AdminDashboard() {
  const [health, setHealth] = useState(null)
  const [chatStatus, setChatStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadSystemStatus = async () => {
      try {
        const [healthResponse, chatResponse] = await Promise.all([
          api.get('/health'),
          api.get('/chat/status'),
        ])

        setHealth(healthResponse.data)
        setChatStatus(chatResponse.data)
      } catch (loadError) {
        setError(getApiErrorMessage(loadError))
      } finally {
        setLoading(false)
      }
    }

    loadSystemStatus()
  }, [])

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Admin</span>
          <h1>Operations dashboard</h1>
        </div>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {loading ? (
        <section className="panel-card">
          <p>Loading system status...</p>
        </section>
      ) : (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <p>Application health</p>
              <strong>{health?.status || 'UNKNOWN'}</strong>
            </div>
            <div className="stat-card">
              <p>Chat pipeline</p>
              <strong>{chatStatus?.pipeline || 'UNAVAILABLE'}</strong>
            </div>
            <div className="stat-card">
              <p>System mode</p>
              <strong>{chatStatus?.status || 'N/A'}</strong>
            </div>
          </div>

          <div className="content-grid">
            <section className="panel-card">
              <h2>Healthcare RAG overview</h2>
              <ul className="bullet-list">
                <li>Secure patient and doctor access is enforced before retrieval.</li>
                <li>Structured clinical facts are merged with vector search before answer generation.</li>
                <li>Medical documents are queued, processed, and indexed for retrieval.</li>
              </ul>
            </section>

            <section className="panel-card">
              <h2>Operational checks</h2>
              <ul className="bullet-list">
                <li>Backend API: {health?.status === 'UP' ? 'Healthy' : 'Needs attention'}</li>
                <li>Chat pipeline: {chatStatus?.status === 'ready' ? 'Ready' : 'Needs review'}</li>
                <li>Access/authorization: Patient-doctor approval flow active</li>
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
