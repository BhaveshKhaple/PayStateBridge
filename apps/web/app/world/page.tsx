'use client'

import { useEffect, useMemo, useState } from 'react'
import { useSimStream } from '@/lib/useSimStream'
import { PhonePane } from '@/components/world/PhonePane'
import { RailsPane } from '@/components/world/RailsPane'
import { ConsolePane } from '@/components/world/ConsolePane'
import { MetricsRibbon } from '@/components/world/MetricsRibbon'
import { Timeline } from '@/components/world/Timeline'
import { StoryPicker, type StoryMeta } from '@/components/world/StoryPicker'
import { Scrubber } from '@/components/world/Scrubber'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WorldPage() {
  const { state, play, reset } = useSimStream()
  const [stories, setStories] = useState<StoryMeta[]>([])
  // null → live (full stream); number → replay as-of that event index.
  const [scrubIndex, setScrubIndex] = useState<number | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/v1/sim/stories`)
      .then((r) => r.json())
      .then(setStories)
      .catch(() => setStories([]))
  }, [])

  const handlePlay = (id: string) => {
    setScrubIndex(null)
    play(id)
  }

  const handleReset = () => {
    setScrubIndex(null)
    reset()
  }

  // When scrubbing, panes render the world AS OF the selected event index.
  const viewEvents = useMemo(() => {
    if (scrubIndex === null) return state.events
    return state.events.slice(0, scrubIndex + 1)
  }, [state.events, scrubIndex])

  // The decision only exists once the agent_decision event is within view.
  const viewDecision = useMemo(() => {
    if (scrubIndex === null) return state.decision
    const decisionSeen = viewEvents.some((e) => e.type === 'agent_decision')
    return decisionSeen ? state.decision : null
  }, [state.decision, scrubIndex, viewEvents])

  const started = state.events.length > 0 || state.running
  const activeStory = stories.find((s) => s.story_id === state.storyId)

  return (
    <div
      className="relative h-[100dvh] flex flex-col overflow-hidden"
      style={{ background: 'var(--bg-0)' }}
    >
      {/* Hero overlay — story cards, shown until a story starts */}
      {!started && <StoryPicker stories={stories} onPlay={handlePlay} />}

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
              onClick={() => handlePlay(s.story_id)}
              className="mono text-xs px-3 py-1.5 rounded-md border transition-all hover:bg-bg-2"
              style={{
                borderColor:
                  s.story_id === state.storyId
                    ? 'var(--accent)'
                    : 'var(--hairline-strong)',
                color: s.story_id === state.storyId ? 'var(--ink)' : 'var(--body)',
              }}
            >
              {s.title}
            </button>
          ))}
          <button
            onClick={handleReset}
            className="mono text-xs px-3 py-1.5 rounded-md"
            style={{ color: 'var(--muted)' }}
          >
            reset
          </button>
        </div>
      </header>

      {/* Metrics ribbon (always live totals) */}
      <MetricsRibbon events={state.events} decision={state.decision} />

      {/* Narration caption */}
      {activeStory?.narration && (
        <div
          className="px-6 py-2 border-b"
          style={{ borderColor: 'var(--hairline)', background: 'var(--bg-0)' }}
        >
          <p className="mono text-[11px] leading-snug" style={{ color: 'var(--muted)' }}>
            {activeStory.narration}
          </p>
        </div>
      )}

      {/* Scrubber */}
      <Scrubber
        events={state.events}
        scrubIndex={scrubIndex}
        setScrubIndex={setScrubIndex}
        running={state.running}
      />

      {/* Three panes */}
      <div className="flex-1 grid min-h-0" style={{ gridTemplateColumns: '1fr 1.2fr 1fr' }}>
        <div className="border-r" style={{ borderColor: 'var(--hairline)' }}>
          <PhonePane events={viewEvents} decision={viewDecision} />
        </div>
        <div className="border-r" style={{ borderColor: 'var(--hairline)' }}>
          <RailsPane events={viewEvents} />
        </div>
        <div>
          <ConsolePane events={viewEvents} decision={viewDecision} />
        </div>
      </div>

      {/* Timeline */}
      <div className="border-t" style={{ borderColor: 'var(--hairline)' }}>
        <Timeline events={state.events} decision={state.decision} />
      </div>
    </div>
  )
}
