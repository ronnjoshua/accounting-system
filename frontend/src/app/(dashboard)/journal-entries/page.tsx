'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { journalEntriesApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { cn } from '@/lib/utils'

interface JournalEntry {
  id: number
  entry_number: string
  entry_date: string
  description: string
  status: string
  lines: Array<{ debit: number; credit: number }>
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  posted: 'bg-green-100 text-green-800',
  void: 'bg-red-100 text-red-800',
}

export default function JournalEntriesPage() {
  const router = useRouter()

  const { data: entries, isLoading } = useQuery({
    queryKey: ['journal-entries'],
    queryFn: async () => {
      const response = await journalEntriesApi.list()
      return response.data as JournalEntry[]
    },
  })

  const calculateTotal = (lines: Array<{ debit: number; credit: number }>) => {
    return lines.reduce((sum, line) => sum + (line.debit || 0), 0)
  }

  const columns = [
    { header: 'Entry #', accessor: 'entry_number' as const },
    {
      header: 'Date',
      accessor: (row: JournalEntry) => formatDate(row.entry_date),
    },
    { header: 'Description', accessor: 'description' as const },
    {
      header: 'Status',
      accessor: (row: JournalEntry) => (
        <span
          className={cn(
            'inline-flex rounded-full px-2 py-1 text-xs font-semibold capitalize',
            statusColors[row.status] || 'bg-gray-100'
          )}
        >
          {row.status}
        </span>
      ),
    },
    {
      header: 'Amount',
      accessor: (row: JournalEntry) => formatCurrency(calculateTotal(row.lines || [])),
      className: 'text-right',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Journal Entries"
        description="Manage manual journal entries"
        action={{
          label: 'New Entry',
          onClick: () => router.push('/journal-entries/new'),
        }}
      />

      <div className="rounded-lg border bg-white">
        <DataTable
          columns={columns}
          data={entries || []}
          onRowClick={(entry) => router.push(`/journal-entries/${entry.id}`)}
          isLoading={isLoading}
          emptyMessage="No journal entries found"
        />
      </div>
    </div>
  )
}
