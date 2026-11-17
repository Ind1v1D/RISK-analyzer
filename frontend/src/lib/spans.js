// Step 5 of the pipeline, client side: find each flagged clause inside the
// original contract text so it can be highlighted inline.
//
// Matching is case-insensitive and whitespace-insensitive because the LLM may
// not reproduce spacing exactly. A flag that can't be located is reported in
// `notFound` (it still appears in the side panel). A flag that is located but
// overlaps an earlier highlight is reported in `overlapped` together with the
// index of the highlight that covers it, so the panel can still scroll to it.

/**
 * Lowercase + collapse whitespace, one source character at a time. Lowercasing
 * per character matters: some characters change length when lowercased
 * ('İ' -> 'i̇', two code units), which would desync a whole-string lowercase
 * from the index map. Every produced character maps back to its source index.
 */
function normalize(text) {
  const map = []
  let norm = ''
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i]
    if (/\s/.test(ch)) {
      if (norm.length > 0 && !norm.endsWith(' ')) {
        norm += ' '
        map.push(i)
      }
    } else {
      for (const out of ch.toLowerCase()) {
        norm += out
        map.push(i)
      }
    }
  }
  return { norm, map }
}

/**
 * @returns {{
 *   spans: {start:number,end:number,flag:object,index:number}[],  // non-overlapping, sorted
 *   notFound: number[],                                           // flag indices with no match
 *   overlapped: {index:number, hostIndex:number}[],               // matched but merged into another mark
 *   hostOf: Map<number, number>,                                  // flag index -> index of the mark that shows it
 * }}
 */
export function locateFlags(fullText, flags = []) {
  const text = String(fullText || '')
  const { norm, map } = normalize(text)

  const found = []
  const notFound = []
  flags.forEach((flag, index) => {
    let query = normalize(String(flag?.clause_text || '')).norm
    if (query.endsWith(' ')) query = query.slice(0, -1)
    if (!query) {
      notFound.push(index)
      return
    }

    let at = norm.indexOf(query)
    let matchedLen = query.length
    if (at === -1) {
      // Fallback: match the beginning of the excerpt (in case the model
      // appended/trimmed a trailing sentence).
      const partial = query.slice(0, 80)
      at = norm.indexOf(partial)
      matchedLen = partial.length
      if (at === -1) {
        notFound.push(index)
        return
      }
    }

    const start = map[at]
    const end = map[Math.min(at + matchedLen, map.length) - 1] + 1
    found.push({ start, end, flag, index })
  })

  // Sort by position and drop overlapping spans (first one wins) so the
  // rendered document never nests <mark> elements.
  found.sort((a, b) => a.start - b.start || a.end - b.end)
  const spans = []
  const overlapped = []
  const hostOf = new Map()
  for (const span of found) {
    const last = spans[spans.length - 1]
    if (last && span.start < last.end) {
      overlapped.push({ index: span.index, hostIndex: last.index })
      hostOf.set(span.index, last.index)
      continue
    }
    spans.push(span)
    hostOf.set(span.index, span.index)
  }
  overlapped.sort((a, b) => a.index - b.index)
  notFound.sort((a, b) => a - b)
  return { spans, notFound, overlapped, hostOf }
}
