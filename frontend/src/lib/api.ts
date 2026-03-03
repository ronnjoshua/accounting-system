import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  me: () => api.get('/auth/me'),

  invite: (email: string, roleId: number) =>
    api.post('/auth/invite', { email, role_id: roleId }),

  acceptInvite: (token: string, password: string, firstName: string, lastName: string) =>
    api.post('/auth/accept-invite', { token, password, first_name: firstName, last_name: lastName }),

  verifyInvite: (token: string) =>
    api.get(`/auth/verify-invite/${token}`),
}

// Users API
export const usersApi = {
  list: () => api.get('/users'),
  get: (id: number) => api.get(`/users/${id}`),
  update: (id: number, data: any) => api.patch(`/users/${id}`, data),
  deactivate: (id: number) => api.delete(`/users/${id}`),
  listRoles: () => api.get('/users/roles'),
  listInvites: () => api.get('/users/invites'),
  revokeInvite: (id: number) => api.delete(`/users/invites/${id}`),
}

// Company API
export const companyApi = {
  get: () => api.get('/company'),
  create: (data: any) => api.post('/company', data),
  update: (data: any) => api.patch('/company', data),
}

// Accounts API
export const accountsApi = {
  list: (params?: { category?: string; is_active?: boolean }) =>
    api.get('/accounts', { params }),
  listTypes: () => api.get('/accounts/types'),
  get: (id: number) => api.get(`/accounts/${id}`),
  create: (data: any) => api.post('/accounts', data),
  update: (id: number, data: any) => api.patch(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
}

// Journal Entries API
export const journalEntriesApi = {
  list: (params?: { status?: string; start_date?: string; end_date?: string }) =>
    api.get('/journal-entries', { params }),
  get: (id: number) => api.get(`/journal-entries/${id}`),
  create: (data: any) => api.post('/journal-entries', data),
  update: (id: number, data: any) => api.patch(`/journal-entries/${id}`, data),
  post: (id: number) => api.post(`/journal-entries/${id}/post`),
  void: (id: number, reason: string) =>
    api.post(`/journal-entries/${id}/void`, null, { params: { reason } }),
}

// Customers API
export const customersApi = {
  list: (params?: { is_active?: boolean }) =>
    api.get('/customers', { params }),
  get: (id: number) => api.get(`/customers/${id}`),
  create: (data: any) => api.post('/customers', data),
  update: (id: number, data: any) => api.patch(`/customers/${id}`, data),
  delete: (id: number) => api.delete(`/customers/${id}`),
}

// Invoices API
export const invoicesApi = {
  list: (params?: { status?: string; customer_id?: number }) =>
    api.get('/invoices', { params }),
  get: (id: number) => api.get(`/invoices/${id}`),
  create: (data: any) => api.post('/invoices', data),
  update: (id: number, data: any) => api.patch(`/invoices/${id}`, data),
  send: (id: number) => api.post(`/invoices/${id}/send`),
  void: (id: number) => api.post(`/invoices/${id}/void`),
}

// Vendors API
export const vendorsApi = {
  list: (params?: { is_active?: boolean }) =>
    api.get('/vendors', { params }),
  get: (id: number) => api.get(`/vendors/${id}`),
  create: (data: any) => api.post('/vendors', data),
  update: (id: number, data: any) => api.patch(`/vendors/${id}`, data),
  delete: (id: number) => api.delete(`/vendors/${id}`),
}

// Bills API
export const billsApi = {
  list: (params?: { status?: string; vendor_id?: number }) =>
    api.get('/bills', { params }),
  get: (id: number) => api.get(`/bills/${id}`),
  create: (data: any) => api.post('/bills', data),
  update: (id: number, data: any) => api.patch(`/bills/${id}`, data),
  receive: (id: number) => api.post(`/bills/${id}/receive`),
  void: (id: number) => api.post(`/bills/${id}/void`),
}

// Products API
export const productsApi = {
  list: (params?: { product_type?: string; is_active?: boolean }) =>
    api.get('/products', { params }),
  get: (id: number) => api.get(`/products/${id}`),
  create: (data: any) => api.post('/products', data),
  update: (id: number, data: any) => api.patch(`/products/${id}`, data),
  delete: (id: number) => api.delete(`/products/${id}`),
}

// Warehouses API
export const warehousesApi = {
  list: (params?: { is_active?: boolean }) =>
    api.get('/warehouses', { params }),
  get: (id: number) => api.get(`/warehouses/${id}`),
  create: (data: any) => api.post('/warehouses', data),
  update: (id: number, data: any) => api.patch(`/warehouses/${id}`, data),
  delete: (id: number) => api.delete(`/warehouses/${id}`),
}

// Purchase Orders API
export const purchaseOrdersApi = {
  list: (params?: { status?: string; vendor_id?: number }) =>
    api.get('/purchase-orders', { params }),
  get: (id: number) => api.get(`/purchase-orders/${id}`),
  create: (data: any) => api.post('/purchase-orders', data),
  update: (id: number, data: any) => api.patch(`/purchase-orders/${id}`, data),
  send: (id: number) => api.post(`/purchase-orders/${id}/send`),
  cancel: (id: number) => api.post(`/purchase-orders/${id}/cancel`),
}

// Reports API
export const reportsApi = {
  trialBalance: (asOfDate?: string) =>
    api.get('/reports/trial-balance', { params: { as_of_date: asOfDate } }),
  balanceSheet: (asOfDate?: string) =>
    api.get('/reports/balance-sheet', { params: { as_of_date: asOfDate } }),
  incomeStatement: (startDate?: string, endDate?: string) =>
    api.get('/reports/income-statement', { params: { start_date: startDate, end_date: endDate } }),
  arAging: (asOfDate?: string) =>
    api.get('/reports/ar-aging', { params: { as_of_date: asOfDate } }),
  apAging: (asOfDate?: string) =>
    api.get('/reports/ap-aging', { params: { as_of_date: asOfDate } }),
  dashboard: () => api.get('/reports/dashboard'),
}
