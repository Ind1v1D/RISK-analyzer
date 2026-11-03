import { useI18n } from '../i18n/I18nContext.jsx'
import { useEscape } from '../lib/useEscape.js'

/** Non-blocking explainer opened from "Learn How It Works" / the navbar. */
export default function HowItWorksModal({ onClose }) {
  const { t } = useI18n()
  useEscape(onClose)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={t('how.title')}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="modal__title">{t('how.title')}</h2>
        <ol className="modal__steps">
          <li>
            <strong>{t('how.step1.title')}</strong> {t('how.step1.body')}
          </li>
          <li>
            <strong>{t('how.step2.title')}</strong> {t('how.step2.body')}
          </li>
          <li>
            <strong>{t('how.step3.title')}</strong> {t('how.step3.body')}
          </li>
        </ol>
        <p className="modal__note">{t('how.note')}</p>
        <button className="pill-btn modal__close" onClick={onClose}>
          {t('how.close')}
        </button>
      </div>
    </div>
  )
}
