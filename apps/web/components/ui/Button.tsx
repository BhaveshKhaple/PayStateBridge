type Variant = 'primary' | 'ghost' | 'danger' | 'safe'

const VARIANTS: Record<Variant, string> = {
  primary: 'text-white',
  ghost: 'text-body border',
  danger: 'text-white',
  safe: 'text-white',
}

export function Button({
  variant = 'primary',
  children,
  className = '',
  style = {},
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const base = 'inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed'
  const variantStyle: React.CSSProperties =
    variant === 'primary' ? { background: 'var(--accent)' }
    : variant === 'danger' ? { background: 'var(--blocked)' }
    : variant === 'safe' ? { background: 'var(--recovered)' }
    : { background: 'transparent', borderColor: 'var(--hairline-strong)' }
  return (
    <button className={`${base} ${VARIANTS[variant]} ${className}`} style={{ ...variantStyle, ...style }} {...props}>
      {children}
    </button>
  )
}
