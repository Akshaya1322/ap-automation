import api from './api'

export const exceptionsApi = {
  list: (params) => api.get('/exceptions/', { params }),
  resolve: (id, comment) => api.post(`/exceptions/${id}/resolve/`, { comment }),
  reject: (id, comment) => api.post(`/exceptions/${id}/reject/`, { comment }),
  override: (id, comment) => api.post(`/exceptions/${id}/override/`, { comment }),
}
