import { LogOut, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { topbarActionBtnClass } from '@/lib/ui-classes'
import { cn } from '@/lib/cn'

function initials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || '')
    .join('')
}

export function UserMenu({ variant = 'default' }: { variant?: 'default' | 'onDark' | 'onTopbar' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const name = user?.name || 'Usuário'
  const onTopbar = variant === 'onTopbar'
  const onDark = variant === 'onDark' || onTopbar

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'relative h-9 w-9 rounded-full',
            onTopbar && topbarActionBtnClass,
            onDark && !onTopbar && 'text-aurora-sidebar-fg/80 hover:bg-white/10 hover:text-aurora-sidebar-fg',
          )}
        >
          <Avatar className="h-8 w-8">
            <AvatarFallback
              className={cn(
                onTopbar
                  ? 'bg-aurora-accent/15 text-slate-900 font-semibold'
                  : onDark
                    ? 'bg-aurora-accent/20 text-aurora-sidebar-fg'
                    : 'bg-aurora-accent-muted text-aurora-accent',
              )}
            >
              {initials(name)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{name}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/perfil')}>
          <User className="mr-2 h-4 w-4" />
          Perfil
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
          <LogOut className="mr-2 h-4 w-4" />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
