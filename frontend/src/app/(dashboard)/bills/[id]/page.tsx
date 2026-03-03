'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billsApi, paymentsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/shared/DataTable'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { ArrowLeft, CheckCircle, Ban, DollarSign } from 'lucide-react'
import Link from 'next/link'

export default function BillDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isVoidDialogOpen, setIsVoidDialogOpen] = useState(false)

  const { data: bill, isLoading } = useQuery({
    queryKey: ['bill', id],
    queryFn: async () => {
      const response = await billsApi.get(Number(id))
      return response.data
    },
  })

  const { data: payments } = useQuery({
    queryKey: ['bill-payments', id],
    queryFn: async () => {
      const response = await paymentsApi.listVendorPayments({ bill_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const approveMutation = useMutation({
    mutationFn: async () => billsApi.approve(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bill', id] })
    },
  })

  const voidMutation = useMutation({
    mutationFn: async () => billsApi.void(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bill', id] })
      setIsVoidDialogOpen(false)
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'secondary',
      received: 'outline',
      approved: 'outline',
      paid: 'default',
      partial: 'outline',
      overdue: 'destructive',
      void: 'secondary',
    }
    return colors[status] || 'secondary'
  }

  const lineColumns = [
    { header: 'Description', accessor: 'description' as const },
    {
      header: 'Qty',
      accessor: (row: any) => row.quantity?.toLocaleString(),
    },
    {
      header: 'Unit Price',
      accessor: (row: any) => `$${row.unit_price?.toLocaleString()}`,
    },
    {
      header: 'Tax',
      accessor: (row: any) => `$${row.tax_amount?.toLocaleString()}`,
    },
    {
      header: 'Total',
      accessor: (row: any) => `$${row.line_total?.toLocaleString()}`,
    },
  ]

  const paymentColumns = [
    { header: 'Payment #', accessor: 'payment_number' as const },
    {
      header: 'Date',
      accessor: (row: any) => new Date(row.payment_date).toLocaleDateString(),
    },
    {
      header: 'Amount',
      accessor: (row: any) => `$${row.amount?.toLocaleString()}`,
    },
    { header: 'Method', accessor: 'payment_method' as const },
  ]

  if (isLoading) {
    return <div className="p-8">Loading...</div>
  }

  if (!bill) {
    return <div className="p-8">Bill not found</div>
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/bills">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Bills
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Bill {bill.bill_number}</h1>
            <Badge variant={getStatusColor(bill.status) as any}>
              {bill.status}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            {bill.vendor?.name || 'Unknown Vendor'}
          </p>
        </div>
        <div className="flex gap-2">
          {(bill.status === 'draft' || bill.status === 'received') && (
            <Button onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending}>
              <CheckCircle className="h-4 w-4 mr-2" />
              {approveMutation.isPending ? 'Approving...' : 'Approve Bill'}
            </Button>
          )}
          {bill.status !== 'void' && bill.status !== 'paid' && (
            <Link href={`/payments/make?bill_id=${id}`}>
              <Button variant="outline">
                <DollarSign className="h-4 w-4 mr-2" />
                Make Payment
              </Button>
            </Link>
          )}
          {bill.status !== 'void' && (
            <Button variant="destructive" onClick={() => setIsVoidDialogOpen(true)}>
              <Ban className="h-4 w-4 mr-2" />
              Void
            </Button>
          )}
        </div>
      </div>

      {/* Bill Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Bill Date</p>
            <p className="text-lg font-medium">
              {new Date(bill.bill_date).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Due Date</p>
            <p className="text-lg font-medium">
              {new Date(bill.due_date).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Amount</p>
            <p className="text-lg font-bold">${bill.total_amount?.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Balance Due</p>
            <p className={`text-lg font-bold ${bill.balance_due > 0 ? 'text-red-600' : 'text-green-600'}`}>
              ${bill.balance_due?.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3 mb-6">
        {/* Vendor Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Vendor</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{bill.vendor?.name}</p>
            {bill.vendor?.address_line1 && <p className="text-sm text-muted-foreground">{bill.vendor.address_line1}</p>}
            {bill.vendor?.city && (
              <p className="text-sm text-muted-foreground">
                {[bill.vendor.city, bill.vendor.state, bill.vendor.postal_code].filter(Boolean).join(', ')}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Bill Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bill Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Vendor Invoice #:</span>
              <span>{bill.vendor_invoice_number || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Currency:</span>
              <span>{bill.currency_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Terms:</span>
              <span>{bill.vendor?.payment_terms_days || 30} days</span>
            </div>
          </CardContent>
        </Card>

        {/* Amounts */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Amount Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Subtotal:</span>
              <span>${bill.subtotal?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tax:</span>
              <span>${bill.tax_amount?.toLocaleString()}</span>
            </div>
            <hr />
            <div className="flex justify-between font-bold">
              <span>Total:</span>
              <span>${bill.total_amount?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-green-600">
              <span>Paid:</span>
              <span>${bill.amount_paid?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between font-bold text-lg">
              <span>Balance:</span>
              <span className={bill.balance_due > 0 ? 'text-red-600' : 'text-green-600'}>
                ${bill.balance_due?.toLocaleString()}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Line Items */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Line Items</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={lineColumns}
            data={bill.lines || []}
          />
        </CardContent>
      </Card>

      {/* Payments */}
      {payments && payments.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Payments Made</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={paymentColumns}
              data={payments}
            />
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {bill.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{bill.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Void Confirmation */}
      <AlertDialog open={isVoidDialogOpen} onOpenChange={setIsVoidDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Void Bill</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to void bill {bill.bill_number}?
              This will reverse all accounting entries and cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => voidMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {voidMutation.isPending ? 'Voiding...' : 'Void Bill'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
