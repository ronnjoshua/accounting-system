'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companyApi, usersApi, authApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DataTable } from '@/components/shared/DataTable'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState(4) // Default to viewer

  const { data: company } = useQuery({
    queryKey: ['company'],
    queryFn: async () => {
      try {
        const response = await companyApi.get()
        return response.data
      } catch {
        return null
      }
    },
  })

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await usersApi.list()
      return response.data
    },
  })

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: async () => {
      const response = await usersApi.listRoles()
      return response.data
    },
  })

  const { data: invites } = useQuery({
    queryKey: ['invites'],
    queryFn: async () => {
      const response = await usersApi.listInvites()
      return response.data
    },
  })

  const inviteMutation = useMutation({
    mutationFn: async () => {
      await authApi.invite(inviteEmail, inviteRole)
    },
    onSuccess: () => {
      setInviteEmail('')
      queryClient.invalidateQueries({ queryKey: ['invites'] })
    },
  })

  const userColumns = [
    { header: 'Name', accessor: (row: any) => `${row.first_name} ${row.last_name}` },
    { header: 'Email', accessor: 'email' as const },
    {
      header: 'Role',
      accessor: (row: any) => row.roles?.map((r: any) => r.name).join(', ') || '-',
    },
    {
      header: 'Status',
      accessor: (row: any) => (
        <span
          className={`rounded-full px-2 py-1 text-xs ${
            row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Manage company and user settings"
      />

      <div className="space-y-6">
        {/* Company Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Company Settings</CardTitle>
          </CardHeader>
          <CardContent>
            {company ? (
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Company Name</Label>
                  <p className="text-sm text-gray-600">{company.company_name}</p>
                </div>
                <div>
                  <Label>Base Currency</Label>
                  <p className="text-sm text-gray-600">{company.base_currency_code}</p>
                </div>
                <div>
                  <Label>Fiscal Year Start</Label>
                  <p className="text-sm text-gray-600">
                    Month {company.fiscal_year_start_month}, Day {company.fiscal_year_start_day}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Company settings not configured.</p>
            )}
          </CardContent>
        </Card>

        {/* Invite Users */}
        <Card>
          <CardHeader>
            <CardTitle>Invite User</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  type="email"
                  placeholder="Email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
              </div>
              <select
                className="rounded-md border px-3"
                value={inviteRole}
                onChange={(e) => setInviteRole(Number(e.target.value))}
              >
                {roles?.map((role: any) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
              <Button
                onClick={() => inviteMutation.mutate()}
                disabled={!inviteEmail || inviteMutation.isPending}
              >
                {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Users List */}
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={userColumns}
              data={users || []}
              emptyMessage="No users found"
            />
          </CardContent>
        </Card>

        {/* Pending Invites */}
        {invites && invites.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Pending Invites</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {invites.map((invite: any) => (
                  <div
                    key={invite.id}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div>
                      <p className="font-medium">{invite.email}</p>
                      <p className="text-sm text-gray-500">
                        Role: {invite.role.name}
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={async () => {
                        await usersApi.revokeInvite(invite.id)
                        queryClient.invalidateQueries({ queryKey: ['invites'] })
                      }}
                    >
                      Revoke
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
