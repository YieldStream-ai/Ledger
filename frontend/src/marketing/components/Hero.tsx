import { Container } from './ui/Container'
import { Button } from './ui/Button'
import { hero } from '../content'

export function Hero() {
  return (
    <section className="pt-32 pb-20 md:pt-40 md:pb-28">
      <Container>
        <div className="max-w-3xl">
          {/* Eyebrow */}
          <p className="mb-5 text-xs font-medium uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
            {hero.eyebrow}
          </p>

          {/* Headline */}
          <h1 className="text-[clamp(2rem,6vw,4.5rem)] font-bold leading-[1.05] tracking-[-0.03em] text-[var(--text-primary)]">
            {hero.headline}
          </h1>

          {/* Subheadline */}
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-[var(--text-secondary)]">
            {hero.subheadline}
          </p>

          {/* CTAs */}
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button href={hero.primaryCTA.href} size="lg">
              {hero.primaryCTA.label}
            </Button>
            <Button href={hero.secondaryCTA.href} variant="secondary" size="lg">
              {hero.secondaryCTA.label}
            </Button>
          </div>

          {/* Curl example */}
          <div className="mt-10 overflow-x-auto rounded-lg bg-[var(--code-bg)] p-4">
            <pre className="font-[var(--font-mono)] text-sm leading-relaxed text-[#A1A1AA]">
              <code>
                <span className="text-[#E4E4E7]">$</span> {hero.curlExample}
              </code>
            </pre>
          </div>
        </div>
      </Container>
    </section>
  )
}
