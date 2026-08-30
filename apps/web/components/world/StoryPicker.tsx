'use client'

import { Pill, stateToPillVariant } from '@/components/ui'

export interface StoryMeta {
  story_id: string
  title: string
  subtitle: string
  expected_final_state: string
  narration: string
}

// The hero landing: 3 story cards shown as an overlay when no story has run.
// Clicking a card plays it; once running, the World takes over.

export function StoryPicker({
  stories,
  onPlay,
}: {
  stories: StoryMeta[]
  onPlay: (id: string) => void
}) {
  return (
    <div
      className="absolute inset-0 z-20 flex flex-col items-center justify-center px-8"
      style={{ background: 'rgba(10,10,11,0.94)' }}
    >
      <div className="max-w-4xl w-full">
        <div className="text-center mb-10">
          <p
            className="mono text-xs uppercase mb-3"
            style={{ letterSpacing: '0.08em', color: 'var(--muted)' }}
          >
            JUDGE MODE — press a button, break the world
          </p>
          <h1
            className="text-[28px] font-[600]"
            style={{ color: 'var(--ink)', letterSpacing: '-0.02em', lineHeight: 1.15 }}
          >
            Three parties. Three truths. One stuck payment.
          </h1>
          <p className="text-sm mt-3" style={{ color: 'var(--body)' }}>
            Watch the ambiguity window — and an agent that provably refuses to make it worse.
          </p>
        </div>

        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          {stories.map((s) => (
            <button
              key={s.story_id}
              onClick={() => onPlay(s.story_id)}
              className="group text-left rounded-lg border p-5 transition-all hover:bg-bg-2"
              style={{ borderColor: 'var(--hairline-strong)', background: 'var(--bg-1)' }}
            >
              <div className="flex items-start justify-between mb-3 gap-2">
                <h3 className="text-[17px] font-[590]" style={{ color: 'var(--ink)' }}>
                  {s.title}
                </h3>
              </div>
              <p className="text-xs mb-4 leading-relaxed" style={{ color: 'var(--body)' }}>
                {s.subtitle}
              </p>
              <div className="mb-3">
                <Pill state={stateToPillVariant(s.expected_final_state)} mono>
                  {s.expected_final_state}
                </Pill>
              </div>
              {s.narration && (
                <p
                  className="mono text-[11px] leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ color: 'var(--muted)' }}
                >
                  {s.narration}
                </p>
              )}
            </button>
          ))}
        </div>

        {stories.length === 0 && (
          <p className="mono text-xs text-center mt-6" style={{ color: 'var(--faint)' }}>
            waiting for API at localhost:8000 — start the sim server
          </p>
        )}
      </div>
    </div>
  )
}
