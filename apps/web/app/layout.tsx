import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PayState Bridge',
  description:
    'Resolves payment ambiguity before retrying — Razorpay AI Buildathon Track 03',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased" style={{ background: 'var(--bg-0)', color: 'var(--ink)' }}>
        {children}
      </body>
    </html>
  )
}
