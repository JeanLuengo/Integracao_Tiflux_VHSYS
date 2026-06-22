import * as React from 'react'
import * as ProgressPrimitive from '@radix-ui/react-progress'
import { cn } from '@/lib/cn'

type ProgressProps = React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> & {
  variant?: 'default' | 'accent'
}

const Progress = React.forwardRef<React.ComponentRef<typeof ProgressPrimitive.Root>, ProgressProps>(
  ({ className, value, variant = 'default', ...props }, ref) => (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn('relative h-2 w-full overflow-hidden rounded-full bg-secondary', className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          'h-full w-full flex-1 transition-all duration-300 ease-out',
          variant === 'accent' ? 'bg-aurora-accent' : 'bg-primary',
        )}
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  ),
)
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
