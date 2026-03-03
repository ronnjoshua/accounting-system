'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { accountsApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Account {
  id: number
  code: string
  name: string
  account_type: {
    name: string
    category: string
  }
  current_balance: number
  is_active: boolean
}

export default function AccountsPage() {
  const router = useRouter()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts', selectedCategory],
    queryFn: async () => {
      const params: any = { is_active: true }
      if (selectedCategory) {
        params.category = selectedCategory
      }
      const response = await accountsApi.list(params)
      return response.data as Account[]
    },
  })

  const categories = [
    { value: null, label: 'All' },
    { value: 'asset', label: 'Assets' },
    { value: 'liability', label: 'Liabilities' },
    { value: 'equity', label: 'Equity' },
    { value: 'revenue', label: 'Revenue' },
    { value: 'expense', label: 'Expenses' },
  ]

  const columns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Account Name', accessor: 'name' as const },
    {
      header: 'Type',
      accessor: (row: Account) => row.account_type.name,
    },
    {
      header: 'Category',
      accessor: (row: Account) => (
        <span className="capitalize">{row.account_type.category}</span>
      ),
    },
    {
      header: 'Balance',
      accessor: (row: Account) => formatCurrency(row.current_balance),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Chart of Accounts"
        description="Manage your account structure"
        action={{
          label: 'New Account',
          onClick: () => router.push('/accounts/new'),
        }}
      />

      {/* Category Filter */}
      <div className="mb-6 flex gap-2">
        {categories.map((cat) => (
          <Button
            key={cat.label}
            variant={selectedCategory === cat.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory(cat.value)}
          >
            {cat.label}
          </Button>
        ))}
      </div>

      {/* Accounts Table */}
      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={accounts || []}
          onRowClick={(account) => router.push(`/accounts/${account.id}`)}
          isLoading={isLoading}
          emptyMessage="No accounts found"
        />
      </div>
    </div>
  )
}
