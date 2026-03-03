'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { warehousesApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

export default function NewWarehousePage() {
  const router = useRouter()
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (data: any) => warehousesApi.create(data),
    onSuccess: () => {
      router.push('/inventory/warehouses')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create warehouse')
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      code: formData.get('code'),
      name: formData.get('name'),
      address: formData.get('address') || null,
      city: formData.get('city') || null,
      state: formData.get('state') || null,
      postal_code: formData.get('postal_code') || null,
      country: formData.get('country') || null,
      phone: formData.get('phone') || null,
      is_default: formData.get('is_default') === 'on',
      is_active: true,
    })
  }

  return (
    <div>
      <PageHeader
        title="New Warehouse"
        description="Add a new stock location"
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
                <Label htmlFor="code">Warehouse Code</Label>
                <Input id="code" name="code" placeholder="WH-001" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Warehouse Name</Label>
                <Input id="name" name="name" placeholder="Main Warehouse" required />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input id="address" name="address" placeholder="123 Warehouse Lane" />
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Input id="city" name="city" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="state">State</Label>
                <Input id="state" name="state" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="postal_code">Postal Code</Label>
                <Input id="postal_code" name="postal_code" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">Country</Label>
                <Input id="country" name="country" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" name="phone" placeholder="+1 234 567 8900" />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_default"
                name="is_default"
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="is_default" className="text-sm font-normal">
                Set as default warehouse
              </Label>
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Creating...' : 'Create Warehouse'}
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
