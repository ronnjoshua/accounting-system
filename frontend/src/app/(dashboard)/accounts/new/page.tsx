'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'

interface AccountType {
  id: number
  name: string
  category: string
}

export default function NewAccountPage() {
  const router = useRouter()
  const [error, setError] = useState('')

  const { data: accountTypes } = useQuery({
    queryKey: ['account-types'],
    queryFn: async () => {
      const response = await accountsApi.listTypes()
      return response.data as AccountType[]
    },
  })

  const mutation = useMutation({
    mutationFn: (data: any) => accountsApi.create(data),
    onSuccess: () => {
      router.push('/accounts')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create account')
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    mutation.mutate({
      code: formData.get('code'),
      name: formData.get('name'),
      account_type_id: parseInt(formData.get('account_type_id') as string),
      description: formData.get('description') || null,
      is_active: true,
    })
  }

  return (
    <div>
      <PageHeader
        title="New Account"
        description="Create a new chart of accounts entry"
      />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="code">Account Code</Label>
              <Input id="code" name="code" placeholder="1000" required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Account Name</Label>
              <Input id="name" name="name" placeholder="Cash" required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="account_type_id">Account Type</Label>
              <select
                id="account_type_id"
                name="account_type_id"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="">Select type...</option>
                {accountTypes?.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name} ({type.category})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" placeholder="Optional description" />
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Creating...' : 'Create Account'}
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
