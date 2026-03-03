'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { warehousesApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'

interface Warehouse {
  id: number
  code: string
  name: string
  city: string | null
  state: string | null
  country: string | null
  is_default: boolean
  is_active: boolean
}

export default function WarehousesPage() {
  const router = useRouter()

  const { data: warehouses, isLoading } = useQuery({
    queryKey: ['warehouses'],
    queryFn: async () => {
      const response = await warehousesApi.list()
      return response.data as Warehouse[]
    },
  })

  const columns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Name', accessor: 'name' as const },
    { header: 'City', accessor: (row: Warehouse) => row.city || '-' },
    { header: 'State', accessor: (row: Warehouse) => row.state || '-' },
    { header: 'Country', accessor: (row: Warehouse) => row.country || '-' },
    {
      header: 'Default',
      accessor: (row: Warehouse) =>
        row.is_default ? (
          <span className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">
            Default
          </span>
        ) : null,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Warehouses"
        description="Manage stock locations"
        action={{
          label: 'New Warehouse',
          onClick: () => router.push('/inventory/warehouses/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={warehouses || []}
          onRowClick={(warehouse) =>
            router.push(`/inventory/warehouses/${warehouse.id}`)
          }
          isLoading={isLoading}
          emptyMessage="No warehouses found"
        />
      </div>
    </div>
  )
}
