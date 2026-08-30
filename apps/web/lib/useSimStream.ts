'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SimEvent {
  seq: number
  t_offset_ms: number
  type: string
  node: string | null
  label: string
  payload: Record<string, unknown>
  pane: 'customer' | 'rails' | 'merchant' | 'all'
}

export interface AgentDecision {
  state: string
  action: string
  reason_codes: string[]
  customer_message: string
  authoritative_evidence_ids: string[]
  policy_version: string
}

export interface SimState {
  running: boolean
  storyId: string | null
  events: SimEvent[]
  decision: AgentDecision | null
  finished: boolean
}

const INITIAL: SimState = {
  running: false,
  storyId: null,
  events: [],
  decision: null,
  finished: false,
}

export function useSimStream() {
  const [state, setState] = useState<SimState>(INITIAL)
  const esRef = useRef<EventSource | null>(null)

  const stop = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
    setState((s) => ({ ...s, running: false }))
  }, [])

  const play = useCallback((storyId: string, speed = 1.5) => {
    esRef.current?.close()
    setState({ ...INITIAL, running: true, storyId })

    const es = new EventSource(`${API_URL}/v1/sim/stream?story=${storyId}&speed=${speed}`)
    esRef.current = es

    es.addEventListener('sim', (e) => {
      const ev = JSON.parse((e as MessageEvent).data) as SimEvent
      setState((s) => ({ ...s, events: [...s.events, ev] }))
    })
    es.addEventListener('decision', (e) => {
      const d = JSON.parse((e as MessageEvent).data) as AgentDecision
      setState((s) => ({ ...s, decision: d }))
    })
    es.addEventListener('end', () => {
      setState((s) => ({ ...s, running: false, finished: true }))
      es.close()
      esRef.current = null
    })
    es.onerror = () => {
      setState((s) => ({ ...s, running: false }))
      es.close()
      esRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
    setState(INITIAL)
  }, [])

  useEffect(() => () => esRef.current?.close(), [])

  return { state, play, stop, reset }
}
