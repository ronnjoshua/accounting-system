'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { customersApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'

interface Customer {
  id: number
  code: string
  name: string
  email: string | null
  phone: string | null
  currency_code: string
  payment_terms_days: number
  is_active: boolean
}

export default function CustomersPage() {
  const router = useRouter()

  const { data: customers, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const response = await customersApi.list()
      return response.data as Customer[]
    },
  })

  const columns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Name', accessor: 'name' as const },
    { header: 'Email', accessor: (row: Customer) => row.email || '-' },
    { header: 'Phone', accessor: (row: Customer) => row.phone || '-' },
    { header: 'Currency', accessor: 'currency_code' as const },
    {
      header: 'Terms',
      accessor: (row: Customer) => `${row.payment_terms_days} days`,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Customers"
        description="Manage your customer accounts"
        action={{
          label: 'New Customer',
          onClick: () => router.push('/customers/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={customers || []}
          onRowClick={(customer) => router.push(`/customers/${customer.id}`)}
          isLoading={isLoading}
          emptyMessage="No customers found"
        />
      </div>
    </div>
  )
}
