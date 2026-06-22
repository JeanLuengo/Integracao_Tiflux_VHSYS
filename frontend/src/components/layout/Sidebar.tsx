import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  UserPlus,
  UserX,
  Search,
  Clock,
  PanelLeftClose,
  PanelLeft,
  LogOut,
} from 'lucide-react'
import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/cn'

const NAV: { to: string; label: string; icon: typeof LayoutDashboard; end?: boolean }[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/cadastrar', label: 'Cadastrar', icon: UserPlus },
  { to: '/inativar', label: 'Inativar', icon: UserX },
  { to: '/consultar', label: 'Consultar', icon: Search },
  { to: '/empresas-inativas', label: 'Empresas inativas', icon: Clock },
]

type Props = {
  collapsed: boolean
  onToggleCollapse: () => void
  onNavigate?: () => void
  className?: string
}

export function Sidebar({ collapsed, onToggleCollapse, onNavigate, className }: Props) {
  const { logout } = useAuth()

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'aurora-sidebar-pattern relative flex h-full flex-col overflow-hidden border-r border-aurora-sidebar-border text-aurora-sidebar-fg transition-[width] duration-300',
          collapsed ? 'w-16' : 'w-64',
          className,
        )}
      >
        <div className={cn('relative z-10 flex flex-col items-center gap-1 p-4', collapsed && 'px-2')}>
          <Logo variant="sidebar" collapsed={collapsed} />
          {!collapsed && (
            <p className="text-xs text-aurora-sidebar-muted">TiFlux · VHSYS</p>
          )}
        </div>

        <Separator className="relative z-10 bg-aurora-sidebar-border" />

        <nav className="relative z-10 flex-1 space-y-1 p-2">
          {NAV.map(({ to, label, icon: Icon, end }) => {
            const link = (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    'aurora-motion flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium',
                    isActive
                      ? 'border-l-2 border-aurora-sidebar-accent bg-white/10 text-aurora-sidebar-fg'
                      : 'border-l-2 border-transparent text-aurora-sidebar-muted hover:bg-white/5 hover:text-aurora-sidebar-fg',
                    collapsed && 'justify-center px-2',
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{label}</span>}
              </NavLink>
            )

            if (collapsed) {
              return (
                <Tooltip key={to}>
                  <TooltipTrigger asChild>{link}</TooltipTrigger>
                  <TooltipContent side="right">{label}</TooltipContent>
                </Tooltip>
              )
            }
            return link
          })}
        </nav>

        <div className="relative z-10 space-y-2 border-t border-aurora-sidebar-border p-2">
          {!collapsed && (
            <Button
              type="button"
              onClick={logout}
              className="w-full bg-aurora-brand-red font-semibold text-white hover:brightness-110"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </Button>
          )}
          {collapsed && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  onClick={logout}
                  aria-label="Sair"
                  className="w-full bg-aurora-brand-red text-white hover:brightness-110"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Sair</TooltipContent>
            </Tooltip>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            aria-label="Alternar sidebar"
            className="w-full text-aurora-sidebar-muted hover:bg-white/10 hover:text-aurora-sidebar-fg"
          >
            {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  )
}
