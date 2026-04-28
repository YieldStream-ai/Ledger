import { Container } from './ui/Container'
import { SectionHeader } from './ui/SectionHeader'
import { CodeBlock } from './ui/CodeBlock'
import { howItWorks } from '../content'

export function HowItWorks() {
  return (
    <section className="border-t border-[var(--border)] py-20 md:py-30">
      <Container>
        <SectionHeader
          eyebrow={howItWorks.eyebrow}
          heading={howItWorks.headline}
        />

        <div className="mt-12 grid gap-8 lg:grid-cols-2">
          {/* Left: Tabbed code block */}
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
              Request
            </p>
            <CodeBlock tabs={howItWorks.tabs} />
          </div>

          {/* Right: JSON response with callouts */}
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
              Response
            </p>
            <div className="overflow-hidden rounded-lg bg-[var(--code-bg)]">
              <div className="overflow-x-auto p-4">
                <pre className="font-[var(--font-mono)] text-sm leading-relaxed">
                  <code className="block text-[#D4D4D4]">
                    {highlightJson(howItWorks.response)}
                  </code>
                </pre>
              </div>

              {/* Callouts */}
              <div className="border-t border-white/10 px-4 py-3">
                <div className="flex flex-wrap gap-3">
                  {howItWorks.callouts.map((callout) => (
                    <span
                      key={callout.field}
                      className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-2 py-1 text-xs text-[#A1A1AA]"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-success)]" />
                      {callout.label}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Docs link */}
            <a
              href="/docs/schema"
              className="mt-4 inline-flex items-center gap-1 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            >
              View the full schema
              <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
        </div>
      </Container>
    </section>
  )
}

function highlightJson(json: string): React.ReactNode[] {
  const lines = json.split('\n')
  return lines.map((line, i) => {
    const tokens: React.ReactNode[] = []
    let remaining = line
    let key = 0

    while (remaining.length > 0) {
      // Keys
      const keyMatch = remaining.match(/^("[\w_]+")\s*:/)
      if (keyMatch) {
        tokens.push(
          <span key={key++} className="text-[#9CDCFE]">
            {keyMatch[1]}
          </span>
        )
        remaining = remaining.slice(keyMatch[1].length)
        continue
      }

      // String values
      const strMatch = remaining.match(/^("(?:[^"\\]|\\.)*")/)
      if (strMatch) {
        tokens.push(
          <span key={key++} className="text-[#CE9178]">
            {strMatch[1]}
          </span>
        )
        remaining = remaining.slice(strMatch[1].length)
        continue
      }

      // Numbers
      const numMatch = remaining.match(/^(-?\d+\.?\d*)/)
      if (numMatch) {
        tokens.push(
          <span key={key++} className="text-[#B5CEA8]">
            {numMatch[1]}
          </span>
        )
        remaining = remaining.slice(numMatch[1].length)
        continue
      }

      // Booleans / null
      const boolMatch = remaining.match(/^(true|false|null)/)
      if (boolMatch) {
        tokens.push(
          <span key={key++} className="text-[#569CD6]">
            {boolMatch[1]}
          </span>
        )
        remaining = remaining.slice(boolMatch[1].length)
        continue
      }

      // Default char
      tokens.push(
        <span key={key++} className="text-[#D4D4D4]">
          {remaining[0]}
        </span>
      )
      remaining = remaining.slice(1)
    }

    return (
      <span key={i} className="block">
        {tokens}
      </span>
    )
  })
}
