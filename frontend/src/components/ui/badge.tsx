import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-aurora-accent focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-aurora-brand-red text-white shadow',
        secondary: 'border-transparent bg-aurora-surface-2 text-aurora-fg',
        destructive: 'border-transparent bg-aurora-danger text-white',
        outline: 'border-aurora-border text-aurora-fg',
        success: 'border-transparent bg-aurora-success/15 text-aurora-success',
        warning: 'border-transparent bg-aurora-warning/20 text-aurora-warning',
        info: 'border-transparent bg-aurora-info/15 text-aurora-info',
        low: 'border-transparent bg-aurora-muted/15 text-aurora-muted',
        medium: 'border-transparent bg-aurora-info/15 text-aurora-info',
        high: 'border-transparent bg-aurora-warning/20 text-aurora-warning',
        urgent: 'border-transparent bg-aurora-danger text-white',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
