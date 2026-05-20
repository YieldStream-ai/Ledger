import { Container } from './ui/Container'
import { trustBar } from '../content'

export function TrustBar() {
  return (
    <section className="border-y border-[var(--border)] py-16 md:py-20">
      <Container>
        <div className="flex flex-col items-center justify-center gap-8 md:flex-row md:gap-16">
          {trustBar.metrics.map((metric) => (
            <div key={metric.label} className="flex items-baseline gap-2">
              <span className="font-[var(--font-mono)] text-2xl font-semibold text-[var(--text-primary)]">
                {metric.value}
              </span>
              <span className="text-sm text-[var(--text-tertiary)]">{metric.label}</span>
            </div>
          ))}
        </div>
      </Container>
    </section>
  )
}
