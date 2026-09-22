import api from './api'

export const approvalsApi = {
  list: (params) => api.get('/approvals/', { params }),
  get: (id) => api.get(`/approvals/${id}/`),
  approve: (id, comment) => api.post(`/approvals/${id}/approve/`, { comment }),
  reject: (id, comment) => api.post(`/approvals/${id}/reject/`, { comment }),
  requestChanges: (id, comment) => api.post(`/approvals/${id}/request-changes/`, { comment }),
}
