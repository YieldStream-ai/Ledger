import { CheckCircle, Building2 } from 'lucide-react'

const cards = [
  {
    bank: 'Wells Fargo',
    period: 'Jan 2024',
    endingBalance: '$8,241.90',
    confidence: '98.7%',
    template: 'wells_fargo_v2',
  },
  {
    bank: 'Bank of America',
    period: 'Feb 2024',
    endingBalance: '$21,340.55',
    confidence: '99.1%',
    template: 'bofa_checking_v3',
  },
  {
    bank: 'JPMorgan Chase',
    period: 'Mar 2024',
    endingBalance: '$14,892.37',
    confidence: '99.4%',
    template: 'chase_checking_v3',
  },
]

// 30-day daily balance series. Mirrors the response: starts ~12,450, dips to
// the min_balance ($9,134) on day 18, ends at the ending_balance ($14,892).
const dailyBalances = [
  12450, 12180, 11920, 11650, 12340, 12810, 13050, 12690, 12420, 12880,
  13340, 13510, 13180, 12950, 13420, 13890, 13720, 9134, 11200, 12640,
  13180, 13540, 13720, 13980, 14210, 14380, 14150, 14420, 14710, 14892,
]

const debtPositions = [
  { type: 'Term loan', lender: 'Bluevine', cadence: '$482/mo', firstSeen: 'Nov 2023' },
]

const underwritingRows = [
  { label: 'DSCR',              value: '5.06',       conf: '0.992' },
  { label: 'Stacking Burden',   value: '5.4%',       conf: '0.985' },
  { label: 'NSF (90d)',         value: '1',          conf: '0.998' },
  { label: 'Avg Daily Balance', value: '$13,420.15', conf: '0.998' },
  { label: 'Min Balance',       value: '$9,134.20',  conf: '0.998' },
  { label: 'Ending Balance',    value: '$14,892.37', conf: '0.998' },
]

export function ParseCardStack() {
  return (
    <div className="relative w-full h-full min-h-[600px] lg:min-h-[640px]">
      {/* Gradient backdrop */}
      <div
        className="absolute inset-0 rounded-2xl"
        style={{
          background:
            'linear-gradient(135deg, #1f2937 0%, #111827 60%, #0f172a 100%)',
        }}
      />

      {/* Card stack */}
      <div className="relative flex h-full items-center justify-center p-8 md:p-10 lg:p-12">
        {cards.map((card, i) => {
          const isTop = i === cards.length - 1
          const offset = (cards.length - 1 - i) * 22
          const scale = 1 - (cards.length - 1 - i) * 0.04
          const opacity = isTop ? 1 : 0.6 - (cards.length - 1 - i) * 0.15

          return (
            <div
              key={card.bank}
              className={`absolute w-[calc(100%-4rem)] md:w-[calc(100%-5rem)] lg:w-[calc(100%-6rem)] ${
                isTop ? 'h-[calc(100%-4rem)] md:h-[calc(100%-5rem)] lg:h-[calc(100%-6rem)]' : ''
              }`}
              style={{
                transform: `translateY(${-offset}px) scale(${scale})`,
                opacity: isTop ? 1 : opacity,
                zIndex: i,
              }}
            >
              <div
                className={`rounded-xl border p-5 shadow-lg ${
                  isTop
                    ? 'flex h-full flex-col border-[var(--border)] bg-[var(--surface)]'
                    : 'border-[var(--border)] bg-[var(--surface)]'
                }`}
              >
                {/* Bank header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--bg)]">
                      <Building2 className="h-4 w-4 text-[var(--text-tertiary)]" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[var(--text-primary)]">
                        {card.bank}
                      </p>
                      <p className="text-[11px] text-[var(--text-tertiary)]">
                        Checking &middot; {card.period}
                      </p>
                    </div>
                  </div>
                  <span className="rounded-full bg-[var(--bg)] px-2.5 py-0.5 font-[var(--font-mono)] text-[10px] text-[var(--text-tertiary)]">
                    {card.template}
                  </span>
                </div>

                {isTop ? (
                  <>
                    {/* Validation status bar */}
                    <div className="mt-4 flex items-center justify-between rounded-lg bg-[rgba(22,163,74,0.07)] px-3 py-2">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle className="h-3.5 w-3.5 text-[var(--accent-success)]" />
                        <span className="text-xs font-medium text-[var(--accent-success)]">
                          Balance Validated
                        </span>
                      </div>
                      <span className="font-[var(--font-mono)] text-xs font-semibold text-[var(--text-primary)]">
                        {card.confidence}
                      </span>
                    </div>

                    {/* Daily balance sparkline */}
                    <DailyBalanceSparkline />

                    {/* Debt stack */}
                    <div className="mt-3">
                      <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-[11px] text-[var(--text-tertiary)]">
                          Debt Stack
                        </span>
                        <span className="text-[10px] text-[var(--text-tertiary)]">
                          {debtPositions.length} active
                        </span>
                      </div>
                      <div className="space-y-1.5">
                        {debtPositions.map((pos) => (
                          <div
                            key={`${pos.type}-${pos.lender}`}
                            className="flex items-center justify-between rounded-md border border-[var(--border)] bg-[var(--bg)] px-2.5 py-1.5"
                          >
                            <div className="flex min-w-0 items-center gap-2">
                              <span className="rounded bg-[var(--surface)] px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-[var(--text-tertiary)]">
                                {pos.type}
                              </span>
                              <span className="truncate text-[12px] font-medium text-[var(--text-primary)]">
                                {pos.lender}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 whitespace-nowrap">
                              <span className="text-[10px] text-[var(--text-tertiary)]">
                                since {pos.firstSeen}
                              </span>
                              <span className="font-[var(--font-mono)] text-[12px] font-semibold text-[var(--text-primary)]">
                                {pos.cadence}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Underwriting rows */}
                    <div className="mt-3 flex-1 overflow-hidden">
                      <div className="divide-y divide-[var(--border)]">
                        {underwritingRows.map((row) => (
                          <div
                            key={row.label}
                            className="flex items-center justify-between py-2"
                          >
                            <span className="text-[11px] text-[var(--text-tertiary)]">
                              {row.label}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="font-[var(--font-mono)] text-[12px] font-medium text-[var(--text-primary)]">
                                {row.value}
                              </span>
                              <span className="rounded bg-[var(--bg)] px-1.5 py-0.5 font-[var(--font-mono)] text-[9px] text-[var(--text-tertiary)]">
                                {row.conf}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  /* Collapsed card - just balance + confidence */
                  <div className="mt-4 flex items-end justify-between">
                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-[var(--text-tertiary)]">
                        Ending Balance
                      </p>
                      <p className="mt-0.5 font-[var(--font-mono)] text-xl font-bold text-[var(--text-primary)]">
                        {card.endingBalance}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <CheckCircle className="h-3.5 w-3.5 text-[var(--accent-success)]" />
                      <span className="font-[var(--font-mono)] text-xs text-[var(--text-secondary)]">
                        {card.confidence}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function DailyBalanceSparkline() {
  const w = 300
  const h = 44
  const pad = 4

  const min = Math.min(...dailyBalances)
  const max = Math.max(...dailyBalances)
  const range = max - min || 1
  const lastIdx = dailyBalances.length - 1

  const points = dailyBalances.map((v, i) => {
    const x = (i / lastIdx) * w
    const y = pad + (1 - (v - min) / range) * (h - 2 * pad)
    return [x, y] as const
  })

  const linePath = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ')

  return (
    <div className="mt-3">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] text-[var(--text-tertiary)]">
          Daily Balance · 30d
        </span>
        <span className="font-[var(--font-mono)] text-[11px] text-[var(--text-secondary)]">
          $12,450 → $14,892
        </span>
      </div>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        className="block h-11 w-full"
        aria-hidden="true"
      >
        <path
          d={linePath}
          fill="none"
          stroke="var(--text-secondary)"
          strokeOpacity="0.55"
          strokeWidth="1.25"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  )
}
