// Thin wrapper around the backend endpoints. All network calls live here so
// components never touch fetch() directly.
//
// Every request carries the UI language (`lang`) so the backend can write the
// AI explanations and error messages in it.

/** Error with a machine-readable `code` so the UI can show a translated message. */
export class ApiError extends Error {
  constructor(code, message = '') {
    super(message)
    this.code = code // 'network' | 'server'
  }
}

const errorFrom = async (res) => {
  const data = await res.json().catch(() => ({}))
  return new ApiError('server', data.detail || '')
}

async function request(url, options) {
  try {
    return await fetch(url, options)
  } catch {
    throw new ApiError('network')
  }
}

/** POST the contract (file and/or pasted text) for analysis. Step 1 -> 5 of the pipeline. */
export async function analyzeContract({ file = null, text = '', lang = 'en' }) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (text) form.append('text', text)
  form.append('lang', lang)

  const res = await request('/api/analyze', { method: 'POST', body: form })
  if (!res.ok) throw await errorFrom(res)
  return res.json()
}

/** Fetch the bundled sample contract (used by "See Example Analysis"). */
export async function fetchSample(lang = 'en') {
  const res = await request(`/api/sample?lang=${encodeURIComponent(lang)}`)
  if (!res.ok) throw await errorFrom(res)
  return res.json()
}

/** Compare two pasted versions or two uploaded files. */
export async function compareContracts({ v1 = '', v2 = '', files = null }) {
  let res
  if (files?.[0] && files?.[1]) {
    const form = new FormData()
    form.append('v1', files[0])
    form.append('v2', files[1])
    res = await request('/api/compare/files', { method: 'POST', body: form })
  } else {
    res = await request('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ v1, v2 }),
    })
  }
  if (!res.ok) throw await errorFrom(res)
  return res.json()
}
