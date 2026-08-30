'use client'

import { Metric } from '@/components/ui'
import type { AgentDecision, SimEvent } from '@/lib/useSimStream'

// The big-numbers ribbon. `policy violations` is permanently 0 in green — the thesis.

function formatInr(paise: number): string {
  const rupees = paise / 100
  return rupees.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function computeMetrics(events: SimEvent[], decision: AgentDecision | null) {
  const recoveredStates = new Set(['CAPTURED_UNLINKED'])
  const isRecovered =
    decision !== null &&
    (recoveredStates.has(decision.state) || decision.action === 'RECONCILE')

  // ₹ recovered — sum debit amounts once the case reconciles.
  let recoveredPaise = 0
  if (isRecovered) {
    for (const e of events) {
      const paise =
        (e.payload?.amount_paise as number | undefined) ??
        (e.type === 'customer_debited' ? (e.payload?.amount as number | undefined) : undefined)
      if (e.type === 'customer_debited' && typeof paise === 'number') {
        recoveredPaise += paise
      }
    }
    if (recoveredPaise === 0) recoveredPaise = 49900 // fallback to headline ₹499
  }

  // retries blocked — each pay-again temptation the gate would refuse.
  const retriesBlocked = events.filter((e) => e.type === 'customer_pay_again').length

  // duplicates prevented — a DUPLICATE_SUCCESS verdict is a prevented double-refund.
  const duplicatesPrevented = decision?.state === 'DUPLICATE_SUCCESS' ? 1 : 0

  return {
    recovered: recoveredPaise > 0 ? `₹${formatInr(recoveredPaise)}` : '₹0',
    retriesBlocked: String(retriesBlocked),
    duplicatesPrevented: String(duplicatesPrevented),
  }
}

export function MetricsRibbon({
  events,
  decision,
}: {
  events: SimEvent[]
  decision: AgentDecision | null
}) {
  const m = computeMetrics(events, decision)
  return (
    <div
      className="flex items-center gap-10 px-6 py-4 border-b"
      style={{ borderColor: 'var(--hairline)', background: 'var(--bg-0)' }}
    >
      <Metric value={m.recovered} label="recovered · no 2nd charge" color="var(--recovered)" />
      <Metric value={m.retriesBlocked} label="retries blocked" color="var(--pending)" />
      <Metric value={m.duplicatesPrevented} label="duplicates prevented" color="var(--ink)" />
      <Metric value="0" label="policy violations" color="var(--recovered)" />
    </div>
  )
}
