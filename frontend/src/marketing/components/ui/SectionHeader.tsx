import { clsx } from 'clsx'

interface SectionHeaderProps {
  eyebrow?: string
  heading: string
  subheading?: string
  align?: 'left' | 'center'
}

export function SectionHeader({
  eyebrow,
  heading,
  subheading,
  align = 'left',
}: SectionHeaderProps) {
  return (
    <div className={clsx(align === 'center' && 'text-center')}>
      {eyebrow && (
        <p className="mb-4 text-xs font-medium uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
          {eyebrow}
        </p>
      )}
      <h2 className="text-[clamp(1.5rem,4vw,2.5rem)] font-semibold leading-tight tracking-[-0.02em] text-[var(--text-primary)]">
        {heading}
      </h2>
      {subheading && (
        <p className="mt-4 max-w-2xl text-lg leading-relaxed text-[var(--text-secondary)]">
          {subheading}
        </p>
      )}
    </div>
  )
}
