import Link from 'next/link'
import { notFound } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface EvidenceItem {
  id: string
  source_type: string
  event_reference: string | null
  amount_paise: number | null
  status: string | null
  occurred_at: string | null
}

interface AuditEventOut {
  id: string
  event_type: string
  actor: string
  prior_state: string | null
  new_state: string | null
  action: string | null
  reason_codes: string[] | null
  customer_message: string | null
  occurred_at: string
}

interface CaseDetail {
  id: string
  order_id: string
  state: string
  payment_state: string | null
  action: string | null
  customer_message: string | null
  incident_id: string | null
  created_at: string
  evidence: EvidenceItem[]
  audit_trail: AuditEventOut[]
}

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  gateway_event: { label: 'Gateway (authoritative)', color: 'bg-green-100 text-green-800' },
  merchant_order: { label: 'Merchant Order', color: 'bg-blue-100 text-blue-800' },
  customer_report: { label: 'Customer Report (untrusted)', color: 'bg-yellow-100 text-yellow-800' },
  synthetic_screenshot: { label: 'Synthetic Screenshot (untrusted)', color: 'bg-orange-100 text-orange-800' },
  policy: { label: 'Policy Engine', color: 'bg-purple-100 text-purple-800' },
}

async function getCase(id: string): Promise<CaseDetail | null> {
  try {
    const res = await fetch(`${API_URL}/v1/cases/${id}`, { cache: 'no-store' })
    if (res.status === 404) return null
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

function formatPaise(paise: number | null): string {
  if (!paise) return '—'
  return `₹${(paise / 100).toFixed(2)}`
}

function SafeCustomerMessage({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p className="text-xs font-medium text-blue-700 mb-1 uppercase tracking-wide">
        Safe customer reply
      </p>
      <p className="text-sm text-blue-900">{message}</p>
    </div>
  )
}

export default async function CaseDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const caseData = await getCase(params.id)
  if (!caseData) notFound()

  const isPending = caseData.payment_state === 'PENDING'
  const isOutcomeUnknown = caseData.payment_state === 'OUTCOME_UNKNOWN'
  const recoveryLinkBlocked = isPending || isOutcomeUnknown

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">PayState Bridge</h1>
            <p className="text-xs text-gray-500">Merchant Support Console</p>
          </div>
          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded border border-amber-200">
            Synthetic · Test Mode
          </span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-5">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/cases" className="hover:text-gray-700">Cases</Link>
          <span>›</span>
          <span className="text-gray-900 font-mono">{caseData.order_id}</span>
        </div>

        {/* Recovery decision banner */}
        {recoveryLinkBlocked && (
          <div className="bg-red-50 border border-red-300 rounded-lg p-4 flex items-start gap-3">
            <div className="flex-shrink-0 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center mt-0.5">
              <span className="text-white text-xs font-bold">!</span>
            </div>
            <div>
              <p className="font-semibold text-red-800 text-sm">
                Do not ask customer to pay again.
              </p>
              <p className="text-red-700 text-xs mt-0.5">
                {isPending
                  ? 'Original payment is still PENDING — outcome is unknown.'
                  : 'Payment outcome is unknown — gateway evidence is missing or conflicting.'}
              </p>
            </div>
          </div>
        )}

        {/* Case summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="font-medium text-gray-900">
              Order {caseData.order_id}
              {caseData.incident_id && (
                <span className="ml-2 text-xs text-gray-400 font-mono">
                  {caseData.incident_id}
                </span>
              )}
            </h2>
            <div className="flex items-center gap-2 flex-wrap">
              {caseData.payment_state && (
                <span className="text-xs font-mono font-medium bg-gray-100 text-gray-700 px-2 py-0.5 rounded border border-gray-300">
                  {caseData.payment_state}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <div>
              <p className="text-xs text-gray-500">Case state</p>
              <p className="font-mono text-gray-900 text-xs mt-0.5">{caseData.state}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Decision</p>
              <p className="font-mono text-gray-900 text-xs mt-0.5">{caseData.action ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Opened</p>
              <p className="text-gray-900 text-xs mt-0.5">
                {new Date(caseData.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Safe customer message */}
        <SafeCustomerMessage message={caseData.customer_message} />

        {/* Recovery action panel */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Recovery action</h3>

          {/* PENDING / OUTCOME_UNKNOWN — blocked */}
          {recoveryLinkBlocked && (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <button
                  disabled
                  className="px-4 py-2 text-sm rounded bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed"
                >
                  Create recovery link
                </button>
                <p className="text-xs text-gray-500">
                  Blocked while payment is{' '}
                  <span className="font-mono font-medium">{caseData.payment_state}</span>
                </p>
              </div>
              {isOutcomeUnknown && (
                <a
                  href={`/api/v1/cases/${caseData.id}/evidence-packet`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-4 py-2 text-sm rounded bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100"
                >
                  Download evidence packet →
                </a>
              )}
            </div>
          )}

          {/* CAPTURED_UNLINKED — reconcile */}
          {caseData.action === 'RECONCILE_ORDER' && !recoveryLinkBlocked && (
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 text-sm rounded bg-green-600 text-white hover:bg-green-700 font-medium">
                Reconcile order
              </button>
              <span className="text-xs text-gray-500">
                Links captured payment to order without new charge
              </span>
            </div>
          )}

          {/* DUPLICATE_SUCCESS — open review */}
          {caseData.action === 'OPEN_DUPLICATE_REVIEW' && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <button className="px-4 py-2 text-sm rounded bg-purple-600 text-white hover:bg-purple-700 font-medium">
                  Open duplicate review
                </button>
                <span className="text-xs text-gray-500">
                  Records both payments — no automatic refund
                </span>
              </div>
              <p className="text-xs text-amber-700 bg-amber-50 px-3 py-1.5 rounded border border-amber-200">
                Refund requires explicit merchant approval. No automatic refund in v0.
              </p>
            </div>
          )}

          {/* FAILED — recovery link (Slice 4) */}
          {caseData.action === 'CREATE_RECOVERY_PERMIT' && (
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 font-medium">
                Create Test Mode recovery link
              </button>
              <span className="text-xs text-gray-400">Razorpay Test Mode — implemented in Slice 4</span>
            </div>
          )}

          {/* WRONG_RECIPIENT */}
          {caseData.payment_state === 'WRONG_RECIPIENT' && (
            <div className="space-y-2">
              <p className="text-xs text-red-700 bg-red-50 px-3 py-2 rounded border border-red-200">
                Wrong-recipient transfer cannot be reversed by the merchant.
              </p>
              <a
                href={`/api/v1/cases/${caseData.id}/evidence-packet`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-4 py-2 text-sm rounded bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100"
              >
                Official route guidance →
              </a>
            </div>
          )}

          {/* UNAUTHORIZED */}
          {caseData.action === 'SECURITY_ESCALATION' && (
            <div className="space-y-2">
              <p className="text-xs text-red-800 bg-red-100 px-3 py-2 rounded border border-red-300 font-medium">
                Security escalation — stop normal recovery flow.
              </p>
              <p className="text-xs text-gray-500">
                Customer should contact their bank and use the official cybercrime/security process.
              </p>
            </div>
          )}
        </div>

        {/* Evidence timeline */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-4">
            Evidence ({caseData.evidence.length})
          </h3>
          {caseData.evidence.length === 0 ? (
            <p className="text-xs text-gray-400">No evidence attached.</p>
          ) : (
            <div className="space-y-3">
              {caseData.evidence.map((ev) => {
                const srcInfo = SOURCE_LABELS[ev.source_type] ?? {
                  label: ev.source_type,
                  color: 'bg-gray-100 text-gray-700',
                }
                return (
                  <div
                    key={ev.id}
                    className="flex items-start gap-3 text-sm border-l-2 border-gray-200 pl-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded font-medium ${srcInfo.color}`}
                        >
                          {srcInfo.label}
                        </span>
                        {ev.status && (
                          <span className="text-xs font-mono text-gray-600">
                            {ev.status}
                          </span>
                        )}
                      </div>
                      <div className="flex gap-3 mt-1 text-xs text-gray-500 flex-wrap">
                        {ev.event_reference && (
                          <span className="font-mono">{ev.event_reference}</span>
                        )}
                        {ev.amount_paise && (
                          <span>{formatPaise(ev.amount_paise)}</span>
                        )}
                        {ev.occurred_at && (
                          <span>{new Date(ev.occurred_at).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Audit trail */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-medium text-gray-900 mb-4">
            Audit trail ({caseData.audit_trail.length})
          </h3>
          {caseData.audit_trail.length === 0 ? (
            <p className="text-xs text-gray-400">No audit events.</p>
          ) : (
            <div className="space-y-3">
              {caseData.audit_trail.map((ae) => (
                <div
                  key={ae.id}
                  className="text-sm border-l-2 border-indigo-200 pl-3 space-y-0.5"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-medium text-xs text-gray-800">
                      {ae.event_type}
                    </span>
                    <span className="text-xs text-gray-400">by {ae.actor}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(ae.occurred_at).toLocaleString()}
                    </span>
                  </div>
                  {ae.prior_state && ae.new_state && (
                    <p className="text-xs text-gray-500 font-mono">
                      {ae.prior_state} → {ae.new_state}
                    </p>
                  )}
                  {ae.reason_codes && ae.reason_codes.length > 0 && (
                    <p className="text-xs text-gray-400">
                      {ae.reason_codes.join(' · ')}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
