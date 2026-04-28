import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { templateCoverage } from '../content'

export function TemplateCoverage() {
  return (
    <section id="templates" className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={templateCoverage.eyebrow}
          heading={templateCoverage.headline}
        />

        <div className="mt-12 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
          {templateCoverage.banks.map((bank) => (
            <div
              key={bank.name}
              className="flex flex-col items-center rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-4 text-center"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[#F4F4F5] font-[var(--font-mono)] text-xs font-semibold text-[var(--text-secondary)]">
                {bank.name.slice(0, 2).toUpperCase()}
              </div>
              <p className="mt-2 text-xs font-medium text-[var(--text-primary)]">
                {bank.name}
              </p>
              <p className="mt-0.5 font-[var(--font-mono)] text-xs text-[var(--accent-success)]">
                {bank.accuracy}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-8 text-sm text-[var(--text-secondary)]">
          {templateCoverage.fallbackNote}{' '}
          <a
            href={templateCoverage.fallbackCTA.href}
            className="text-[var(--text-primary)] underline underline-offset-2 transition-colors hover:text-[var(--accent-success)]"
          >
            {templateCoverage.fallbackCTA.label} &rarr;
          </a>
        </p>
      </Container>
    </section>
  )
}
