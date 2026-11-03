// Thin wrapper around the backend endpoints. All network calls live here so
// components never touch fetch() directly.

const errorFrom = async (res) => {
  const data = await res.json().catch(() => ({}))
  return new Error(data.detail || 'Something went wrong while analyzing the contract.')
}

/** POST the contract (file and/or pasted text) for analysis. Step 1 -> 5 of the pipeline. */
export async function analyzeContract({ file = null, text = '' }) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (text) form.append('text', text)

  const res = await fetch('/api/analyze', { method: 'POST', body: form })
  if (!res.ok) throw await errorFrom(res)
  return res.json()
}

/** Fetch the bundled sample contract (used by "See Example Analysis"). */
export async function fetchSample() {
  const res = await fetch('/api/sample')
  if (!res.ok) throw await errorFrom(res)
  return res.json()
}
