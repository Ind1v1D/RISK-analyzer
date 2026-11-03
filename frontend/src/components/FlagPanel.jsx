import { useI18n } from '../i18n/I18nContext.jsx'

/**
 * Side panel listing every flag: risk badge, the flagged excerpt (truncated),
 * and the plain-language explanation a non-lawyer can understand.
 * Entries are scroll-linked with the highlights in the document.
 */
export default function FlagPanel({ flags, activeIndex, onSelect, unmatchedCount }) {
  const { t } = useI18n()
  if (flags.length === 0) {
    return (
      <aside className="flag-panel">
        <div className="empty-state">
          <strong>{t('panel.emptyTitle')}</strong>
          <p>{t('panel.emptyBody')}</p>
        </div>
      </aside>
    )
  }

  return (
    <aside className="flag-panel">
      <div className="flag-panel__header">
        <h2 className="flag-panel__title">{t('panel.title', { count: flags.length })}</h2>
        <p className="flag-panel__notice">{t('panel.notice')}</p>
      </div>

      {flags.map((flag, i) => (
        <div
          key={i}
          id={`panel-${i}`}
          className={`flag-item${activeIndex === i ? ' flag-item--active' : ''}`}
          onClick={() => onSelect(i, 'panel')}
        >
          <div className="flag-item__head">
            <span className={`risk-badge risk-badge--${flag.risk_level.toLowerCase()}`}>
              {t(`risk.${flag.risk_level.toLowerCase()}`)}
            </span>
            <span className="flag-item__num">#{i + 1}</span>
          </div>
          <p className="flag-item__quote">“{flag.clause_text}”</p>
          <p className="flag-item__why">{flag.explanation}</p>
        </div>
      ))}

      {unmatchedCount > 0 && (
        <p className="flag-panel__footnote">{t('panel.unmatched', { count: unmatchedCount })}</p>
      )}
    </aside>
  )
}
