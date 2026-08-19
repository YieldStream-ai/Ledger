import { Container } from './ui/Container'
import { Button } from './ui/Button'
import { ParseCardStack } from './ParseCardStack'
import { hero } from '../content'

export function Hero() {
  return (
    <section className="flex min-h-[80vh] items-center pt-28 pb-16 md:pt-32 md:pb-20">
      <Container>
        <div className="flex flex-col items-center gap-12 lg:flex-row lg:items-stretch lg:justify-between lg:gap-16">
          {/* Left column: text content */}
          <div className="max-w-2xl lg:max-w-lg xl:max-w-xl flex-1">
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

            {/* Curl example */}
            <div className="mt-10 overflow-x-auto rounded-lg bg-[var(--code-bg)] p-4">
              <pre className="font-[var(--font-mono)] text-sm leading-relaxed text-[#A1A1AA]">
                <code>
                  <span className="text-[#E4E4E7]">$</span> {hero.curlExample}
                </code>
              </pre>
            </div>
          </div>

          {/* Right column: card stack */}
          <div className="w-full max-w-md lg:max-w-none lg:w-[480px] xl:w-[540px] flex-shrink-0 self-stretch">
            <ParseCardStack />
          </div>
        </div>
      </Container>
    </section>
  )
}
