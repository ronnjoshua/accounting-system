'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { auditApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Eye, Filter } from 'lucide-react'

export default function AuditLogPage() {
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    start_date: '',
    end_date: '',
  })
  const [selectedLog, setSelectedLog] = useState<any>(null)

  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: () => auditApi.list({
      action: filters.action || undefined,
      entity_type: filters.entity_type || undefined,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
    }),
  })

  const { data: summary } = useQuery({
    queryKey: ['audit-summary'],
    queryFn: () => auditApi.getSummary(),
  })

  const getActionColor = (action: string) => {
    switch (action) {
      case 'create':
        return 'bg-green-100 text-green-800'
      case 'update':
        return 'bg-blue-100 text-blue-800'
      case 'delete':
        return 'bg-red-100 text-red-800'
      case 'login':
        return 'bg-purple-100 text-purple-800'
      case 'post':
        return 'bg-orange-100 text-orange-800'
      case 'void':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns = [
    {
      key: 'timestamp',
      label: 'Time',
      render: (v: string) => new Date(v).toLocaleString(),
    },
    { key: 'user_email', label: 'User' },
    {
      key: 'action',
      label: 'Action',
      render: (v: string) => (
        <Badge className={getActionColor(v)}>{v}</Badge>
      ),
    },
    { key: 'entity_type', label: 'Entity Type' },
    { key: 'entity_id', label: 'Entity ID' },
    { key: 'description', label: 'Description' },
    {
      key: 'actions',
      label: '',
      render: (_: any, row: any) => (
        <Button variant="ghost" size="sm" onClick={() => setSelectedLog(row)}>
          <Eye className="h-4 w-4" />
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Audit Logs"
        description="View system activity and changes"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Entries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.data?.total_entries || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Creates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {summary?.data?.by_action?.create || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Updates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {summary?.data?.by_action?.update || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Deletes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {summary?.data?.by_action?.delete || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Action</Label>
              <Select
                value={filters.action}
                onValueChange={(v) => setFilters({ ...filters, action: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="create">Create</SelectItem>
                  <SelectItem value="update">Update</SelectItem>
                  <SelectItem value="delete">Delete</SelectItem>
                  <SelectItem value="login">Login</SelectItem>
                  <SelectItem value="post">Post</SelectItem>
                  <SelectItem value="void">Void</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Entity Type</Label>
              <Select
                value={filters.entity_type}
                onValueChange={(v) => setFilters({ ...filters, entity_type: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="invoice">Invoice</SelectItem>
                  <SelectItem value="bill">Bill</SelectItem>
                  <SelectItem value="journal_entry">Journal Entry</SelectItem>
                  <SelectItem value="customer">Customer</SelectItem>
                  <SelectItem value="vendor">Vendor</SelectItem>
                  <SelectItem value="product">Product</SelectItem>
                  <SelectItem value="account">Account</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={logs?.data || []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit Log Detail</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Timestamp</Label>
                  <p>{new Date(selectedLog.timestamp).toLocaleString()}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">User</Label>
                  <p>{selectedLog.user_email}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Action</Label>
                  <p><Badge className={getActionColor(selectedLog.action)}>{selectedLog.action}</Badge></p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Entity</Label>
                  <p>{selectedLog.entity_type} #{selectedLog.entity_id}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">IP Address</Label>
                  <p>{selectedLog.ip_address || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Description</Label>
                  <p>{selectedLog.description || 'N/A'}</p>
                </div>
              </div>

              {selectedLog.old_values && (
                <div>
                  <Label className="text-muted-foreground">Old Values</Label>
                  <pre className="mt-2 p-4 bg-slate-100 rounded-md text-sm overflow-auto">
                    {JSON.stringify(selectedLog.old_values, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.new_values && (
                <div>
                  <Label className="text-muted-foreground">New Values</Label>
                  <pre className="mt-2 p-4 bg-slate-100 rounded-md text-sm overflow-auto">
                    {JSON.stringify(selectedLog.new_values, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
