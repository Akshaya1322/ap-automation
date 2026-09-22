import api from './api'

const ENDPOINTS = {
  aging: '/reports/aging/',
  invoices: '/reports/invoices/',
  exceptions: '/reports/exceptions/',
  vendors: '/reports/vendors/',
  payments: '/reports/payments/',
  gst: '/reports/gst/',
  audit: '/reports/audit/',
}

export const reportsApi = {
  get: (type, params) => api.get(ENDPOINTS[type], { params }),
  downloadCsv: async (type, params, filename) => {
    const response = await api.get(ENDPOINTS[type], { params: { ...params, export: 'csv' }, responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
