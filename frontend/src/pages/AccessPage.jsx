import { useEffect, useMemo, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import api, { getApiErrorMessage } from '../services/api'

export default function AccessPage() {
  const { user, token } = useAuth()
  const [records, setRecords] = useState([])
  const [patientId, setPatientId] = useState('')
  const [expiresDays, setExpiresDays] = useState(30)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)

  const canManageAccess = useMemo(() => {
    return user?.role === 'PATIENT' || user?.role === 'DOCTOR'
  }, [user])

  const fetchAccessRecords = async (role, currentUser) => {
    if (!currentUser) {
      setLoading(false)
      return
    }

    const targetPatientId = currentUser.profile?.id || currentUser.profile?.patient_id || currentUser.profile?.patientId || ''
    const targetDoctorId = currentUser.profile?.id || currentUser.profile?.doctor_id || currentUser.profile?.doctorId || currentUser.id || ''

    try {
      const endpoint = role === 'DOCTOR'
        ? `/patient-access/doctors/${targetDoctorId}`
        : `/patient-access/patients/${targetPatientId}`

      const response = await api.get(endpoint, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setRecords(Array.isArray(response.data) ? response.data : response.data?.data || [])
    } catch (fetchError) {
      setError(getApiErrorMessage(fetchError))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    const nextPatientId = user.profile?.id || user.profile?.patient_id || user.profile?.patientId || ''
    setPatientId(nextPatientId)
    fetchAccessRecords(user.role, user)
  }, [user, token])

  const handleRequestAccess = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!patientId.trim()) {
      setError('Please provide a patient ID.')
      return
    }

    const doctorId = user?.profile?.id || user?.profile?.doctor_id || user?.profile?.doctorId || user?.id

    try {
      const response = await api.post(
        '/patient-access/request',
        {
          patient_id: patientId,
          doctor_id: doctorId,
          expires_days: expiresDays,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )

      const nextRecord = response.data?.data || response.data
      setRecords((current) => [nextRecord, ...current])
      setSuccess('Access request sent successfully.')
      setPatientId('')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    }
  }

  const handleDecision = async (accessId, status) => {
    setError('')
    setSuccess('')

    try {
      const response = await api.patch(
        `/patient-access/${accessId}/status`,
        {
          status,
          remarks: status === 'APPROVED' ? 'Approved from patient dashboard.' : 'Rejected from patient dashboard.',
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )

      const nextRecord = response.data?.data || response.data
      setRecords((current) => current.map((item) => item.id === accessId ? nextRecord : item))
      setSuccess(`Access request ${status.toLowerCase()}.`)
    } catch (decisionError) {
      setError(getApiErrorMessage(decisionError))
    }
  }

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Access</span>
          <h1>Patient access management</h1>
        </div>
      </div>

      {user?.role === 'DOCTOR' ? (
        <section className="panel-card">
          <h2>Request access</h2>
          <form className="stack-form" onSubmit={handleRequestAccess}>
            <label>
              <span>Patient ID</span>
              <input value={patientId} onChange={(event) => setPatientId(event.target.value)} />
            </label>
            <label>
              <span>Expiry (days)</span>
              <input type="number" min="1" max="365" value={expiresDays} onChange={(event) => setExpiresDays(Number(event.target.value))} />
            </label>
            <button type="submit" className="primary-button">Request access</button>
          </form>
        </section>
      ) : null}

      {error ? <p className="form-error">{error}</p> : null}
      {success ? <p className="success-message">{success}</p> : null}

      {loading ? (
        <section className="panel-card">
          <p>Loading access records...</p>
        </section>
      ) : !canManageAccess ? (
        <section className="panel-card">
          <p>You do not have permission to manage patient access.</p>
        </section>
      ) : (
        <section className="panel-card">
          <h2>Access records</h2>
          {records.length === 0 ? (
            <p>No access records found.</p>
          ) : (
            <div className="list-table">
              <div className="list-row list-header">
                <span>Patient</span>
                <span>Doctor</span>
                <span>Status</span>
                <span>Actions</span>
              </div>
              {records.map((record) => {
                const isPending = (record.status || '').toUpperCase() === 'PENDING'
                const canReview = user?.role === 'PATIENT'
                  ? String(record.patient_id || record.patientId) === String(user?.profile?.id || user?.profile?.patient_id || user?.profile?.patientId || '')
                  : user?.role === 'DOCTOR'
                    ? String(record.doctor_id || record.doctorId) === String(user?.profile?.id || user?.profile?.doctor_id || user?.profile?.doctorId || user?.id || '')
                    : false

                return (
                  <div key={record.id} className="list-row access-row">
                    <span>{record.patient_id || record.patientId || 'N/A'}</span>
                    <span>{record.doctor_id || record.doctorId || 'N/A'}</span>
                    <span>{record.status || 'PENDING'}</span>
                    <span>
                      {isPending && canReview ? (
                        <div className="inline-actions">
                          <button type="button" className="small-button success" onClick={() => handleDecision(record.id, 'APPROVED')}>
                            Approve
                          </button>
                          <button type="button" className="small-button danger" onClick={() => handleDecision(record.id, 'REJECTED')}>
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="muted-label">No action</span>
                      )}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
