import api from './api'

export const paymentsApi = {
  list: (params) => api.get('/payments/', { params }),
  get: (id) => api.get(`/payments/${id}/`),
  create: (invoice, method) => api.post('/payments/', { invoice, method }),
  process: (id) => api.post(`/payments/${id}/process/`),
  cancel: (id) => api.post(`/payments/${id}/cancel/`),
}
