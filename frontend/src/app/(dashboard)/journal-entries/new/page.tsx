'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import { journalEntriesApi, accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

interface Account {
  id: number
  code: string
  name: string
}

interface Line {
  account_id: string
  description: string
  debit: string
  credit: string
}

export default function NewJournalEntryPage() {
  const router = useRouter()
  const [error, setError] = useState('')
  const [lines, setLines] = useState<Line[]>([
    { account_id: '', description: '', debit: '', credit: '' },
    { account_id: '', description: '', debit: '', credit: '' },
  ])

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await accountsApi.list()
      return response.data as Account[]
    },
  })

  const mutation = useMutation({
    mutationFn: (data: any) => journalEntriesApi.create(data),
    onSuccess: () => {
      router.push('/journal-entries')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create journal entry')
    },
  })

  const addLine = () => {
    setLines([...lines, { account_id: '', description: '', debit: '', credit: '' }])
  }

  const updateLine = (index: number, field: keyof Line, value: string) => {
    const newLines = [...lines]
    newLines[index][field] = value
    setLines(newLines)
  }

  const removeLine = (index: number) => {
    if (lines.length > 2) {
      setLines(lines.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)

    const entryLines = lines
      .filter(line => line.account_id && (line.debit || line.credit))
      .map(line => ({
        account_id: parseInt(line.account_id),
        description: line.description,
        debit: parseFloat(line.debit) || 0,
        credit: parseFloat(line.credit) || 0,
        currency_code: 'USD',
        exchange_rate: 1,
      }))

    mutation.mutate({
      entry_date: formData.get('entry_date'),
      description: formData.get('description'),
      reference: formData.get('reference') || null,
      is_adjusting: false,
      lines: entryLines,
    })
  }

  const totalDebit = lines.reduce((sum, line) => sum + (parseFloat(line.debit) || 0), 0)
  const totalCredit = lines.reduce((sum, line) => sum + (parseFloat(line.credit) || 0), 0)

  return (
    <div>
      <PageHeader
        title="New Journal Entry"
        description="Create a new manual journal entry"
      />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="entry_date">Date</Label>
                <Input
                  id="entry_date"
                  name="entry_date"
                  type="date"
                  defaultValue={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reference">Reference</Label>
                <Input id="reference" name="reference" placeholder="Optional" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input id="description" name="description" placeholder="Entry description" required />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Entry Lines</Label>
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Account</th>
                    <th className="text-left p-2">Description</th>
                    <th className="text-right p-2">Debit</th>
                    <th className="text-right p-2">Credit</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, index) => (
                    <tr key={index} className="border-b">
                      <td className="p-2">
                        <select
                          className="w-full rounded-md border px-2 py-1"
                          value={line.account_id}
                          onChange={(e) => updateLine(index, 'account_id', e.target.value)}
                        >
                          <option value="">Select...</option>
                          {accounts?.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                              {acc.code} - {acc.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="p-2">
                        <Input
                          value={line.description}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                          placeholder="Line description"
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="0.01"
                          className="text-right"
                          value={line.debit}
                          onChange={(e) => updateLine(index, 'debit', e.target.value)}
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="0.01"
                          className="text-right"
                          value={line.credit}
                          onChange={(e) => updateLine(index, 'credit', e.target.value)}
                        />
                      </td>
                      <td className="p-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeLine(index)}
                          disabled={lines.length <= 2}
                        >
                          X
                        </Button>
                      </td>
                    </tr>
                  ))}
                  <tr className="font-semibold">
                    <td colSpan={2} className="p-2 text-right">Totals:</td>
                    <td className="p-2 text-right">{totalDebit.toFixed(2)}</td>
                    <td className="p-2 text-right">{totalCredit.toFixed(2)}</td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                + Add Line
              </Button>
              {totalDebit !== totalCredit && (
                <p className="text-sm text-red-600">Debits and credits must be equal</p>
              )}
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending || totalDebit !== totalCredit}>
                {mutation.isPending ? 'Creating...' : 'Create Entry'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
