import api from './api'

export const vendorsApi = {
  list: (params) => api.get('/vendors/', { params }),
  get: (id) => api.get(`/vendors/${id}/`),
  create: (data) => api.post('/vendors/', data),
  update: (id, data) => api.patch(`/vendors/${id}/`, data),
  submit: (id) => api.post(`/vendors/${id}/submit/`),
  startReview: (id) => api.post(`/vendors/${id}/start-review/`),
  approve: (id) => api.post(`/vendors/${id}/approve/`),
  activate: (id) => api.post(`/vendors/${id}/activate/`),
  deactivate: (id) => api.post(`/vendors/${id}/deactivate/`),
}
