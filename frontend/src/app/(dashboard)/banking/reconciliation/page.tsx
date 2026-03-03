'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bankingApi, accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, CheckCircle, XCircle } from 'lucide-react'

export default function BankReconciliationPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedReconciliation, setSelectedReconciliation] = useState<any>(null)
  const queryClient = useQueryClient()

  const { data: reconciliations, isLoading } = useQuery({
    queryKey: ['reconciliations'],
    queryFn: () => bankingApi.listReconciliations(),
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list({ category: 'ASSET' }),
  })

  const { data: unclearedItems } = useQuery({
    queryKey: ['uncleared', selectedReconciliation?.id],
    queryFn: () => bankingApi.getUnclearedTransactions(selectedReconciliation.id),
    enabled: !!selectedReconciliation,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => bankingApi.createReconciliation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] })
      setIsDialogOpen(false)
    },
  })

  const completeMutation = useMutation({
    mutationFn: (id: number) => bankingApi.completeReconciliation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] })
      setSelectedReconciliation(null)
    },
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    createMutation.mutate({
      account_id: parseInt(formData.get('account_id') as string),
      statement_date: formData.get('statement_date'),
      statement_balance: parseFloat(formData.get('statement_balance') as string),
      notes: formData.get('notes') || null,
    })
  }

  const bankAccounts = accounts?.data?.filter((a: any) =>
    a.code.startsWith('100') || a.code.startsWith('101') || a.code.startsWith('102')
  ) || []

  const columns = [
    {
      key: 'statement_date',
      label: 'Statement Date',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    { key: 'account_id', label: 'Account' },
    {
      key: 'statement_balance',
      label: 'Statement Balance',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'gl_balance',
      label: 'GL Balance',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'difference',
      label: 'Difference',
      render: (v: number) => (
        <span className={v === 0 ? 'text-green-600' : 'text-red-600'}>
          ${Math.abs(v).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (v: string) => (
        <Badge variant={v === 'completed' ? 'default' : 'secondary'}>
          {v}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (_: any, row: any) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSelectedReconciliation(row)}
          disabled={row.status === 'completed'}
        >
          {row.status === 'completed' ? 'View' : 'Reconcile'}
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Bank Reconciliation"
        description="Reconcile bank statements with general ledger"
        action={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Reconciliation
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Start New Reconciliation</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Bank Account</Label>
                  <Select name="account_id" required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      {bankAccounts.map((acc: any) => (
                        <SelectItem key={acc.id} value={acc.id.toString()}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Statement Date</Label>
                  <Input type="date" name="statement_date" required />
                </div>

                <div className="space-y-2">
                  <Label>Statement Ending Balance</Label>
                  <Input type="number" name="statement_balance" step="0.01" required />
                </div>

                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Input name="notes" placeholder="Optional notes" />
                </div>

                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? 'Creating...' : 'Start Reconciliation'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={reconciliations?.data || []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Reconciliation Detail Dialog */}
      <Dialog open={!!selectedReconciliation} onOpenChange={() => setSelectedReconciliation(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Reconcile Bank Account</DialogTitle>
          </DialogHeader>
          {selectedReconciliation && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">Statement Balance</p>
                    <p className="text-xl font-bold">
                      ${selectedReconciliation.statement_balance.toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">GL Balance</p>
                    <p className="text-xl font-bold">
                      ${selectedReconciliation.gl_balance.toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">Reconciled</p>
                    <p className="text-xl font-bold">
                      ${selectedReconciliation.reconciled_balance.toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">Difference</p>
                    <p className={`text-xl font-bold ${selectedReconciliation.difference === 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${Math.abs(selectedReconciliation.difference).toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Uncleared Items */}
              <div>
                <h3 className="font-semibold mb-4">Uncleared Transactions</h3>
                <div className="space-y-2">
                  {unclearedItems?.data?.map((item: any) => (
                    <div
                      key={item.journal_entry_line_id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{item.entry_number}</p>
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                        <p className="text-xs text-muted-foreground">{item.entry_date}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={item.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${Math.abs(item.amount).toLocaleString()}
                        </span>
                        <Button variant="outline" size="sm">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Clear
                        </Button>
                      </div>
                    </div>
                  ))}
                  {!unclearedItems?.data?.length && (
                    <p className="text-muted-foreground text-center py-4">
                      No uncleared transactions
                    </p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setSelectedReconciliation(null)}>
                  Close
                </Button>
                <Button
                  onClick={() => completeMutation.mutate(selectedReconciliation.id)}
                  disabled={selectedReconciliation.difference !== 0 || completeMutation.isPending}
                >
                  {completeMutation.isPending ? 'Completing...' : 'Complete Reconciliation'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
