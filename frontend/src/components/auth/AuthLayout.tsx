import { Link } from 'react-router-dom'
import { Logo } from '@/components/brand/Logo'
import { linkClass } from '@/lib/ui-classes'
import { cn } from '@/lib/cn'

export function AuthLayout({
  children,
  title,
  subtitle,
  showBackLink = true,
}: {
  children: React.ReactNode
  title: string
  subtitle?: string
  showBackLink?: boolean
}) {
  return (
    <div className="aurora-sidebar-pattern flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="hub-panel-enter w-full max-w-sm rounded-2xl border border-aurora-border bg-aurora-surface p-8 shadow-lg">
        <div className="mb-6 flex flex-col items-center text-center">
          <Logo variant="auth" className="mb-4" />
          <p className="text-sm text-aurora-muted">
            Plataforma interna para operações TiFlux, VHSYS e consultas CNPJ.
          </p>
        </div>

        <h2 className="text-xl font-bold tracking-tight text-aurora-fg">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-aurora-muted">{subtitle}</p>}
        <div className="mt-6">{children}</div>

        {showBackLink && (
          <p className="mt-6 text-center text-sm text-aurora-muted">
            <Link to="/login" className={cn(linkClass)}>
              Voltar ao login
            </Link>
          </p>
        )}
      </div>
    </div>
  )
}
