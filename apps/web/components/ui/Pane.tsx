export function Pane({
  eyebrow,
  title,
  children,
  className = '',
}: {
  eyebrow: string
  title?: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section
      className={`flex flex-col h-full p-5 ${className}`}
      style={{ background: 'var(--bg-1)' }}
    >
      <div className="mb-4">
        <p className="mono text-xs uppercase" style={{ letterSpacing: '0.08em', color: 'var(--muted)' }}>
          {eyebrow}
        </p>
        {title && (
          <h2 className="text-[17px] font-[590] mt-1" style={{ color: 'var(--ink)', letterSpacing: '-0.012em' }}>
            {title}
          </h2>
        )}
      </div>
      <div className="flex-1 min-h-0">{children}</div>
    </section>
  )
}
