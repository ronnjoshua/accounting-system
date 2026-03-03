import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

interface PageHeaderProps {
  title: string
  description?: string
  action?: ReactNode | {
    label: string
    onClick: () => void
  }
}

export function PageHeader({ title, description, action }: PageHeaderProps) {
  const renderAction = () => {
    if (!action) return null

    // If action is a React element, render it directly
    if (typeof action === 'object' && 'type' in action) {
      return action
    }

    // Otherwise, it's the {label, onClick} format
    const actionProps = action as { label: string; onClick: () => void }
    return (
      <Button onClick={actionProps.onClick}>
        <Plus className="mr-2 h-4 w-4" />
        {actionProps.label}
      </Button>
    )
  }

  return (
    <div className="mb-8 flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
      </div>
      {renderAction()}
    </div>
  )
}
