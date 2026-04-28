import { BadgeDollarSign, Building2, Calculator } from 'lucide-react'
import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { useCases } from '../content'

const iconMap: Record<string, React.ComponentType<{ size?: number; strokeWidth?: number }>> = {
  BadgeDollarSign,
  Building2,
  Calculator,
}

export function UseCases() {
  return (
    <section className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={useCases.eyebrow}
          heading={useCases.headline}
        />

        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {useCases.items.map((item) => {
            const Icon = iconMap[item.icon]
            return (
              <div
                key={item.title}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6"
              >
                {Icon && <Icon size={22} strokeWidth={1.5} />}
                <h3 className="mt-4 text-base font-semibold text-[var(--text-primary)]">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                  {item.description}
                </p>
              </div>
            )
          })}
        </div>
      </Container>
    </section>
  )
}
