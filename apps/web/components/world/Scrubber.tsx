'use client'

import type { SimEvent } from '@/lib/useSimStream'

// Timeline scrubber — drag back into the ambiguity window and watch each
// pane's truth diverge and re-converge. The event log IS the state.
//
// scrubIndex === null → live (full stream). Set → panes render as-of that index.

function formatOffset(ms: number): string {
  const s = ms / 1000
  return `T+${s.toFixed(1)}s`
}

export function Scrubber({
  events,
  scrubIndex,
  setScrubIndex,
  running,
}: {
  events: SimEvent[]
  scrubIndex: number | null
  setScrubIndex: (i: number | null) => void
  running: boolean
}) {
  const max = Math.max(0, events.length - 1)
  const live = scrubIndex === null
  const current = live ? max : scrubIndex
  const currentEvent = events[current]

  return (
    <div
      className="flex items-center gap-4 px-6 py-2.5 border-b"
      style={{ borderColor: 'var(--hairline)', background: 'var(--bg-0)' }}
    >
      <button
        onClick={() => setScrubIndex(live ? max : null)}
        disabled={running}
        className="mono text-[11px] px-3 py-1 rounded-md border transition-all disabled:opacity-40"
        style={{
          borderColor: 'var(--hairline-strong)',
          color: live ? 'var(--accent)' : 'var(--body)',
          background: live ? 'var(--accent-soft)' : 'transparent',
        }}
      >
        {live ? '● live' : '⏸ scrubbing'}
      </button>

      <input
        type="range"
        min={0}
        max={max}
        value={current}
        onChange={(e) => setScrubIndex(Number(e.target.value))}
        disabled={running || events.length === 0}
        className="flex-1 disabled:opacity-40"
        style={{ accentColor: 'var(--accent)' }}
      />

      <span
        className="mono tabular text-[11px] w-20 text-right"
        style={{ color: 'var(--body)' }}
      >
        {currentEvent ? formatOffset(currentEvent.t_offset_ms) : 'T+0.0s'}
      </span>
      <span
        className="mono text-[11px] w-40 truncate"
        style={{ color: 'var(--muted)' }}
        title={currentEvent?.label}
      >
        {currentEvent?.label ?? '—'}
      </span>
    </div>
  )
}
