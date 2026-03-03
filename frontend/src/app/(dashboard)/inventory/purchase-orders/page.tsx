'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { purchaseOrdersApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { cn } from '@/lib/utils'

interface PurchaseOrder {
  id: number
  po_number: string
  vendor_id: number
  order_date: string
  expected_date: string
  status: string
  total: number
  currency_code: string
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  partially_received: 'bg-yellow-100 text-yellow-800',
  received: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function PurchaseOrdersPage() {
  const router = useRouter()

  const { data: purchaseOrders, isLoading } = useQuery({
    queryKey: ['purchase-orders'],
    queryFn: async () => {
      const response = await purchaseOrdersApi.list()
      return response.data as PurchaseOrder[]
    },
  })

  const columns = [
    { header: 'PO #', accessor: 'po_number' as const },
    {
      header: 'Order Date',
      accessor: (row: PurchaseOrder) => formatDate(row.order_date),
    },
    {
      header: 'Expected Date',
      accessor: (row: PurchaseOrder) => formatDate(row.expected_date),
    },
    {
      header: 'Status',
      accessor: (row: PurchaseOrder) => (
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
      accessor: (row: PurchaseOrder) => formatCurrency(row.total, row.currency_code),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        description="Manage purchase orders"
        action={{
          label: 'New Purchase Order',
          onClick: () => router.push('/inventory/purchase-orders/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={purchaseOrders || []}
          onRowClick={(po) => router.push(`/inventory/purchase-orders/${po.id}`)}
          isLoading={isLoading}
          emptyMessage="No purchase orders found"
        />
      </div>
    </div>
  )
}
