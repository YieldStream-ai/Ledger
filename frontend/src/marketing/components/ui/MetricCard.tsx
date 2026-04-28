interface MetricCardProps {
  value: string
  label: string
}

export function MetricCard({ value, label }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6 text-center">
      <p className="font-[var(--font-mono)] text-3xl font-semibold text-[var(--text-primary)]">
        {value}
      </p>
      <p className="mt-2 text-sm text-[var(--text-secondary)]">{label}</p>
    </div>
  )
}
