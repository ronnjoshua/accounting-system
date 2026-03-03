'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentsApi, vendorsApi, billsApi, accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
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

export default function MakePaymentsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<string>('')
  const [selectedBill, setSelectedBill] = useState<string>('')
  const queryClient = useQueryClient()

  const { data: payments, isLoading } = useQuery({
    queryKey: ['vendor-payments'],
    queryFn: () => paymentsApi.listVendorPayments(),
  })

  const { data: vendors } = useQuery({
    queryKey: ['vendors'],
    queryFn: () => vendorsApi.list(),
  })

  const { data: bills } = useQuery({
    queryKey: ['bills', selectedVendor],
    queryFn: () => billsApi.list({ vendor_id: parseInt(selectedVendor), status: 'received' }),
    enabled: !!selectedVendor,
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list({ category: 'ASSET' }),
  })

  const mutation = useMutation({
    mutationFn: (data: any) => paymentsApi.createVendorPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-payments'] })
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      setIsDialogOpen(false)
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      vendor_id: parseInt(formData.get('vendor_id') as string),
      payment_date: formData.get('payment_date'),
      amount: parseFloat(formData.get('amount') as string),
      payment_method: formData.get('payment_method'),
      bank_account_id: parseInt(formData.get('bank_account_id') as string),
      reference: formData.get('reference') || null,
      bill_id: selectedBill ? parseInt(selectedBill) : null,
      notes: formData.get('notes') || null,
    })
  }

  const columns = [
    { key: 'payment_number', label: 'Payment #' },
    { key: 'payment_date', label: 'Date' },
    { key: 'vendor_id', label: 'Vendor' },
    { key: 'amount', label: 'Amount', render: (v: number) => `$${v.toLocaleString()}` },
    { key: 'payment_method', label: 'Method' },
    { key: 'bill_id', label: 'Bill' },
  ]

  const bankAccounts = accounts?.data?.filter((a: any) =>
    a.code.startsWith('100') || a.code.startsWith('101') || a.code.startsWith('102')
  ) || []

  return (
    <div>
      <PageHeader
        title="Make Payments"
        description="Record payments made to vendors"
        action={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Make Payment
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Make Vendor Payment</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Vendor</Label>
                  <Select
                    name="vendor_id"
                    required
                    onValueChange={(v) => setSelectedVendor(v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select vendor" />
                    </SelectTrigger>
                    <SelectContent>
                      {vendors?.data?.map((v: any) => (
                        <SelectItem key={v.id} value={v.id.toString()}>
                          {v.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedVendor && bills?.data?.length > 0 && (
                  <div className="space-y-2">
                    <Label>Apply to Bill (Optional)</Label>
                    <Select onValueChange={(v) => setSelectedBill(v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select bill" />
                      </SelectTrigger>
                      <SelectContent>
                        {bills?.data?.map((bill: any) => (
                          <SelectItem key={bill.id} value={bill.id.toString()}>
                            {bill.bill_number} - ${bill.balance_due}
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
                        <SelectItem value="check">Check</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="ach">ACH</SelectItem>
                        <SelectItem value="wire">Wire Transfer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Pay From</Label>
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
