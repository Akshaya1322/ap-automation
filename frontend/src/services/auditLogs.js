import api from './api'

export const auditLogsApi = {
  list: (params) => api.get('/audit-logs/', { params }),
}
