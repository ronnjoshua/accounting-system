'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { invoicesApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { cn } from '@/lib/utils'

interface Invoice {
  id: number
  invoice_number: string
  customer_id: number
  invoice_date: string
  due_date: string
  status: string
  total: number
  balance_due: number
  currency_code: string
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  partially_paid: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
  void: 'bg-gray-100 text-gray-500',
}

export default function InvoicesPage() {
  const router = useRouter()

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => {
      const response = await invoicesApi.list()
      return response.data as Invoice[]
    },
  })

  const columns = [
    { header: 'Invoice #', accessor: 'invoice_number' as const },
    {
      header: 'Date',
      accessor: (row: Invoice) => formatDate(row.invoice_date),
    },
    {
      header: 'Due Date',
      accessor: (row: Invoice) => formatDate(row.due_date),
    },
    {
      header: 'Status',
      accessor: (row: Invoice) => (
        <span
          className={cn(
            'inline-flex rounded-full px-2 py-1 text-xs font-semibold capitalize',
            statusColors[row.status] || 'bg-gray-100'
          )}
        >
          {row.status.replace('_', ' ')}
        </span>
      ),
    },
    {
      header: 'Total',
      accessor: (row: Invoice) => formatCurrency(row.total, row.currency_code),
      className: 'text-right',
    },
    {
      header: 'Balance',
      accessor: (row: Invoice) =>
        formatCurrency(row.balance_due, row.currency_code),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Invoices"
        description="Manage sales invoices"
        action={{
          label: 'New Invoice',
          onClick: () => router.push('/invoices/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={invoices || []}
          onRowClick={(invoice) => router.push(`/invoices/${invoice.id}`)}
          isLoading={isLoading}
          emptyMessage="No invoices found"
        />
      </div>
    </div>
  )
}
