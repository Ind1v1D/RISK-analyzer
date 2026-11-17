import { useI18n } from '../i18n/I18nContext.jsx'

const asList = (v) => (Array.isArray(v) ? v.map((x) => String(x ?? '').trim()).filter(Boolean) : [])
const asText = (v) => (typeof v === 'string' ? v.trim() : '')

/** Normalizes a possibly missing / partial summary from the backend. */
export function cleanSummary(summary) {
  if (!summary || typeof summary !== 'object') return null
  const clean = {
    contractType: asText(summary.contract_type),
    parties: asList(summary.parties),
    overview: asText(summary.overview),
    keyTerms: asList(summary.key_terms),
  }
  const empty = !clean.contractType && !clean.overview && !clean.parties.length && !clean.keyTerms.length
  return empty ? null : clean
}

/** "Contract summary" card shown above the document / flag columns. */
export default function SummaryCard({ summary }) {
  const { t } = useI18n()
  const s = cleanSummary(summary)
  if (!s) return null

  return (
    <section className="summary-card" aria-labelledby="summary-title">
      <h2 id="summary-title" className="summary-card__title">
        {t('summary.title')}
      </h2>
      <dl className="summary-card__grid">
        {s.contractType && (
          <div>
            <dt>{t('summary.type')}</dt>
            <dd>{s.contractType}</dd>
          </div>
        )}
        {s.parties.length > 0 && (
          <div>
            <dt>{t('summary.parties')}</dt>
            <dd>{s.parties.join(' · ')}</dd>
          </div>
        )}
      </dl>
      {s.overview && (
        <div className="summary-card__block">
          <h3>{t('summary.overview')}</h3>
          <p>{s.overview}</p>
        </div>
      )}
      {s.keyTerms.length > 0 && (
        <div className="summary-card__block">
          <h3>{t('summary.keyTerms')}</h3>
          <ul>
            {s.keyTerms.map((term, i) => (
              <li key={i}>{term}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
