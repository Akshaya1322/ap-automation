import api from './api'

export const dashboardApi = {
  get: (params) => api.get('/dashboard/', { params }),
}
