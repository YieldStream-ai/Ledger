import { clsx } from 'clsx'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  href?: string
  className?: string
  onClick?: () => void
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  href,
  className,
  onClick,
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center font-medium transition-colors duration-150'

  const variants = {
    primary: 'bg-[var(--accent-cta)] text-white hover:bg-[#27272A]',
    secondary:
      'border border-[var(--border-strong)] text-[var(--text-primary)] hover:bg-[var(--border)]/30',
    ghost: 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm rounded-md',
    md: 'px-5 py-2.5 text-sm rounded-lg',
    lg: 'px-6 py-3 text-base rounded-lg',
  }

  const classes = clsx(base, variants[variant], sizes[size], className)

  if (href) {
    return (
      <a href={href} className={classes}>
        {children}
      </a>
    )
  }

  return (
    <button onClick={onClick} className={classes}>
      {children}
    </button>
  )
}
