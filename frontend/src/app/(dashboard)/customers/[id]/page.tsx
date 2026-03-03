'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { customersApi, invoicesApi, paymentsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
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
import { ArrowLeft, Pencil, Trash2, FileText, DollarSign, Mail, Phone, MapPin } from 'lucide-react'
import Link from 'next/link'

export default function CustomerDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    code: '',
    email: '',
    phone: '',
    website: '',
    tax_id: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    payment_terms_days: '30',
    credit_limit: '',
    notes: '',
  })

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: async () => {
      const response = await customersApi.get(Number(id))
      return response.data
    },
  })

  const { data: invoices } = useQuery({
    queryKey: ['customer-invoices', id],
    queryFn: async () => {
      const response = await invoicesApi.list({ customer_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const { data: payments } = useQuery({
    queryKey: ['customer-payments', id],
    queryFn: async () => {
      const response = await paymentsApi.listCustomerPayments({ customer_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      return customersApi.update(Number(id), data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer', id] })
      setIsEditDialogOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      return customersApi.delete(Number(id))
    },
    onSuccess: () => {
      router.push('/customers')
    },
  })

  const openEditDialog = () => {
    if (customer) {
      setEditForm({
        name: customer.name || '',
        code: customer.code || '',
        email: customer.email || '',
        phone: customer.phone || '',
        website: customer.website || '',
        tax_id: customer.tax_id || '',
        address_line1: customer.address_line1 || '',
        address_line2: customer.address_line2 || '',
        city: customer.city || '',
        state: customer.state || '',
        postal_code: customer.postal_code || '',
        country: customer.country || '',
        payment_terms_days: String(customer.payment_terms_days || 30),
        credit_limit: customer.credit_limit ? String(customer.credit_limit) : '',
        notes: customer.notes || '',
      })
    }
    setIsEditDialogOpen(true)
  }

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      ...editForm,
      payment_terms_days: parseInt(editForm.payment_terms_days),
      credit_limit: editForm.credit_limit ? parseFloat(editForm.credit_limit) : null,
    })
  }

  const invoiceColumns = [
    { key: 'invoice_number', label: 'Invoice #' },
    {
      key: 'invoice_date',
      label: 'Date',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'due_date',
      label: 'Due Date',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'total_amount',
      label: 'Total',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'amount_paid',
      label: 'Paid',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    {
      key: 'balance_due',
      label: 'Balance',
      render: (v: number) => (
        <span className={v > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
          ${v.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (v: string) => {
        const colors: Record<string, string> = {
          draft: 'secondary',
          sent: 'outline',
          paid: 'default',
          partial: 'outline',
          overdue: 'destructive',
          void: 'secondary',
        }
        return <Badge variant={colors[v] as any}>{v}</Badge>
      },
    },
    {
      key: 'actions',
      label: '',
      render: (_: any, row: any) => (
        <Link href={`/invoices/${row.id}`}>
          <Button variant="ghost" size="sm">View</Button>
        </Link>
      ),
    },
  ]

  const paymentColumns = [
    { key: 'payment_number', label: 'Payment #' },
    {
      key: 'payment_date',
      label: 'Date',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'amount',
      label: 'Amount',
      render: (v: number) => `$${v.toLocaleString()}`,
    },
    { key: 'payment_method', label: 'Method' },
    { key: 'reference', label: 'Reference' },
  ]

  if (isLoading) {
    return <div className="p-8">Loading...</div>
  }

  if (!customer) {
    return <div className="p-8">Customer not found</div>
  }

  // Calculate summary stats
  const totalInvoiced = invoices?.reduce((sum: number, inv: any) => sum + inv.total_amount, 0) || 0
  const totalPaid = invoices?.reduce((sum: number, inv: any) => sum + inv.amount_paid, 0) || 0
  const totalOutstanding = totalInvoiced - totalPaid

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/customers">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Customers
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{customer.name}</h1>
          <p className="text-muted-foreground">Customer Code: {customer.code}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={openEditDialog}>
            <Pencil className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="destructive" onClick={() => setIsDeleteDialogOpen(true)}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Invoiced</p>
            <p className="text-2xl font-bold">${totalInvoiced.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Paid</p>
            <p className="text-2xl font-bold text-green-600">${totalPaid.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Outstanding</p>
            <p className={`text-2xl font-bold ${totalOutstanding > 0 ? 'text-red-600' : 'text-green-600'}`}>
              ${totalOutstanding.toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Credit Limit</p>
            <p className="text-2xl font-bold">
              {customer.credit_limit ? `$${customer.credit_limit.toLocaleString()}` : 'No limit'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="details" className="space-y-6">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="invoices">
            <FileText className="h-4 w-4 mr-2" />
            Invoices ({invoices?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="payments">
            <DollarSign className="h-4 w-4 mr-2" />
            Payments ({payments?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="details">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {customer.email && (
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Email</p>
                      <p>{customer.email}</p>
                    </div>
                  </div>
                )}
                {customer.phone && (
                  <div className="flex items-center gap-3">
                    <Phone className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Phone</p>
                      <p>{customer.phone}</p>
                    </div>
                  </div>
                )}
                {(customer.address_line1 || customer.city) && (
                  <div className="flex items-start gap-3">
                    <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-sm text-muted-foreground">Address</p>
                      {customer.address_line1 && <p>{customer.address_line1}</p>}
                      {customer.address_line2 && <p>{customer.address_line2}</p>}
                      <p>
                        {[customer.city, customer.state, customer.postal_code]
                          .filter(Boolean)
                          .join(', ')}
                      </p>
                      {customer.country && <p>{customer.country}</p>}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Account Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Payment Terms</p>
                    <p className="font-medium">{customer.payment_terms_days} days</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Tax ID</p>
                    <p className="font-medium">{customer.tax_id || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Currency</p>
                    <p className="font-medium">{customer.currency_code}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <Badge variant={customer.is_active ? 'default' : 'secondary'}>
                      {customer.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
                {customer.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground">Notes</p>
                    <p className="text-sm">{customer.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="invoices">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Invoices</CardTitle>
              <Link href={`/invoices/new?customer_id=${id}`}>
                <Button size="sm">Create Invoice</Button>
              </Link>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={invoiceColumns}
                data={invoices || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Payments</CardTitle>
              <Link href={`/payments/receive?customer_id=${id}`}>
                <Button size="sm">Record Payment</Button>
              </Link>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={paymentColumns}
                data={payments || []}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Edit Customer</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Customer Name *</Label>
                <Input
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Customer Code *</Label>
                <Input
                  required
                  value={editForm.code}
                  onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Address Line 1</Label>
              <Input
                value={editForm.address_line1}
                onChange={(e) => setEditForm({ ...editForm, address_line1: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Address Line 2</Label>
              <Input
                value={editForm.address_line2}
                onChange={(e) => setEditForm({ ...editForm, address_line2: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label>City</Label>
                <Input
                  value={editForm.city}
                  onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>State</Label>
                <Input
                  value={editForm.state}
                  onChange={(e) => setEditForm({ ...editForm, state: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Postal Code</Label>
                <Input
                  value={editForm.postal_code}
                  onChange={(e) => setEditForm({ ...editForm, postal_code: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Country</Label>
                <Input
                  value={editForm.country}
                  onChange={(e) => setEditForm({ ...editForm, country: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Tax ID</Label>
                <Input
                  value={editForm.tax_id}
                  onChange={(e) => setEditForm({ ...editForm, tax_id: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Payment Terms (days)</Label>
                <Input
                  type="number"
                  value={editForm.payment_terms_days}
                  onChange={(e) => setEditForm({ ...editForm, payment_terms_days: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Credit Limit</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={editForm.credit_limit}
                  onChange={(e) => setEditForm({ ...editForm, credit_limit: e.target.value })}
                  placeholder="No limit"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Customer</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{customer.name}"? This action cannot be undone.
              All associated invoices and payments will also be affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
