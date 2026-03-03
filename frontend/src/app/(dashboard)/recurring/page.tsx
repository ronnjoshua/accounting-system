'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { recurringApi } from '@/lib/api'
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
import { Plus, Play, Pause, RefreshCw, AlertCircle } from 'lucide-react'

export default function RecurringPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: templates, isLoading } = useQuery({
    queryKey: ['recurring'],
    queryFn: () => recurringApi.list(),
  })

  const { data: dueTemplates } = useQuery({
    queryKey: ['recurring-due'],
    queryFn: () => recurringApi.getDue(),
  })

  const pauseMutation = useMutation({
    mutationFn: (id: number) => recurringApi.pause(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring'] })
    },
  })

  const resumeMutation = useMutation({
    mutationFn: (id: number) => recurringApi.resume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring'] })
    },
  })

  const executeMutation = useMutation({
    mutationFn: (id: number) => recurringApi.execute(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring'] })
      queryClient.invalidateQueries({ queryKey: ['recurring-due'] })
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'default'
      case 'paused':
        return 'secondary'
      case 'completed':
        return 'outline'
      case 'cancelled':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'recurring_type', label: 'Type' },
    { key: 'frequency', label: 'Frequency' },
    {
      key: 'next_run_date',
      label: 'Next Run',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'last_run_date',
      label: 'Last Run',
      render: (v: string) => v ? new Date(v).toLocaleDateString() : 'Never',
    },
    {
      key: 'occurrences_completed',
      label: 'Completed',
      render: (v: number, row: any) =>
        row.total_occurrences ? `${v}/${row.total_occurrences}` : v,
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
        <div className="flex gap-1">
          {row.status === 'active' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => executeMutation.mutate(row.id)}
                title="Execute now"
              >
                <Play className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => pauseMutation.mutate(row.id)}
                title="Pause"
              >
                <Pause className="h-4 w-4" />
              </Button>
            </>
          )}
          {row.status === 'paused' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => resumeMutation.mutate(row.id)}
              title="Resume"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Recurring Transactions"
        description="Manage recurring journal entries, invoices, and bills"
        action={
          <Button onClick={() => setIsDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Recurring
          </Button>
        }
      />

      {/* Due Templates Alert */}
      {dueTemplates?.data?.length > 0 && (
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-orange-800">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">
                {dueTemplates.data.length} recurring transaction(s) are due for execution
              </span>
            </div>
            <div className="mt-3 space-y-2">
              {dueTemplates.data.map((item: any) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between bg-white p-3 rounded-lg"
                >
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">
                      Due: {item.next_run_date} ({item.days_overdue} days overdue)
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => executeMutation.mutate(item.id)}
                    disabled={executeMutation.isPending}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Execute
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={templates?.data || []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Create Dialog - simplified for now */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Recurring Transaction</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-muted-foreground">
              To create a recurring transaction, first create a journal entry, invoice, or bill,
              then use the "Make Recurring" option from that transaction's detail page.
            </p>
            <p className="text-sm text-muted-foreground">
              This feature allows you to automate repetitive accounting entries like monthly
              rent payments, subscription invoices, or depreciation entries.
            </p>
          </div>
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
