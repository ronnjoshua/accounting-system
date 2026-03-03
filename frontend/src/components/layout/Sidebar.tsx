'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  Users,
  Building2,
  Receipt,
  FileSpreadsheet,
  Package,
  Warehouse,
  ShoppingCart,
  BarChart3,
  Settings,
  LogOut,
} from 'lucide-react'
import { signOut } from 'next-auth/react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Chart of Accounts', href: '/accounts', icon: BookOpen },
  { name: 'Journal Entries', href: '/journal-entries', icon: FileText },
  { divider: true, label: 'Receivables' },
  { name: 'Customers', href: '/customers', icon: Users },
  { name: 'Invoices', href: '/invoices', icon: Receipt },
  { divider: true, label: 'Payables' },
  { name: 'Vendors', href: '/vendors', icon: Building2 },
  { name: 'Bills', href: '/bills', icon: FileSpreadsheet },
  { divider: true, label: 'Inventory' },
  { name: 'Products', href: '/inventory/products', icon: Package },
  { name: 'Warehouses', href: '/inventory/warehouses', icon: Warehouse },
  { name: 'Purchase Orders', href: '/inventory/purchase-orders', icon: ShoppingCart },
  { divider: true, label: 'Reports' },
  { name: 'Reports', href: '/reports', icon: BarChart3 },
  { divider: true },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-slate-900">
      {/* Logo */}
      <div className="flex h-16 items-center px-6">
        <span className="text-xl font-bold text-white">Accounting</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {navigation.map((item, index) => {
          if ('divider' in item && item.divider) {
            return (
              <div key={index} className="pt-4">
                {item.label && (
                  <p className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    {item.label}
                  </p>
                )}
              </div>
            )
          }

          const Icon = item.icon
          const isActive = pathname === item.href

          return (
            <Link
              key={item.name}
              href={item.href!}
              className={cn(
                'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              {Icon && <Icon className="mr-3 h-5 w-5 flex-shrink-0" />}
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="border-t border-slate-800 p-3">
        <button
          onClick={() => signOut({ callbackUrl: '/login' })}
          className="flex w-full items-center rounded-md px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </button>
      </div>
    </div>
  )
}
