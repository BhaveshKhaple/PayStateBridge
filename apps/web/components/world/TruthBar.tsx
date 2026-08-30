'use client'

import type { AgentDecision } from '@/lib/useSimStream'

// One-sentence verdict, pinned at the ConsolePane bottom.
// mono prefix `verdict ›`.

function verdictLine(decision: AgentDecision | null): { text: string; color: string } {
  if (!decision) {
    return { text: 'waiting for evidence…', color: 'var(--muted)' }
  }
  switch (decision.state) {
    case 'PENDING':
      return { text: 'hold — first capture event pending', color: 'var(--pending)' }
    case 'OUTCOME_UNKNOWN':
      return { text: 'hold — outcome not yet knowable, evidence packet prepared', color: 'var(--unknown)' }
    case 'CAPTURED_UNLINKED':
      return { text: 'reconcile — capture found, link to order, no new charge', color: 'var(--recovered)' }
    case 'DUPLICATE_SUCCESS':
      return { text: 'refund review — second success detected, human approves', color: 'var(--pending)' }
    case 'FAILED':
      return { text: 'safe to retry — first attempt confirmed failed', color: 'var(--accent)' }
    default:
      return { text: decision.action?.toLowerCase() || 'decision recorded', color: 'var(--body)' }
  }
}

export function TruthBar({ decision }: { decision: AgentDecision | null }) {
  const { text, color } = verdictLine(decision)
  return (
    <div
      className="mt-4 pt-3 border-t flex items-baseline gap-2"
      style={{ borderColor: 'var(--hairline)' }}
    >
      <span className="mono text-xs" style={{ color: 'var(--faint)' }}>
        verdict ›
      </span>
      <span className="mono text-xs leading-snug" style={{ color }}>
        {text}
      </span>
    </div>
  )
}
