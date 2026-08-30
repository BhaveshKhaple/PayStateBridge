export function Metric({
  value,
  label,
  color = 'var(--ink)',
}: {
  value: string
  label: string
  color?: string
}) {
  return (
    <div className="flex flex-col">
      <span className="mono text-[32px] leading-none font-[600] tabular" style={{ color }}>
        {value}
      </span>
      <span className="mono text-xs mt-1.5 uppercase" style={{ letterSpacing: '0.06em', color: 'var(--muted)' }}>
        {label}
      </span>
    </div>
  )
}
