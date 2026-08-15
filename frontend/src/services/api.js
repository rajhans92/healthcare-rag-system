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
  if (typeof detail === 'string') {
    return detail
  }

  if (detail?.detail) {
    return detail.detail
  }

  if (detail?.message) {
    return detail.message
  }

  return error.message || 'Something went wrong while calling the backend.'
}

export default api
