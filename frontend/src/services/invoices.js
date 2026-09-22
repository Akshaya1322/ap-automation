import api from './api'

export const invoicesApi = {
  list: (params) => api.get('/invoices/', { params }),
  get: (id) => api.get(`/invoices/${id}/`),
  update: (id, data) => api.patch(`/invoices/${id}/`, data),
  updateExtractedFields: (id, fields) => api.post(`/invoices/${id}/extracted-fields/`, { fields }),
  upload: (files, department, onProgress) => {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    if (department) formData.append('department', department)
    return api.post('/invoices/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded * 100) / evt.total))
      },
    })
  },
  validate: (id) => api.post(`/invoices/${id}/validate/`),
  matchPo: (id) => api.post(`/invoices/${id}/match-po/`),
  submitForApproval: (id) => api.post(`/invoices/${id}/submit-for-approval/`),
}
