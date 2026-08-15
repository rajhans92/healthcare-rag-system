import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../services/api'

const roles = ['PATIENT', 'DOCTOR', 'ADMIN']

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    role: 'PATIENT',
  })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateField = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await register(form)
      navigate('/dashboard')
    } catch (submitError) {
      // Clear previous field errors
      setFieldErrors({})

      // Try to extract structured validation errors from the API response
      const resp = submitError?.response?.data
      if (resp && resp.error && Array.isArray(resp.error.details)) {
        const details = resp.error.details
        const nextFieldErrors = {}
        details.forEach((d) => {
          const loc = Array.isArray(d.loc) ? d.loc : []
          const field = loc.length > 0 ? loc[loc.length - 1] : '_general'
          const msg = d.msg || (d.ctx && d.ctx.error) || JSON.stringify(d)
          if (!nextFieldErrors[field]) nextFieldErrors[field] = []
          nextFieldErrors[field].push(msg)
        })
        setFieldErrors(nextFieldErrors)
        // Set a top-level message if provided
        setError(resp.error.message || 'Validation failed.')
      } else {
        setError(getApiErrorMessage(submitError))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <span className="badge">Create account</span>
          <h1>Join the platform</h1>
          <p>Create a patient, doctor, or admin account for the healthcare RAG workspace.</p>
        </div>

        <form className="stack-form" onSubmit={handleSubmit}>
          <div className="two-column-grid">
            <label>
              <span>First name</span>
              <input name="first_name" value={form.first_name} onChange={updateField} required />
              {fieldErrors.first_name && fieldErrors.first_name.map((m, i) => (
                <p key={i} className="form-error">{m}</p>
              ))}
            </label>

            <label>
              <span>Last name</span>
              <input name="last_name" value={form.last_name} onChange={updateField} required />
              {fieldErrors.last_name && fieldErrors.last_name.map((m, i) => (
                <p key={i} className="form-error">{m}</p>
              ))}
            </label>
          </div>

          <label>
            <span>Email</span>
            <input type="email" name="email" value={form.email} onChange={updateField} required />
            {fieldErrors.email && fieldErrors.email.map((m, i) => (
              <p key={i} className="form-error">{m}</p>
            ))}
          </label>

          <label>
            <span>Password</span>
            <input type="password" name="password" value={form.password} onChange={updateField} required />
            {fieldErrors.password && fieldErrors.password.map((m, i) => (
              <p key={i} className="form-error">{m}</p>
            ))}
          </label>

          <label>
            <span>Role</span>
            <select name="role" value={form.role} onChange={updateField}>
              {roles.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
            {fieldErrors.role && fieldErrors.role.map((m, i) => (
              <p key={i} className="form-error">{m}</p>
            ))}
          </label>

          {error ? (
            // Show multi-line validation messages returned from the API as separate lines
            error.split('\n').map((line, idx) => (
              <p key={idx} className="form-error">{line}</p>
            ))
          ) : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
