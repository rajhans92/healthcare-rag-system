import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import api, { setAuthToken } from '../services/api'

const AuthContext = createContext(null)

const normalizeUser = (payload) => {
  if (!payload) return null

  if (payload.user) return payload.user
  if (payload.data?.user) return payload.data.user
  if (payload.data) return payload.data

  return payload
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [loading, setLoading] = useState(true)

  const logout = () => {
    setAuthToken(null)
    setToken(null)
    setUser(null)
  }

  const loadUser = async () => {
    const nextToken = localStorage.getItem('token')

    if (!nextToken) {
      setToken(null)
      setUser(null)
      setLoading(false)
      return
    }

    setToken(nextToken)

    try {
      const response = await api.get('/auth/me')
      const nextUser = normalizeUser(response.data)
      setUser(nextUser)
    } catch (error) {
      setAuthToken(null)
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
  }, [])

  const login = async (payload) => {
    const response = await api.post('/auth/login', payload)
    const nextToken = response.data.access_token || response.data.data?.access_token

    if (!nextToken) {
      throw new Error('Login response did not include an access token.')
    }

    setAuthToken(nextToken)
    setToken(nextToken)
    const me = await api.get('/auth/me')
    const nextUser = normalizeUser(me.data)
    setUser(nextUser)
    return nextUser
  }

  const register = async (payload) => {
    const response = await api.post('/auth/register', payload)
    const nextToken = response.data.access_token || response.data.data?.access_token

    if (nextToken) {
      setAuthToken(nextToken)
      setToken(nextToken)
      const me = await api.get('/auth/me')
      const nextUser = normalizeUser(me.data)
      setUser(nextUser)
      return nextUser
    }

    const nextUser = normalizeUser(response.data)
    setUser(nextUser)
    return nextUser
  }

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      register,
      logout,
      refreshUser: loadUser,
    }),
    [user, token, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}
