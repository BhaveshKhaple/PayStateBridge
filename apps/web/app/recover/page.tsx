'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button, Pill, stateToPillVariant } from '@/components/ui'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Citation = {
  rule_id: string
  title: string
  principle: string
  source: string
  source_kind: 'razorpay' | 'npci' | 'paystate_policy'
}

type LookupResult = {
  found?: boolean
  error?: string
  data_source?: string
  note?: string
  lookup_id?: string
  payment?: {
    payment_id: string
    order_id: string | null
    amount_paise: number | null
    amount_rupees: number
    status: string | null
    raw_status: string | null
    method: string | null
  }
  decision?: {
    state: string
    action: string
    reason_codes: string[]
    citations?: Citation[]
    customer_message: string
    policy_version: string
  }
  safe?: boolean
}

const EXAMPLES: { id: string; label: string }[] = [
  { id: 'pay_demo_001', label: 'pending' },
  { id: 'pay_demo_002', label: 'captured' },
  { id: 'pay_demo_005', label: 'failed' },
  { id: 'pay_demo_007', label: 'captured-unlinked' },
]

const DANGER_STATES = new Set(['PENDING', 'OUTCOME_UNKNOWN'])

const SOURCE_CHIP: Record<
  Citation['source_kind'],
  { label: string; bg: string; fg: string; border: string }
> = {
  razorpay: {
    label: 'Razorpay',
    bg: 'var(--accent-soft, rgba(99,102,241,0.12))',
    fg: 'var(--accent, #a5b4fc)',
    border: '1px solid rgba(99,102,241,0.35)',
  },
  npci: {
    label: 'NPCI / RBI',
    bg: 'var(--pending-soft)',
    fg: 'var(--pending)',
    border: '1px solid rgba(232,163,61,0.35)',
  },
  paystate_policy: {
    label: 'PayState policy',
    bg: 'var(--bg-2)',
    fg: 'var(--muted)',
    border: '1px solid var(--hairline-strong)',
  },
}

export default function RecoverPage() {
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LookupResult | null>(null)

  async function check(id?: string) {
    const lookupId = (id ?? value).trim()
    if (!lookupId) {
      setError('Paste a payment or order ID first.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`${API_URL}/v1/recover/lookup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_id: lookupId }),
      })
      if (!res.ok) {
        throw new Error(`Lookup failed (${res.status})`)
      }
      const data: LookupResult = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (e) {
      setError(
        e instanceof Error
          ? `${e.message}. Is the API running at ${API_URL}?`
          : 'Lookup failed.',
      )
    } finally {
      setLoading(false)
    }
  }

  function fillExample(id: string) {
    setValue(id)
    setError(null)
    check(id)
  }

  const isReal = result?.data_source === 'razorpay_test'
  const state = result?.decision?.state
  const isDanger = state ? DANGER_STATES.has(state) : false
  const isFailed = state === 'FAILED'

  return (
    <main
      className="min-h-screen px-4 py-16 flex justify-center"
      style={{ background: 'var(--bg-0)', color: 'var(--ink)' }}
    >
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="space-y-3">
          <div
            className="mono text-xs uppercase tracking-widest"
            style={{ color: 'var(--muted)', letterSpacing: '0.08em' }}
          >
            PayState Bridge · Recover
          </div>
          <h1
            className="text-[28px] font-semibold leading-tight"
            style={{ letterSpacing: '-0.02em' }}
          >
            Check a payment
          </h1>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--body)' }}>
            Paste a Razorpay payment or order ID. We tell you the safe next action
            — before you ask the customer to pay again.
          </p>
        </div>

        {/* Input */}
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') check()
              }}
              placeholder="pay_XXXXXXXXXXXX or order_XXXXXXXXXXXX"
              spellCheck={false}
              className="mono flex-1 px-3 py-2 rounded-md text-sm outline-none"
              style={{
                background: 'var(--bg-2)',
                border: '1px solid var(--hairline-strong)',
                color: 'var(--ink)',
              }}
            />
            <Button
              variant="primary"
              onClick={() => check()}
              disabled={loading}
            >
              {loading ? 'Checking…' : 'Check'}
            </Button>
          </div>

          {/* Examples */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="mono text-xs" style={{ color: 'var(--faint)' }}>
              try:
            </span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.id}
                onClick={() => fillExample(ex.id)}
                className="mono text-xs px-2 py-1 rounded-md transition-colors"
                style={{
                  background: 'var(--bg-2)',
                  border: '1px solid var(--hairline)',
                  color: 'var(--body)',
                }}
              >
                {ex.id}
                <span style={{ color: 'var(--faint)' }}> · {ex.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div
            className="rounded-md px-4 py-3 text-sm"
            style={{
              background: 'var(--blocked-soft)',
              border: '1px solid rgba(229,72,77,0.3)',
              color: 'var(--blocked)',
            }}
          >
            {error}
          </div>
        )}

        {/* Not found */}
        {result && result.found === false && (
          <div
            className="rounded-md px-4 py-3 text-sm"
            style={{
              background: 'var(--bg-2)',
              border: '1px solid var(--hairline)',
              color: 'var(--body)',
            }}
          >
            <span className="mono">{result.lookup_id}</span> — {result.note}
          </div>
        )}

        {/* Result card */}
        {result && result.found && result.decision && result.payment && (
          <div
            className="rounded-lg overflow-hidden"
            style={{ background: 'var(--bg-1)', border: '1px solid var(--hairline)' }}
          >
            {/* Data-source badge */}
            <div
              className="px-5 py-3 flex items-center justify-between"
              style={{ borderBottom: '1px solid var(--hairline)' }}
            >
              <span
                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium"
                style={
                  isReal
                    ? {
                        background: 'var(--recovered-soft)',
                        color: 'var(--recovered)',
                        border: '1px solid rgba(70,167,88,0.3)',
                      }
                    : {
                        background: 'var(--pending-soft)',
                        color: 'var(--pending)',
                        border: '1px solid rgba(232,163,61,0.3)',
                      }
                }
              >
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{
                    background: isReal ? 'var(--recovered)' : 'var(--pending)',
                  }}
                />
                {isReal ? 'Razorpay Test Mode' : 'Demo data (add keys for live)'}
              </span>
              <span className="mono text-xs" style={{ color: 'var(--faint)' }}>
                policy {result.decision.policy_version}
              </span>
            </div>

            {/* State + action */}
            <div className="px-5 py-4 space-y-4">
              <div className="flex items-center gap-3">
                <Pill state={stateToPillVariant(result.decision.state)}>
                  {result.decision.state}
                </Pill>
                <span className="mono text-sm" style={{ color: 'var(--body)' }}>
                  {result.decision.action}
                </span>
              </div>

              {/* Amount + payment meta */}
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                <span className="mono" style={{ color: 'var(--ink)' }}>
                  ₹{result.payment.amount_rupees.toFixed(2)}
                </span>
                <span className="mono" style={{ color: 'var(--muted)' }}>
                  {result.payment.payment_id}
                </span>
                {result.payment.method && (
                  <span className="mono" style={{ color: 'var(--muted)' }}>
                    {result.payment.method}
                  </span>
                )}
                {result.payment.raw_status && (
                  <span className="mono" style={{ color: 'var(--faint)' }}>
                    raw: {result.payment.raw_status}
                  </span>
                )}
              </div>

              {/* Reason codes */}
              <div className="flex flex-wrap gap-2">
                {result.decision.reason_codes.map((code) => (
                  <span
                    key={code}
                    className="mono text-xs px-2 py-0.5 rounded"
                    style={{
                      background: 'var(--bg-2)',
                      border: '1px solid var(--hairline)',
                      color: 'var(--muted)',
                    }}
                  >
                    {code}
                  </span>
                ))}
              </div>

              {/* Why this decision — sourced audit trail */}
              {result.decision.citations && result.decision.citations.length > 0 && (
                <div className="space-y-3">
                  <div
                    className="mono text-xs uppercase tracking-widest"
                    style={{ color: 'var(--muted)', letterSpacing: '0.08em' }}
                  >
                    Why this decision
                  </div>
                  <div className="space-y-2">
                    {result.decision.citations.map((cite) => {
                      const chip = SOURCE_CHIP[cite.source_kind]
                      return (
                        <div
                          key={cite.rule_id}
                          className="rounded-md px-4 py-3 space-y-2"
                          style={{
                            background: 'var(--bg-2)',
                            border: '1px solid var(--hairline)',
                          }}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span
                              className="mono text-xs"
                              style={{ color: 'var(--faint)' }}
                            >
                              {cite.rule_id}
                            </span>
                            <span
                              className="text-xs font-medium px-2 py-0.5 rounded-md whitespace-nowrap"
                              style={{
                                background: chip.bg,
                                color: chip.fg,
                                border: chip.border,
                              }}
                            >
                              {chip.label}
                            </span>
                          </div>
                          <div
                            className="text-sm font-semibold leading-snug"
                            style={{ color: 'var(--ink)' }}
                          >
                            {cite.title}
                          </div>
                          <p
                            className="text-sm leading-relaxed"
                            style={{ color: 'var(--body)' }}
                          >
                            {cite.principle}
                          </p>
                          <div
                            className="mono text-xs leading-relaxed"
                            style={{ color: 'var(--faint)' }}
                          >
                            {cite.source}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Customer message */}
              <div
                className="rounded-md px-4 py-3 text-sm leading-relaxed"
                style={{
                  background: 'var(--bg-2)',
                  border: '1px solid var(--hairline)',
                  color: 'var(--body)',
                }}
              >
                {result.decision.customer_message}
              </div>

              {/* Verdict banner */}
              {isDanger && (
                <div
                  className="rounded-md px-4 py-3 text-sm font-medium"
                  style={{
                    background: 'var(--blocked-soft)',
                    border: '1px solid rgba(229,72,77,0.3)',
                    color: 'var(--blocked)',
                  }}
                >
                  Do not ask the customer to pay again. The first payment is not
                  conclusively resolved.
                </div>
              )}
              {isFailed && (
                <div
                  className="rounded-md px-4 py-3 text-sm font-medium"
                  style={{
                    background: 'var(--recovered-soft)',
                    border: '1px solid rgba(70,167,88,0.3)',
                    color: 'var(--recovered)',
                  }}
                >
                  Safe to send one recovery link.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Back link */}
        <div>
          <Link
            href="/"
            className="mono text-xs"
            style={{ color: 'var(--muted)' }}
          >
            ← back
          </Link>
        </div>
      </div>
    </main>
  )
}
