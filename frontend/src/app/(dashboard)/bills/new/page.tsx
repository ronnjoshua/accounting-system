'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import { billsApi, vendorsApi, productsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

interface Vendor {
  id: number
  code: string
  name: string
  payment_terms: number
}

interface Product {
  id: number
  code: string
  name: string
  cost_price: number
}

interface Line {
  product_id: string
  description: string
  quantity: string
  unit_price: string
}

export default function NewBillPage() {
  const router = useRouter()
  const [error, setError] = useState('')
  const [vendorId, setVendorId] = useState('')
  const [lines, setLines] = useState<Line[]>([
    { product_id: '', description: '', quantity: '1', unit_price: '0' },
  ])

  const { data: vendors } = useQuery({
    queryKey: ['vendors'],
    queryFn: async () => {
      const response = await vendorsApi.list()
      return response.data as Vendor[]
    },
  })

  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await productsApi.list()
      return response.data as Product[]
    },
  })

  const mutation = useMutation({
    mutationFn: (data: any) => billsApi.create(data),
    onSuccess: () => {
      router.push('/bills')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create bill')
    },
  })

  const addLine = () => {
    setLines([...lines, { product_id: '', description: '', quantity: '1', unit_price: '0' }])
  }

  const updateLine = (index: number, field: keyof Line, value: string) => {
    const newLines = [...lines]
    newLines[index][field] = value

    // Auto-fill price when product is selected
    if (field === 'product_id' && value) {
      const product = products?.find(p => p.id === parseInt(value))
      if (product) {
        newLines[index].description = product.name
        newLines[index].unit_price = product.cost_price.toString()
      }
    }

    setLines(newLines)
  }

  const removeLine = (index: number) => {
    if (lines.length > 1) {
      setLines(lines.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)

    const billLines = lines
      .filter(line => line.description && parseFloat(line.quantity) > 0)
      .map(line => ({
        product_id: line.product_id ? parseInt(line.product_id) : null,
        description: line.description,
        quantity: parseFloat(line.quantity),
        unit_price: parseFloat(line.unit_price),
      }))

    mutation.mutate({
      vendor_id: parseInt(vendorId),
      bill_number: formData.get('bill_number'),
      bill_date: formData.get('bill_date'),
      due_date: formData.get('due_date'),
      notes: formData.get('notes') || null,
      currency_code: 'USD',
      lines: billLines,
    })
  }

  const subtotal = lines.reduce(
    (sum, line) => sum + (parseFloat(line.quantity) || 0) * (parseFloat(line.unit_price) || 0),
    0
  )

  // Calculate due date based on vendor payment terms
  const getDefaultDueDate = () => {
    const vendor = vendors?.find(v => v.id === parseInt(vendorId))
    const days = vendor?.payment_terms || 30
    const dueDate = new Date()
    dueDate.setDate(dueDate.getDate() + days)
    return dueDate.toISOString().split('T')[0]
  }

  return (
    <div>
      <PageHeader
        title="New Bill"
        description="Create a new vendor bill/purchase invoice"
      />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="vendor_id">Vendor</Label>
                <select
                  id="vendor_id"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value)}
                  required
                >
                  <option value="">Select vendor...</option>
                  {vendors?.map((vendor) => (
                    <option key={vendor.id} value={vendor.id}>
                      {vendor.code} - {vendor.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="bill_number">Vendor Bill Number</Label>
                <Input
                  id="bill_number"
                  name="bill_number"
                  placeholder="Vendor's invoice number"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="bill_date">Bill Date</Label>
                <Input
                  id="bill_date"
                  name="bill_date"
                  type="date"
                  defaultValue={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="due_date">Due Date</Label>
                <Input
                  id="due_date"
                  name="due_date"
                  type="date"
                  defaultValue={getDefaultDueDate()}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Bill Lines</Label>
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Product</th>
                    <th className="text-left p-2">Description</th>
                    <th className="text-right p-2 w-24">Quantity</th>
                    <th className="text-right p-2 w-32">Unit Price</th>
                    <th className="text-right p-2 w-32">Amount</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, index) => (
                    <tr key={index} className="border-b">
                      <td className="p-2">
                        <select
                          className="w-full rounded-md border px-2 py-1"
                          value={line.product_id}
                          onChange={(e) => updateLine(index, 'product_id', e.target.value)}
                        >
                          <option value="">Select...</option>
                          {products?.map((product) => (
                            <option key={product.id} value={product.id}>
                              {product.code} - {product.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="p-2">
                        <Input
                          value={line.description}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                          placeholder="Description"
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="1"
                          min="1"
                          className="text-right"
                          value={line.quantity}
                          onChange={(e) => updateLine(index, 'quantity', e.target.value)}
                        />
                      </td>
                      <td className="p-2">
                        <Input
                          type="number"
                          step="0.01"
                          className="text-right"
                          value={line.unit_price}
                          onChange={(e) => updateLine(index, 'unit_price', e.target.value)}
                        />
                      </td>
                      <td className="p-2 text-right">
                        {((parseFloat(line.quantity) || 0) * (parseFloat(line.unit_price) || 0)).toFixed(2)}
                      </td>
                      <td className="p-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeLine(index)}
                          disabled={lines.length <= 1}
                        >
                          X
                        </Button>
                      </td>
                    </tr>
                  ))}
                  <tr className="font-semibold">
                    <td colSpan={4} className="p-2 text-right">Subtotal:</td>
                    <td className="p-2 text-right">{subtotal.toFixed(2)}</td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                + Add Line
              </Button>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Input id="notes" name="notes" placeholder="Optional notes" />
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending || !vendorId}>
                {mutation.isPending ? 'Creating...' : 'Create Bill'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
