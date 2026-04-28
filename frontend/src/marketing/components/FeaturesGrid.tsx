import { Layers, Scale, Target, ShieldAlert, EyeOff, FileStack } from 'lucide-react'
import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { features } from '../content'

const iconMap: Record<string, React.ComponentType<{ size?: number; strokeWidth?: number }>> = {
  Layers,
  Scale,
  Target,
  ShieldAlert,
  EyeOff,
  FileStack,
}

export function FeaturesGrid() {
  return (
    <section id="features" className="py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow="CAPABILITIES"
          heading="Built for documents underwriters actually receive."
        />

        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = iconMap[feature.icon]
            return (
              <div
                key={feature.title}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6"
              >
                {Icon && (
                  <Icon size={22} strokeWidth={1.5} />
                )}
                <h3 className="mt-4 text-base font-semibold text-[var(--text-primary)]">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </Container>
    </section>
  )
}
