import { Check } from 'lucide-react'
import { clsx } from 'clsx'
import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { Button } from './ui/Button'
import { pricing } from '../content'

export function Pricing() {
  return (
    <section id="pricing" className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={pricing.eyebrow}
          heading={pricing.headline}
          subheading={pricing.subheadline}
        />

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {pricing.tiers.map((tier) => (
            <div
              key={tier.name}
              className={clsx(
                'flex flex-col rounded-lg border p-6',
                tier.highlighted
                  ? 'border-[var(--accent-cta)] bg-[var(--surface)]'
                  : 'border-[var(--border)] bg-[var(--surface)]'
              )}
            >
              <p className="text-sm font-medium text-[var(--text-secondary)]">{tier.name}</p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="font-[var(--font-mono)] text-3xl font-semibold text-[var(--text-primary)]">
                  {tier.price}
                </span>
                <span className="text-sm text-[var(--text-tertiary)]">{tier.priceDetail}</span>
              </div>

              <ul className="mt-6 flex flex-1 flex-col gap-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                    <Check size={16} strokeWidth={2} className="mt-0.5 shrink-0 text-[var(--accent-success)]" />
                    {feature}
                  </li>
                ))}
              </ul>

              <div className="mt-6">
                <Button
                  href={tier.cta.href}
                  variant={tier.highlighted ? 'primary' : 'secondary'}
                  className="w-full"
                >
                  {tier.cta.label}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  )
}
