import axios from 'axios'

const ACCESS_KEY = 'ap_access_token'
const REFRESH_KEY = 'ap_refresh_token'

export const tokenStore = {
  getAccess: () => sessionStorage.getItem(ACCESS_KEY),
  getRefresh: () => sessionStorage.getItem(REFRESH_KEY),
  setTokens: (access, refresh) => {
    sessionStorage.setItem(ACCESS_KEY, access)
    if (refresh) sessionStorage.setItem(REFRESH_KEY, refresh)
  },
  clear: () => {
    sessionStorage.removeItem(ACCESS_KEY)
    sessionStorage.removeItem(REFRESH_KEY)
  },
}

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshingPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry && tokenStore.getRefresh()) {
      originalRequest._retry = true
      try {
        if (!refreshingPromise) {
          refreshingPromise = axios
            .post('/api/auth/refresh/', { refresh: tokenStore.getRefresh() })
            .then((res) => {
              tokenStore.setTokens(res.data.access, res.data.refresh)
              return res.data.access
            })
            .finally(() => {
              refreshingPromise = null
            })
        }
        const newAccess = await refreshingPromise
        originalRequest.headers.Authorization = `Bearer ${newAccess}`
        return api(originalRequest)
      } catch {
        tokenStore.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export function extractErrorMessage(error) {
  const data = error?.response?.data
  if (!data) return error?.message || 'Something went wrong. Please try again.'
  if (data.message) return data.message
  if (data.detail) return data.detail
  if (typeof data === 'string') return data
  if (data.errors && typeof data.errors === 'object') {
    const firstKey = Object.keys(data.errors)[0]
    const val = data.errors[firstKey]
    return Array.isArray(val) ? val[0] : String(val)
  }
  return 'Something went wrong. Please try again.'
}

export default api
