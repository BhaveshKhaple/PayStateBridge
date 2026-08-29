'use client'

import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SCREENSHOT_FIXTURES = [
  { value: 'phonepay_success_999', label: 'PhonePe — ₹999 success (synthetic)' },
  { value: 'phonepay_pending_499', label: 'PhonePe — ₹499 pending (synthetic)' },
  { value: 'gpay_failed_1499', label: 'Google Pay — ₹1,499 failed (synthetic)' },
]

interface ExtractionResult {
  extraction_status: string
  provider: string
  source_type: string
  trust_boundary: string
  extracted_fields: {
    reported_amount_paise: number | null
    reported_status: string | null
    utr_like_reference: string | null
    confidence_level: string
    missing_fields: string[]
    extraction_notes: string
  } | null
  error_message: string | null
  fallback_action: string | null
  safety_note: string
}

export function EvidenceIntakePanel({ caseId }: { caseId: string }) {
  const [mode, setMode] = useState<'text' | 'screenshot'>('text')
  const [text, setText] = useState('')
  const [fixture, setFixture] = useState(SCREENSHOT_FIXTURES[0].value)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleExtract() {
    setLoading(true)
    setError(null)
    setResult(null)

    const body =
      mode === 'text'
        ? { text }
        : { screenshot_fixture: fixture }

    try {
      const res = await fetch(`${API_URL}/v1/cases/${caseId}/extract-evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Extraction failed.')
      } else {
        setResult(data)
      }
    } catch {
      setError('Network error — is the API running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          AI Evidence Intake
        </h3>
        <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded border border-yellow-200">
          Untrusted customer evidence
        </span>
      </div>

      <p className="text-xs text-gray-500">
        AI extracts fields from customer text or synthetic screenshots.
        Output is always labelled untrusted — gateway evidence decides payment state.
      </p>

      {/* Mode selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setMode('text')}
          className={`px-3 py-1.5 text-xs rounded border ${
            mode === 'text'
              ? 'bg-gray-900 text-white border-gray-900'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          Customer text
        </button>
        <button
          onClick={() => setMode('screenshot')}
          className={`px-3 py-1.5 text-xs rounded border ${
            mode === 'screenshot'
              ? 'bg-gray-900 text-white border-gray-900'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          Synthetic screenshot
        </button>
      </div>

      {/* Input */}
      {mode === 'text' ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste synthetic customer message (e.g. 'My PhonePe shows ₹999 deducted. SYN-UTR-001.')"
          className="w-full text-sm border border-gray-200 rounded p-3 resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
          rows={4}
          maxLength={2000}
        />
      ) : (
        <select
          value={fixture}
          onChange={(e) => setFixture(e.target.value)}
          className="w-full text-sm border border-gray-200 rounded p-2 focus:outline-none focus:ring-1 focus:ring-gray-400"
        >
          {SCREENSHOT_FIXTURES.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      )}

      <button
        onClick={handleExtract}
        disabled={loading || (mode === 'text' && !text.trim())}
        className="px-4 py-2 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? 'Extracting…' : 'Extract fields'}
      </button>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-3">
          {/* Status + trust banner */}
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded border text-xs font-medium ${
              result.extraction_status === 'success'
                ? 'bg-green-50 text-green-700 border-green-200'
                : result.extraction_status === 'partial'
                ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                : 'bg-red-50 text-red-700 border-red-200'
            }`}
          >
            <span className="uppercase">{result.extraction_status}</span>
            <span className="ml-auto font-normal">
              via {result.provider}
            </span>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded px-3 py-2 text-xs text-amber-800">
            {result.safety_note}
          </div>

          {/* Extracted fields */}
          {result.extracted_fields && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-700">
                Extracted fields{' '}
                <span className="font-normal text-gray-400">
                  (confidence: {result.extracted_fields.confidence_level})
                </span>
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-50 rounded p-2">
                  <p className="text-gray-400">Amount (reported)</p>
                  <p className="font-mono text-gray-800 mt-0.5">
                    {result.extracted_fields.reported_amount_paise
                      ? `₹${(result.extracted_fields.reported_amount_paise / 100).toFixed(2)}`
                      : '—'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <p className="text-gray-400">Reported status</p>
                  <p className="font-mono text-gray-800 mt-0.5">
                    {result.extracted_fields.reported_status ?? '—'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded p-2 col-span-2">
                  <p className="text-gray-400">UTR-like reference</p>
                  <p className="font-mono text-gray-800 mt-0.5">
                    {result.extracted_fields.utr_like_reference ?? '—'}
                  </p>
                </div>
              </div>

              {result.extracted_fields.missing_fields.length > 0 && (
                <p className="text-xs text-gray-400">
                  Missing:{' '}
                  {result.extracted_fields.missing_fields.join(', ')}
                </p>
              )}
            </div>
          )}

          {/* Fallback notice for failures */}
          {result.fallback_action && (
            <p className="text-xs text-gray-500 bg-gray-50 rounded px-3 py-2">
              Extraction failed &rarr; fallback:{' '}
              <span className="font-mono font-medium">{result.fallback_action}</span>
            </p>
          )}

          {result.error_message && (
            <p className="text-xs text-red-600">{result.error_message}</p>
          )}
        </div>
      )}
    </div>
  )
}
