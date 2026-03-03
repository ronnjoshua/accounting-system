'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, authApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { Plus, UserPlus, Mail, Trash2 } from 'lucide-react'

export default function UserManagementPage() {
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false)
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(),
  })

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: () => usersApi.listRoles(),
  })

  const { data: invites, isLoading: invitesLoading } = useQuery({
    queryKey: ['invites'],
    queryFn: () => usersApi.listInvites(),
  })

  const inviteMutation = useMutation({
    mutationFn: (data: { email: string; role_id: number }) =>
      authApi.invite(data.email, data.role_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invites'] })
      setIsInviteDialogOpen(false)
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to send invite')
    },
  })

  const revokeInviteMutation = useMutation({
    mutationFn: (id: number) => usersApi.revokeInvite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invites'] })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => usersApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const handleInvite = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    inviteMutation.mutate({
      email: formData.get('email') as string,
      role_id: parseInt(formData.get('role_id') as string),
    })
  }

  const userColumns = [
    { key: 'email', label: 'Email' },
    { key: 'first_name', label: 'First Name' },
    { key: 'last_name', label: 'Last Name' },
    {
      key: 'is_active',
      label: 'Status',
      render: (v: boolean) => (
        <Badge variant={v ? 'default' : 'secondary'}>
          {v ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'is_superuser',
      label: 'Role',
      render: (v: boolean) => (
        <Badge variant={v ? 'destructive' : 'outline'}>
          {v ? 'Admin' : 'User'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_: any, row: any) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (confirm('Are you sure you want to deactivate this user?')) {
              deactivateMutation.mutate(row.id)
            }
          }}
          disabled={row.is_superuser}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      ),
    },
  ]

  const inviteColumns = [
    { key: 'email', label: 'Email' },
    {
      key: 'is_accepted',
      label: 'Status',
      render: (v: boolean) => (
        <Badge variant={v ? 'default' : 'secondary'}>
          {v ? 'Accepted' : 'Pending'}
        </Badge>
      ),
    },
    {
      key: 'expires_at',
      label: 'Expires',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_: any, row: any) =>
        !row.is_accepted && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => revokeInviteMutation.mutate(row.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="User Management"
        description="Manage users and invitations"
        action={
          <Dialog open={isInviteDialogOpen} onOpenChange={setIsInviteDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="mr-2 h-4 w-4" />
                Invite User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite New User</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleInvite} className="space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <Input type="email" name="email" required placeholder="user@example.com" />
                </div>

                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select name="role_id" required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles?.data?.map((role: any) => (
                        <SelectItem key={role.id} value={role.id.toString()}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsInviteDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={inviteMutation.isPending}>
                    <Mail className="mr-2 h-4 w-4" />
                    {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="invites">Pending Invites</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={userColumns}
                data={users?.data || []}
                isLoading={usersLoading}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invites">
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={inviteColumns}
                data={invites?.data || []}
                isLoading={invitesLoading}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
