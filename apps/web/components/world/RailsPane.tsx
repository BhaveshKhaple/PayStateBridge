'use client'

import { useState } from 'react'
import type { SimEvent } from '@/lib/useSimStream'

// The god view. Four nodes on a horizontal line; a packet dot travels the line
// driven by packet_* events. This is the "nobody shows you this" moment —
// keep it diagram-clean.

const NODES = [
  { id: 'customer_bank', label: 'Customer Bank' },
  { id: 'upi_switch', label: 'UPI Switch' },
  { id: 'razorpay', label: 'Razorpay' },
  { id: 'merchant', label: 'Merchant' },
] as const

// Map an event's node -> index on the line.
const NODE_INDEX: Record<string, number> = {
  customer_bank: 0,
  upi_switch: 1,
  razorpay: 2,
  merchant: 3,
}

// Map packet_* event types to the node position they represent.
const PACKET_NODE: Record<string, string> = {
  packet_at_bank: 'customer_bank',
  packet_at_switch: 'upi_switch',
  packet_at_psp: 'razorpay',
  packet_at_merchant: 'merchant',
}

interface PacketDerived {
  index: number | null // 0..3 node index the packet currently sits at
  stuck: boolean
  lost: boolean
}

function derivePacket(events: SimEvent[]): PacketDerived {
  let index: number | null = null
  let stuck = false
  let lost = false

  for (const e of events) {
    if (e.type in PACKET_NODE) {
      index = NODE_INDEX[PACKET_NODE[e.type]]
      stuck = false
      lost = false
    } else if (e.type === 'packet_stuck') {
      // node may indicate where it stalled
      if (e.node && e.node in NODE_INDEX) index = NODE_INDEX[e.node]
      stuck = true
    } else if (e.type === 'packet_lost') {
      if (e.node && e.node in NODE_INDEX) index = NODE_INDEX[e.node]
      lost = true
      stuck = true
    }
  }

  return { index, stuck, lost }
}

const CHAOS = [
  { id: 'lose_webhook', label: 'lose webhook' },
  { id: 'retry_storm', label: 'retry storm' },
  { id: 'bank_timeout', label: 'bank timeout' },
  { id: 'double_click', label: 'double-click race' },
] as const

export function RailsPane({ events }: { events: SimEvent[] }) {
  const packet = derivePacket(events)
  const [armed, setArmed] = useState<Record<string, boolean>>({})
  const [delay, setDelay] = useState(0)

  const toggle = (id: string) =>
    setArmed((a) => ({ ...a, [id]: !a[id] }))

  const anyArmed = Object.values(armed).some(Boolean) || delay > 0

  // Packet horizontal position as a % across the 4 nodes (0%, 33%, 66%, 100%).
  const pct = packet.index === null ? 0 : (packet.index / (NODES.length - 1)) * 100
  const packetColor = packet.lost || packet.stuck ? 'var(--pending)' : 'var(--accent)'

  return (
    <div className="flex flex-col h-full p-5" style={{ background: 'var(--bg-1)' }}>
      <div className="mb-4">
        <p
          className="mono text-xs uppercase"
          style={{ letterSpacing: '0.08em', color: 'var(--muted)' }}
        >
          THE RAILS
        </p>
        <h2
          className="text-[17px] font-[590] mt-1"
          style={{ color: 'var(--ink)', letterSpacing: '-0.012em' }}
        >
          God view — the network nobody shows you
        </h2>
      </div>

      {/* Node diagram */}
      <div className="flex-1 min-h-0 flex flex-col justify-center">
        <div className="relative px-6 py-10">
          {/* Base line */}
          <div
            className="absolute left-6 right-6 top-1/2 -translate-y-1/2"
            style={{
              height: '2px',
              background: packet.stuck ? 'transparent' : 'var(--hairline-strong)',
              borderTop: packet.stuck
                ? '2px dashed var(--pending)'
                : undefined,
            }}
          />

          {/* Travelling packet */}
          {packet.index !== null && (
            <div
              className="absolute top-1/2 -translate-y-1/2"
              style={{
                left: `calc(1.5rem + (100% - 3rem) * ${pct / 100})`,
                transform: 'translate(-50%, -50%)',
                transition: 'left 600ms cubic-bezier(0.25,0.46,0.45,0.94)',
              }}
            >
              <span
                className={`block w-3.5 h-3.5 rounded-full ${packet.stuck ? 'animate-packet-pulse' : ''}`}
                style={{
                  background: packetColor,
                  boxShadow: `0 0 12px ${packetColor}`,
                }}
              />
            </div>
          )}

          {/* Nodes */}
          <div className="relative flex items-center justify-between">
            {NODES.map((n, i) => {
              const active = packet.index !== null && i <= packet.index
              return (
                <div key={n.id} className="flex flex-col items-center gap-2" style={{ width: '72px' }}>
                  <span
                    className="w-12 h-12 rounded-full flex items-center justify-center text-[10px] mono"
                    style={{
                      background: 'var(--bg-2)',
                      border: `1.5px solid ${active ? 'var(--accent)' : 'var(--hairline-strong)'}`,
                      color: active ? 'var(--ink)' : 'var(--faint)',
                    }}
                  >
                    {i + 1}
                  </span>
                  <span
                    className="mono text-[10px] text-center leading-tight"
                    style={{ color: 'var(--muted)' }}
                  >
                    {n.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Lost webhook label */}
        {packet.lost && (
          <div className="text-center mb-2">
            <span
              className="mono text-xs px-2 py-1 rounded-md"
              style={{ background: 'var(--blocked-soft)', color: 'var(--blocked)' }}
            >
              webhook LOST — merchant never told
            </span>
          </div>
        )}
        {packet.stuck && !packet.lost && (
          <div className="text-center mb-2">
            <span
              className="mono text-xs px-2 py-1 rounded-md"
              style={{ background: 'var(--pending-soft)', color: 'var(--pending)' }}
            >
              packet STUCK — capture pending
            </span>
          </div>
        )}
      </div>

      {/* Chaos Panel */}
      <div className="mt-auto pt-4 border-t" style={{ borderColor: 'var(--hairline)' }}>
        <p
          className="mono text-[10px] uppercase mb-3"
          style={{ letterSpacing: '0.08em', color: 'var(--faint)' }}
        >
          CHAOS PANEL — break the world
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
          {CHAOS.map((c) => (
            <button
              key={c.id}
              onClick={() => toggle(c.id)}
              className="mono text-[11px] px-2.5 py-1.5 rounded-md border transition-all"
              style={{
                borderColor: armed[c.id] ? 'rgba(232,163,61,0.4)' : 'var(--hairline-strong)',
                background: armed[c.id] ? 'var(--pending-soft)' : 'transparent',
                color: armed[c.id] ? 'var(--pending)' : 'var(--body)',
              }}
            >
              {c.label}
              {armed[c.id] && ' · armed'}
            </button>
          ))}
        </div>

        {/* Webhook delay slider */}
        <div className="flex items-center gap-3">
          <label className="mono text-[11px] whitespace-nowrap" style={{ color: 'var(--body)' }}>
            webhook delay
          </label>
          <input
            type="range"
            min={0}
            max={120}
            value={delay}
            onChange={(e) => setDelay(Number(e.target.value))}
            className="flex-1"
            style={{ accentColor: 'var(--pending)' }}
          />
          <span
            className="mono tabular text-[11px] w-12 text-right"
            style={{ color: delay > 0 ? 'var(--pending)' : 'var(--faint)' }}
          >
            {delay}s
          </span>
        </div>

        {anyArmed && (
          <p className="mono text-[10px] mt-2" style={{ color: 'var(--faint)' }}>
            armed — replays in next story run
          </p>
        )}
      </div>
    </div>
  )
}
