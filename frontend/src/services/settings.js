import api from './api'

export const settingsApi = {
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
  listMatrixRules: () => api.get('/approvals/matrix/'),
  createMatrixRule: (data) => api.post('/approvals/matrix/', data),
  updateMatrixRule: (id, data) => api.patch(`/approvals/matrix/${id}/`, data),
  deleteMatrixRule: (id) => api.delete(`/approvals/matrix/${id}/`),
}
