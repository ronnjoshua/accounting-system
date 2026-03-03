'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { vendorsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'

interface Vendor {
  id: number
  code: string
  name: string
  email: string | null
  phone: string | null
  currency_code: string
  payment_terms_days: number
  is_active: boolean
}

export default function VendorsPage() {
  const router = useRouter()

  const { data: vendors, isLoading } = useQuery({
    queryKey: ['vendors'],
    queryFn: async () => {
      const response = await vendorsApi.list()
      return response.data as Vendor[]
    },
  })

  const columns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Name', accessor: 'name' as const },
    { header: 'Email', accessor: (row: Vendor) => row.email || '-' },
    { header: 'Phone', accessor: (row: Vendor) => row.phone || '-' },
    { header: 'Currency', accessor: 'currency_code' as const },
    {
      header: 'Terms',
      accessor: (row: Vendor) => `${row.payment_terms_days} days`,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Vendors"
        description="Manage your vendor/supplier accounts"
        action={{
          label: 'New Vendor',
          onClick: () => router.push('/vendors/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={vendors || []}
          onRowClick={(vendor) => router.push(`/vendors/${vendor.id}`)}
          isLoading={isLoading}
          emptyMessage="No vendors found"
        />
      </div>
    </div>
  )
}
