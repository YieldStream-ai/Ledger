import { Check, X, Minus } from 'lucide-react'
import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { comparison } from '../content'

function StatusCell({ value }: { value: boolean | string }) {
  if (value === true) {
    return <Check size={18} strokeWidth={2} className="mx-auto text-[var(--accent-success)]" />
  }
  if (value === 'partial') {
    return <Minus size={18} strokeWidth={2} className="mx-auto text-[var(--text-tertiary)]" />
  }
  return <X size={18} strokeWidth={2} className="mx-auto text-[var(--text-tertiary)]" />
}

export function ComparisonTable() {
  return (
    <section className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={comparison.eyebrow}
          heading={comparison.headline}
        />

        <div className="mt-12 overflow-x-auto">
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
              {comparison.rows.map((row) => (
                <tr key={row.feature} className="border-b border-[var(--border)]">
                  <td className="py-4 pr-4 text-[var(--text-primary)]">{row.feature}</td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.ledger} />
                  </td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.ocr} />
                  </td>
                  <td className="py-4 text-center">
                    <StatusCell value={row.llm} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Container>
    </section>
  )
}
