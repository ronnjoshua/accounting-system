'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { invoicesApi, paymentsApi } from '@/lib/api'
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
import { ArrowLeft, Send, Ban, Printer, DollarSign } from 'lucide-react'
import Link from 'next/link'

export default function InvoiceDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isVoidDialogOpen, setIsVoidDialogOpen] = useState(false)

  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: async () => {
      const response = await invoicesApi.get(Number(id))
      return response.data
    },
  })

  const { data: payments } = useQuery({
    queryKey: ['invoice-payments', id],
    queryFn: async () => {
      const response = await paymentsApi.listCustomerPayments({ invoice_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const postMutation = useMutation({
    mutationFn: async () => invoicesApi.post(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] })
    },
  })

  const voidMutation = useMutation({
    mutationFn: async () => invoicesApi.void(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] })
      setIsVoidDialogOpen(false)
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'secondary',
      sent: 'outline',
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
      header: 'Discount',
      accessor: (row: any) => row.discount_percent ? `${row.discount_percent}%` : '-',
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

  if (!invoice) {
    return <div className="p-8">Invoice not found</div>
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/invoices">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Invoices
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Invoice {invoice.invoice_number}</h1>
            <Badge variant={getStatusColor(invoice.status) as any}>
              {invoice.status}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            {invoice.customer?.name || 'Unknown Customer'}
          </p>
        </div>
        <div className="flex gap-2">
          {invoice.status === 'draft' && (
            <Button onClick={() => postMutation.mutate()} disabled={postMutation.isPending}>
              <Send className="h-4 w-4 mr-2" />
              {postMutation.isPending ? 'Posting...' : 'Post Invoice'}
            </Button>
          )}
          {invoice.status !== 'void' && invoice.status !== 'paid' && (
            <Link href={`/payments/receive?invoice_id=${id}`}>
              <Button variant="outline">
                <DollarSign className="h-4 w-4 mr-2" />
                Record Payment
              </Button>
            </Link>
          )}
          <Button variant="outline" onClick={() => window.print()}>
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
          {invoice.status !== 'void' && (
            <Button variant="destructive" onClick={() => setIsVoidDialogOpen(true)}>
              <Ban className="h-4 w-4 mr-2" />
              Void
            </Button>
          )}
        </div>
      </div>

      {/* Invoice Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Invoice Date</p>
            <p className="text-lg font-medium">
              {new Date(invoice.invoice_date).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Due Date</p>
            <p className="text-lg font-medium">
              {new Date(invoice.due_date).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Amount</p>
            <p className="text-lg font-bold">${invoice.total_amount?.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Balance Due</p>
            <p className={`text-lg font-bold ${invoice.balance_due > 0 ? 'text-red-600' : 'text-green-600'}`}>
              ${invoice.balance_due?.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3 mb-6">
        {/* Customer Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bill To</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{invoice.customer?.name}</p>
            {invoice.customer?.address_line1 && <p className="text-sm text-muted-foreground">{invoice.customer.address_line1}</p>}
            {invoice.customer?.city && (
              <p className="text-sm text-muted-foreground">
                {[invoice.customer.city, invoice.customer.state, invoice.customer.postal_code].filter(Boolean).join(', ')}
              </p>
            )}
            {invoice.customer?.email && <p className="text-sm text-muted-foreground mt-2">{invoice.customer.email}</p>}
          </CardContent>
        </Card>

        {/* Invoice Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invoice Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Reference:</span>
              <span>{invoice.reference || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Currency:</span>
              <span>{invoice.currency_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Terms:</span>
              <span>{invoice.customer?.payment_terms_days || 30} days</span>
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
              <span>${invoice.subtotal?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tax:</span>
              <span>${invoice.tax_amount?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Discount:</span>
              <span>-${invoice.discount_amount?.toLocaleString()}</span>
            </div>
            <hr />
            <div className="flex justify-between font-bold">
              <span>Total:</span>
              <span>${invoice.total_amount?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-green-600">
              <span>Paid:</span>
              <span>${invoice.amount_paid?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between font-bold text-lg">
              <span>Balance:</span>
              <span className={invoice.balance_due > 0 ? 'text-red-600' : 'text-green-600'}>
                ${invoice.balance_due?.toLocaleString()}
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
            data={invoice.lines || []}
          />
        </CardContent>
      </Card>

      {/* Payments */}
      {payments && payments.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Payments Received</CardTitle>
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
      {invoice.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{invoice.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Void Confirmation */}
      <AlertDialog open={isVoidDialogOpen} onOpenChange={setIsVoidDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Void Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to void invoice {invoice.invoice_number}?
              This will reverse all accounting entries and cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => voidMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {voidMutation.isPending ? 'Voiding...' : 'Void Invoice'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
