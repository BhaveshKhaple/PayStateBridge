'use client'

import { useEffect, useState } from 'react'
import { useSimStream } from '@/lib/useSimStream'
import { PhonePane } from '@/components/world/PhonePane'
import { RailsPane } from '@/components/world/RailsPane'
import { ConsolePane } from '@/components/world/ConsolePane'
import { MetricsRibbon } from '@/components/world/MetricsRibbon'
import { Timeline } from '@/components/world/Timeline'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface StoryMeta {
  story_id: string
  title: string
  subtitle: string
  expected_final_state: string
  narration: string
}

export default function WorldPage() {
  const { state, play, reset } = useSimStream()
  const [stories, setStories] = useState<StoryMeta[]>([])

  useEffect(() => {
    fetch(`${API_URL}/v1/sim/stories`)
      .then((r) => r.json())
      .then(setStories)
      .catch(() => setStories([]))
  }, [])

  return (
    <div className="h-[100dvh] flex flex-col overflow-hidden" style={{ background: 'var(--bg-0)' }}>
      {/* TopBar */}
      <header
        className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: 'var(--hairline)' }}
      >
        <div className="flex items-center gap-3">
          <span className="font-[590] text-ink">PayState Bridge</span>
          <span className="mono text-xs text-muted">· Track 03 · PayState World</span>
        </div>
        <div className="flex items-center gap-2">
          {stories.map((s) => (
            <button
              key={s.story_id}
              onClick={() => play(s.story_id)}
              className="mono text-xs px-3 py-1.5 rounded-md border transition-all hover:bg-bg-2"
              style={{ borderColor: 'var(--hairline-strong)', color: 'var(--body)' }}
            >
              {s.title}
            </button>
          ))}
          <button
            onClick={reset}
            className="mono text-xs px-3 py-1.5 rounded-md"
            style={{ color: 'var(--muted)' }}
          >
            reset
          </button>
        </div>
      </header>

      {/* Metrics ribbon */}
      <MetricsRibbon events={state.events} decision={state.decision} />

      {/* Three panes */}
      <div className="flex-1 grid min-h-0" style={{ gridTemplateColumns: '1fr 1.2fr 1fr' }}>
        <div className="border-r" style={{ borderColor: 'var(--hairline)' }}>
          <PhonePane events={state.events} decision={state.decision} />
        </div>
        <div className="border-r" style={{ borderColor: 'var(--hairline)' }}>
          <RailsPane events={state.events} />
        </div>
        <div>
          <ConsolePane events={state.events} decision={state.decision} />
        </div>
      </div>

      {/* Timeline */}
      <div className="border-t" style={{ borderColor: 'var(--hairline)' }}>
        <Timeline events={state.events} decision={state.decision} />
      </div>
    </div>
  )
}
