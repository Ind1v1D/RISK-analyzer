import { useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext.jsx'

const STEP_KEYS = ['loading.step1', 'loading.step2', 'loading.step3']

/**
 * Loading state — rendered inside the same pill-card shell as InputCard so
 * the hero layout doesn't jump while the LLM call runs (often several seconds).
 */
export default function LoadingState() {
  const { t } = useI18n()
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStep((s) => (s + 1) % STEP_KEYS.length), 2200)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="input-card input-card--loading" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="loading__title">{t('loading.title')}</p>
      <p className="loading__step">{t(STEP_KEYS[step])}</p>
      <p className="loading__hint">{t('loading.hint')}</p>
    </div>
  )
}
