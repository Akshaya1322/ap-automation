import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api, { extractErrorMessage, tokenStore } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadProfile = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setLoading(false)
      return
    }
    try {
      const { data } = await api.get('/auth/profile/')
      setUser(data)
    } catch {
      tokenStore.clear()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const login = async (username, password) => {
    try {
      const { data } = await api.post('/auth/login/', { username, password })
      tokenStore.setTokens(data.access, data.refresh)
      setUser(data.user)
      return { success: true }
    } catch (error) {
      return { success: false, message: extractErrorMessage(error) }
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout/')
    } catch {
      /* ignore network errors on logout */
    }
    tokenStore.clear()
    setUser(null)
  }

  const refreshProfile = () => loadProfile()

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
