import InputCard from './InputCard.jsx'
import LoadingState from './LoadingState.jsx'
import '../styles/Hero.css'

/**
 * The landing hero: headline, the pill-shaped input card (the main call to
 * action), and the secondary CTAs — all vertically centered on the gradient
 * background. The loading state reuses the card shell so nothing jumps.
 */
export default function Hero({ loading, error, onRun, onExample, onHowItWorks }) {
  return (
    <section className="hero">
      <h1 className="hero__headline">Know what you&rsquo;re signing.</h1>
      <p className="hero__sub">
        Paste a contract or drop in a file — get a plain-language, clause-by-clause
        risk review in seconds.
      </p>

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
            See Example Analysis
          </button>
          <button className="pill-btn" onClick={onHowItWorks}>
            Learn How It Works
          </button>
        </div>
      )}
    </section>
  )
}
