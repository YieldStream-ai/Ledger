import { Check, X, Minus } from 'lucide-react'
import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { comparison } from '../content'

function StatusCell({ value, delay = 0 }: { value: boolean | string; delay?: number }) {
  if (value === true) {
    return (
      <span
        className="mx-auto flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(22,163,74,0.08)] animate-[status-pop_0.4s_ease-out_both]"
        style={{ animationDelay: `${delay}ms` }}
      >
        <Check size={14} strokeWidth={2.5} className="text-[var(--accent-success)]" />
      </span>
    )
  }
  if (value === 'partial') {
    return (
      <span
        className="mx-auto flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg)] animate-[status-pop_0.4s_ease-out_both]"
        style={{ animationDelay: `${delay}ms` }}
      >
        <Minus size={14} strokeWidth={2.5} className="text-[var(--text-tertiary)]" />
      </span>
    )
  }
  return (
    <span
      className="mx-auto flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(220,38,38,0.08)] animate-[status-pop_0.4s_ease-out_both]"
      style={{ animationDelay: `${delay}ms` }}
    >
      <X size={14} strokeWidth={2.5} className="text-[var(--accent-error)]" />
    </span>
  )
}

export function ComparisonTable() {
  return (
    <section className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={comparison.eyebrow}
          heading={comparison.headline}
        />

        <div className="mt-12 rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          {/* Browser title bar */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg)]">
            <span className="h-3 w-3 rounded-full bg-[#FF5F57]" />
            <span className="h-3 w-3 rounded-full bg-[#FEBC2E]" />
            <span className="h-3 w-3 rounded-full bg-[#28C840]" />
          </div>

          <div className="overflow-x-auto px-6 py-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {comparison.headers.map((header, i) => (
                  <th
                    key={header}
                    className={`pb-3 text-xs font-medium uppercase tracking-wider text-[var(--text-tertiary)] ${
                      i === 0 ? 'text-left' : 'text-center'
                    } ${i === 1 ? 'text-[var(--text-primary)]' : ''}`}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparison.rows.map((row, i) => (
                <tr key={row.feature} className="border-b border-[var(--border)]">
                  <td className="py-4 pr-4 text-[var(--text-primary)]">{row.feature}</td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.ledger} delay={i * 80} />
                  </td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.ocr} delay={i * 80 + 30} />
                  </td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.llm} delay={i * 80 + 60} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      </Container>

      <style>{`
        @keyframes status-pop {
          from {
            opacity: 0;
            transform: scale(0.5);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </section>
  )
}
