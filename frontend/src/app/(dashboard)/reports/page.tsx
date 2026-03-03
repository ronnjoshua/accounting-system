'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

type ReportType = 'trial-balance' | 'balance-sheet' | 'income-statement' | 'ar-aging' | 'ap-aging'

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<ReportType>('trial-balance')

  const { data: reportData, isLoading } = useQuery({
    queryKey: ['report', selectedReport],
    queryFn: async () => {
      switch (selectedReport) {
        case 'trial-balance':
          return (await reportsApi.trialBalance()).data
        case 'balance-sheet':
          return (await reportsApi.balanceSheet()).data
        case 'income-statement':
          return (await reportsApi.incomeStatement()).data
        case 'ar-aging':
          return (await reportsApi.arAging()).data
        case 'ap-aging':
          return (await reportsApi.apAging()).data
        default:
          return null
      }
    },
  })

  const reports = [
    { id: 'trial-balance', name: 'Trial Balance' },
    { id: 'balance-sheet', name: 'Balance Sheet' },
    { id: 'income-statement', name: 'Income Statement' },
    { id: 'ar-aging', name: 'AR Aging' },
    { id: 'ap-aging', name: 'AP Aging' },
  ]

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
            <tr key={account.account_id}>
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
            <td className="px-4 py-3 text-sm text-right">{formatCurrency(data.total_debit)}</td>
            <td className="px-4 py-3 text-sm text-right">{formatCurrency(data.total_credit)}</td>
          </tr>
        </tfoot>
      </table>
      <div className="mt-4 text-center">
        <span className={`text-sm ${data.is_balanced ? 'text-green-600' : 'text-red-600'}`}>
          {data.is_balanced ? 'Balanced' : 'Out of Balance'}
        </span>
      </div>
    </div>
  )

  const renderBalanceSheet = (data: any) => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Assets</h3>
        {data.assets?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm">
            <span>{account.account_name}</span>
            <span>{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2">
          <span>Total Assets</span>
          <span>{formatCurrency(data.assets?.total)}</span>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-2">Liabilities</h3>
        {data.liabilities?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm">
            <span>{account.account_name}</span>
            <span>{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2">
          <span>Total Liabilities</span>
          <span>{formatCurrency(data.liabilities?.total)}</span>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-2">Equity</h3>
        {data.equity?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm">
            <span>{account.account_name}</span>
            <span>{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2">
          <span>Total Equity</span>
          <span>{formatCurrency(data.equity?.total)}</span>
        </div>
      </div>
    </div>
  )

  const renderIncomeStatement = (data: any) => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Revenue</h3>
        {data.revenue?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm">
            <span>{account.account_name}</span>
            <span>{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2">
          <span>Total Revenue</span>
          <span>{formatCurrency(data.revenue?.total)}</span>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-2">Expenses</h3>
        {data.expenses?.accounts?.map((account: any) => (
          <div key={account.account_id} className="flex justify-between py-1 text-sm">
            <span>{account.account_name}</span>
            <span>{formatCurrency(account.balance)}</span>
          </div>
        ))}
        <div className="flex justify-between py-2 font-bold border-t mt-2">
          <span>Total Expenses</span>
          <span>{formatCurrency(data.expenses?.total)}</span>
        </div>
      </div>
      <div className="border-t-2 pt-4">
        <div className="flex justify-between font-bold text-lg">
          <span>Net Income</span>
          <span className={data.net_income >= 0 ? 'text-green-600' : 'text-red-600'}>
            {formatCurrency(data.net_income)}
          </span>
        </div>
      </div>
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
      default:
        return <pre className="text-sm">{JSON.stringify(reportData, null, 2)}</pre>
    }
  }

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Financial reports and analytics"
      />

      <div className="mb-6 flex gap-2 flex-wrap">
        {reports.map((report) => (
          <Button
            key={report.id}
            variant={selectedReport === report.id ? 'default' : 'outline'}
            onClick={() => setSelectedReport(report.id as ReportType)}
          >
            {report.name}
          </Button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{reports.find((r) => r.id === selectedReport)?.name}</CardTitle>
        </CardHeader>
        <CardContent>{renderReport()}</CardContent>
      </Card>
    </div>
  )
}
