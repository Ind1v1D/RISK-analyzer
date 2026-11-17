import { describe, expect, it } from 'vitest'
import { locateFlags } from './spans.js'

const flag = (clause_text, risk_level = 'High') => ({ clause_text, risk_level, explanation: 'x' })
const slice = (text, span) => text.slice(span.start, span.end)

describe('locateFlags', () => {
  const doc = 'Intro. The Tenant shall pay all fees.  Late payment incurs 10% interest. End.'

  it('matches an exact clause', () => {
    const r = locateFlags(doc, [flag('Late payment incurs 10% interest.')])
    expect(r.spans).toHaveLength(1)
    expect(slice(doc, r.spans[0])).toBe('Late payment incurs 10% interest.')
    expect(r.notFound).toEqual([])
    expect(r.overlapped).toEqual([])
  })

  it('matches ignoring case and whitespace differences', () => {
    const r = locateFlags(doc, [flag('the  TENANT\n shall pay   all fees.')])
    expect(r.spans).toHaveLength(1)
    expect(slice(doc, r.spans[0])).toBe('The Tenant shall pay all fees.')
  })

  it('falls back to the first 80 characters', () => {
    const long = 'The supplier may terminate this agreement at any time without notice and without liability to the customer whatsoever.'
    const text = `Header. ${long} Footer.`
    const clause = `${long} And then some extra text the model invented.`
    const r = locateFlags(text, [flag(clause)])
    expect(r.spans).toHaveLength(1)
    expect(slice(text, r.spans[0]).startsWith('The supplier may terminate')).toBe(true)
    expect(r.notFound).toEqual([])
  })

  it('reports clauses that are not in the text', () => {
    const r = locateFlags(doc, [flag('Nothing like this appears'), flag('')])
    expect(r.spans).toEqual([])
    expect(r.notFound).toEqual([0, 1])
  })

  it('reports overlapping flags as overlapped, not missing', () => {
    const r = locateFlags(doc, [
      flag('The Tenant shall pay all fees.  Late payment'),
      flag('all fees. Late payment incurs 10% interest.'),
    ])
    expect(r.spans).toHaveLength(1)
    expect(r.spans[0].index).toBe(0)
    expect(r.notFound).toEqual([])
    expect(r.overlapped).toEqual([{ index: 1, hostIndex: 0 }])
    expect(r.hostOf.get(1)).toBe(0)
    expect(r.hostOf.get(0)).toBe(0)
  })

  it('keeps indices aligned when lowercasing changes length', () => {
    const text = 'İstanbul İS the place. Pay the penalty of 5000 now. Done.'
    const r = locateFlags(text, [flag('Pay the penalty of 5000 now.')])
    expect(r.spans).toHaveLength(1)
    expect(slice(text, r.spans[0])).toBe('Pay the penalty of 5000 now.')
    // and a clause that itself contains the special character
    const r2 = locateFlags(text, [flag('İstanbul İS the place.')])
    expect(slice(text, r2.spans[0])).toBe('İstanbul İS the place.')
  })

  it('handles empty input', () => {
    expect(locateFlags('', [flag('abc')]).notFound).toEqual([0])
    const r = locateFlags('some text', [])
    expect(r.spans).toEqual([])
    expect(r.notFound).toEqual([])
    expect(locateFlags(undefined, undefined).spans).toEqual([])
  })
})
