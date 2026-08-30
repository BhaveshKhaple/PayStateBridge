'use client'

import { useState } from 'react'
import { Pill, stateToPillVariant } from '@/components/ui'
import type { AgentDecision, SimEvent } from '@/lib/useSimStream'
import { TruthBar } from './TruthBar'

// The merchant's truth. Order card + the gated action.
// Pressing "Ask customer to pay again" while PENDING/UNKNOWN triggers the
// gate-slam: the real policy decision made visible.

const BLOCKING_STATES = new Set(['PENDING', 'OUTCOME_UNKNOWN', ''])

function LockGlyph({ color }: { color: string }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
      <rect x="2.5" y="5.5" width="7" height="5" rx="1" stroke={color} strokeWidth="1.1" />
      <path d="M4 5.5V4a2 2 0 0 1 4 0v1.5" stroke={color} strokeWidth="1.1" />
    </svg>
  )
}

export function ConsolePane({
  decision,
}: {
  events: SimEvent[]
  decision: AgentDecision | null
}) {
  const [slammed, setSlammed] = useState(false)

  const state = decision?.state ?? ''
  const isBlocking = decision === null || BLOCKING_STATES.has(state)
  const evidenceIds = decision?.authoritative_evidence_ids ?? []

  const handleGatedPress = () => {
    if (!isBlocking) return
    setSlammed(false)
    // restart the shake animation on each press
    requestAnimationFrame(() => setSlammed(true))
  }

  // Resolved-state action variants
  const resolved = decision && !isBlocking

  return (
    <div className="flex flex-col h-full p-5" style={{ background: 'var(--bg-1)' }}>
      <div className="mb-4">
        <p
          className="mono text-xs uppercase"
          style={{ letterSpacing: '0.08em', color: 'var(--muted)' }}
        >
          MERCHANT&apos;S TRUTH
        </p>
        <h2
          className="text-[17px] font-[590] mt-1"
          style={{ color: 'var(--ink)', letterSpacing: '-0.012em' }}
        >
          FitCart console
        </h2>
      </div>

      <div className="flex-1 min-h-0 flex flex-col">
        {/* Order card */}
        <div
          className="rounded-lg border overflow-hidden"
          style={{ borderColor: 'var(--hairline)', background: 'var(--bg-2)' }}
        >
          <div
            className="flex items-center justify-between px-4 py-3 border-b"
            style={{ borderColor: 'var(--hairline)' }}
          >
            <span className="mono tabular text-sm text-ink">#1241 · ₹499.00</span>
            {decision ? (
              <Pill state={stateToPillVariant(state)} mono>
                {state || 'UNPAID'}
              </Pill>
            ) : (
              <Pill state="pending" mono>
                UNPAID
              </Pill>
            )}
          </div>
          <div className="px-4 py-2.5 flex justify-between border-b" style={{ borderColor: 'var(--hairline)' }}>
            <span className="text-xs text-muted">Customer</span>
            <span className="mono text-xs text-body">Aarav S.</span>
          </div>
          <div className="px-4 py-2.5 flex justify-between">
            <span className="text-xs text-muted">Items</span>
            <span className="mono text-xs text-body">FitCart · 1 item</span>
          </div>
        </div>

        {/* Gated action */}
        <div className="mt-4">
          {isBlocking && (
            <>
              <button
                onClick={handleGatedPress}
                onAnimationEnd={() => setSlammed(false)}
                className={`w-full py-3 rounded-md text-sm font-medium transition-all ${slammed ? 'animate-shake' : ''}`}
                style={{
                  background: slammed ? 'var(--blocked)' : 'var(--bg-3)',
                  color: slammed ? '#fff' : 'var(--body)',
                  border: `1px solid ${slammed ? 'var(--blocked)' : 'var(--hairline-strong)'}`,
                }}
              >
                Ask customer to pay again
              </button>

              {slammed && (
                <div
                  className="mt-3 p-3 rounded-md border"
                  style={{ background: 'var(--blocked-soft)', borderColor: 'rgba(229,72,77,0.3)' }}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <LockGlyph color="var(--blocked)" />
                    <span className="mono text-xs font-semibold" style={{ color: 'var(--blocked)' }}>
                      BLOCKED · Payment still {state || 'PENDING'}
                    </span>
                  </div>
                  <p className="mono text-[11px] leading-relaxed" style={{ color: 'var(--body)' }}>
                    Rule: never retry while unresolved
                  </p>
                  {evidenceIds.length > 0 && (
                    <p className="mono text-[11px] mt-1" style={{ color: 'var(--muted)' }}>
                      Evidence: {evidenceIds.join(', ')}
                    </p>
                  )}
                </div>
              )}
            </>
          )}

          {resolved && state === 'FAILED' && (
            <button
              className="w-full py-3 rounded-md text-sm font-medium text-white"
              style={{ background: 'var(--accent)' }}
            >
              Create one recovery link (Test Mode)
            </button>
          )}

          {resolved && state === 'CAPTURED_UNLINKED' && (
            <>
              <button
                className="w-full py-3 rounded-md text-sm font-medium text-white"
                style={{ background: 'var(--recovered)' }}
              >
                Reconcile order
              </button>
              <p className="mono text-[11px] mt-2" style={{ color: 'var(--muted)' }}>
                no new charge — links the existing capture to #1241
              </p>
            </>
          )}

          {resolved && state === 'DUPLICATE_SUCCESS' && (
            <>
              <button
                className="w-full py-3 rounded-md text-sm font-medium"
                style={{
                  background: 'var(--pending-soft)',
                  color: 'var(--pending)',
                  border: '1px solid rgba(232,163,61,0.3)',
                }}
              >
                Open refund review
              </button>
              <p className="mono text-[11px] mt-2" style={{ color: 'var(--muted)' }}>
                no automatic refund — human approves
              </p>
            </>
          )}
        </div>
      </div>

      {/* TruthBar pinned at bottom */}
      <TruthBar decision={decision} />
    </div>
  )
}
