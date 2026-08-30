import { Pill, stateToPillVariant } from './Pill'

export function EventRow({
  timestamp,
  label,
  state,
  isNew = false,
}: {
  timestamp: string
  label: string
  state?: string
  isNew?: boolean
}) {
  return (
    <div
      className={`flex items-center gap-3 py-1.5 px-2 text-xs border-b ${isNew ? 'animate-row-flash' : ''}`}
      style={{ borderColor: 'var(--hairline)' }}
    >
      <span className="mono tabular flex-shrink-0" style={{ color: 'var(--faint)', width: '64px' }}>
        {timestamp}
      </span>
      <span className="mono flex-1 min-w-0 truncate" style={{ color: 'var(--body)' }}>
        {label}
      </span>
      {state && (
        <Pill state={stateToPillVariant(state)} mono>
          {state}
        </Pill>
      )}
    </div>
  )
}
