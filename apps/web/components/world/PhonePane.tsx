'use client'

import type { AgentDecision, SimEvent } from '@/lib/useSimStream'

// The customer's truth — a fake UPI app phone frame.
// The inner screen is LIGHT (#ffffff, dark text): a deliberate contrast island
// that pops out of the dark war room.

type PhoneStage = 'idle' | 'processing' | 'debited' | 'paying_again' | 'confirmed'

function deriveStage(events: SimEvent[], decision: AgentDecision | null): PhoneStage {
  const types = new Set(events.map((e) => e.type))
  const recovered =
    decision?.state === 'CAPTURED_UNLINKED' || decision?.action === 'RECONCILE'

  if (decision && recovered) return 'confirmed'
  if (types.has('customer_pay_again')) return 'paying_again'
  if (types.has('customer_debited')) return 'debited'
  if (types.has('customer_initiated')) return 'processing'
  return 'idle'
}

// Pull the SMS ref + amount out of the debit event payload, with sane fallbacks.
function debitDetails(events: SimEvent[]): { amount: string; ref: string } {
  const debit = events.find((e) => e.type === 'customer_debited')
  const paise =
    (debit?.payload?.amount_paise as number | undefined) ??
    (debit?.payload?.amount as number | undefined)
  const amount = typeof paise === 'number' ? formatInr(paise) : '499.00'
  const ref =
    (debit?.payload?.ref as string | undefined) ??
    (debit?.payload?.utr as string | undefined) ??
    '3124'
  return { amount, ref }
}

function formatInr(paise: number): string {
  const rupees = paise / 100
  return rupees.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function Spinner({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-6">
      <span
        className="inline-block w-8 h-8 rounded-full border-[3px] border-neutral-200 animate-spin"
        style={{ borderTopColor: '#111827' }}
      />
      <span className="text-sm font-medium text-neutral-900">{label}</span>
      <span className="text-xs text-neutral-400">Do not press back</span>
    </div>
  )
}

export function PhonePane({
  events,
  decision,
}: {
  events: SimEvent[]
  decision: AgentDecision | null
}) {
  const stage = deriveStage(events, decision)
  const { amount, ref } = debitDetails(events)
  const showSms = stage === 'debited' || stage === 'paying_again' || stage === 'confirmed'

  return (
    <div className="flex flex-col h-full p-5" style={{ background: 'var(--bg-1)' }}>
      <div className="mb-4">
        <p
          className="mono text-xs uppercase"
          style={{ letterSpacing: '0.08em', color: 'var(--muted)' }}
        >
          CUSTOMER&apos;S TRUTH
        </p>
        <h2
          className="text-[17px] font-[590] mt-1"
          style={{ color: 'var(--ink)', letterSpacing: '-0.012em' }}
        >
          Aarav&apos;s phone
        </h2>
      </div>

      {/* Phone frame */}
      <div className="flex-1 min-h-0 flex items-center justify-center">
        <div
          className="relative w-[280px] h-[560px] max-h-full flex flex-col overflow-hidden"
          style={{
            borderRadius: 'var(--r-phone)',
            border: '1px solid var(--hairline-strong)',
            background: 'var(--bg-0)',
            padding: '10px',
            boxShadow: 'var(--shadow-float)',
          }}
        >
          {/* Inner LIGHT screen — the contrast island */}
          <div
            className="relative flex-1 flex flex-col overflow-hidden text-neutral-900"
            style={{ borderRadius: '28px', background: '#ffffff' }}
          >
            {/* Status bar */}
            <div className="flex items-center justify-between px-5 pt-3 pb-1">
              <span className="mono text-xs text-neutral-900">8:00</span>
              <span className="flex items-center gap-1">
                {/* battery glyph */}
                <span className="relative inline-block w-6 h-3 rounded-[3px] border border-neutral-400">
                  <span className="absolute inset-[2px] right-[6px] rounded-[1px] bg-neutral-800" />
                </span>
                <span className="inline-block w-[2px] h-1.5 rounded-r-sm bg-neutral-400" />
              </span>
            </div>

            {/* SMS banner slides down from top */}
            {showSms && (
              <div
                className="mx-3 mt-1 mb-2 px-3 py-2 rounded-lg border"
                style={{
                  background: '#f4f6f8',
                  borderColor: '#e2e6ea',
                  animation: 'phoneSmsDrop 320ms ease-out',
                }}
              >
                <p className="mono text-[11px] leading-snug text-neutral-700">
                  <span className="font-semibold text-neutral-900">BH-HDFCBK</span>
                  {' • '}
                  ₹{amount} debited
                  {' • '}
                  Ref {ref}
                </p>
              </div>
            )}

            {/* Wordmark */}
            <div className="px-5 pt-2">
              <span className="text-lg font-semibold tracking-tight text-neutral-900">
                UPI Pay
              </span>
              <span className="ml-2 text-[10px] uppercase tracking-wider text-neutral-400 align-middle">
                demo
              </span>
            </div>

            {/* Pay sheet */}
            <div className="flex-1 flex flex-col justify-end p-4">
              <div
                className="rounded-2xl border p-4"
                style={{ borderColor: '#eceff2', background: '#fafbfc' }}
              >
                {/* Payee */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold text-white bg-neutral-800">
                    FC
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-neutral-900 truncate">FitCart</p>
                    <p className="mono text-[11px] text-neutral-500 truncate">
                      Paying from Aarav S.
                    </p>
                  </div>
                </div>

                {/* Amount */}
                <div className="text-center mb-4">
                  <span className="mono tabular text-[28px] font-semibold text-neutral-900">
                    ₹{amount}
                  </span>
                </div>

                {/* Stage-driven action area */}
                {stage === 'idle' && (
                  <button
                    className="w-full py-3 rounded-xl text-sm font-semibold text-white bg-neutral-900"
                    disabled
                  >
                    Pay ₹{amount}
                  </button>
                )}

                {(stage === 'processing' || stage === 'paying_again') && (
                  <Spinner label="Processing…" />
                )}

                {stage === 'debited' && (
                  <button
                    className="w-full py-3 rounded-xl text-sm font-semibold text-neutral-900 bg-white animate-border-pulse"
                    style={{ border: '2px solid var(--pending)' }}
                    disabled
                  >
                    Pay again
                  </button>
                )}

                {stage === 'confirmed' && (
                  <div
                    className="w-full py-3 rounded-xl text-sm font-semibold text-center flex items-center justify-center gap-2"
                    style={{ background: 'var(--recovered-soft)', color: 'var(--recovered)' }}
                  >
                    <span
                      className="inline-block w-4 h-4 rounded-full"
                      style={{ background: 'var(--recovered)' }}
                    />
                    Order confirmed
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
