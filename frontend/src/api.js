// Thin wrapper around the backend endpoints. All network calls live here so
// components never touch fetch() directly.
//
// Every request carries the UI language (`lang`) so the backend can write the
// AI explanations and error messages in it.

// Optional API origin for split deployments (e.g. https://api.example.com).
const API_BASE = (import.meta.env?.VITE_API_BASE || '').replace(/\/+$/, '')

// Analysis can take a while when the model is busy; give up after this long.
export const REQUEST_TIMEOUT_MS = 150_000

/** Error with a machine-readable `code` so the UI can show a translated message. */
export class ApiError extends Error {
  constructor(code, message = '', extra = {}) {
    super(message)
    this.code = code // 'network' | 'timeout' | 'aborted' | 'server'
    this.status = extra.status ?? null
    this.retryAfter = extra.retryAfter ?? null // seconds, from the Retry-After header
  }
}

function parseRetryAfter(res) {
  const n = Number.parseInt(res.headers.get('Retry-After') ?? '', 10)
  return Number.isFinite(n) && n > 0 ? n : null
}

/**
 * fetch + JSON body, with a timeout and an optional caller-supplied AbortSignal.
 * Throws ApiError: 'aborted' (caller cancelled), 'timeout', 'network', 'server'.
 */
async function request(path, options = {}, signal = null) {
  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, REQUEST_TIMEOUT_MS)
  const onAbort = () => controller.abort()
  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', onAbort, { once: true })
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new ApiError('server', typeof data.detail === 'string' ? data.detail : '', {
        status: res.status,
        retryAfter: parseRetryAfter(res),
      })
    }
    return await res.json()
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (timedOut) throw new ApiError('timeout')
    if (signal?.aborted) throw new ApiError('aborted')
    throw new ApiError('network')
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', onAbort)
  }
}

/** POST the contract (file and/or pasted text) for analysis. Step 1 -> 5 of the pipeline. */
export function analyzeContract({ file = null, text = '', lang = 'en', signal = null }) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (text) form.append('text', text)
  form.append('lang', lang)
  return request(`/api/analyze?lang=${encodeURIComponent(lang)}`, { method: 'POST', body: form }, signal)
}

/** Fetch the bundled sample contract (used by "See Example Analysis"). */
export function fetchSample(lang = 'en', signal = null) {
  return request(`/api/sample?lang=${encodeURIComponent(lang)}`, {}, signal)
}
