import { Landmark } from 'lucide-react'
import { templateCoverage } from '../content'

const allBanks = templateCoverage.banks

export function TemplateCoverage() {
  return (
    <section id="templates" className="py-16 md:py-20">
      <div className="mx-auto w-full max-w-[1440px] px-6 md:px-16">
        <div className="flex flex-col md:flex-row md:items-center md:h-[180px] overflow-hidden">

          {/* Left: White Panel with slanted right edge */}
          <div
            className="relative z-10 w-full md:w-[360px] shrink-0 bg-[var(--surface)] px-8 py-6"
            style={{ clipPath: 'polygon(0 0, calc(100% - 80px) 0, 100% 100%, 0 100%)' }}
          >
            <div className="flex items-center gap-2">
              <Landmark size={14} className="text-[var(--text-tertiary)]" />
              <span className="font-[var(--font-mono)] text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--text-tertiary)]">
                BANK TEMPLATES
              </span>
            </div>
            <div className="mt-3">
              <p className="text-xl font-semibold text-[var(--text-primary)] leading-snug">
                Multiple templates.
              </p>
              <p className="text-xl font-semibold text-[var(--text-primary)] leading-snug">
                4,200+ institutions.
              </p>
            </div>
            <a
              href={templateCoverage.fallbackCTA.href}
              className="mt-3 inline-block text-xs text-[var(--text-tertiary)] underline underline-offset-2 transition-colors hover:text-[var(--accent-success)]"
            >
              Request a template &rarr;
            </a>
          </div>

          {/* Right: Marquee Strip */}
          <div className="relative mt-4 md:mt-0 md:-ml-4 flex-1 overflow-hidden">
            {/* Left gradient fade — pills emerge */}
            <div className="pointer-events-none absolute inset-y-0 left-0 z-[5] w-32 bg-gradient-to-r from-[var(--bg)] to-transparent" />
            {/* Right gradient fade — pills dissolve out */}
            <div className="pointer-events-none absolute inset-y-0 right-0 z-[5] w-32 bg-gradient-to-r from-transparent to-[var(--bg)]" />

            {/* Row 1 — scrolls left-to-right */}
            <div className="group">
              <div className="flex gap-4 animate-[marquee-right_40s_linear_infinite] group-hover:[animation-play-state:paused]">
                {[...allBanks, ...allBanks].map((bank, i) => (
                  <BankChip key={`r1-${i}`} name={bank.name} accuracy={bank.accuracy} />
                ))}
              </div>
            </div>

            {/* Row 2 — scrolls right-to-left */}
            <div className="group mt-4">
              <div className="flex gap-4 animate-[marquee-left_40s_linear_infinite] group-hover:[animation-play-state:paused]">
                {[...allBanks.slice().reverse(), ...allBanks.slice().reverse()].map((bank, i) => (
                  <BankChip key={`r2-${i}`} name={bank.name} accuracy={bank.accuracy} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes marquee-left {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }
        @keyframes marquee-right {
          from { transform: translateX(-50%); }
          to   { transform: translateX(0); }
        }
      `}</style>
    </section>
  )
}

function BankChip({ name, accuracy }: { name: string; accuracy: string }) {
  return (
    <div className="flex flex-shrink-0 items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5">
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#F4F4F5] font-[var(--font-mono)] text-[8px] font-semibold text-[var(--text-secondary)]">
        {name.slice(0, 2).toUpperCase()}
      </div>
      <span className="text-xs font-medium text-[var(--text-primary)] whitespace-nowrap">
        {name}
      </span>
      <span className="font-[var(--font-mono)] text-[10px] text-[var(--accent-success)] whitespace-nowrap">
        {accuracy}
      </span>
    </div>
  )
}
