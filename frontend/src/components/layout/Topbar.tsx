import { Menu, Search } from 'lucide-react'
import { Logo } from '@/components/brand/Logo'
import { Breadcrumbs } from '@/components/layout/Breadcrumbs'
import { UserMenu } from '@/components/layout/UserMenu'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { Button } from '@/components/ui/button'
import { useCommandPalette } from '@/hooks/useCommandPalette'
import { topbarActionBtnClass } from '@/lib/ui-classes'
import { cn } from '@/lib/cn'

type Props = {
  onMenuClick: () => void
  showMenuButton?: boolean
}

export function Topbar({ onMenuClick, showMenuButton }: Props) {
  const { setOpen } = useCommandPalette()

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-white/10 bg-aurora-topbar-bg text-white">
      <div className="relative flex h-full items-center gap-3 px-4">
        {showMenuButton && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            aria-label="Abrir menu"
            className={cn(topbarActionBtnClass, 'lg:hidden')}
          >
            <Menu className="h-4 w-4" />
          </Button>
        )}

        <Breadcrumbs className="hidden min-w-0 flex-1 text-white/80 xl:flex [&_a:hover]:text-white [&_span]:text-white" />

        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <Logo variant="topbar" />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className={cn(topbarActionBtnClass, 'hidden h-9 w-auto gap-2 px-3 sm:flex')}
            onClick={() => setOpen(true)}
          >
            <Search className="h-3.5 w-3.5" />
            <span className="text-xs font-medium">Buscar…</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className={cn(topbarActionBtnClass, 'sm:hidden')}
            onClick={() => setOpen(true)}
            aria-label="Buscar"
          >
            <Search className="h-4 w-4" />
          </Button>
          <ThemeToggle />
          <UserMenu variant="onTopbar" />
        </div>
      </div>
    </header>
  )
}
