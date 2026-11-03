import { useEffect, useState } from 'react'

const STEPS = [
  'Reading your document…',
  'Identifying risky and unclear clauses…',
  'Writing plain-language explanations…',
]

/**
 * Loading state — rendered inside the same pill-card shell as InputCard so
 * the hero layout doesn't jump while the LLM call runs (often several seconds).
 */
export default function LoadingState() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStep((s) => (s + 1) % STEPS.length), 2200)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="input-card input-card--loading" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="loading__title">Reviewing your contract…</p>
      <p className="loading__step">{STEPS[step]}</p>
      <p className="loading__hint">This can take up to a minute when demand is high.</p>
    </div>
  )
}
