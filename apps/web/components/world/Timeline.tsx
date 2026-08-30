'use client'

import { useEffect, useRef } from 'react'
import { EventRow } from '@/components/ui'
import type { AgentDecision, SimEvent } from '@/lib/useSimStream'

// The audit trail made visible — a bottom strip of event rows.
// New rows flash once (animate-row-flash) then settle.

function formatOffset(ms: number): string {
  const s = ms / 1000
  return `T+${s.toFixed(1)}s`
}

export function Timeline({
  events,
  decision,
}: {
  events: SimEvent[]
  decision: AgentDecision | null
}) {
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const prevLen = useRef(0)

  // Auto-scroll to the newest row as events stream in.
  useEffect(() => {
    if (events.length > prevLen.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
    prevLen.current = events.length
  }, [events.length])

  const lastSeq = events.length ? events[events.length - 1].seq : -1

  return (
    <div className="h-[120px] flex flex-col" style={{ background: 'var(--bg-0)' }}>
      <div
        className="px-4 py-1.5 border-b flex items-center justify-between"
        style={{ borderColor: 'var(--hairline)' }}
      >
        <span
          className="mono text-[10px] uppercase"
          style={{ letterSpacing: '0.08em', color: 'var(--faint)' }}
        >
          EVENT TIMELINE — audit trail
        </span>
        <span className="mono text-[10px]" style={{ color: 'var(--faint)' }}>
          {events.length} events
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-2">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <span className="mono text-xs text-faint">pick a story to begin</span>
          </div>
        ) : (
          events.map((e, i) => {
            const isLast = i === events.length - 1
            // Attach the resolved state pill to the agent_decision row.
            const showState =
              e.type === 'agent_decision' && decision ? decision.state : undefined
            return (
              <EventRow
                key={e.seq}
                timestamp={formatOffset(e.t_offset_ms)}
                label={e.label}
                state={showState}
                isNew={isLast && e.seq === lastSeq}
              />
            )
          })
        )}
      </div>
    </div>
  )
}
