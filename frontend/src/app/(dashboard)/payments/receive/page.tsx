'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentsApi, customersApi, invoicesApi, accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { Plus } from 'lucide-react'

export default function ReceivePaymentsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<string>('')
  const [selectedInvoice, setSelectedInvoice] = useState<string>('')
  const queryClient = useQueryClient()

  const { data: payments, isLoading } = useQuery({
    queryKey: ['customer-payments'],
    queryFn: () => paymentsApi.listCustomerPayments(),
  })

  const { data: customers } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.list(),
  })

  const { data: invoices } = useQuery({
    queryKey: ['invoices', selectedCustomer],
    queryFn: () => invoicesApi.list({ customer_id: parseInt(selectedCustomer), status: 'sent' }),
    enabled: !!selectedCustomer,
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list({ category: 'ASSET' }),
  })

  const mutation = useMutation({
    mutationFn: (data: any) => paymentsApi.createCustomerPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer-payments'] })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setIsDialogOpen(false)
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      customer_id: parseInt(formData.get('customer_id') as string),
      payment_date: formData.get('payment_date'),
      amount: parseFloat(formData.get('amount') as string),
      payment_method: formData.get('payment_method'),
      bank_account_id: parseInt(formData.get('bank_account_id') as string),
      reference: formData.get('reference') || null,
      invoice_id: selectedInvoice ? parseInt(selectedInvoice) : null,
      notes: formData.get('notes') || null,
    })
  }

  const columns = [
    { header: 'Payment #', accessor: 'payment_number' as const },
    { header: 'Date', accessor: 'payment_date' as const },
    { header: 'Customer', accessor: 'customer_id' as const },
    { header: 'Amount', accessor: (row: any) => `$${row.amount?.toLocaleString()}` },
    { header: 'Method', accessor: 'payment_method' as const },
    { header: 'Invoice', accessor: 'invoice_id' as const },
  ]

  const bankAccounts = accounts?.data?.filter((a: any) =>
    a.code.startsWith('100') || a.code.startsWith('101') || a.code.startsWith('102')
  ) || []

  return (
    <div>
      <PageHeader
        title="Receive Payments"
        description="Record payments received from customers"
        action={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Receive Payment
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Receive Customer Payment</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Customer</Label>
                  <Select
                    name="customer_id"
                    required
                    onValueChange={(v) => setSelectedCustomer(v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {customers?.data?.map((c: any) => (
                        <SelectItem key={c.id} value={c.id.toString()}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedCustomer && invoices?.data?.length > 0 && (
                  <div className="space-y-2">
                    <Label>Apply to Invoice (Optional)</Label>
                    <Select onValueChange={(v) => setSelectedInvoice(v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select invoice" />
                      </SelectTrigger>
                      <SelectContent>
                        {invoices?.data?.map((inv: any) => (
                          <SelectItem key={inv.id} value={inv.id.toString()}>
                            {inv.invoice_number} - ${inv.balance_due}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Payment Date</Label>
                    <Input
                      type="date"
                      name="payment_date"
                      defaultValue={new Date().toISOString().split('T')[0]}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Amount</Label>
                    <Input type="number" name="amount" step="0.01" required />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Payment Method</Label>
                    <Select name="payment_method" required>
                      <SelectTrigger>
                        <SelectValue placeholder="Select method" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="check">Check</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="credit_card">Credit Card</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Deposit To</Label>
                    <Select name="bank_account_id" required>
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
                </div>

                <div className="space-y-2">
                  <Label>Reference</Label>
                  <Input name="reference" placeholder="Check number, transaction ID, etc." />
                </div>

                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Input name="notes" placeholder="Optional notes" />
                </div>

                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? 'Recording...' : 'Record Payment'}
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
            data={payments?.data || []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  )
}
