import { useMemo, useState } from 'react'
import HighlightedText from './HighlightedText.jsx'
import FlagPanel from './FlagPanel.jsx'
import SummaryCard from './SummaryCard.jsx'
import { locateFlags } from '../lib/spans.js'
import { useI18n } from '../i18n/I18nContext.jsx'
import '../styles/Results.css'

const pad = (n) => String(n).padStart(2, '0')

/** Opens the browser print dialog with a dated document title (-> PDF file name). */
function printReport() {
  const d = new Date()
  const previous = document.title
  document.title = `ClauseCheck-report-${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  const restore = () => {
    document.title = previous
    window.removeEventListener('afterprint', restore)
  }
  window.addEventListener('afterprint', restore)
  window.print()
}

/**
 * Results screen — intentionally denser than the landing hero:
 * two columns, highlighted contract on the left, flag-by-flag explanations on
 * the right, scroll-linked in both directions.
 */
export default function Results({ result, onReset }) {
  const { t } = useI18n()
  const { full_text: fullText, flags } = result
  const [activeIndex, setActiveIndex] = useState(null)

  const located = useMemo(() => locateFlags(fullText, flags), [fullText, flags])
  // Only flags that truly couldn't be found; overlapped ones are still highlighted.
  const unmatchedCount = located.notFound.length
  // The mark that visually represents the selected flag (itself, or the one it overlaps).
  const activeMark = activeIndex === null ? null : (located.hostOf.get(activeIndex) ?? null)

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
    const markIndex = located.hostOf.get(index) ?? index
    const target =
      from === 'panel' ? document.getElementById(`flag-${markIndex}`) : document.getElementById(`panel-${index}`)
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
        <div className="results__actions">
          <button className="btn-secondary" onClick={printReport}>
            {t('results.download')}
          </button>
          <button className="btn-primary" onClick={onReset}>
            {t('results.again')}
          </button>
        </div>
      </header>

      <div className="results__banner" role="note">
        <p>
          <strong>{t('results.banner.title')}</strong> {t('results.banner.body')}
        </p>
      </div>

      <SummaryCard summary={result.summary} />

      <div className="results__grid">
        <section className="doc-panel">
          <p className="doc-panel__label">{t('results.docLabel')}</p>
          <HighlightedText
            fullText={fullText}
            spans={located.spans}
            activeIndex={activeMark}
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
