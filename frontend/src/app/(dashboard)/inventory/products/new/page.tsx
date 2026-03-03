'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { productsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

const productTypes = [
  { value: 'inventory', label: 'Inventory Item' },
  { value: 'non_inventory', label: 'Non-Inventory Item' },
  { value: 'service', label: 'Service' },
]

const unitsOfMeasure = [
  'Each',
  'Piece',
  'Box',
  'Case',
  'Dozen',
  'Pack',
  'Kg',
  'Lb',
  'Liter',
  'Gallon',
  'Meter',
  'Foot',
  'Hour',
]

export default function NewProductPage() {
  const router = useRouter()
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (data: any) => productsApi.create(data),
    onSuccess: () => {
      router.push('/inventory/products')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create product')
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      code: formData.get('code'),
      name: formData.get('name'),
      product_type: formData.get('product_type'),
      category: formData.get('category') || null,
      description: formData.get('description') || null,
      unit_of_measure: formData.get('unit_of_measure'),
      purchase_price: parseFloat(formData.get('purchase_price') as string) || 0,
      selling_price: parseFloat(formData.get('selling_price') as string) || 0,
      reorder_point: parseInt(formData.get('reorder_point') as string) || 0,
      reorder_quantity: parseInt(formData.get('reorder_quantity') as string) || 0,
      is_active: true,
    })
  }

  return (
    <div>
      <PageHeader
        title="New Product"
        description="Add a new product to the catalog"
      />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="code">Product Code</Label>
                <Input id="code" name="code" placeholder="PROD-001" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Product Name</Label>
                <Input id="name" name="name" placeholder="Widget" required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="product_type">Product Type</Label>
                <select
                  id="product_type"
                  name="product_type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  required
                >
                  {productTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Input id="category" name="category" placeholder="Electronics" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" placeholder="Product description" />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="unit_of_measure">Unit of Measure</Label>
                <select
                  id="unit_of_measure"
                  name="unit_of_measure"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  required
                >
                  {unitsOfMeasure.map((uom) => (
                    <option key={uom} value={uom}>
                      {uom}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="purchase_price">Purchase Price</Label>
                <Input
                  id="purchase_price"
                  name="purchase_price"
                  type="number"
                  step="0.01"
                  defaultValue="0"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="selling_price">Selling Price</Label>
                <Input
                  id="selling_price"
                  name="selling_price"
                  type="number"
                  step="0.01"
                  defaultValue="0"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="reorder_point">Reorder Point</Label>
                <Input
                  id="reorder_point"
                  name="reorder_point"
                  type="number"
                  defaultValue="0"
                  placeholder="Minimum stock level"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reorder_quantity">Reorder Quantity</Label>
                <Input
                  id="reorder_quantity"
                  name="reorder_quantity"
                  type="number"
                  defaultValue="0"
                  placeholder="Quantity to reorder"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Creating...' : 'Create Product'}
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
