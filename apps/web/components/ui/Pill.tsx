type PillState = 'pending' | 'blocked' | 'recovered' | 'unknown' | 'neutral'

const STATE_STYLES: Record<PillState, { dot: string; text: string; bg: string; border: string }> = {
  pending: { dot: 'var(--pending)', text: 'var(--pending)', bg: 'var(--pending-soft)', border: 'rgba(232,163,61,0.3)' },
  blocked: { dot: 'var(--blocked)', text: 'var(--blocked)', bg: 'var(--blocked-soft)', border: 'rgba(229,72,77,0.3)' },
  recovered: { dot: 'var(--recovered)', text: 'var(--recovered)', bg: 'var(--recovered-soft)', border: 'rgba(70,167,88,0.3)' },
  unknown: { dot: 'var(--unknown)', text: 'var(--unknown)', bg: 'rgba(139,139,147,0.12)', border: 'rgba(139,139,147,0.3)' },
  neutral: { dot: 'var(--muted)', text: 'var(--body)', bg: 'var(--bg-2)', border: 'var(--hairline)' },
}

// Map a PaymentState string to a pill state
export function stateToPillVariant(state: string | null | undefined): PillState {
  switch (state) {
    case 'PENDING': return 'pending'
    case 'FAILED': return 'blocked'
    case 'CAPTURED_UNLINKED': return 'recovered'
    case 'DUPLICATE_SUCCESS': return 'pending'
    case 'OUTCOME_UNKNOWN': return 'unknown'
    case 'WRONG_RECIPIENT': return 'pending'
    case 'UNAUTHORIZED': return 'blocked'
    default: return 'neutral'
  }
}

export function Pill({ state = 'neutral', children, mono = false }: {
  state?: PillState
  children: React.ReactNode
  mono?: boolean
}) {
  const s = STATE_STYLES[state]
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium ${mono ? 'mono' : ''}`}
      style={{ background: s.bg, color: s.text, border: `1px solid ${s.border}` }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.dot }} />
      {children}
    </span>
  )
}
