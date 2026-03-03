'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Download, FileText, DollarSign, TrendingUp, TrendingDown, Calendar } from 'lucide-react'

type ReportType = 'trial-balance' | 'balance-sheet' | 'income-statement' | 'ar-aging' | 'ap-aging' | 'general-ledger' | 'cash-flow'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<ReportType>('trial-balance')
  const [dateFilters, setDateFilters] = useState({
    start_date: '',
    end_date: new Date().toISOString().split('T')[0],
  })

  const { data: reportData, isLoading } = useQuery({
    queryKey: ['report', selectedReport, dateFilters],
    queryFn: async () => {
      switch (selectedReport) {
        case 'trial-balance':
          return (await reportsApi.trialBalance()).data
        case 'balance-sheet':
          return (await reportsApi.balanceSheet()).data
        case 'income-statement':
          return (await reportsApi.incomeStatement(dateFilters.start_date, dateFilters.end_date)).data
        case 'ar-aging':
          return (await reportsApi.arAging()).data
        case 'ap-aging':
          return (await reportsApi.apAging()).data
        case 'general-ledger':
          return (await reportsApi.generalLedger({ start_date: dateFilters.start_date, end_date: dateFilters.end_date })).data
        case 'cash-flow':
          return (await reportsApi.cashFlow(dateFilters.start_date, dateFilters.end_date)).data
        default:
          return null
      }
    },
  })

  const reports = [
    { id: 'trial-balance', name: 'Trial Balance', icon: FileText },
    { id: 'balance-sheet', name: 'Balance Sheet', icon: DollarSign },
    { id: 'income-statement', name: 'Income Statement', icon: TrendingUp },
    { id: 'ar-aging', name: 'AR Aging', icon: TrendingUp },
    { id: 'ap-aging', name: 'AP Aging', icon: TrendingDown },
    { id: 'general-ledger', name: 'General Ledger', icon: FileText },
    { id: 'cash-flow', name: 'Cash Flow', icon: DollarSign },
  ]

  const handleExport = async () => {
    const token = localStorage.getItem('auth_token')
    let url = `${API_URL}/api/v1/reports/export/${selectedReport}`

    const params = new URLSearchParams()
    if (dateFilters.start_date) params.append('start_date', dateFilters.start_date)
    if (dateFilters.end_date) params.append('end_date', dateFilters.end_date)

    if (params.toString()) {
      url += `?${params.toString()}`
    }

    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `${selectedReport}_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Export error:', error)
    }
  }

  const renderTrialBalance = (data: any) => (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Account</th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Debit</th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Credit</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {data.accounts?.map((account: any) => (
            <tr key={account.account_id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm">
                <span className="text-gray-500 mr-2">{account.account_code}</span>
                {account.account_name}
              </td>
              <td className="px-4 py-3 text-sm text-right">
                {account.debit ? formatCurrency(account.debit) : ''}
              </td>
              <td className="px-4 py-3 text-sm text-right">
                {account.credit ? formatCurrency(account.credit) : ''}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-gray-50 font-bold">
          <tr>
            <td className="px-4 py-3 text-sm">Total</td>
            <td className="px-4 py-3 text-sm text-right">{formatCurrency(data.total_debits || data.total_debit)}</td>
            <td className="px-4 py-3 text-sm text-right">{formatCurrency(data.total_credits || data.total_credit)}</td>
          </tr>
        </tfoot>
      </table>
      <div className="mt-4 text-center">
        <Badge variant={data.is_balanced ? 'default' : 'destructive'}>
          {data.is_balanced ? 'Balanced' : 'Out of Balance'}
        </Badge>
      </div>
    </div>
  )

  const renderBalanceSheet = (data: any) => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Badge variant="outline">Assets</Badge>
        </h3>
        {data.assets?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm hover:bg-gray-50 px-2 rounded">
            <span className="text-gray-700">{account.account_code} - {account.account_name}</span>
            <span className="font-medium">{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2 bg-green-50 px-2 rounded">
          <span>Total Assets</span>
          <span className="text-green-600">{formatCurrency(data.assets?.total)}</span>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Badge variant="outline">Liabilities</Badge>
        </h3>
        {data.liabilities?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm hover:bg-gray-50 px-2 rounded">
            <span className="text-gray-700">{account.account_code} - {account.account_name}</span>
            <span className="font-medium">{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2 bg-red-50 px-2 rounded">
          <span>Total Liabilities</span>
          <span className="text-red-600">{formatCurrency(data.liabilities?.total)}</span>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Badge variant="outline">Equity</Badge>
        </h3>
        {data.equity?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm hover:bg-gray-50 px-2 rounded">
            <span className="text-gray-700">{account.account_code} - {account.account_name}</span>
            <span className="font-medium">{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2 bg-blue-50 px-2 rounded">
          <span>Total Equity</span>
          <span className="text-blue-600">{formatCurrency(data.equity?.total)}</span>
        </div>
      </div>

      <div className="border-t-2 pt-4">
        <div className="flex justify-between font-bold text-lg bg-gray-100 p-3 rounded">
          <span>Total Liabilities & Equity</span>
          <span>{formatCurrency(data.total_liabilities_and_equity)}</span>
        </div>
      </div>
    </div>
  )

  const renderIncomeStatement = (data: any) => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Badge className="bg-green-100 text-green-800">Revenue</Badge>
        </h3>
        {data.revenue?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm hover:bg-gray-50 px-2 rounded">
            <span className="text-gray-700">{account.account_code} - {account.account_name}</span>
            <span className="font-medium text-green-600">{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2 bg-green-50 px-2 rounded">
          <span>Total Revenue</span>
          <span className="text-green-600">{formatCurrency(data.revenue?.total)}</span>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Badge className="bg-red-100 text-red-800">Expenses</Badge>
        </h3>
        {data.expenses?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm hover:bg-gray-50 px-2 rounded">
            <span className="text-gray-700">{account.account_code} - {account.account_name}</span>
            <span className="font-medium text-red-600">{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2 bg-red-50 px-2 rounded">
          <span>Total Expenses</span>
          <span className="text-red-600">{formatCurrency(data.expenses?.total)}</span>
        </div>
      </div>

      <div className="border-t-2 pt-4">
        <div className={`flex justify-between font-bold text-lg p-3 rounded ${data.net_income >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
          <span>Net Income</span>
          <span className={data.net_income >= 0 ? 'text-green-600' : 'text-red-600'}>
            {formatCurrency(data.net_income)}
          </span>
        </div>
      </div>
    </div>
  )

  const renderAgingReport = (data: any, type: 'ar' | 'ap') => {
    const bucketLabels: Record<string, string> = {
      current: 'Current',
      '1_30': '1-30 Days',
      '31_60': '31-60 Days',
      '61_90': '61-90 Days',
      over_90: 'Over 90 Days',
    }

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-5 gap-4">
          {Object.entries(bucketLabels).map(([key, label]) => (
            <Card key={key}>
              <CardContent className="pt-4">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-lg font-bold">{formatCurrency(data.totals?.[key] || 0)}</p>
                <p className="text-xs text-muted-foreground">
                  {data.buckets?.[key]?.length || 0} items
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Detail Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                  {type === 'ar' ? 'Invoice' : 'Bill'} #
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                  {type === 'ar' ? 'Customer' : 'Vendor'}
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Due Date</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Balance</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Days</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(data.buckets || {}).flatMap(([bucket, items]: [string, any]) =>
                items.map((item: any) => (
                  <tr key={item[type === 'ar' ? 'invoice_id' : 'bill_id']} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">
                      {item[type === 'ar' ? 'invoice_number' : 'bill_number']}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {item[type === 'ar' ? 'customer_name' : 'vendor_name']}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {new Date(item.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      {formatCurrency(item.balance_due)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      {item.days_overdue}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge
                        variant={
                          bucket === 'current' ? 'outline' :
                          bucket === 'over_90' ? 'destructive' : 'secondary'
                        }
                      >
                        {bucketLabels[bucket]}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            <tfoot className="bg-gray-50 font-bold">
              <tr>
                <td className="px-4 py-3 text-sm" colSpan={3}>Total</td>
                <td className="px-4 py-3 text-sm text-right">{formatCurrency(data.totals?.total)}</td>
                <td colSpan={2}></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    )
  }

  const renderGeneralLedger = (data: any) => (
    <div className="space-y-6">
      {data.accounts?.map((account: any) => (
        <Card key={account.account_id}>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span>{account.account_code} - {account.account_name}</span>
              <span className="text-sm font-normal text-muted-foreground">
                Net: {formatCurrency(account.net_change)}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 text-left">Date</th>
                  <th className="px-2 py-1 text-left">Entry #</th>
                  <th className="px-2 py-1 text-left">Description</th>
                  <th className="px-2 py-1 text-right">Debit</th>
                  <th className="px-2 py-1 text-right">Credit</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {account.transactions?.slice(0, 10).map((tx: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-2 py-1">{tx.entry_date}</td>
                    <td className="px-2 py-1">{tx.entry_number}</td>
                    <td className="px-2 py-1">{tx.description}</td>
                    <td className="px-2 py-1 text-right">{tx.debit ? formatCurrency(tx.debit) : ''}</td>
                    <td className="px-2 py-1 text-right">{tx.credit ? formatCurrency(tx.credit) : ''}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 font-bold">
                <tr>
                  <td colSpan={3} className="px-2 py-1">Total</td>
                  <td className="px-2 py-1 text-right">{formatCurrency(account.total_debits)}</td>
                  <td className="px-2 py-1 text-right">{formatCurrency(account.total_credits)}</td>
                </tr>
              </tfoot>
            </table>
          </CardContent>
        </Card>
      ))}
    </div>
  )

  const renderCashFlow = (data: any) => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Operating Activities</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between py-1">
            <span>Net Income</span>
            <span className="font-medium">{formatCurrency(data.operating_activities?.net_income)}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Customer Payments Received</span>
            <span className="font-medium text-green-600">
              {formatCurrency(data.operating_activities?.customer_payments_received)}
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span>Vendor Payments Made</span>
            <span className="font-medium text-red-600">
              {formatCurrency(data.operating_activities?.vendor_payments_made)}
            </span>
          </div>
          <div className="flex justify-between py-2 font-bold border-t mt-2">
            <span>Net Cash from Operations</span>
            <span>{formatCurrency(data.operating_activities?.net_cash_from_operations)}</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Investing Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between py-2 font-bold">
              <span>Net Cash from Investing</span>
              <span>{formatCurrency(data.investing_activities?.net_cash_from_investing)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Financing Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between py-2 font-bold">
              <span>Net Cash from Financing</span>
              <span>{formatCurrency(data.financing_activities?.net_cash_from_financing)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-gray-50">
        <CardHeader>
          <CardTitle className="text-base">Cash Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between py-1">
            <span>Beginning Cash Balance</span>
            <span className="font-medium">{formatCurrency(data.summary?.beginning_cash_balance)}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Net Increase in Cash</span>
            <span className={`font-medium ${data.summary?.net_increase_in_cash >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(data.summary?.net_increase_in_cash)}
            </span>
          </div>
          <div className="flex justify-between py-2 font-bold border-t mt-2 text-lg">
            <span>Ending Cash Balance</span>
            <span>{formatCurrency(data.summary?.ending_cash_balance)}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderReport = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      )
    }

    if (!reportData) return null

    switch (selectedReport) {
      case 'trial-balance':
        return renderTrialBalance(reportData)
      case 'balance-sheet':
        return renderBalanceSheet(reportData)
      case 'income-statement':
        return renderIncomeStatement(reportData)
      case 'ar-aging':
        return renderAgingReport(reportData, 'ar')
      case 'ap-aging':
        return renderAgingReport(reportData, 'ap')
      case 'general-ledger':
        return renderGeneralLedger(reportData)
      case 'cash-flow':
        return renderCashFlow(reportData)
      default:
        return <pre className="text-sm">{JSON.stringify(reportData, null, 2)}</pre>
    }
  }

  const needsDateFilter = ['income-statement', 'general-ledger', 'cash-flow'].includes(selectedReport)

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Financial reports and analytics"
      />

      <div className="mb-6 flex gap-2 flex-wrap">
        {reports.map((report) => {
          const Icon = report.icon
          return (
            <Button
              key={report.id}
              variant={selectedReport === report.id ? 'default' : 'outline'}
              onClick={() => setSelectedReport(report.id as ReportType)}
              className="gap-2"
            >
              <Icon className="h-4 w-4" />
              {report.name}
            </Button>
          )
        })}
      </div>

      {/* Date Filters */}
      {needsDateFilter && (
        <Card className="mb-6">
          <CardContent className="pt-4">
            <div className="flex items-end gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Start Date
                </Label>
                <Input
                  type="date"
                  value={dateFilters.start_date}
                  onChange={(e) => setDateFilters({ ...dateFilters, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={dateFilters.end_date}
                  onChange={(e) => setDateFilters({ ...dateFilters, end_date: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{reports.find((r) => r.id === selectedReport)?.name}</CardTitle>
          <Button variant="outline" onClick={handleExport} className="gap-2">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </CardHeader>
        <CardContent>{renderReport()}</CardContent>
      </Card>
    </div>
  )
}
