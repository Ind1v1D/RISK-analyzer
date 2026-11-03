// Step 5 of the pipeline, client side: find each flagged clause inside the
// original contract text so it can be highlighted inline.
//
// Matching is case-insensitive and whitespace-insensitive because the LLM may
// not reproduce spacing exactly. If a clause can't be located we return no
// span for it — the flag still appears in the side panel (graceful fallback).

function normalizeQuery(text) {
  return String(text || '').trim().toLowerCase().replace(/\s+/g, ' ')
}

export function locateFlags(fullText, flags = []) {
  // Build a normalized copy of the document (lowercase, single-spaced) while
  // mapping every normalized character back to its index in the original text.
  const map = []
  let norm = ''
  for (let i = 0; i < fullText.length; i += 1) {
    const ch = fullText[i]
    if (/\s/.test(ch)) {
      if (norm.length > 0 && !norm.endsWith(' ')) {
        norm += ' '
        map.push(i)
      }
    } else {
      norm += ch.toLowerCase()
      map.push(i)
    }
  }

  const spans = []
  flags.forEach((flag, index) => {
    const query = normalizeQuery(flag.clause_text)
    if (!query) return

    let at = norm.indexOf(query)
    let matchedLen = query.length
    if (at === -1) {
      // Fallback: match the beginning of the excerpt (in case the model
      // appended/trimmed a trailing sentence).
      const partial = query.slice(0, 80)
      at = norm.indexOf(partial)
      matchedLen = partial.length
      if (at === -1) return // not found -> panel-only flag
    }

    const start = map[at]
    const end = map[Math.min(at + matchedLen, map.length) - 1] + 1
    spans.push({ start, end, flag, index })
  })

  // Sort by position and drop overlapping spans (first one wins) so the
  // rendered document never nests <mark> elements.
  spans.sort((a, b) => a.start - b.start || a.end - b.end)
  const kept = []
  for (const span of spans) {
    const last = kept[kept.length - 1]
    if (last && span.start < last.end) continue
    kept.push(span)
  }
  return kept
}
