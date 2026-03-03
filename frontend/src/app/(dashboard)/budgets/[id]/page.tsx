'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetsApi, accountsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/shared/DataTable'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ArrowLeft, Plus, CheckCircle, Play, BarChart3 } from 'lucide-react'
import Link from 'next/link'

export default function BudgetDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isLineDialogOpen, setIsLineDialogOpen] = useState(false)
  const [lineForm, setLineForm] = useState({
    account_id: '',
    period: '1',
    amount: '',
  })

  const { data: budget, isLoading } = useQuery({
    queryKey: ['budget', id],
    queryFn: async () => {
      const response = await budgetsApi.get(Number(id))
      return response.data
    },
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await accountsApi.list()
      return response.data
    },
  })

  const { data: comparison } = useQuery({
    queryKey: ['budget-comparison', id],
    queryFn: async () => {
      const response = await budgetsApi.getComparison(Number(id))
      return response.data
    },
    enabled: budget?.status === 'active',
  })

  const addLineMutation = useMutation({
    mutationFn: async (data: any) => budgetsApi.addLine(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget', id] })
      setIsLineDialogOpen(false)
      setLineForm({ account_id: '', period: '1', amount: '' })
    },
  })

  const approveMutation = useMutation({
    mutationFn: async () => budgetsApi.approve(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget', id] })
    },
  })

  const activateMutation = useMutation({
    mutationFn: async () => budgetsApi.activate(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget', id] })
    },
  })

  const handleAddLine = (e: React.FormEvent) => {
    e.preventDefault()
    addLineMutation.mutate({
      account_id: parseInt(lineForm.account_id),
      period: parseInt(lineForm.period),
      amount: parseFloat(lineForm.amount),
    })
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'secondary',
      approved: 'outline',
      active: 'default',
      closed: 'destructive',
    }
    return colors[status] || 'secondary'
  }

  const getPeriodLabel = (period: number, periodType: string) => {
    if (periodType === 'monthly') {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      return months[period - 1] || `Period ${period}`
    }
    if (periodType === 'quarterly') {
      return `Q${period}`
    }
    return `Year`
  }

  // Group budget lines by account for display
  const groupedLines = budget?.lines?.reduce((acc: any, line: any) => {
    const key = line.account_id
    if (!acc[key]) {
      acc[key] = {
        account: line.account,
        periods: {},
        total: 0,
      }
    }
    acc[key].periods[line.period] = line.amount
    acc[key].total += line.amount
    return acc
  }, {}) || {}

  const lineColumns = [
    {
      header: 'Account',
      accessor: (row: any) => (
        <div>
          <p className="font-medium">{row.account?.code}</p>
          <p className="text-sm text-muted-foreground">{row.account?.name}</p>
        </div>
      ),
    },
    {
      header: 'Period',
      accessor: (row: any) => getPeriodLabel(row.period, budget?.period_type || 'monthly'),
    },
    {
      header: 'Budget Amount',
      accessor: (row: any) => `$${row.amount?.toLocaleString()}`,
    },
  ]

  const comparisonColumns = [
    { header: 'Account', accessor: 'account_code' as const },
    { header: 'Name', accessor: 'account_name' as const },
    {
      header: 'Budget',
      accessor: (row: any) => `$${row.budget_amount?.toLocaleString()}`,
    },
    {
      header: 'Actual',
      accessor: (row: any) => `$${row.actual_amount?.toLocaleString()}`,
    },
    {
      header: 'Variance',
      accessor: (row: any) => (
        <span className={row.variance >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${Math.abs(row.variance).toLocaleString()} {row.variance >= 0 ? 'under' : 'over'}
        </span>
      ),
    },
    {
      header: '%',
      accessor: (row: any) => (
        <span className={row.variance_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
          {row.variance_percent?.toFixed(1)}%
        </span>
      ),
    },
  ]

  const numPeriods = budget?.period_type === 'monthly' ? 12 : budget?.period_type === 'quarterly' ? 4 : 1

  if (isLoading) {
    return <div className="p-8">Loading...</div>
  }

  if (!budget) {
    return <div className="p-8">Budget not found</div>
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/budgets">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Budgets
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{budget.name}</h1>
            <Badge variant={getStatusColor(budget.status) as any}>
              {budget.status}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            FY {budget.fiscal_year} | {budget.period_type} budget
          </p>
        </div>
        <div className="flex gap-2">
          {budget.status === 'draft' && (
            <>
              <Button variant="outline" onClick={() => setIsLineDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Line
              </Button>
              <Button onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending}>
                <CheckCircle className="h-4 w-4 mr-2" />
                {approveMutation.isPending ? 'Approving...' : 'Approve'}
              </Button>
            </>
          )}
          {budget.status === 'approved' && (
            <Button onClick={() => activateMutation.mutate()} disabled={activateMutation.isPending}>
              <Play className="h-4 w-4 mr-2" />
              {activateMutation.isPending ? 'Activating...' : 'Activate'}
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Revenue</p>
            <p className="text-2xl font-bold text-green-600">
              ${budget.total_revenue?.toLocaleString() || 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Expense</p>
            <p className="text-2xl font-bold text-red-600">
              ${budget.total_expense?.toLocaleString() || 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Net Income</p>
            <p className={`text-2xl font-bold ${budget.net_income >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${budget.net_income?.toLocaleString() || 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Budget Lines</p>
            <p className="text-2xl font-bold">{budget.lines?.length || 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Budget Lines */}
      <Card className="mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Budget Lines</CardTitle>
          {budget.status === 'draft' && (
            <Button size="sm" onClick={() => setIsLineDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Line
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {budget.lines?.length > 0 ? (
            <DataTable
              columns={lineColumns}
              data={budget.lines}
            />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No budget lines added yet. Add accounts to start building your budget.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Budget vs Actual Comparison (only for active budgets) */}
      {budget.status === 'active' && comparison && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Budget vs Actual
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={comparisonColumns}
              data={comparison.accounts || []}
            />
            <div className="mt-4 grid grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">Total Budget</p>
                  <p className="text-xl font-bold">${comparison.total_budget?.toLocaleString()}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">Total Actual</p>
                  <p className="text-xl font-bold">${comparison.total_actual?.toLocaleString()}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">Total Variance</p>
                  <p className={`text-xl font-bold ${comparison.total_variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${Math.abs(comparison.total_variance || 0).toLocaleString()}
                  </p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {budget.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{budget.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Add Line Dialog */}
      <Dialog open={isLineDialogOpen} onOpenChange={setIsLineDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Budget Line</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddLine} className="space-y-4">
            <div className="space-y-2">
              <Label>Account</Label>
              <Select
                value={lineForm.account_id}
                onValueChange={(v) => setLineForm({ ...lineForm, account_id: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts?.map((acc: any) => (
                    <SelectItem key={acc.id} value={String(acc.id)}>
                      {acc.code} - {acc.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Period</Label>
              <Select
                value={lineForm.period}
                onValueChange={(v) => setLineForm({ ...lineForm, period: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: numPeriods }, (_, i) => i + 1).map((p) => (
                    <SelectItem key={p} value={String(p)}>
                      {getPeriodLabel(p, budget.period_type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Budget Amount</Label>
              <Input
                type="number"
                step="0.01"
                required
                value={lineForm.amount}
                onChange={(e) => setLineForm({ ...lineForm, amount: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsLineDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={addLineMutation.isPending}>
                {addLineMutation.isPending ? 'Adding...' : 'Add Line'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
