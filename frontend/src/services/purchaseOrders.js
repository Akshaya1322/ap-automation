import api from './api'

export const purchaseOrdersApi = {
  list: (params) => api.get('/purchase-orders/', { params }),
  get: (id) => api.get(`/purchase-orders/${id}/`),
}
