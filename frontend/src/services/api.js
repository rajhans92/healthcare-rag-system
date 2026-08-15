import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = 'Bearer ' + token
  }

  return config
})

export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('token', token)
    return
  }

  localStorage.removeItem('token')
}

export const getApiErrorMessage = (error) => {
  const detail = error?.response?.data
  // If backend returned a plain string
  if (typeof detail === 'string') {
    return detail
  }

  // FastAPI default detail
  if (detail?.detail) {
    return detail.detail
  }

  // Custom ErrorResponse shape: { error: { message, details } }
  if (detail?.error) {
    const err = detail.error
    // If there are structured validation details (list), format them nicely
    if (Array.isArray(err.details) && err.details.length > 0) {
      const lines = err.details.map((d) => {
        // d is typically { loc, msg, type, ctx }
        const loc = Array.isArray(d.loc) ? d.loc : []
        const field = loc.length > 0 ? loc[loc.length - 1] : null
        const msg = d.msg || (d.ctx && d.ctx.error) || JSON.stringify(d)
        return field ? `${field}: ${msg}` : msg
      })
      // Prepend top-level message if present
      if (err.message) {
        return `${err.message}\n${lines.join('\n')}`
      }
      return lines.join('\n')
    }

    if (err.message) {
      return err.message
    }
  }

  if (detail?.message) {
    return detail.message
  }

  return error.message || 'Something went wrong while calling the backend.'
}

export default api
