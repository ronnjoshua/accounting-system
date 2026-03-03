'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { taxesApi } from '@/lib/api'
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { Plus, Calculator, FileCheck } from 'lucide-react'

export default function TaxManagementPage() {
  const [isRateDialogOpen, setIsRateDialogOpen] = useState(false)
  const [isPeriodDialogOpen, setIsPeriodDialogOpen] = useState(false)
  const [summaryDates, setSummaryDates] = useState({
    start_date: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  })
  const queryClient = useQueryClient()

  const { data: taxRates, isLoading: ratesLoading } = useQuery({
    queryKey: ['tax-rates'],
    queryFn: () => taxesApi.listRates(),
  })

  const { data: taxPeriods, isLoading: periodsLoading } = useQuery({
    queryKey: ['tax-periods'],
    queryFn: () => taxesApi.listPeriods(),
  })

  const { data: taxSummary } = useQuery({
    queryKey: ['tax-summary', summaryDates],
    queryFn: () => taxesApi.getSummary(summaryDates.start_date, summaryDates.end_date),
  })

  const createRateMutation = useMutation({
    mutationFn: (data: any) => taxesApi.createRate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tax-rates'] })
      setIsRateDialogOpen(false)
    },
  })

  const createPeriodMutation = useMutation({
    mutationFn: (data: any) => taxesApi.createPeriod(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tax-periods'] })
      setIsPeriodDialogOpen(false)
    },
  })

  const calculatePeriodMutation = useMutation({
    mutationFn: (id: number) => taxesApi.calculatePeriod(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tax-periods'] })
    },
  })

  const filePeriodMutation = useMutation({
    mutationFn: (id: number) => taxesApi.filePeriod(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tax-periods'] })
    },
  })

  const handleCreateRate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    createRateMutation.mutate({
      code: formData.get('code'),
      name: formData.get('name'),
      tax_type: formData.get('tax_type'),
      rate: parseFloat(formData.get('rate') as string),
      country: formData.get('country') || null,
      state: formData.get('state') || null,
    })
  }

  const handleCreatePeriod = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    createPeriodMutation.mutate({
      name: formData.get('name'),
      tax_type: formData.get('tax_type'),
      period_start: formData.get('period_start'),
      period_end: formData.get('period_end'),
      due_date: formData.get('due_date'),
    })
  }

  const rateColumns = [
    { header: 'Code', accessor: 'code' as const },
    { header: 'Name', accessor: 'name' as const },
    { header: 'Type', accessor: 'tax_type' as const },
    {
      header: 'Rate',
      accessor: (row: any) => `${row.rate}%`,
    },
    { header: 'Country', accessor: 'country' as const },
    { header: 'State', accessor: 'state' as const },
    {
      header: 'Status',
      accessor: (row: any) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
  ]

  const periodColumns = [
    { header: 'Period', accessor: 'name' as const },
    { header: 'Type', accessor: 'tax_type' as const },
    {
      header: 'Start',
      accessor: (row: any) => new Date(row.period_start).toLocaleDateString(),
    },
    {
      header: 'End',
      accessor: (row: any) => new Date(row.period_end).toLocaleDateString(),
    },
    {
      header: 'Due Date',
      accessor: (row: any) => new Date(row.due_date).toLocaleDateString(),
    },
    {
      header: 'Collected',
      accessor: (row: any) => `$${row.tax_collected?.toLocaleString()}`,
    },
    {
      header: 'Paid',
      accessor: (row: any) => `$${row.tax_paid?.toLocaleString()}`,
    },
    {
      header: 'Net Due',
      accessor: (row: any) => (
        <span className={row.net_tax_due >= 0 ? 'text-red-600' : 'text-green-600'}>
          ${Math.abs(row.net_tax_due || 0).toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: (row: any) => (
        <Badge variant={row.is_filed ? 'default' : 'secondary'}>
          {row.is_filed ? 'Filed' : 'Pending'}
        </Badge>
      ),
    },
    {
      header: '',
      accessor: (row: any) => (
        <div className="flex gap-1">
          {!row.is_filed && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => calculatePeriodMutation.mutate(row.id)}
                title="Calculate"
              >
                <Calculator className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => filePeriodMutation.mutate(row.id)}
                title="Mark as Filed"
              >
                <FileCheck className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Tax Management"
        description="Manage tax rates, periods, and filing"
      />

      {/* Tax Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Tax Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={summaryDates.start_date}
                onChange={(e) => setSummaryDates({ ...summaryDates, start_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={summaryDates.end_date}
                onChange={(e) => setSummaryDates({ ...summaryDates, end_date: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Tax Collected</p>
                <p className="text-xl font-bold text-green-600">
                  ${taxSummary?.data?.tax_collected?.toLocaleString() || 0}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Tax Paid</p>
                <p className="text-xl font-bold text-blue-600">
                  ${taxSummary?.data?.tax_paid?.toLocaleString() || 0}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Net Tax Liability</p>
                <p className={`text-xl font-bold ${(taxSummary?.data?.net_tax_liability || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ${Math.abs(taxSummary?.data?.net_tax_liability || 0).toLocaleString()}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Taxable Transactions</p>
                <p className="text-xl font-bold">
                  {(taxSummary?.data?.taxable_sales_count || 0) + (taxSummary?.data?.taxable_purchases_count || 0)}
                </p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="rates">
        <TabsList>
          <TabsTrigger value="rates">Tax Rates</TabsTrigger>
          <TabsTrigger value="periods">Tax Periods</TabsTrigger>
        </TabsList>

        <TabsContent value="rates">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Tax Rates</CardTitle>
              <Dialog open={isRateDialogOpen} onOpenChange={setIsRateDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Rate
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Tax Rate</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateRate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Code</Label>
                        <Input name="code" required placeholder="VAT-STD" />
                      </div>
                      <div className="space-y-2">
                        <Label>Name</Label>
                        <Input name="name" required placeholder="Standard VAT" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Tax Type</Label>
                        <Select name="tax_type" required>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="sales_tax">Sales Tax</SelectItem>
                            <SelectItem value="vat">VAT</SelectItem>
                            <SelectItem value="gst">GST</SelectItem>
                            <SelectItem value="withholding">Withholding</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Rate (%)</Label>
                        <Input name="rate" type="number" step="0.01" required placeholder="10.00" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Country</Label>
                        <Input name="country" placeholder="USA" />
                      </div>
                      <div className="space-y-2">
                        <Label>State</Label>
                        <Input name="state" placeholder="CA" />
                      </div>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={() => setIsRateDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={createRateMutation.isPending}>
                        {createRateMutation.isPending ? 'Creating...' : 'Create Rate'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={rateColumns}
                data={taxRates?.data || []}
                isLoading={ratesLoading}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="periods">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Tax Periods</CardTitle>
              <Dialog open={isPeriodDialogOpen} onOpenChange={setIsPeriodDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Period
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Tax Period</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreatePeriod} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Period Name</Label>
                      <Input name="name" required placeholder="Q1 2024 Sales Tax" />
                    </div>
                    <div className="space-y-2">
                      <Label>Tax Type</Label>
                      <Select name="tax_type" required>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="sales_tax">Sales Tax</SelectItem>
                          <SelectItem value="vat">VAT</SelectItem>
                          <SelectItem value="gst">GST</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Period Start</Label>
                        <Input name="period_start" type="date" required />
                      </div>
                      <div className="space-y-2">
                        <Label>Period End</Label>
                        <Input name="period_end" type="date" required />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Due Date</Label>
                      <Input name="due_date" type="date" required />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={() => setIsPeriodDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={createPeriodMutation.isPending}>
                        {createPeriodMutation.isPending ? 'Creating...' : 'Create Period'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={periodColumns}
                data={taxPeriods?.data || []}
                isLoading={periodsLoading}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
