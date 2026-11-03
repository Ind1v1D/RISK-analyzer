import { useI18n } from '../i18n/I18nContext.jsx'
import { useEscape } from '../lib/useEscape.js'

/** Settings dialog — currently the interface language (English / Русский / Қазақша). */
export default function SettingsModal({ onClose }) {
  const { t, lang, setLang, languages } = useI18n()
  useEscape(onClose)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={t('settings.title')}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="modal__title">{t('settings.title')}</h2>

        <h3 className="modal__section">{t('settings.language')}</h3>
        <div className="lang-options" role="radiogroup" aria-label={t('settings.language')}>
          {languages.map(({ code, label }) => (
            <button
              key={code}
              role="radio"
              aria-checked={lang === code}
              className={`lang-option${lang === code ? ' lang-option--active' : ''}`}
              onClick={() => setLang(code)}
            >
              <span>{label}</span>
              {lang === code && (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M5 12.5l4.5 4.5L19 7.5"
                    stroke="currentColor"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
            </button>
          ))}
        </div>
        <p className="modal__hint">{t('settings.languageHint')}</p>

        <button className="pill-btn modal__close" onClick={onClose}>
          {t('settings.close')}
        </button>
      </div>
    </div>
  )
}
