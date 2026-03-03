'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { billsApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { cn } from '@/lib/utils'

interface Bill {
  id: number
  bill_number: string
  vendor_bill_number: string | null
  vendor_id: number
  bill_date: string
  due_date: string
  status: string
  total: number
  balance_due: number
  currency_code: string
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  received: 'bg-blue-100 text-blue-800',
  partially_paid: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
  void: 'bg-gray-100 text-gray-500',
}

export default function BillsPage() {
  const router = useRouter()

  const { data: bills, isLoading } = useQuery({
    queryKey: ['bills'],
    queryFn: async () => {
      const response = await billsApi.list()
      return response.data as Bill[]
    },
  })

  const columns = [
    { header: 'Bill #', accessor: 'bill_number' as const },
    {
      header: 'Vendor Ref',
      accessor: (row: Bill) => row.vendor_bill_number || '-',
    },
    {
      header: 'Date',
      accessor: (row: Bill) => formatDate(row.bill_date),
    },
    {
      header: 'Due Date',
      accessor: (row: Bill) => formatDate(row.due_date),
    },
    {
      header: 'Status',
      accessor: (row: Bill) => (
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
      accessor: (row: Bill) => formatCurrency(row.total, row.currency_code),
      className: 'text-right',
    },
    {
      header: 'Balance',
      accessor: (row: Bill) => formatCurrency(row.balance_due, row.currency_code),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Bills"
        description="Manage vendor bills"
        action={{
          label: 'New Bill',
          onClick: () => router.push('/bills/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={bills || []}
          onRowClick={(bill) => router.push(`/bills/${bill.id}`)}
          isLoading={isLoading}
          emptyMessage="No bills found"
        />
      </div>
    </div>
  )
}
