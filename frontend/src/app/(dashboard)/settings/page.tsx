'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companyApi, usersApi, authApi, currenciesApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/shared/DataTable'
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
import { Building2, Users, Mail, Globe, Pencil, UserPlus, Shield } from 'lucide-react'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('4')
  const [isCompanyDialogOpen, setIsCompanyDialogOpen] = useState(false)
  const [companyForm, setCompanyForm] = useState({
    company_name: '',
    legal_name: '',
    tax_id: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    phone: '',
    email: '',
    website: '',
    fiscal_year_start_month: '1',
    fiscal_year_start_day: '1',
    base_currency_code: 'USD',
  })

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

  const { data: currencies } = useQuery({
    queryKey: ['currencies'],
    queryFn: async () => {
      const response = await currenciesApi.list()
      return response.data
    },
  })

  const { data: users, isLoading: usersLoading } = useQuery({
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

  const updateCompanyMutation = useMutation({
    mutationFn: async (data: typeof companyForm) => {
      if (company) {
        return companyApi.update(data)
      } else {
        return companyApi.create(data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company'] })
      setIsCompanyDialogOpen(false)
    },
  })

  const inviteMutation = useMutation({
    mutationFn: async () => {
      await authApi.invite(inviteEmail, parseInt(inviteRole))
    },
    onSuccess: () => {
      setInviteEmail('')
      queryClient.invalidateQueries({ queryKey: ['invites'] })
    },
  })

  const toggleUserStatusMutation = useMutation({
    mutationFn: async ({ userId, isActive }: { userId: number; isActive: boolean }) => {
      return usersApi.update(userId, { is_active: !isActive })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const openCompanyDialog = () => {
    if (company) {
      setCompanyForm({
        company_name: company.company_name || '',
        legal_name: company.legal_name || '',
        tax_id: company.tax_id || '',
        address_line1: company.address_line1 || '',
        address_line2: company.address_line2 || '',
        city: company.city || '',
        state: company.state || '',
        postal_code: company.postal_code || '',
        country: company.country || '',
        phone: company.phone || '',
        email: company.email || '',
        website: company.website || '',
        fiscal_year_start_month: String(company.fiscal_year_start_month || 1),
        fiscal_year_start_day: String(company.fiscal_year_start_day || 1),
        base_currency_code: company.base_currency_code || 'USD',
      })
    }
    setIsCompanyDialogOpen(true)
  }

  const handleCompanySubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateCompanyMutation.mutate({
      ...companyForm,
      fiscal_year_start_month: companyForm.fiscal_year_start_month,
      fiscal_year_start_day: companyForm.fiscal_year_start_day,
    })
  }

  const userColumns = [
    {
      key: 'name',
      label: 'Name',
      render: (_: any, row: any) => (
        <div>
          <p className="font-medium">{row.first_name} {row.last_name}</p>
          <p className="text-sm text-muted-foreground">{row.email}</p>
        </div>
      ),
    },
    {
      key: 'roles',
      label: 'Role',
      render: (_: any, row: any) => (
        <div className="flex gap-1">
          {row.roles?.map((r: any) => (
            <Badge key={r.id} variant="outline">{r.name}</Badge>
          )) || <span className="text-muted-foreground">-</span>}
        </div>
      ),
    },
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
      key: 'created_at',
      label: 'Joined',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'actions',
      label: '',
      render: (_: any, row: any) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => toggleUserStatusMutation.mutate({ userId: row.id, isActive: row.is_active })}
        >
          {row.is_active ? 'Deactivate' : 'Activate'}
        </Button>
      ),
    },
  ]

  const months = [
    { value: '1', label: 'January' },
    { value: '2', label: 'February' },
    { value: '3', label: 'March' },
    { value: '4', label: 'April' },
    { value: '5', label: 'May' },
    { value: '6', label: 'June' },
    { value: '7', label: 'July' },
    { value: '8', label: 'August' },
    { value: '9', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' },
  ]

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Manage company and system settings"
      />

      <Tabs defaultValue="company" className="space-y-6">
        <TabsList>
          <TabsTrigger value="company">
            <Building2 className="h-4 w-4 mr-2" />
            Company
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="h-4 w-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
        </TabsList>

        {/* Company Settings Tab */}
        <TabsContent value="company">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Company Info Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Company Information</CardTitle>
                  <CardDescription>Basic company details</CardDescription>
                </div>
                <Dialog open={isCompanyDialogOpen} onOpenChange={setIsCompanyDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" onClick={openCompanyDialog}>
                      <Pencil className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
                    <DialogHeader>
                      <DialogTitle>
                        {company ? 'Edit Company Settings' : 'Setup Company'}
                      </DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCompanySubmit} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Company Name *</Label>
                          <Input
                            required
                            value={companyForm.company_name}
                            onChange={(e) => setCompanyForm({ ...companyForm, company_name: e.target.value })}
                            placeholder="Acme Corporation"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Legal Name</Label>
                          <Input
                            value={companyForm.legal_name}
                            onChange={(e) => setCompanyForm({ ...companyForm, legal_name: e.target.value })}
                            placeholder="Acme Corporation Inc."
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Tax ID</Label>
                          <Input
                            value={companyForm.tax_id}
                            onChange={(e) => setCompanyForm({ ...companyForm, tax_id: e.target.value })}
                            placeholder="12-3456789"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Base Currency</Label>
                          <Select
                            value={companyForm.base_currency_code}
                            onValueChange={(v) => setCompanyForm({ ...companyForm, base_currency_code: v })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {currencies?.map((c: any) => (
                                <SelectItem key={c.code} value={c.code}>
                                  {c.code} - {c.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Address Line 1</Label>
                        <Input
                          value={companyForm.address_line1}
                          onChange={(e) => setCompanyForm({ ...companyForm, address_line1: e.target.value })}
                          placeholder="123 Main Street"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Address Line 2</Label>
                        <Input
                          value={companyForm.address_line2}
                          onChange={(e) => setCompanyForm({ ...companyForm, address_line2: e.target.value })}
                          placeholder="Suite 100"
                        />
                      </div>

                      <div className="grid grid-cols-4 gap-4">
                        <div className="space-y-2">
                          <Label>City</Label>
                          <Input
                            value={companyForm.city}
                            onChange={(e) => setCompanyForm({ ...companyForm, city: e.target.value })}
                            placeholder="New York"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>State</Label>
                          <Input
                            value={companyForm.state}
                            onChange={(e) => setCompanyForm({ ...companyForm, state: e.target.value })}
                            placeholder="NY"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Postal Code</Label>
                          <Input
                            value={companyForm.postal_code}
                            onChange={(e) => setCompanyForm({ ...companyForm, postal_code: e.target.value })}
                            placeholder="10001"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Country</Label>
                          <Input
                            value={companyForm.country}
                            onChange={(e) => setCompanyForm({ ...companyForm, country: e.target.value })}
                            placeholder="USA"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Phone</Label>
                          <Input
                            value={companyForm.phone}
                            onChange={(e) => setCompanyForm({ ...companyForm, phone: e.target.value })}
                            placeholder="+1 (555) 123-4567"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Email</Label>
                          <Input
                            type="email"
                            value={companyForm.email}
                            onChange={(e) => setCompanyForm({ ...companyForm, email: e.target.value })}
                            placeholder="info@acme.com"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Website</Label>
                        <Input
                          value={companyForm.website}
                          onChange={(e) => setCompanyForm({ ...companyForm, website: e.target.value })}
                          placeholder="https://www.acme.com"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Fiscal Year Start Month</Label>
                          <Select
                            value={companyForm.fiscal_year_start_month}
                            onValueChange={(v) => setCompanyForm({ ...companyForm, fiscal_year_start_month: v })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {months.map((m) => (
                                <SelectItem key={m.value} value={m.value}>
                                  {m.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Fiscal Year Start Day</Label>
                          <Input
                            type="number"
                            min="1"
                            max="31"
                            value={companyForm.fiscal_year_start_day}
                            onChange={(e) => setCompanyForm({ ...companyForm, fiscal_year_start_day: e.target.value })}
                          />
                        </div>
                      </div>

                      <div className="flex justify-end gap-2 pt-4">
                        <Button type="button" variant="outline" onClick={() => setIsCompanyDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button type="submit" disabled={updateCompanyMutation.isPending}>
                          {updateCompanyMutation.isPending ? 'Saving...' : 'Save Changes'}
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {company ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Building2 className="h-10 w-10 text-muted-foreground" />
                      <div>
                        <p className="font-semibold text-lg">{company.company_name}</p>
                        {company.legal_name && (
                          <p className="text-sm text-muted-foreground">{company.legal_name}</p>
                        )}
                      </div>
                    </div>
                    {company.tax_id && (
                      <div>
                        <Label className="text-muted-foreground">Tax ID</Label>
                        <p>{company.tax_id}</p>
                      </div>
                    )}
                    {(company.address_line1 || company.city) && (
                      <div>
                        <Label className="text-muted-foreground">Address</Label>
                        <p>{company.address_line1}</p>
                        {company.address_line2 && <p>{company.address_line2}</p>}
                        <p>
                          {[company.city, company.state, company.postal_code]
                            .filter(Boolean)
                            .join(', ')}
                        </p>
                        {company.country && <p>{company.country}</p>}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">Company settings not configured</p>
                    <Button onClick={openCompanyDialog}>Setup Company</Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Contact & Fiscal Info Card */}
            <Card>
              <CardHeader>
                <CardTitle>Contact & Fiscal Settings</CardTitle>
                <CardDescription>Contact info and accounting periods</CardDescription>
              </CardHeader>
              <CardContent>
                {company ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-muted-foreground">Phone</Label>
                        <p>{company.phone || '-'}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Email</Label>
                        <p>{company.email || '-'}</p>
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Website</Label>
                      <p>{company.website || '-'}</p>
                    </div>
                    <hr />
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-muted-foreground">Base Currency</Label>
                        <p className="font-medium">{company.base_currency_code}</p>
                      </div>
                      <div>
                        <Label className="text-muted-foreground">Fiscal Year Start</Label>
                        <p className="font-medium">
                          {months.find(m => m.value === String(company.fiscal_year_start_month))?.label} {company.fiscal_year_start_day}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Configure company settings to view details
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users">
          <div className="space-y-6">
            {/* Invite User Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="h-5 w-5" />
                  Invite User
                </CardTitle>
                <CardDescription>
                  Send an invitation to add a new user to the system
                </CardDescription>
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
                  <Select value={inviteRole} onValueChange={setInviteRole}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles?.map((role: any) => (
                        <SelectItem key={role.id} value={String(role.id)}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={() => inviteMutation.mutate()}
                    disabled={!inviteEmail || inviteMutation.isPending}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Pending Invites */}
            {invites && invites.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Pending Invites</CardTitle>
                  <CardDescription>{invites.length} pending invitation(s)</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {invites.map((invite: any) => (
                      <div
                        key={invite.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Mail className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{invite.email}</p>
                            <p className="text-sm text-muted-foreground">
                              Role: {invite.role?.name || 'Unknown'} |
                              Sent: {new Date(invite.created_at).toLocaleDateString()}
                            </p>
                          </div>
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

            {/* Users List */}
            <Card>
              <CardHeader>
                <CardTitle>All Users</CardTitle>
                <CardDescription>
                  {users?.length || 0} registered user(s)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DataTable
                  columns={userColumns}
                  data={users || []}
                  isLoading={usersLoading}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Roles & Permissions</CardTitle>
                <CardDescription>System roles and their access levels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {roles?.map((role: any) => (
                    <div key={role.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{role.name}</p>
                        <p className="text-sm text-muted-foreground">{role.description}</p>
                      </div>
                      <Badge variant="outline">Level {role.id}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>Account and access settings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Invite-Only Registration</p>
                      <p className="text-sm text-muted-foreground">
                        Only invited users can create accounts
                      </p>
                    </div>
                    <Badge variant="default">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Session Timeout</p>
                      <p className="text-sm text-muted-foreground">
                        Automatic logout after inactivity
                      </p>
                    </div>
                    <Badge variant="outline">30 days</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Audit Logging</p>
                      <p className="text-sm text-muted-foreground">
                        Track all system changes
                      </p>
                    </div>
                    <Badge variant="default">Enabled</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
