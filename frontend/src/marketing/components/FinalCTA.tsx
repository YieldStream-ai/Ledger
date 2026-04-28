import { Container } from './ui/Container'
import { Button } from './ui/Button'
import { finalCTA } from '../content'

export function FinalCTA() {
  return (
    <section className="bg-[#F4F4F5] py-20 md:py-28">
      <Container className="text-center">
        <h2 className="text-[clamp(1.5rem,4vw,2.5rem)] font-semibold leading-tight tracking-[-0.02em] text-[var(--text-primary)]">
          {finalCTA.headline}
        </h2>
        <p className="mx-auto mt-4 max-w-md text-lg text-[var(--text-secondary)]">
          {finalCTA.subheadline}
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button href={finalCTA.primaryCTA.href} size="lg">
            {finalCTA.primaryCTA.label}
          </Button>
          <Button href={finalCTA.secondaryCTA.href} variant="secondary" size="lg">
            {finalCTA.secondaryCTA.label}
          </Button>
        </div>

        <div className="mt-8">
          <code className="rounded-md bg-[var(--code-bg)] px-4 py-2 font-[var(--font-mono)] text-sm text-[#A1A1AA]">
            {finalCTA.installLine}
          </code>
        </div>
      </Container>
    </section>
  )
}
