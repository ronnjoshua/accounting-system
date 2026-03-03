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

// Currencies API
export const currenciesApi = {
  list: () => api.get('/currencies'),
  get: (code: string) => api.get(`/currencies/${code}`),
  create: (data: any) => api.post('/currencies', data),
  update: (code: string, data: any) => api.patch(`/currencies/${code}`, data),
  getExchangeRates: (baseCurrency: string, date?: string) =>
    api.get('/currencies/exchange-rates', { params: { base_currency: baseCurrency, date } }),
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
  post: (id: number) => api.post(`/invoices/${id}/post`),
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
  approve: (id: number) => api.post(`/bills/${id}/approve`),
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
  generalLedger: (params?: { account_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/reports/general-ledger', { params }),
  cashFlow: (startDate?: string, endDate?: string) =>
    api.get('/reports/cash-flow', { params: { start_date: startDate, end_date: endDate } }),
  accountTransactions: (accountId: number, params?: { start_date?: string; end_date?: string }) =>
    api.get(`/reports/account-transactions/${accountId}`, { params }),
}

// Payments API
export const paymentsApi = {
  // Customer Payments
  listCustomerPayments: (params?: { customer_id?: number; invoice_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/payments/customer-payments', { params }),
  createCustomerPayment: (data: any) => api.post('/payments/customer-payments', data),
  getCustomerPayment: (id: number) => api.get(`/payments/customer-payments/${id}`),

  // Vendor Payments
  listVendorPayments: (params?: { vendor_id?: number; bill_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/payments/vendor-payments', { params }),
  createVendorPayment: (data: any) => api.post('/payments/vendor-payments', data),
  getVendorPayment: (id: number) => api.get(`/payments/vendor-payments/${id}`),

  // Credit Notes
  listCreditNotes: (params?: { customer_id?: number }) =>
    api.get('/payments/credit-notes', { params }),
  createCreditNote: (data: any) => api.post('/payments/credit-notes', data),
  getCreditNote: (id: number) => api.get(`/payments/credit-notes/${id}`),

  // Debit Notes
  listDebitNotes: (params?: { vendor_id?: number }) =>
    api.get('/payments/debit-notes', { params }),
  createDebitNote: (data: any) => api.post('/payments/debit-notes', data),
  getDebitNote: (id: number) => api.get(`/payments/debit-notes/${id}`),
}

// Stock Movements API
export const stockMovementsApi = {
  list: (params?: { product_id?: number; warehouse_id?: number; movement_type?: string }) =>
    api.get('/stock-movements', { params }),
  create: (data: any) => api.post('/stock-movements', data),
  createAdjustment: (data: any) => api.post('/stock-movements/adjustment', data),
  createTransfer: (data: any) => api.post('/stock-movements/transfer', data),
  getProductStock: (productId: number) => api.get(`/stock-movements/product/${productId}`),
  get: (id: number) => api.get(`/stock-movements/${id}`),
}

// Audit API
export const auditApi = {
  list: (params?: { action?: string; entity_type?: string; user_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/audit', { params }),
  getSummary: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/audit/summary', { params }),
  getEntityHistory: (entityType: string, entityId: number) =>
    api.get(`/audit/entity/${entityType}/${entityId}`),
  get: (id: number) => api.get(`/audit/${id}`),
}

// Documents API
export const documentsApi = {
  list: (params?: { entity_type?: string; entity_id?: number }) =>
    api.get('/documents', { params }),
  upload: (formData: FormData) =>
    api.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  get: (id: number) => api.get(`/documents/${id}`),
  delete: (id: number) => api.delete(`/documents/${id}`),
  link: (documentId: number, data: { entity_type: string; entity_id: number }) =>
    api.post(`/documents/${documentId}/link`, data),
  unlink: (documentId: number, linkId: number) =>
    api.delete(`/documents/${documentId}/link/${linkId}`),
  getLinks: (documentId: number) => api.get(`/documents/${documentId}/links`),
}

// Banking API
export const bankingApi = {
  listReconciliations: (params?: { account_id?: number; status?: string }) =>
    api.get('/banking/reconciliations', { params }),
  createReconciliation: (data: any) => api.post('/banking/reconciliations', data),
  getReconciliation: (id: number) => api.get(`/banking/reconciliations/${id}`),
  getUnclearedTransactions: (reconciliationId: number) =>
    api.get(`/banking/reconciliations/${reconciliationId}/uncleared`),
  addReconciliationItem: (reconciliationId: number, data: any) =>
    api.post(`/banking/reconciliations/${reconciliationId}/items`, data),
  toggleClearItem: (reconciliationId: number, itemId: number) =>
    api.patch(`/banking/reconciliations/${reconciliationId}/items/${itemId}/clear`),
  completeReconciliation: (reconciliationId: number) =>
    api.post(`/banking/reconciliations/${reconciliationId}/complete`),
  getReconciliationSummary: (reconciliationId: number) =>
    api.get(`/banking/reconciliations/${reconciliationId}/summary`),
}

// Budgets API
export const budgetsApi = {
  list: (params?: { fiscal_year?: number; status?: string }) =>
    api.get('/budgets', { params }),
  create: (data: any) => api.post('/budgets', data),
  get: (id: number) => api.get(`/budgets/${id}`),
  update: (id: number, data: any) => api.patch(`/budgets/${id}`, data),
  addLine: (budgetId: number, data: any) => api.post(`/budgets/${budgetId}/lines`, data),
  updateLine: (budgetId: number, lineId: number, data: any) =>
    api.patch(`/budgets/${budgetId}/lines/${lineId}`, data),
  approve: (id: number) => api.post(`/budgets/${id}/approve`),
  activate: (id: number) => api.post(`/budgets/${id}/activate`),
  getBudgetVsActual: (id: number) => api.get(`/budgets/${id}/vs-actual`),
}

// Tax API
export const taxesApi = {
  // Tax Rates
  listRates: (params?: { tax_type?: string; is_active?: boolean }) =>
    api.get('/taxes/rates', { params }),
  createRate: (data: any) => api.post('/taxes/rates', data),
  getRate: (id: number) => api.get(`/taxes/rates/${id}`),
  updateRate: (id: number, data: any) => api.patch(`/taxes/rates/${id}`, data),

  // Tax Exemptions
  listExemptions: (params?: { entity_type?: string; entity_id?: number }) =>
    api.get('/taxes/exemptions', { params }),
  createExemption: (data: any) => api.post('/taxes/exemptions', data),

  // Tax Periods
  listPeriods: (params?: { tax_type?: string; is_filed?: boolean }) =>
    api.get('/taxes/periods', { params }),
  createPeriod: (data: any) => api.post('/taxes/periods', data),
  calculatePeriod: (id: number) => api.post(`/taxes/periods/${id}/calculate`),
  filePeriod: (id: number, data?: any) => api.post(`/taxes/periods/${id}/file`, data),

  // Tax Summary
  getSummary: (startDate: string, endDate: string, taxType?: string) =>
    api.get('/taxes/summary', { params: { start_date: startDate, end_date: endDate, tax_type: taxType } }),
}

// Recurring API
export const recurringApi = {
  list: (params?: { recurring_type?: string; status?: string }) =>
    api.get('/recurring', { params }),
  create: (data: any) => api.post('/recurring', data),
  get: (id: number) => api.get(`/recurring/${id}`),
  update: (id: number, data: any) => api.patch(`/recurring/${id}`, data),
  pause: (id: number) => api.post(`/recurring/${id}/pause`),
  resume: (id: number) => api.post(`/recurring/${id}/resume`),
  execute: (id: number, executionDate?: string) =>
    api.post(`/recurring/${id}/execute`, null, { params: { execution_date: executionDate } }),
  listExecutions: (id: number) => api.get(`/recurring/${id}/executions`),
  getDue: () => api.get('/recurring/due'),
}
