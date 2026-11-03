import { useMemo } from 'react'
import { locateFlags } from '../lib/spans.js'
import { useI18n } from '../i18n/I18nContext.jsx'

/**
 * Renders the original contract text with color-coded <mark> highlights around
 * each flagged clause (step 5 of the pipeline). Clicking a highlight selects
 * the matching flag in the side panel.
 */
export default function HighlightedText({ fullText, flags, activeIndex, onSelect }) {
  const { t } = useI18n()
  const spans = useMemo(() => locateFlags(fullText, flags), [fullText, flags])

  const nodes = []
  let cursor = 0
  for (const span of spans) {
    if (span.start > cursor) {
      nodes.push(<span key={`t${cursor}`}>{fullText.slice(cursor, span.start)}</span>)
    }
    nodes.push(
      <mark
        key={`m${span.index}`}
        id={`flag-${span.index}`}
        className={`mark mark--${span.flag.risk_level.toLowerCase()}${
          activeIndex === span.index ? ' mark--active' : ''
        }`}
        onClick={() => onSelect(span.index, 'mark')}
        title={t('mark.title', { risk: t(`risk.${span.flag.risk_level.toLowerCase()}`) })}
      >
        {fullText.slice(span.start, span.end)}
      </mark>,
    )
    cursor = span.end
  }
  if (cursor < fullText.length) {
    nodes.push(<span key={`t${cursor}`}>{fullText.slice(cursor)}</span>)
  }

  return <p className="doc-text">{nodes}</p>
}
