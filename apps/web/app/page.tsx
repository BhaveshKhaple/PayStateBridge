export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="max-w-2xl w-full space-y-8 text-center">
        {/* Demo badge */}
        <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 text-sm font-medium px-3 py-1 rounded-full border border-amber-200">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
          Synthetic data · Razorpay Test Mode only · Portfolio prototype
        </div>

        {/* Heading */}
        <div className="space-y-3">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">
            PayState Bridge
          </h1>
          <p className="text-xl text-gray-600">
            Resolves a customer&apos;s ambiguous payment before a merchant asks
            them to pay again.
          </p>
        </div>

        {/* Core law */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-mono text-red-700">
            Resolve before retry. Never generate a replacement payment link
            while the first payment is pending or outcome-unknown.
          </p>
        </div>

        {/* Track info */}
        <div className="flex flex-wrap justify-center gap-3 text-sm text-gray-500">
          <span className="bg-gray-100 px-3 py-1 rounded">
            Razorpay AI Buildathon
          </span>
          <span className="bg-gray-100 px-3 py-1 rounded">
            Track 03 — AI Revenue Recovery
          </span>
          <span className="bg-gray-100 px-3 py-1 rounded">
            Deadline: 05/09/2026
          </span>
        </div>

        {/* Status */}
        <p className="text-sm text-gray-400">
          API status:{' '}
          <code className="bg-gray-100 px-1 rounded">
            GET http://localhost:8000/health
          </code>
        </p>
      </div>
    </main>
  )
}
