import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { MetricCard } from './ui/MetricCard'
import { metrics } from '../content'

export function AccuracyMetrics() {
  return (
    <section className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={metrics.eyebrow}
          heading={metrics.headline}
        />

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.items.map((item) => (
            <MetricCard key={item.label} value={item.value} label={item.label} />
          ))}
        </div>

        <p className="mt-8 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">
          {metrics.description}
        </p>
      </Container>
    </section>
  )
}
