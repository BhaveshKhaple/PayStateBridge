import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CaseItem {
  id: string
  order_id: string
  state: string
  payment_state: string | null
  action: string | null
  incident_id: string | null
  created_at: string
}

const STATE_COLORS: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  FAILED: 'bg-red-100 text-red-800 border-red-200',
  CAPTURED_UNLINKED: 'bg-blue-100 text-blue-800 border-blue-200',
  DUPLICATE_SUCCESS: 'bg-purple-100 text-purple-800 border-purple-200',
  OUTCOME_UNKNOWN: 'bg-gray-100 text-gray-800 border-gray-200',
  WRONG_RECIPIENT: 'bg-orange-100 text-orange-800 border-orange-200',
  UNAUTHORIZED: 'bg-red-200 text-red-900 border-red-300',
}

async function getCases(): Promise<CaseItem[]> {
  try {
    const res = await fetch(`${API_URL}/v1/cases`, { cache: 'no-store' })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export default async function CasesPage() {
  const cases = await getCases()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">PayState Bridge</h1>
            <p className="text-xs text-gray-500">Merchant Support Console</p>
          </div>
          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded border border-amber-200">
            Synthetic · Test Mode
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-medium text-gray-900">
            Payment Cases{' '}
            <span className="text-gray-400 font-normal">({cases.length})</span>
          </h2>
          <Link
            href="/"
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Home
          </Link>
        </div>

        {cases.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <p className="text-gray-500 text-sm">No cases found.</p>
            <p className="text-gray-400 text-xs mt-1">
              Run{' '}
              <code className="bg-gray-100 px-1 rounded">
                python -m app.db.seed
              </code>{' '}
              to load synthetic incidents.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {cases.map((c) => (
              <Link
                key={c.id}
                href={`/cases/${c.id}`}
                className="block bg-white rounded-lg border border-gray-200 p-4 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm text-gray-900 font-medium">
                        {c.order_id}
                      </span>
                      {c.incident_id && (
                        <span className="text-xs text-gray-400 font-mono">
                          {c.incident_id}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Case {c.id.slice(0, 8)}… ·{' '}
                      {new Date(c.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-2">
                    {c.payment_state && (
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded border ${
                          STATE_COLORS[c.payment_state] ??
                          'bg-gray-100 text-gray-700 border-gray-200'
                        }`}
                      >
                        {c.payment_state}
                      </span>
                    )}
                    {c.action === 'DO_NOT_RETRY' && (
                      <span className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200">
                        DO NOT RETRY
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
