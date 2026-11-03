import { useMemo, useState } from 'react'
import HighlightedText from './HighlightedText.jsx'
import FlagPanel from './FlagPanel.jsx'
import { locateFlags } from '../lib/spans.js'
import { useI18n } from '../i18n/I18nContext.jsx'
import '../styles/Results.css'

/**
 * Results screen — intentionally denser than the landing hero:
 * two columns, highlighted contract on the left, flag-by-flag explanations on
 * the right, scroll-linked in both directions.
 */
export default function Results({ result, onReset }) {
  const { t } = useI18n()
  const { full_text: fullText, flags } = result
  const [activeIndex, setActiveIndex] = useState(null)

  // Same span computation as HighlightedText — used to count unmatched flags.
  const matchedCount = useMemo(() => locateFlags(fullText, flags).length, [fullText, flags])
  const unmatchedCount = flags.length - matchedCount

  const counts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 }
    flags.forEach((f) => {
      c[f.risk_level] = (c[f.risk_level] || 0) + 1
    })
    return c
  }, [flags])

  /** Select a flag and scroll the *other* column to it. */
  function select(index, from) {
    setActiveIndex(index)
    const target =
      from === 'panel' ? document.getElementById(`flag-${index}`) : document.getElementById(`panel-${index}`)
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <section className="results">
      <header className="results__bar">
        <div>
          <h1 className="results__title">{t('results.title')}</h1>
          <div className="results__counts">
            <span className="count-pill count-pill--high">{t('results.countHigh', { count: counts.High })}</span>
            <span className="count-pill count-pill--medium">{t('results.countMedium', { count: counts.Medium })}</span>
            <span className="count-pill count-pill--low">{t('results.countLow', { count: counts.Low })}</span>
          </div>
        </div>
        <button className="btn-primary" onClick={onReset}>
          {t('results.again')}
        </button>
      </header>

      <div className="results__grid">
        <section className="doc-panel">
          <p className="doc-panel__label">{t('results.docLabel')}</p>
          <HighlightedText
            fullText={fullText}
            flags={flags}
            activeIndex={activeIndex}
            onSelect={select}
          />
        </section>

        <FlagPanel
          flags={flags}
          activeIndex={activeIndex}
          onSelect={select}
          unmatchedCount={unmatchedCount}
        />
      </div>
    </section>
  )
}
