'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetsApi } from '@/lib/api'
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
import { Plus, Eye, CheckCircle, Play } from 'lucide-react'
import Link from 'next/link'

export default function BudgetsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: budgets, isLoading } = useQuery({
    queryKey: ['budgets'],
    queryFn: () => budgetsApi.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => budgetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      setIsDialogOpen(false)
    },
  })

  const approveMutation = useMutation({
    mutationFn: (id: number) => budgetsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: number) => budgetsApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
    },
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    createMutation.mutate({
      name: formData.get('name'),
      description: formData.get('description') || null,
      fiscal_year: parseInt(formData.get('fiscal_year') as string),
      period_type: formData.get('period_type'),
      notes: formData.get('notes') || null,
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'secondary'
      case 'approved':
        return 'outline'
      case 'active':
        return 'default'
      case 'closed':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const columns = [
    { key: 'name', label: 'Budget Name' },
    { key: 'fiscal_year', label: 'Fiscal Year' },
    { key: 'period_type', label: 'Period Type' },
    {
      key: 'total_revenue',
      label: 'Total Revenue',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'total_expense',
      label: 'Total Expense',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'net_income',
      label: 'Net Income',
      render: (v: number) => (
        <span className={v >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${v.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (v: string) => (
        <Badge variant={getStatusColor(v) as any}>{v}</Badge>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (_: any, row: any) => (
        <div className="flex gap-2">
          <Link href={`/budgets/${row.id}`}>
            <Button variant="ghost" size="sm">
              <Eye className="h-4 w-4" />
            </Button>
          </Link>
          {row.status === 'draft' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => approveMutation.mutate(row.id)}
            >
              <CheckCircle className="h-4 w-4" />
            </Button>
          )}
          {row.status === 'approved' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => activateMutation.mutate(row.id)}
            >
              <Play className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ]

  const currentYear = new Date().getFullYear()

  return (
    <div>
      <PageHeader
        title="Budgets"
        description="Manage fiscal year budgets and track performance"
        action={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Budget
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Budget</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Budget Name</Label>
                  <Input name="name" required placeholder="FY 2024 Operating Budget" />
                </div>

                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input name="description" placeholder="Optional description" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Fiscal Year</Label>
                    <Select name="fiscal_year" required defaultValue={currentYear.toString()}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[currentYear - 1, currentYear, currentYear + 1, currentYear + 2].map((year) => (
                          <SelectItem key={year} value={year.toString()}>
                            {year}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Period Type</Label>
                    <Select name="period_type" required defaultValue="monthly">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="quarterly">Quarterly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
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
                    {createMutation.isPending ? 'Creating...' : 'Create Budget'}
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
            data={budgets?.data || []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  )
}
