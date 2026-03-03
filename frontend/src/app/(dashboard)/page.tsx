'use client'

import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  DollarSign,
  CreditCard,
  ArrowDownCircle,
  ArrowUpCircle,
  AlertCircle,
} from 'lucide-react'

export default function DashboardPage() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await reportsApi.dashboard()
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your financial position"
      />

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Accounts Receivable"
          value={formatCurrency(dashboard?.accounts_receivable?.total || 0)}
          description={`${dashboard?.accounts_receivable?.open_invoices || 0} open invoices`}
          icon={ArrowDownCircle}
        />
        <StatCard
          title="Accounts Payable"
          value={formatCurrency(dashboard?.accounts_payable?.total || 0)}
          description={`${dashboard?.accounts_payable?.open_bills || 0} open bills`}
          icon={ArrowUpCircle}
        />
        <StatCard
          title="Net Position"
          value={formatCurrency(dashboard?.net_position || 0)}
          description="AR - AP"
          icon={DollarSign}
        />
        <StatCard
          title="Overdue Items"
          value={
            (dashboard?.accounts_receivable?.overdue_invoices || 0) +
            (dashboard?.accounts_payable?.overdue_bills || 0)
          }
          description="Requires attention"
          icon={AlertCircle}
          className={
            (dashboard?.accounts_receivable?.overdue_invoices || 0) +
              (dashboard?.accounts_payable?.overdue_bills || 0) >
            0
              ? 'border-red-200 bg-red-50'
              : ''
          }
        />
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Receivables Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Outstanding</span>
                <span className="font-medium">
                  {formatCurrency(dashboard?.accounts_receivable?.total || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Open Invoices</span>
                <span className="font-medium">
                  {dashboard?.accounts_receivable?.open_invoices || 0}
                </span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>Overdue</span>
                <span className="font-medium">
                  {dashboard?.accounts_receivable?.overdue_invoices || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Payables Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Outstanding</span>
                <span className="font-medium">
                  {formatCurrency(dashboard?.accounts_payable?.total || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Open Bills</span>
                <span className="font-medium">
                  {dashboard?.accounts_payable?.open_bills || 0}
                </span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>Overdue</span>
                <span className="font-medium">
                  {dashboard?.accounts_payable?.overdue_bills || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <a
                href="/invoices"
                className="block rounded-md bg-primary/10 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/20"
              >
                Create Invoice
              </a>
              <a
                href="/bills"
                className="block rounded-md bg-primary/10 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/20"
              >
                Record Bill
              </a>
              <a
                href="/journal-entries"
                className="block rounded-md bg-primary/10 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/20"
              >
                Journal Entry
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
