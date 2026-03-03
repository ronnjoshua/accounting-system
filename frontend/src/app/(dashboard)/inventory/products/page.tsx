'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { productsApi } from '@/lib/api'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'

interface Product {
  id: number
  code: string
  name: string
  product_type: string
  category: string | null
  unit_of_measure: string
  purchase_price: number
  selling_price: number
  quantity_on_hand: number
  is_active: boolean
}

export default function ProductsPage() {
  const router = useRouter()

  const { data: products, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await productsApi.list()
      return response.data as Product[]
    },
  })

  const columns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Name', accessor: 'name' as const },
    {
      header: 'Type',
      accessor: (row: Product) => (
        <span className="capitalize">{row.product_type.replace('_', ' ')}</span>
      ),
    },
    { header: 'Category', accessor: (row: Product) => row.category || '-' },
    { header: 'UoM', accessor: 'unit_of_measure' as const },
    {
      header: 'Cost',
      accessor: (row: Product) => formatCurrency(row.purchase_price),
      className: 'text-right',
    },
    {
      header: 'Price',
      accessor: (row: Product) => formatCurrency(row.selling_price),
      className: 'text-right',
    },
    {
      header: 'On Hand',
      accessor: (row: Product) => formatNumber(row.quantity_on_hand),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Products"
        description="Manage your product catalog"
        action={{
          label: 'New Product',
          onClick: () => router.push('/inventory/products/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={products || []}
          onRowClick={(product) => router.push(`/inventory/products/${product.id}`)}
          isLoading={isLoading}
          emptyMessage="No products found"
        />
      </div>
    </div>
  )
}
