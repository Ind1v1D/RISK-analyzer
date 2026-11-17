import { useMemo } from 'react'
import { cleanSummary } from './SummaryCard.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'
import '../styles/Print.css'

/**
 * Print-only report (hidden on screen, the only visible thing under
 * @media print). Used for "Download PDF report" -> window.print() -> Save as PDF.
 */
export default function PrintReport({ result, docName }) {
  const { t, lang } = useI18n()
  const flags = result.flags || []
  const summary = cleanSummary(result.summary)

  // Moment the results were shown.
  const generatedAt = useMemo(() => new Date(), [result])
  const when = useMemo(() => {
    try {
      return new Intl.DateTimeFormat(lang, { dateStyle: 'long', timeStyle: 'short' }).format(generatedAt)
    } catch {
      return generatedAt.toLocaleString()
    }
  }, [generatedAt, lang])

  const counts = { High: 0, Medium: 0, Low: 0 }
  flags.forEach((f) => {
    counts[f.risk_level] = (counts[f.risk_level] || 0) + 1
  })

  return (
    <article className="print-report" lang={lang}>
      <header className="pr-header">
        <h1>{t('print.title')}</h1>
        <p>{t('print.generated', { date: when })}</p>
        <p>{t('print.document', { name: docName || t('print.pasted') })}</p>
      </header>

      <p className="pr-disclaimer">
        <strong>{t('results.banner.title')}</strong> {t('results.banner.body')}
      </p>

      <p className="pr-counts">
        {t('results.countHigh', { count: counts.High })} · {t('results.countMedium', { count: counts.Medium })} ·{' '}
        {t('results.countLow', { count: counts.Low })}
      </p>

      {summary && (
        <section className="pr-summary">
          <h2>{t('summary.title')}</h2>
          {summary.contractType && (
            <p>
              <strong>{t('summary.type')}:</strong> {summary.contractType}
            </p>
          )}
          {summary.parties.length > 0 && (
            <p>
              <strong>{t('summary.parties')}:</strong> {summary.parties.join('; ')}
            </p>
          )}
          {summary.overview && (
            <p>
              <strong>{t('summary.overview')}:</strong> {summary.overview}
            </p>
          )}
          {summary.keyTerms.length > 0 && (
            <>
              <p>
                <strong>{t('summary.keyTerms')}:</strong>
              </p>
              <ul>
                {summary.keyTerms.map((term, i) => (
                  <li key={i}>{term}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      <h2 className="pr-flags-title">{t('panel.title', { count: flags.length })}</h2>
      {flags.length === 0 && <p>{t('panel.emptyBody')}</p>}
      {flags.map((flag, i) => (
        <section key={i} className={`pr-flag pr-flag--${String(flag.risk_level).toLowerCase()}`}>
          <h3>
            #{i + 1} — {t(`risk.${String(flag.risk_level).toLowerCase()}`)}
          </h3>
          <blockquote>“{flag.clause_text}”</blockquote>
          <p>{flag.explanation}</p>
        </section>
      ))}

      <footer className="pr-footer">{t('disclaimer.text')}</footer>
    </article>
  )
}
