import InputCard from './InputCard.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'
import LoadingState from './LoadingState.jsx'
import '../styles/Hero.css'

/**
 * The landing hero: headline, the pill-shaped input card (the main call to
 * action), and the secondary CTAs — all vertically centered on the gradient
 * background. The loading state reuses the card shell so nothing jumps.
 */
export default function Hero({ loading, error, onRun, onExample, onHowItWorks }) {
  const { t } = useI18n()
  return (
    <section className="hero">
      <h1 className="hero__headline">{t('hero.headline')}</h1>
      <p className="hero__sub">{t('hero.sub')}</p>

      {error && (
        <div className="hero__error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <LoadingState />
      ) : (
        <InputCard onSubmit={onRun} />
      )}

      {!loading && (
        <div className="hero__ctas">
          <button className="pill-btn" onClick={onExample}>
            {t('hero.seeExample')}
          </button>
          <button className="pill-btn" onClick={onHowItWorks}>
            {t('hero.learnHow')}
          </button>
        </div>
      )}
    </section>
  )
}
