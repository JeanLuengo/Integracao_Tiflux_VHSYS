import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeProvider'
import { Button } from '@/components/ui/button'
import { topbarActionBtnClass } from '@/lib/ui-classes'
import { cn } from '@/lib/cn'

export function ThemeToggle({ className }: { className?: string }) {
  const { mode, toggleMode } = useTheme()
  const Icon = mode === 'dark' ? Moon : Sun
  const label = mode === 'dark' ? 'Tema escuro' : 'Tema claro'

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={toggleMode}
      className={cn(topbarActionBtnClass, className)}
      aria-label={label}
      title={label}
    >
      <Icon className="h-4 w-4 transition-transform duration-[var(--motion-duration-fast)]" />
    </Button>
  )
}
