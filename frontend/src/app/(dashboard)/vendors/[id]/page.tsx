'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vendorsApi, billsApi, paymentsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

export default function VendorDetailPage() {
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
    notes: '',
  })

  const { data: vendor, isLoading } = useQuery({
    queryKey: ['vendor', id],
    queryFn: async () => {
      const response = await vendorsApi.get(Number(id))
      return response.data
    },
  })

  const { data: bills } = useQuery({
    queryKey: ['vendor-bills', id],
    queryFn: async () => {
      const response = await billsApi.list({ vendor_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const { data: payments } = useQuery({
    queryKey: ['vendor-payments', id],
    queryFn: async () => {
      const response = await paymentsApi.listVendorPayments({ vendor_id: Number(id) })
      return response.data
    },
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      return vendorsApi.update(Number(id), data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor', id] })
      setIsEditDialogOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      return vendorsApi.delete(Number(id))
    },
    onSuccess: () => {
      router.push('/vendors')
    },
  })

  const openEditDialog = () => {
    if (vendor) {
      setEditForm({
        name: vendor.name || '',
        code: vendor.code || '',
        email: vendor.email || '',
        phone: vendor.phone || '',
        website: vendor.website || '',
        tax_id: vendor.tax_id || '',
        address_line1: vendor.address_line1 || '',
        address_line2: vendor.address_line2 || '',
        city: vendor.city || '',
        state: vendor.state || '',
        postal_code: vendor.postal_code || '',
        country: vendor.country || '',
        payment_terms_days: String(vendor.payment_terms_days || 30),
        notes: vendor.notes || '',
      })
    }
    setIsEditDialogOpen(true)
  }

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      ...editForm,
      payment_terms_days: parseInt(editForm.payment_terms_days),
    })
  }

  const billColumns = [
    { header: 'Bill #', accessor: 'bill_number' as const },
    {
      header: 'Date',
      accessor: (row: any) => new Date(row.bill_date).toLocaleDateString(),
    },
    {
      header: 'Due Date',
      accessor: (row: any) => new Date(row.due_date).toLocaleDateString(),
    },
    {
      header: 'Total',
      accessor: (row: any) => `$${row.total_amount?.toLocaleString()}`,
    },
    {
      header: 'Paid',
      accessor: (row: any) => `$${row.amount_paid?.toLocaleString()}`,
    },
    {
      header: 'Balance',
      accessor: (row: any) => (
        <span className={row.balance_due > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
          ${row.balance_due?.toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: (row: any) => {
        const colors: Record<string, string> = {
          draft: 'secondary',
          received: 'outline',
          paid: 'default',
          partial: 'outline',
          overdue: 'destructive',
          void: 'secondary',
        }
        return <Badge variant={colors[row.status] as any}>{row.status}</Badge>
      },
    },
    {
      header: '',
      accessor: (row: any) => (
        <Link href={`/bills/${row.id}`}>
          <Button variant="ghost" size="sm">View</Button>
        </Link>
      ),
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
    { header: 'Reference', accessor: 'reference' as const },
  ]

  if (isLoading) {
    return <div className="p-8">Loading...</div>
  }

  if (!vendor) {
    return <div className="p-8">Vendor not found</div>
  }

  // Calculate summary stats
  const totalBilled = bills?.reduce((sum: number, bill: any) => sum + bill.total_amount, 0) || 0
  const totalPaid = bills?.reduce((sum: number, bill: any) => sum + bill.amount_paid, 0) || 0
  const totalOutstanding = totalBilled - totalPaid

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/vendors">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Vendors
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{vendor.name}</h1>
          <p className="text-muted-foreground">Vendor Code: {vendor.code}</p>
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
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">Total Billed</p>
            <p className="text-2xl font-bold">${totalBilled.toLocaleString()}</p>
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
      </div>

      <Tabs defaultValue="details" className="space-y-6">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="bills">
            <FileText className="h-4 w-4 mr-2" />
            Bills ({bills?.length || 0})
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
                {vendor.email && (
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Email</p>
                      <p>{vendor.email}</p>
                    </div>
                  </div>
                )}
                {vendor.phone && (
                  <div className="flex items-center gap-3">
                    <Phone className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Phone</p>
                      <p>{vendor.phone}</p>
                    </div>
                  </div>
                )}
                {(vendor.address_line1 || vendor.city) && (
                  <div className="flex items-start gap-3">
                    <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-sm text-muted-foreground">Address</p>
                      {vendor.address_line1 && <p>{vendor.address_line1}</p>}
                      {vendor.address_line2 && <p>{vendor.address_line2}</p>}
                      <p>
                        {[vendor.city, vendor.state, vendor.postal_code]
                          .filter(Boolean)
                          .join(', ')}
                      </p>
                      {vendor.country && <p>{vendor.country}</p>}
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
                    <p className="font-medium">{vendor.payment_terms_days} days</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Tax ID</p>
                    <p className="font-medium">{vendor.tax_id || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Currency</p>
                    <p className="font-medium">{vendor.currency_code}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <Badge variant={vendor.is_active ? 'default' : 'secondary'}>
                      {vendor.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
                {vendor.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground">Notes</p>
                    <p className="text-sm">{vendor.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="bills">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Bills</CardTitle>
              <Link href={`/bills/new?vendor_id=${id}`}>
                <Button size="sm">Create Bill</Button>
              </Link>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={billColumns}
                data={bills || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Payments</CardTitle>
              <Link href={`/payments/make?vendor_id=${id}`}>
                <Button size="sm">Make Payment</Button>
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
            <DialogTitle>Edit Vendor</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vendor Name *</Label>
                <Input
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Vendor Code *</Label>
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

            <div className="grid grid-cols-2 gap-4">
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
            <AlertDialogTitle>Delete Vendor</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{vendor.name}"? This action cannot be undone.
              All associated bills and payments will also be affected.
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
