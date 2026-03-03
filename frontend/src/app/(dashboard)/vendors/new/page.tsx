'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { vendorsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

export default function NewVendorPage() {
  const router = useRouter()
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (data: any) => vendorsApi.create(data),
    onSuccess: () => {
      router.push('/vendors')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create vendor')
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      code: formData.get('code'),
      name: formData.get('name'),
      email: formData.get('email') || null,
      phone: formData.get('phone') || null,
      address_line1: formData.get('address') || null,
      city: formData.get('city') || null,
      state: formData.get('state') || null,
      postal_code: formData.get('postal_code') || null,
      country: formData.get('country') || null,
      tax_id: formData.get('tax_id') || null,
      payment_terms_days: parseInt(formData.get('payment_terms') as string) || 30,
    })
  }

  return (
    <div>
      <PageHeader
        title="New Vendor"
        description="Add a new vendor/supplier"
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
                <Label htmlFor="code">Vendor Code</Label>
                <Input id="code" name="code" placeholder="VEND-001" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Vendor Name</Label>
                <Input id="name" name="name" placeholder="Supplier Inc" required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" name="email" type="email" placeholder="contact@supplier.com" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" name="phone" placeholder="+1 234 567 8900" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input id="address" name="address" placeholder="456 Vendor St" />
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

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tax_id">Tax ID</Label>
                <Input id="tax_id" name="tax_id" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="payment_terms">Payment Terms (days)</Label>
                <Input id="payment_terms" name="payment_terms" type="number" defaultValue="30" />
              </div>
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Creating...' : 'Create Vendor'}
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
